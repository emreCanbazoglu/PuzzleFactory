# Tasks 014 — Prototype Iteration Loop

## Order is strict. Do not skip ahead.

- [ ] T1. Add `playwright` to `.specify/scripts/python/requirements.txt` (create file if missing). Add install note to CLAUDE.md dev commands.

- [ ] T2. Implement `_run_browser_check(html_path, iterations_dir, round_num)` in `prototype_iteration_runner.py`.
  - Sync Playwright, headless Chromium
  - Capture console errors + pageerror
  - screenshot_initial.png saved to `iterations_dir/round_NN/`
  - Simulate click (first button or canvas center), wait 600ms
  - screenshot_after_tap.png saved to `iterations_dir/round_NN/`
  - Returns `BrowserResult(errors, screenshot_initial_path, screenshot_after_path)`
  - Graceful fallback if playwright missing

- [ ] T3. Implement `_run_vision_critique(screenshot_paths, errors, profile, config)` in `prototype_iteration_runner.py`.
  - Build rubric prompt (board_visible, elements_present, interactive_hint, state_changed, readable)
  - Call `claude` CLI with `--image` flags for both screenshots
  - Parse JSON response, default unclear on parse failure
  - Save `critique.json` and `patch_prompt.txt` to round dir
  - Returns `CritiqueResult(criteria: dict, pass_count: int, notes: str)`

- [ ] T4. Implement `_patch_prototype(html_path, critique, errors, profile, config)` in `prototype_iteration_runner.py`.
  - Read current HTML, truncate source to 6000 chars if needed with note
  - Build patch prompt with errors + failed criteria
  - Call `call_provider(profile, prompt)` — import from `agent_runtime`
  - Extract HTML from response (look for `<!doctype` or `<html` to `</html>`)
  - Return patched HTML string (return original if extraction fails)

- [ ] T5. Implement `run_iteration_loop(...)` in `prototype_iteration_runner.py`.
  - Parse iteration_config with defaults
  - For each round up to max_rounds:
    - T2: browser check
    - Skip visual if playwright unavailable or level not in config levels
    - T3: vision critique (if screenshots exist)
    - Compute pass: Level1=(no errors), Level2=(pass_count >= pass_threshold)
    - If pass → break
    - T4: patch prototype, write to html_path and round dir
    - Check budget_seconds elapsed → break if exceeded
  - Write `iteration_log.md` with per-round summary table
  - Write `.metadata.json` for iteration_log (role: prototype_iterator)
  - Return result dict

- [ ] T6. Integrate into `wave_runner.py`.
  - After prototype_path is written, check `cfg.get("prototype_iteration", {}).get("enabled")`
  - If enabled, call `run_iteration_loop(...)`
  - Append `iteration_log_path` to outputs

- [ ] T7. Update `validate_run_config.py` to accept optional `prototype_iteration` key with documented defaults. No required fields inside it.

- [ ] T8. Update `runs/wave_001/run_config.json` — add `prototype_iteration` block with `enabled: true, max_rounds: 4, levels: ["errors", "visual"], budget_seconds: 300, pass_threshold: 4`.

- [ ] T9. Write `tests/test_prototype_iteration.py` covering the 5 cases in plan.md. Use unittest.mock to patch `_run_browser_check` and `_run_vision_critique`.

- [ ] T10. Run full test suite (`python3 -m pytest tests/ -v`). Fix any failures. Confirm all 5 new tests pass.

- [ ] T11. Update `CLAUDE.md` — add `prototype_iteration` to the run_config reference and add Playwright install to dev commands.

- [ ] T12. Push branch and open PR to main. Title: "feat: prototype iteration loop (spec 014)". Body must include: summary, round budget logic, test coverage, and manual test instructions (run wave_001, check factory/prototypes/wave_001/cell_a/iterations/).
