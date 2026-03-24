# Spec 014 — Prototype Iteration Loop

## Problem

Single-shot LLM generation of prototype.html produces non-playable DOM stubs. The root cause is missing feedback signal: the LLM writes code without ever seeing what it produces. A developer would iterate — play, observe, fix — until the prototype actually works. This spec adds that loop to the factory pipeline.

## Solution

A closed feedback loop that runs after `prototype_builder_web` generates the initial HTML. Each round:

1. **Run** — load prototype.html in a headless Playwright browser
2. **Observe** — capture JS console errors + two screenshots (initial state, after first tap)
3. **Critique** — feed screenshots and errors to Claude vision CLI with a structured rubric
4. **Patch** — feed critique JSON + current prototype source to Claude CLI to produce a patched file
5. **Repeat** — until critique passes or round budget exhausted

## Levels

### Level 1 — Error-free
- No JS runtime errors or uncaught exceptions in the console
- Page loads without crash within 3s

### Level 2 — Visual pass
Claude vision evaluates two screenshots against a fixed rubric:
- `board_visible` — is a game board/arena clearly rendered?
- `elements_present` — are dock/queue items visible?
- `interactive_hint` — is there at least one clickable element?
- `state_changed` — did anything visibly change after the tap?
- `readable` — are colors distinct, text legible, no overlapping UI?

Each criterion: `pass | fail | unclear`. Loop continues while any criterion is `fail`.

### Level 3 — Mechanic smoke test (stub for now, wired up later)
Playwright script simulates a complete interaction sequence defined in `prototype_spec.md` and asserts specific DOM/canvas state changes. Stubbed as a no-op in this spec — architecture must support it as a future plug-in.

## Configuration (run_config.json)

```json
"prototype_iteration": {
  "enabled": true,
  "max_rounds": 4,
  "levels": ["errors", "visual"],
  "budget_seconds": 300,
  "pass_threshold": 4
}
```

`pass_threshold` — how many Level 2 rubric criteria must pass (out of 5) to accept. Default 4.

## Artifacts

All iteration artifacts land in `factory/prototypes/<wave>/<cell>/iterations/`:

```
iterations/
  round_01/
    screenshot_initial.png
    screenshot_after_tap.png
    console_errors.json
    critique.json          ← structured rubric result from Claude vision
    patch_prompt.txt       ← prompt sent to Claude for patching (for audit)
  round_02/ ...
  iteration_log.md         ← per-round summary: level results, pass/fail, diffs applied
```

The final accepted `prototype.html` in `factory/prototypes/<wave>/<cell>/prototype.html` is always the last iteration's output.

## Acceptance Criteria

- `prototype_iteration_runner.py` runs standalone given an HTML path and run_config
- `wave_runner.py` calls it after prototype build when `prototype_iteration.enabled` is true
- All iteration artifacts written with `.metadata.json` pairs (role: `prototype_iterator`)
- If max_rounds reached without passing, wave completes anyway — failure is logged in `iteration_log.md`, not a fatal error
- `run_config.json` with no `prototype_iteration` key behaves identically to today (no iteration)
- Tests cover: clean pass on round 1, error-correction across rounds, max_rounds budget respected
