# Feature Specification: Factory Foundation

**Feature Branch**: `001-factory-foundation`  
**Created**: 2026-03-11  
**Status**: Draft  
**Input**: User description: "Establish strict product structure + spec-kit process layer + run config contract + session continuity"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Strict Structure Bootstrap (Priority: P1)

As a developer, I need the exact mandated project structure and role/template files present so every run and artifact has a known location.

**Why this priority**: No downstream work is reliable without a stable filesystem contract.

**Independent Test**: Can be tested by checking the required directories and required baseline files exist.

**Acceptance Scenarios**:

1. **Given** a fresh repo, **When** the foundation is bootstrapped, **Then** all required `factory/`, `agents/`, `templates/`, and `runs/wave_001/` paths exist.
2. **Given** the `agents/` folder, **When** role files are inspected, **Then** all 9 required role definitions exist.

---

### User Story 2 - Spec-Kit Governance Setup (Priority: P1)

As a developer, I need spec-kit process assets so all implementation work starts from specs and tasks.

**Why this priority**: The project must remain process-driven and resumable across sessions.

**Independent Test**: Can be tested by verifying `.specify/` templates, scripts, and constitution exist and are executable/usable.

**Acceptance Scenarios**:

1. **Given** the repository, **When** `.specify/scripts/bash/check-prerequisites.sh` runs, **Then** prerequisite checks complete without missing-process-file errors.
2. **Given** `.specify/memory/constitution.md`, **When** it is reviewed, **Then** structure, role/template compliance, isolation, sync boundary, and playability gates are explicit.

---

### User Story 3 - Run Config Contract and Baseline Validation (Priority: P1)

As a developer, I need a schema-backed run config and validators so wave setup is configurable and safe.

**Why this priority**: Cell domains, routing, and decision policy must be editable without code changes.

**Independent Test**: Can be tested with a valid run config passing validation and malformed configs failing with clear errors.

**Acceptance Scenarios**:

1. **Given** a run config with valid `cells[]`, routing, decision policy, and human feedback fields, **When** validation runs, **Then** it passes.
2. **Given** a run config missing `prototype_domain`, **When** validation runs, **Then** it fails with a specific contract error.

---

### Edge Cases

- Empty `cells[]` list.
- Duplicate `cell_id` values.
- Decision weights not summing to 1.0.
- Human feedback enabled with invalid mode.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST enforce the exact mandated product-layer directory layout.
- **FR-002**: System MUST provide all required role and template baseline files.
- **FR-003**: System MUST provide `.specify` governance assets required for spec-first development.
- **FR-004**: System MUST define a run-config schema with editable `cells[]` and required `discovery_domain` and `prototype_domain`.
- **FR-005**: System MUST include routing configuration for cloud/local role mapping.
- **FR-006**: System MUST include tunable decision-policy fields.
- **FR-007**: System MUST support optional human feedback settings with advisory-window default.
- **FR-008**: System MUST provide local validation scripts for run config, decision policy, and template field completeness.
- **FR-009**: System MUST provide session-resume checklist and status script.

### Key Entities

- **RunConfig**: Wave-level configuration including cells, routing, decision policy, and human feedback.
- **CellConfig**: Cell identity + domain routing settings for concept/prototype generation.
- **DecisionPolicy**: Weighted scoring and threshold gates used for Iterate/Kill/Escalate.
- **SessionState**: Task progress plus run logs needed for resumable work.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% of required structure paths/files are present after foundation setup.
- **SC-002**: `validate_run_config.py` passes baseline config and fails invalid config with explicit errors.
- **SC-003**: `session-status.sh` reports open/done task counts for all feature task files.
- **SC-004**: New session can resume from repository files only using the documented resume commands.
