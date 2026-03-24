# Plan 014 — Prototype Iteration Loop

## New files

### `.specify/scripts/python/prototype_iteration_runner.py`
Main entry point for the loop. Public interface:

```python
def run_iteration_loop(
    *,
    repo_root: Path,
    html_path: Path,
    wave_id: str,
    cell_id: str,
    iteration_config: dict,      # from run_config["prototype_iteration"]
    profile: dict,               # cloud profile (for Claude CLI calls)
    config: dict,                # full run_config
) -> dict:
    """
    Returns:
    {
      "rounds_run": int,
      "passed": bool,
      "final_html_path": str,
      "iteration_log_path": str,
    }
    """
```

Internally:
1. Parse `iteration_config` — defaults: max_rounds=4, levels=["errors","visual"], budget_seconds=300, pass_threshold=4
2. For each round: call `_run_browser_check()` → `_run_vision_critique()` → decide pass/fail → if fail, call `_patch_prototype()`
3. Write `iteration_log.md` on completion

### `_run_browser_check(html_path) -> BrowserResult`
Uses `playwright` (sync API). Launches Chromium headless, loads `file://html_path`, waits 1500ms, captures:
- Console errors (type=error + pageerror)
- `screenshot_initial.png` (before any input)
- Simulates a click at the first `<button>` or canvas center
- Waits 600ms
- `screenshot_after_tap.png`

Returns `{ errors: list[str], screenshot_initial: bytes, screenshot_after: bytes }`.

Falls back gracefully if Playwright is not installed — returns `{ errors: ["playwright not installed"], screenshot_initial: None, screenshot_after: None }` and skips visual level.

### `_run_vision_critique(screenshots, errors, profile) -> CritiqueResult`
Calls Claude CLI with both screenshots:
```bash
claude -p "<rubric_prompt>" \
  --image screenshot_initial.png \
  --image screenshot_after_tap.png \
  --output-format json
```

Rubric prompt instructs Claude to return exactly:
```json
{
  "board_visible": "pass|fail|unclear",
  "elements_present": "pass|fail|unclear",
  "interactive_hint": "pass|fail|unclear",
  "state_changed": "pass|fail|unclear",
  "readable": "pass|fail|unclear",
  "notes": "..."
}
```

Returns parsed dict. On parse failure, all criteria default to `"unclear"`.

### `_patch_prototype(html_path, critique, errors, profile) -> str`
Reads current HTML source. Builds a patch prompt:
- Current prototype.html source (truncated to 6000 chars if needed)
- Console errors list
- Critique JSON with failed/unclear criteria
- Instruction: "Fix the issues. Return the complete corrected HTML file and nothing else."

Calls `call_provider(profile, prompt)` — works with any provider (`claude`, `codex`, `openai`, `ollama`).

Returns patched HTML string. Caller writes it to `prototype.html` and to `iterations/round_N/prototype_patched.html`.

## Changes to existing files

### `wave_runner.py`
After `generate_prototype_html` writes `prototype.html`, add:

```python
iter_cfg = cfg.get("prototype_iteration", {})
if iter_cfg.get("enabled"):
    from prototype_iteration_runner import run_iteration_loop
    iter_result = run_iteration_loop(
        repo_root=repo_root,
        html_path=prototype_path,
        wave_id=wave_id,
        cell_id=cid,
        iteration_config=iter_cfg,
        profile=resolve_profile_for_role(cfg, "prototype_builder_web"),
        config=cfg,
    )
    outputs.append(iter_result["iteration_log_path"])
```

### `run_config.json` (wave_001)
Add iteration block targeting Level 1+2:
```json
"prototype_iteration": {
  "enabled": true,
  "max_rounds": 4,
  "levels": ["errors", "visual"],
  "budget_seconds": 300,
  "pass_threshold": 4
}
```

### `validate_run_config.py`
Add optional `prototype_iteration` key validation — all fields optional with documented defaults. Never required.

## Dependencies

Add to `.specify/scripts/python/` requirements (document in a `requirements.txt` there):
```
playwright>=1.40
```

Install:
```bash
pip install playwright
playwright install chromium
```

## Test plan

`tests/test_prototype_iteration.py` covers:

1. `test_iteration_skipped_when_not_configured` — run_config with no `prototype_iteration` key; assert `run_cell` output contains no iteration artifacts
2. `test_passes_on_round_1_if_no_errors` — mock `_run_browser_check` to return no errors, mock `_run_vision_critique` to return all pass; assert rounds_run==1, passed==True
3. `test_patches_on_error` — mock browser check returns one error, vision returns fails; second round mock returns clean; assert rounds_run==2, final HTML is patched version
4. `test_budget_respected` — max_rounds=2, always failing mocks; assert rounds_run==2, passed==False, wave still completes
5. `test_artifacts_written` — verify iteration_log.md and per-round dirs created in correct path

## Open questions (deferred)

- Level 3 mechanic tests: architecture supports it (plug-in via `levels: ["errors","visual","mechanic"]`) but test script generation from `prototype_spec.md` is a separate spec
- HPPF plugin output format: switching from standalone HTML to HPPF `prototype.js` is a separate spec and orthogonal to this loop
