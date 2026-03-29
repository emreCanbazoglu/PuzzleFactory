#!/usr/bin/env python3
"""
Prototype Iteration Loop — Spec 014

Runs a closed feedback loop after prototype_builder_web generates prototype.html:
  1. Load in headless Playwright browser — capture JS errors + DOM checks
  2. Code-review critique — send HTML source + prototype spec to Claude CLI as text
  3. Claude CLI patches the HTML targeting identified failures
  4. Repeat until passing or budget exhausted
"""
from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from agent_runtime import call_provider, now_iso, write_metadata

RUBRIC_CRITERIA = [
    "board_visible",
    "elements_present",
    "interactive_hint",
    "state_changed",
    "readable",
]

CODE_REVIEW_PROMPT_TEMPLATE = """You are reviewing a puzzle game prototype HTML file for playability.

PROTOTYPE SPEC (what the game should do):
{spec_section}

CONSOLE ERRORS from running the prototype in a headless browser:
{errors_section}

DOM STRUCTURAL CHECKS (from Playwright):
{dom_checks_section}

CURRENT PROTOTYPE HTML SOURCE:
```html
{html_source}
```

Evaluate the prototype against these 5 criteria and return ONLY valid JSON:

{{
  "board_visible":     "pass" | "fail" | "unclear",
  "elements_present":  "pass" | "fail" | "unclear",
  "interactive_hint":  "pass" | "fail" | "unclear",
  "state_changed":     "pass" | "fail" | "unclear",
  "readable":          "pass" | "fail" | "unclear",
  "notes": "<one sentence identifying the most critical missing or broken thing>"
}}

Criteria:
- board_visible:    HTML renders a visible game board or canvas with actual game content
- elements_present: Game objects (dock, queue, board cells, pieces) are rendered in the DOM
- interactive_hint: At least one button or tappable/clickable element exists and is functional
- state_changed:    Clicking an interactive element changes game state (DOM or canvas updates)
- readable:         Game layout is not a blank page, placeholder text, or unstyled skeleton

Output raw JSON only — no markdown, no explanation."""

PATCH_PROMPT_TEMPLATE = """You are fixing a puzzle game prototype HTML file.

FAILED CRITERIA:
{failed_criteria}

CONSOLE ERRORS:
{errors_section}

CRITIC NOTES:
{critic_notes}

CURRENT PROTOTYPE HTML (may be truncated to {max_chars} chars):
```html
{html_source}
```

Produce a corrected and improved version of the complete prototype HTML that fixes every \
failed criterion above. The prototype must:
- Render an actual game board with visible grid or play area
- Show interactive elements the player can tap/click
- Update game state visibly when the player interacts
- Have no JS runtime errors

Output ONLY the complete corrected HTML file starting with <!doctype html>.
No markdown fencing, no explanation — raw HTML only."""


# ─── Data classes ─────────────────────────────────────────────────────────────

@dataclass
class BrowserResult:
    errors: list[str]
    dom_checks: dict[str, str]          # criterion → "pass" | "fail" | "unclear"
    state_changed: str                  # "pass" | "fail" | "unclear"
    playwright_available: bool = True


@dataclass
class CritiqueResult:
    criteria: dict[str, str] = field(default_factory=dict)
    pass_count: int = 0
    notes: str = ""
    available: bool = True


# ─── T2: Browser check (DOM-based, no vision) ─────────────────────────────────

def _run_browser_check(html_path: Path, round_dir: Path) -> BrowserResult:
    """Load prototype in headless Chromium, capture JS errors and DOM checks."""
    try:
        from playwright.sync_api import sync_playwright  # noqa: PLC0415
    except ImportError:
        return BrowserResult(errors=[], dom_checks={}, state_changed="unclear",
                             playwright_available=False)

    errors: list[str] = []
    dom_checks: dict[str, str] = {}

    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)
            page = browser.new_page(viewport={"width": 480, "height": 800})

            page.on("console", lambda msg: errors.append(f"[{msg.type}] {msg.text}")
                    if msg.type in ("error", "warning") else None)
            page.on("pageerror", lambda err: errors.append(f"[pageerror] {err}"))

            page.goto(f"file://{html_path.resolve()}")
            page.wait_for_timeout(1500)

            # board_visible: canvas or element with board/grid/game in id/class
            has_canvas = page.locator("canvas").count() > 0
            has_board_el = page.locator("[id*=board],[id*=grid],[id*=game],[class*=board],[class*=grid],[class*=game]").count() > 0
            dom_checks["board_visible"] = "pass" if (has_canvas or has_board_el) else "fail"

            # elements_present: game objects in DOM
            has_cells = page.locator("[class*=cell],[class*=node],[class*=dock],[class*=piece],[class*=slot],[class*=queue]").count() > 0
            has_svg = page.locator("svg").count() > 0
            dom_checks["elements_present"] = "pass" if (has_cells or has_svg or has_canvas) else "fail"

            # interactive_hint: at least one button or clickable element
            btn_count = page.locator("button:visible, [onclick]:visible, [class*=btn]:visible").count()
            dom_checks["interactive_hint"] = "pass" if btn_count > 0 else "fail"

            # readable: page has meaningful text content (not blank)
            body_text = (page.locator("body").inner_text() or "").strip()
            dom_checks["readable"] = "pass" if len(body_text) > 20 else "fail"

            # state_changed: snapshot DOM/canvas hash before and after a click
            pre_snapshot = page.locator("body").inner_html()
            try:
                if btn_count > 0:
                    page.locator("button:visible").first.click(timeout=1500)
                else:
                    box = page.locator("canvas").bounding_box() if has_canvas else None
                    if box:
                        page.mouse.click(box["x"] + box["width"] / 2,
                                         box["y"] + box["height"] / 2)
            except Exception:
                pass
            page.wait_for_timeout(600)
            post_snapshot = page.locator("body").inner_html()
            state_changed = "pass" if pre_snapshot != post_snapshot else "fail"

            browser.close()

    except Exception as exc:  # noqa: BLE001
        errors.append(f"[playwright_error] {exc}")
        return BrowserResult(errors=errors, dom_checks={}, state_changed="unclear")

    (round_dir / "console_errors.json").write_text(
        json.dumps(errors, indent=2) + "\n", encoding="utf-8"
    )
    (round_dir / "dom_checks.json").write_text(
        json.dumps(dom_checks, indent=2) + "\n", encoding="utf-8"
    )

    return BrowserResult(errors=errors, dom_checks=dom_checks, state_changed=state_changed)


# ─── T3: Code review critique ─────────────────────────────────────────────────

def _run_code_review_critique(
    html_path: Path,
    browser_result: BrowserResult,
    round_dir: Path,
    profile: dict[str, str],
    config: dict[str, Any],
    spec_path: Path | None,
) -> CritiqueResult:
    """Send HTML source + DOM check results to Claude CLI for code-level critique."""

    # Build spec section
    spec_section = "(no prototype_spec.md found)"
    if spec_path and spec_path.exists():
        spec_text = spec_path.read_text(encoding="utf-8")
        spec_section = spec_text[:3000] + ("\n[spec truncated]" if len(spec_text) > 3000 else "")

    # Build HTML section
    html_source = html_path.read_text(encoding="utf-8")
    max_chars = 5000
    html_section = html_source[:max_chars] + (f"\n<!-- [truncated at {max_chars} chars] -->"
                                              if len(html_source) > max_chars else "")

    # DOM checks summary
    dom_lines = [f"- {k}: {v}" for k, v in browser_result.dom_checks.items()]
    dom_checks_section = "\n".join(dom_lines) if dom_lines else "(playwright unavailable)"

    errors_section = "\n".join(browser_result.errors[:20]) or "(none)"

    prompt = CODE_REVIEW_PROMPT_TEMPLATE.format(
        spec_section=spec_section,
        errors_section=errors_section,
        dom_checks_section=dom_checks_section,
        html_source=html_section,
    )

    # Save prompt for audit
    (round_dir / "critique_prompt.txt").write_text(prompt, encoding="utf-8")

    try:
        raw = call_provider(profile, prompt)
    except Exception as exc:  # noqa: BLE001
        return CritiqueResult(available=False, notes=f"provider error: {exc}")

    # Merge DOM checks with LLM critique
    criteria: dict[str, str] = {}
    notes = ""
    try:
        start = raw.find("{")
        end = raw.rfind("}")
        if start != -1 and end > start:
            parsed = json.loads(raw[start:end + 1])
            for key in RUBRIC_CRITERIA:
                criteria[key] = parsed.get(key, "unclear")
            notes = parsed.get("notes", "")
    except (json.JSONDecodeError, ValueError):
        # Fall back to DOM checks only
        criteria = dict(browser_result.dom_checks)
        criteria["state_changed"] = browser_result.state_changed
        notes = "failed to parse LLM critique — using DOM checks only"

    # Override state_changed with the actual Playwright measurement (more reliable)
    if browser_result.playwright_available and browser_result.state_changed != "unclear":
        criteria["state_changed"] = browser_result.state_changed

    pass_count = sum(1 for v in criteria.values() if v == "pass")

    (round_dir / "critique.json").write_text(
        json.dumps({"criteria": criteria, "pass_count": pass_count, "notes": notes},
                   indent=2) + "\n",
        encoding="utf-8",
    )

    return CritiqueResult(criteria=criteria, pass_count=pass_count, notes=notes)


# ─── T4: Patch prototype ──────────────────────────────────────────────────────

def _patch_prototype(
    html_path: Path,
    browser_result: BrowserResult,
    critique: CritiqueResult,
    profile: dict[str, str],
    config: dict[str, Any],
) -> str:
    """Ask Claude to rewrite the prototype fixing failed criteria."""
    current_html = html_path.read_text(encoding="utf-8")
    max_chars = 6000
    html_source = (current_html[:max_chars] + f"\n<!-- [truncated at {max_chars} chars] -->"
                   if len(current_html) > max_chars else current_html)

    failed = [k for k, v in critique.criteria.items() if v == "fail"]
    failed_criteria = "\n".join(f"- {c}" for c in failed) if failed else "(none)"
    errors_section = "\n".join(browser_result.errors[:20]) or "(none)"

    prompt = PATCH_PROMPT_TEMPLATE.format(
        failed_criteria=failed_criteria,
        errors_section=errors_section,
        critic_notes=critique.notes,
        max_chars=max_chars,
        html_source=html_source,
    )

    try:
        raw = call_provider(profile, prompt).strip()
    except Exception:  # noqa: BLE001
        return current_html

    for marker in ("<!doctype", "<!DOCTYPE", "<html", "<HTML"):
        idx = raw.find(marker)
        if idx != -1:
            end_idx = raw.lower().rfind("</html>")
            if end_idx != -1:
                return raw[idx:end_idx + 7]
            return raw[idx:]

    return current_html


# ─── T5: Main loop ────────────────────────────────────────────────────────────

def run_iteration_loop(
    *,
    html_path: Path,
    repo_root: Path,
    wave_id: str,
    cell_id: str,
    iteration_config: dict[str, Any],
    profile: dict[str, str],
    config: dict[str, Any],
    spec_path: Path | None = None,
) -> dict[str, Any]:
    """
    Run the prototype iteration loop.
    Returns a result dict with keys: rounds_run, passed, final_path, log_path.
    """
    max_rounds: int = iteration_config.get("max_rounds", 4)
    levels: list[str] = iteration_config.get("levels", ["errors", "visual"])
    budget_seconds: float = float(iteration_config.get("budget_seconds", 300))
    pass_threshold: int = int(iteration_config.get("pass_threshold", 4))

    iterations_dir = html_path.parent / "iterations"
    iterations_dir.mkdir(parents=True, exist_ok=True)

    log_rows: list[dict[str, Any]] = []
    passed = False
    start_time = time.monotonic()

    for round_num in range(1, max_rounds + 1):
        round_label = f"round_{round_num:02d}"
        round_dir = iterations_dir / round_label
        round_dir.mkdir(parents=True, exist_ok=True)

        # Level 1 + DOM checks via Playwright
        browser_result = BrowserResult(errors=[], dom_checks={}, state_changed="unclear",
                                       playwright_available=False)
        if "errors" in levels or "visual" in levels:
            browser_result = _run_browser_check(html_path, round_dir)

        l1_errors = len(browser_result.errors)
        l1_pass = l1_errors == 0 and browser_result.playwright_available

        # Level 2 — code review critique
        critique = CritiqueResult(available=False)
        if "visual" in levels:
            critique = _run_code_review_critique(
                html_path, browser_result, round_dir, profile, config, spec_path
            )

        l2_pass_count = critique.pass_count if critique.available else None

        # Determine round result
        if not browser_result.playwright_available:
            round_passed = True
            decision = "skip_no_playwright"
        elif "visual" in levels:
            round_passed = l1_pass and critique.available and critique.pass_count >= pass_threshold
            decision = "pass" if round_passed else "patch"
        else:
            round_passed = l1_pass
            decision = "pass" if round_passed else "patch"

        log_rows.append({
            "round": round_num,
            "l1_errors": l1_errors if browser_result.playwright_available else "n/a",
            "l2_pass_count": l2_pass_count if critique.available else "n/a",
            "decision": decision,
            "notes": (critique.notes if critique.available else
                      ("playwright unavailable" if not browser_result.playwright_available else "")),
        })

        if round_passed:
            passed = True
            break

        if time.monotonic() - start_time >= budget_seconds:
            log_rows[-1]["decision"] = "budget_exceeded"
            break

        # Patch and write for next round
        if round_num < max_rounds:
            patched_html = _patch_prototype(html_path, browser_result, critique, profile, config)
            (round_dir / "prototype_patched.html").write_text(patched_html, encoding="utf-8")
            html_path.write_text(patched_html, encoding="utf-8")

    # Write iteration_log.md
    log_path = iterations_dir / "iteration_log.md"
    _write_iteration_log(log_path, log_rows, wave_id, cell_id)

    meta_path = Path(str(log_path) + ".metadata.json")
    write_metadata(
        metadata_path=meta_path,
        wave_id=wave_id,
        cell_id=cell_id,
        role="prototype_iterator",
        template_name="iteration_log_builtin",
        profile=profile,
        artifact_path=log_path,
        fallback_used=not passed,
    )

    return {
        "rounds_run": len(log_rows),
        "passed": passed,
        "final_path": str(html_path),
        "log_path": str(log_path),
    }


def _write_iteration_log(
    log_path: Path,
    rows: list[dict[str, Any]],
    wave_id: str,
    cell_id: str,
) -> None:
    lines = [
        f"# Prototype Iteration Log — {wave_id} / {cell_id}",
        "",
        f"Generated: {now_iso()}",
        "",
        "| Round | L1 Errors | L2 Pass Count | Decision | Notes |",
        "|-------|-----------|---------------|----------|-------|",
    ]
    for row in rows:
        lines.append(
            f"| {row['round']} "
            f"| {row['l1_errors']} "
            f"| {row['l2_pass_count']} "
            f"| {row['decision']} "
            f"| {row['notes']} |"
        )
    log_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
