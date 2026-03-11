# Tasks: Agent Runtime Integration

**Input**: `specs/004-agent-runtime-integration/`

## Phase 1: Contracts and docs

- [x] T001 Create feature docs (`spec.md`, `plan.md`, `research.md`, `data-model.md`, `quickstart.md`)
- [x] T002 Create routing and metadata contracts in `contracts/`

## Phase 2: Runtime implementation

- [x] T003 Implement model routing module `.specify/scripts/python/model_router.py`
- [x] T004 Implement role/template runtime module `.specify/scripts/python/agent_runtime.py`
- [x] T005 Integrate runtime into `.specify/scripts/python/wave_runner.py`
- [x] T006 Add artifact metadata writer integration for each generated stage

## Phase 3: Tests

- [x] T007 Add routing behavior tests `.specify/scripts/python/tests/test_model_routing.py`
- [x] T008 Add runtime artifact generation tests `.specify/scripts/python/tests/test_agent_runtime_outputs.py`
- [x] T009 Update/extend wave integration tests for runtime path

## Phase 4: Continuity and validation

- [x] T010 Update run log format docs and append execution event in `runs/wave_001/execution_log.md`
- [x] T011 Run full dry-run command chain and ensure passing results
