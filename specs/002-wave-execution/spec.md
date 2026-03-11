# Feature Specification: Wave Execution

**Feature Branch**: `002-wave-execution`  
**Created**: 2026-03-11  
**Status**: Draft  
**Input**: User description: "parallel concept cells with strict isolation and evaluation-stage synchronization"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Parallel Cell Runs (Priority: P1)

As an operator, I need all cells in a wave to run in parallel to maximize throughput.

**Independent Test**: Start a wave and confirm multiple cells execute concurrently.

**Acceptance Scenarios**:

1. **Given** a wave config with 4 cells, **When** a run starts, **Then** all 4 cells are launched concurrently.
2. **Given** one cell failure, **When** run completes, **Then** other cell outputs remain intact.

---

### User Story 2 - Cell Ownership Isolation (Priority: P1)

As a reviewer, I need each cell to write only to its own output scope to keep results attributable and safe.

**Independent Test**: Inspect output paths and ensure no cell writes to another cell area.

**Acceptance Scenarios**:

1. **Given** an executing cell, **When** files are produced, **Then** writes are restricted to the cell-owned output paths.

---

### User Story 3 - Evaluation-Only Synchronization (Priority: P1)

As portfolio scorer, I need cross-cell sync to happen only at evaluation stage.

**Independent Test**: Verify that no cross-cell reads occur during generation/build phases.

**Acceptance Scenarios**:

1. **Given** generation/build stage, **When** pipeline runs, **Then** no cross-cell dependencies are loaded.
2. **Given** evaluation stage, **When** scorer runs, **Then** all completed cell artifacts are aggregated.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST start configured cells in parallel.
- **FR-002**: System MUST enforce per-cell folder ownership boundaries.
- **FR-003**: System MUST defer cross-cell aggregation until evaluation stage.
- **FR-004**: System MUST produce deterministic run lifecycle logs.
- **FR-005**: System MUST tolerate partial-cell failures without corrupting successful cells.

## Success Criteria *(mandatory)*

- **SC-001**: Parallel execution active for all configured cells in wave.
- **SC-002**: No cross-cell writes in generation/build stages.
- **SC-003**: Evaluation aggregation includes all successful cell outputs only.
