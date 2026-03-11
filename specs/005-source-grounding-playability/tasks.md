# Tasks: Source Grounding and Playability

**Input**: `specs/005-source-grounding-playability/`

## Phase 1: Grounding

- [x] T001 Add concrete game library at `factory/references/game_library.json`
- [x] T002 Add runtime loader `.specify/scripts/python/game_library.py`
- [x] T003 Extend run config and validator to require `source_game_ids`
- [x] T003A Document store-linked and human-editable game library contract

## Phase 2: Specific artifact generation

- [x] T004 Ground artifact text generation in specific source game data
- [x] T005 Update baseline `runs/wave_001/run_config.json` with concrete source pairs

## Phase 3: Playability

- [x] T006 Replace placeholder prototype with a real deterministic puzzle loop
- [x] T007 Add win/lose/reset behavior tests or structural checks

## Phase 4: Verification

- [x] T008 Run full wave pipeline and inspect generated artifacts for specificity
- [x] T009 Update execution log and mark task completion
