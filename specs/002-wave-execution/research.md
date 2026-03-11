# Research: Wave Execution

## Key Decisions

- Use process-local Python runner scripts for orchestration.
- Enforce stage model to block cross-cell reads before sync.
- Keep failure isolation per cell and emit run-level status.
