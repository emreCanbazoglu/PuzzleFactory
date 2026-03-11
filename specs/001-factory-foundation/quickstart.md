# Quickstart: Factory Foundation

## Deterministic Current-State Discovery

1. `bash .specify/scripts/bash/check-prerequisites.sh`
2. `bash .specify/scripts/bash/session-status.sh`
3. `python3 .specify/scripts/python/validate_run_config.py runs/wave_001/run_config.json`
4. `python3 .specify/scripts/python/check_decision_policy.py runs/wave_001/run_config.json`
5. `python3 .specify/scripts/python/check_template_fields.py`
6. `python3 .specify/scripts/python/check_wave_isolation.py runs/wave_001/run_config.json`

## Resume Rule

Resume at first unchecked task (`- [ ]`) in the active `specs/<feature>/tasks.md`.
After finishing a task block:

- Mark task as complete (`- [x]`) in `tasks.md`
- Append event in `runs/wave_001/execution_log.md`

## New Feature Initialization

```bash
bash .specify/scripts/bash/create-new-feature.sh "feature description"
```
