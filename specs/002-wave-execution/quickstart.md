# Quickstart: Wave Execution

## Planned Commands

```bash
python3 .specify/scripts/python/wave_runner.py runs/wave_001/run_config.json
python3 .specify/scripts/python/evaluation_sync.py runs/wave_001/run_config.json
```

## Guardrails

- Run `check_wave_isolation.py` before execution.
- Do not run sync scripts before all targeted cell stages complete.
