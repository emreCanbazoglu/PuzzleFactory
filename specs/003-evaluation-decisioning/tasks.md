# Tasks: Evaluation and Decisioning

**Input**: `specs/003-evaluation-decisioning/`

## Phase 1: Contracts

- [x] T001 Create scoring contract doc `specs/003-evaluation-decisioning/contracts/scoring-contract.md`
- [x] T002 Create decision trail contract doc `specs/003-evaluation-decisioning/contracts/decision-trail-contract.md`

## Phase 2: Engine

- [x] T003 Implement weighted scoring module `.specify/scripts/python/decision_engine.py`
- [x] T004 Implement advisory timeout finalizer `.specify/scripts/python/human_feedback.py`
- [x] T005 Implement decision register writer `.specify/scripts/python/decision_register.py`

## Phase 3: Tests

- [x] T006 Add deterministic score test `.specify/scripts/python/tests/test_decision_scores.py`
- [x] T007 Add advisory timeout test `.specify/scripts/python/tests/test_advisory_timeout.py`
- [x] T008 Add override-audit trail test `.specify/scripts/python/tests/test_decision_audit.py`

## Phase 4: Docs

- [x] T009 Add operational decision workflow in `specs/003-evaluation-decisioning/quickstart.md`
