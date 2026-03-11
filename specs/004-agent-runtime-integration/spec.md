# Feature Specification: Agent Runtime Integration

**Feature Branch**: `004-agent-runtime-integration`  
**Created**: 2026-03-11  
**Status**: Draft  
**Input**: User description: "replace stub generation with real role-driven runtime using cloud/local routing"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Role-Driven Artifact Generation (Priority: P1)

As an operator, I need each pipeline artifact generated through role definitions and templates, not hardcoded stubs.

**Why this priority**: This is the core product behavior.

**Independent Test**: Running `wave_runner.py` should generate stage artifacts with role/template traces.

**Acceptance Scenarios**:

1. **Given** a configured cell, **When** wave runner executes, **Then** mechanic/concept/spec/prototype/evaluation artifacts are produced via agent runtime.
2. **Given** role and template files, **When** prompts are built, **Then** each artifact records source role and template usage.

---

### User Story 2 - Hybrid Model Routing (Priority: P1)

As an operator, I need cloud/local routing honored per role for cost-efficient execution.

**Why this priority**: Hybrid routing is a stated execution model requirement.

**Independent Test**: Router resolves cloud roles to cloud profile and local roles to local profile.

**Acceptance Scenarios**:

1. **Given** routing config, **When** role execution starts, **Then** correct profile is selected.
2. **Given** unavailable provider credentials, **When** mock fallback is enabled, **Then** run completes with deterministic fallback output.

---

### User Story 3 - Session-Resumable Runtime Outputs (Priority: P1)

As a collaborator, I need generated outputs and metadata to remain resumable across sessions.

**Why this priority**: Process continuity is a non-negotiable.

**Independent Test**: A fresh session can infer current stage state and continue using files only.

**Acceptance Scenarios**:

1. **Given** partial run state, **When** runner is re-invoked, **Then** completed artifacts are preserved and state remains readable.
2. **Given** generated artifacts, **When** tests validate structure, **Then** required template markers remain present.

## Edge Cases

- Missing role file for a configured stage.
- Missing template file for an artifact type.
- Cloud/local model endpoint timeout.
- Provider unavailable with fallback disabled.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST execute stage generation through role and template inputs.
- **FR-002**: System MUST route each role to cloud or local model profile using run config.
- **FR-003**: System MUST support deterministic mock fallback for unavailable providers when enabled.
- **FR-004**: System MUST write artifact metadata linking role, template, provider profile, and timestamp.
- **FR-005**: System MUST preserve compatibility with existing run config while allowing extended model profile config.
- **FR-006**: System MUST keep cell isolation guarantees intact.

### Key Entities

- **AgentTask**: one role invocation for one artifact stage in one cell.
- **ModelProfile**: provider/model/endpoint settings for cloud or local routing.
- **ArtifactEnvelope**: generated content plus runtime metadata.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% of stage artifacts in wave runs are produced by runtime path, not static constants.
- **SC-002**: Role-to-profile mapping is traceable in artifact metadata for all cells.
- **SC-003**: Wave run succeeds without external keys when mock fallback is enabled.
- **SC-004**: Session status and run logs remain sufficient for deterministic resume.
