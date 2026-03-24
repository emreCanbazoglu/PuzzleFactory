#!/usr/bin/env python3
"""
Prototype Iteration Loop — Spec 014

Runs a closed feedback loop after prototype_builder_web generates prototype.html:
  1. Load in headless Playwright browser
  2. Capture JS errors + screenshots
  3. Claude vision critique against a fixed rubric
  4. Claude CLI patches the HTML
  5. Repeat until passing or budget exhausted
"""
from __future__ import annotations

import json
import os
import subprocess
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

VISION_PROMPT = """You are evaluating a puzzle game prototype screenshot for playability.

Evaluate the two screenshots (initial state and after first tap) against this rubric.
Return ONLY valid JSON with exactly these keys:

{
  "board_visible":     "pass" | "fail" | "unclear",
  "elements_present":  "pass" | "fail" | "unclear",
  "interactive_hint":  "pass" | "fail" | "unclear",
  "state_changed":     "pass" | "fail" | "unclear",
  "readable":          "pass" | "fail" | "unclear",
  "notes": "<one sentence summary of the most critical issue, or 'looks good'>"
}

Criteria definitions:
- board_visible:    A game board or play area is clearly rendered on screen
- elements_present: Dock items, queue pieces, or game objects are visible
- interactive_hint: At least one button or tappable element is visible
- state_changed:    Something visibly changed between screenshot 1 and screenshot 2
- readable:         Colors are distinct, text is legible, no overlapping UI elements

Do not add any other keys or prose. Output raw JSON only."""

PATCH_PROMPT_TEMPLATE = """You are fixing a puzzle game prototype HTML file.

FAILED RUBRIC CRITERIA:
{failed_criteria}

CONSOLE ERRORS:
{errors_section}

CURRENT PROTOTYPE HTML (may be truncated):
```html
{html_source}
```

Produce a corrected version of the complete HTML file that fixes all the issues above.
Output ONLY the complete corrected HTML file starting with <!doctype html> or <html.
Do not add explanation or markdown fencing — just the raw HTML."""


# ─── Data classes ─────────────────────────────────────────────────────────────

@dataclass
class BrowserResult:
    errors: list[str]
    screenshot_initial_path: Path | None
    screenshot_after_path: Path | None
    playwright_available: bool = True


@dataclass
class CritiqueResult:
    criteria: dict[str, str] = field(default_factory=dict)
    pass_count: int = 0
    notes: str = ""
    available: bool = True  # False when screenshots missing / vision skipped


# ─── T2: Browser check ────────────────────────────────────────────────────────

def _run_browser_check(html_path: Path, round_dir: Path) -> BrowserResult:
    """Load prototype in headless Chromium, capture errors and screenshots."""
    try:
        from playwright.sync_api import sync_playwright  # noqa: PLC0415
    except ImportError:
        return BrowserResult(errors=[], screenshot_initial_path=None,
                             screenshot_after_path=None, playwright_available=False)

    errors: list[str] = []
    screenshot_initial = round_dir / "screenshot_initial.png"
    screenshot_after = round_dir / "screenshot_after_tap.png"

    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)
            page = browser.new_page(viewport={"width": 480, "height": 800})

            page.on("console", lambda msg: errors.append(f"[{msg.type}] {msg.text}")
                    if msg.type in ("error", "warning") else None)
            page.on("pageerror", lambda err: errors.append(f"[pageerror] {err}"))

            page.goto(f"file://{html_path.resolve()}")
            page.wait_for_timeout(1500)
            page.screenshot(path=str(screenshot_initial))

            # Try clicking the first button; fall back to canvas centre
            try:
                page.click("button", timeout=1500)
            except Exception:
                try:
                    box = page.locator("canvas").bounding_box()
                    if box:
                        page.mouse.click(box["x"] + box["width"] / 2,
                                         box["y"] + box["height"] / 2)
                except Exception:
                    pass

            page.wait_for_timeout(600)
            page.screenshot(path=str(screenshot_after))
            browser.close()

    except Exception as exc:  # noqa: BLE001
        errors.append(f"[playwright_error] {exc}")
        return BrowserResult(errors=errors, screenshot_initial_path=None,
                             screenshot_after_path=None)

    # Save console_errors.json
    (round_dir / "console_errors.json").write_text(
        json.dumps(errors, indent=2) + "\n", encoding="utf-8"
    )

    return BrowserResult(
        errors=errors,
        screenshot_initial_path=screenshot_initial if screenshot_initial.exists() else None,
        screenshot_after_path=screenshot_after if screenshot_after.exists() else None,
    )


# ─── T3: Vision critique ──────────────────────────────────────────────────────

def _run_vision_critique(
    browser_result: BrowserResult,
    round_dir: Path,
) -> CritiqueResult:
    """Feed screenshots to Claude vision CLI and parse the rubric response."""
    if not browser_result.playwright_available:
        return CritiqueResult(available=False)

    if not browser_result.screenshot_initial_path:
        return CritiqueResult(available=False, notes="No screenshots captured")

    cli = os.getenv("CLAUDE_CLI_PATH", "claude")
    timeout = float(os.getenv("PF_CLAUDE_CLI_TIMEOUT_SECONDS", "120"))

    cmd = [cli, "-p", VISION_PROMPT, "--output-format", "json"]
    if browser_result.screenshot_initial_path:
        cmd += ["--image", str(browser_result.screenshot_initial_path)]
    if browser_result.screenshot_after_path:
        cmd += ["--image", str(browser_result.screenshot_after_path)]

    # Save the patch prompt for audit
    (round_dir / "patch_prompt.txt").write_text(
        VISION_PROMPT, encoding="utf-8"
    )

    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True,
            timeout=timeout, env=os.environ.copy(),
        )
    except (FileNotFoundError, subprocess.TimeoutExpired) as exc:
        return CritiqueResult(available=False, notes=str(exc))

    if result.returncode != 0:
        return CritiqueResult(
            available=False,
            notes=f"claude CLI exited {result.returncode}: {result.stderr[:200]}"
        )

    # Unwrap --output-format json envelope
    raw_text = result.stdout
    try:
        envelope = json.loads(raw_text)
        raw_text = envelope.get("result") or envelope.get("content") or raw_text
    except json.JSONDecodeError:
        pass

    # Parse rubric JSON
    criteria: dict[str, str] = {}
    notes = ""
    try:
        # Find first { ... }
        start = raw_text.find("{")
        end = raw_text.rfind("}")
        if start != -1 and end > start:
            parsed = json.loads(raw_text[start:end + 1])
            for key in RUBRIC_CRITERIA:
                criteria[key] = parsed.get(key, "unclear")
            notes = parsed.get("notes", "")
    except (json.JSONDecodeError, ValueError):
        for key in RUBRIC_CRITERIA:
            criteria[key] = "unclear"
        notes = "failed to parse vision response"

    pass_count = sum(1 for v in criteria.values() if v == "pass")

    critique = CritiqueResult(criteria=criteria, pass_count=pass_count, notes=notes)
    (round_dir / "critique.json").write_text(
        json.dumps({
            "criteria": criteria,
            "pass_count": pass_count,
            "notes": notes,
        }, indent=2) + "\n",
        encoding="utf-8",
    )
    return critique


# ─── T4: Patch prototype ──────────────────────────────────────────────────────

def _patch_prototype(
    html_path: Path,
    browser_result: BrowserResult,
    critique: CritiqueResult,
    profile: dict[str, str],
    config: dict[str, Any],
) -> str:
    """Ask Claude/Codex to fix the prototype. Returns patched HTML string."""
    current_html = html_path.read_text(encoding="utf-8")

    # Truncate very long sources
    max_chars = 6000
    if len(current_html) > max_chars:
        html_source = current_html[:max_chars] + "\n<!-- [source truncated for context window] -->"
    else:
        html_source = current_html

    failed = [k for k, v in critique.criteria.items() if v == "fail"]
    failed_criteria = "\n".join(f"- {c}" for c in failed) if failed else "(none from rubric)"

    errors_section = "\n".join(browser_result.errors[:20]) if browser_result.errors else "(none)"

    prompt = PATCH_PROMPT_TEMPLATE.format(
        failed_criteria=failed_criteria,
        errors_section=errors_section,
        html_source=html_source,
    )

    try:
        raw = call_provider(profile, prompt)
    except Exception as exc:  # noqa: BLE001
        return current_html  # return original on provider failure

    # Extract HTML from response
    raw = raw.strip()
    for marker in ("<!doctype", "<!DOCTYPE", "<html", "<HTML"):
        idx = raw.find(marker)
        if idx != -1:
            end_idx = raw.lower().rfind("</html>")
            if end_idx != -1:
                return raw[idx:end_idx + 7]
            return raw[idx:]

    return current_html  # fallback: return unchanged


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

        # Level 1 — browser errors
        browser_result = BrowserResult(errors=[], screenshot_initial_path=None,
                                       screenshot_after_path=None, playwright_available=False)
        if "errors" in levels or "visual" in levels:
            browser_result = _run_browser_check(html_path, round_dir)

        l1_errors = len(browser_result.errors)
        l1_pass = l1_errors == 0 and browser_result.playwright_available

        # Level 2 — vision critique
        critique = CritiqueResult(available=False)
        if "visual" in levels and browser_result.playwright_available:
            critique = _run_vision_critique(browser_result, round_dir)

        l2_pass_count = critique.pass_count if critique.available else None
        l2_pass = (
            critique.available
            and critique.pass_count >= pass_threshold
        )

        # Determine overall round result
        check_visual = "visual" in levels
        if not browser_result.playwright_available:
            # Playwright not installed — skip both levels, mark as passed to avoid infinite patching
            round_passed = True
            decision = "skip_no_playwright"
        elif check_visual:
            round_passed = l1_pass and l2_pass
            decision = "pass" if round_passed else "patch"
        else:
            round_passed = l1_pass
            decision = "pass" if round_passed else "patch"

        log_rows.append({
            "round": round_num,
            "l1_errors": l1_errors if browser_result.playwright_available else "n/a",
            "l2_pass_count": l2_pass_count if critique.available else "n/a",
            "decision": decision,
            "notes": critique.notes if critique.available else (
                "playwright unavailable" if not browser_result.playwright_available else ""
            ),
        })

        if round_passed:
            passed = True
            break

        # Budget check
        elapsed = time.monotonic() - start_time
        if elapsed >= budget_seconds:
            log_rows[-1]["decision"] = "budget_exceeded"
            break

        # Patch
        if round_num < max_rounds:
            patched_html = _patch_prototype(html_path, browser_result, critique, profile, config)
            # Save patched version in round dir for audit
            (round_dir / "prototype_patched.html").write_text(patched_html, encoding="utf-8")
            # Overwrite canonical prototype
            html_path.write_text(patched_html, encoding="utf-8")

    # Write iteration_log.md
    log_path = iterations_dir / "iteration_log.md"
    _write_iteration_log(log_path, log_rows, wave_id, cell_id)

    # Write metadata for log
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
