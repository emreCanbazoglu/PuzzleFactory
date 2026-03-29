# Feature Specification: Model-Driven Director With Script Validation

**Feature Branch**: `012-model-driven-director`  
**Created**: 2026-03-11  
**Status**: Draft  
**Input**: User description: "director_plan should be model-driven with script validation fallback"

## Requirements *(mandatory)*

- **FR-001**: The fusion director must attempt to generate `director_plan` via the routed model before ideation starts.
- **FR-002**: The model output must be strict JSON and must be validated by script before downstream use.
- **FR-003**: If model output is invalid, incomplete, or unavailable, the system must fall back to a scripted director plan.
- **FR-004**: The persisted `director_plan` must indicate whether it came from model output or scripted fallback.
