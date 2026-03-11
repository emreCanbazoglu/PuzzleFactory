# PuzzleFusionFactory Constitution

## Purpose

This constitution defines non-negotiable engineering and process rules for PuzzleFusionFactory.

## Core Principles

1. Structure is contract
- The product layer folder structure is mandatory and must remain stable.
- Runtime artifacts must be written only to the designated `factory/*` folders.

2. Spec before implementation
- Every feature must have `spec.md`, `plan.md`, and `tasks.md` before implementation.
- Work must follow task order unless an explicit blocker is documented.

3. Role and template compliance
- Agent role behavior is sourced from `agents/*.md`.
- Artifacts must conform to `templates/*.md` headings and required fields.

4. Cell isolation and synchronization boundary
- Concept cells run independently with isolated outputs.
- Cross-cell synchronization is allowed only at evaluation/portfolio stage.

5. Playability gate
- A concept is not evaluable unless a playable prototype exists with deterministic win/lose checks.

6. Decisioning is tunable and auditable
- Decision policy must be configurable through run config.
- Human feedback defaults to advisory window mode with timeout fallback.
- Final decisions must preserve auto decision, human override (if any), and rationale.

7. Session continuity
- Current state must be recoverable from repository files only.
- No hidden memory is required to resume implementation.

## Required Artifacts Per Concept

- Mechanic Sheet
- Concept Card
- Prototype Spec
- Playable Prototype
- Evaluation Report
- Scorecard
- Decision record

## Change Control

Any change to this constitution requires:

1. Update this file.
2. Update impacted `specs/*/spec.md` and `specs/*/plan.md`.
3. Add migration notes in affected feature quickstart docs.
