# Tasks: Factory Foundation

**Input**: `specs/001-factory-foundation/`  
**Prerequisites**: `spec.md`, `plan.md`, `research.md`, `data-model.md`, `contracts/`

## Phase 1: Setup (Shared Infrastructure)

- [x] T001 Create strict product-layer directories under `factory/`, `agents/`, `templates/`, `runs/wave_001/`
- [x] T002 Create baseline role definition files in `agents/*.md`
- [x] T003 Create baseline template files in `templates/*.md`
- [x] T004 Bootstrap `.specify/` process folders and script/template assets

## Phase 2: Foundational Contracts

- [x] T005 Write constitution in `.specify/memory/constitution.md`
- [x] T006 Define run config schema in `specs/001-factory-foundation/contracts/run-config.schema.json`
- [x] T007 Define run config contract doc in `specs/001-factory-foundation/contracts/run-config-contract.md`
- [x] T008 Define template field contract in `specs/001-factory-foundation/contracts/template-field-contract.md`
- [x] T009 Create baseline `runs/wave_001/run_config.json`

## Phase 3: Validation and Continuity

- [x] T010 Add run config validator `.specify/scripts/python/validate_run_config.py`
- [x] T011 Add decision policy validator `.specify/scripts/python/check_decision_policy.py`
- [x] T012 Add template completeness validator `.specify/scripts/python/check_template_fields.py`
- [x] T013 Add cell isolation checker `.specify/scripts/python/check_wave_isolation.py`
- [x] T014 Add session status script `.specify/scripts/bash/session-status.sh`
- [x] T015 Add resume checklist `.specify/checklists/session-resume.md`
- [x] T016 Add wave execution and decision baseline files in `runs/wave_001/`

## Phase 4: Documentation

- [x] T017 Create feature docs: `spec.md`, `plan.md`, `research.md`, `data-model.md`, `quickstart.md`
- [x] T018 Update root `README.md` with strict structure + resume commands
