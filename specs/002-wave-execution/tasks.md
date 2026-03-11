# Tasks: Wave Execution

**Input**: `specs/002-wave-execution/`

## Phase 1: Foundation

- [x] T001 Create lifecycle contract doc `specs/002-wave-execution/contracts/wave-lifecycle.md`
- [x] T002 Create output ownership contract `specs/002-wave-execution/contracts/output-ownership.md`

## Phase 2: Runner Implementation

- [x] T003 Implement parallel runner in `.specify/scripts/python/wave_runner.py`
- [x] T004 Implement per-cell path guard in `.specify/scripts/python/path_guard.py`
- [x] T005 Add run-state writer in `.specify/scripts/python/run_state.py`
- [x] T006 Add sync-stage aggregator in `.specify/scripts/python/evaluation_sync.py`

## Phase 3: Tests

- [x] T007 Add parallel launch test `.specify/scripts/python/tests/test_parallel_cells.py`
- [x] T008 Add isolation test `.specify/scripts/python/tests/test_cell_isolation.py`
- [x] T009 Add evaluation-only sync test `.specify/scripts/python/tests/test_evaluation_sync_boundary.py`

## Phase 4: Docs and logging

- [x] T010 Update `runs/wave_001/execution_log.md` integration format section
- [x] T011 Add operator usage section in `specs/002-wave-execution/quickstart.md`
