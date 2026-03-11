# Puzzle Fusion Prototype Factory

AI-driven system for generating, prototyping, and evaluating hybrid puzzle game concepts.

## Goal

Produce playable prototypes (1-2 levels) from fused puzzle mechanics, evaluate them objectively, and iterate or kill concepts rapidly.

## Required Project Structure

```text
PuzzleFusionFactory/
├── factory/
│   ├── references/
│   ├── mechanics/
│   ├── concepts/
│   ├── specs/
│   ├── prototypes/
│   ├── evaluations/
│   ├── scorecards/
│   └── portfolio/
├── agents/
├── templates/
├── runs/
│   └── wave_001/
├── .specify/
└── specs/
```

## Output of a Successful Run

- Concept Card
- Prototype Spec
- Playable Prototype
- Evaluation Report
- Scorecard
- Decision (Iterate / Kill / Escalate)

## Constraints

- Focus on hybrid casual puzzle mechanics
- Prioritize clarity and depth over novelty alone
- Prototypes must be playable
- Avoid idea-only outputs

## Primary Domains

- Sort
- Color match
- Block puzzle
- Spatial reasoning

These are presets only. Domains are configurable in run config.

## Spec-Kit Process (Mandatory)

Implementation order is strict:

1. `spec.md`
2. `plan.md`
3. `tasks.md`
4. implementation by task order

Feature specs live in `specs/` and process assets live in `.specify/`.

## Resume Workflow (Fresh Session)

1. Check prerequisites:

```bash
bash .specify/scripts/bash/check-prerequisites.sh
```

2. Show open tasks and current execution state:

```bash
bash .specify/scripts/bash/session-status.sh
```

3. Validate run config contract:

```bash
python3 .specify/scripts/python/validate_run_config.py runs/wave_001/run_config.json
```

4. Validate template completeness:

```bash
python3 .specify/scripts/python/check_template_fields.py
```

5. Resume from first unchecked task in the active feature `tasks.md`.

## Wave 001 State Tracking

- Run log: `runs/wave_001/execution_log.md`
- Decision register: `runs/wave_001/decision_register.json`
- Active config: `runs/wave_001/run_config.json`

## Decisioning Defaults

- Decision policy is tunable via run config.
- Human feedback mode defaults to advisory override window.
- If no human feedback arrives before timeout, automated decision is finalized.
