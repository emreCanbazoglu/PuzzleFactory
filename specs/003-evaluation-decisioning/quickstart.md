# Quickstart: Evaluation and Decisioning

## Planned Commands

```bash
python3 .specify/scripts/python/decision_engine.py runs/wave_001/run_config.json
python3 .specify/scripts/python/human_feedback.py runs/wave_001/run_config.json
```

## Default Mode

- `human_feedback.mode=advisory_window`
- Timeout finalizes automated decision if no override input exists.
