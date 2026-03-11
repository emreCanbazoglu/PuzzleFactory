# Data Model: Wave Execution

## WaveState

- `wave_id`
- `status`
- `started_at`
- `finished_at`
- `cell_states[]`

## CellState

- `cell_id`
- `status`
- `stage`
- `artifacts`
- `error` (nullable)
