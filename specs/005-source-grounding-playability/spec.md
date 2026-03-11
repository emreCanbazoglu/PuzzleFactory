# Feature Specification: Source Grounding and Playability

**Feature Branch**: `005-source-grounding-playability`  
**Created**: 2026-03-11  
**Status**: Draft  
**Input**: User description: "Artifacts must be grounded in specific source games like Pixel Flow + Screw Jam, and prototype output must be an actual playable puzzle."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Specific Fusion Artifacts (Priority: P1)

As a designer, I need mechanic sheets, concept cards, and prototype specs to be grounded in named source games so I can understand the game without inferring missing meaning.

**Why this priority**: Generic domain pairs like `sort + sort` are not useful design outputs.

**Independent Test**: Generate a cell and verify artifacts name concrete source games and describe specific merged mechanics.

**Acceptance Scenarios**:

1. **Given** a cell configured with `pixel-flow` and `screw-jam`, **When** the wave runner executes, **Then** generated artifacts explicitly describe that fusion.
2. **Given** a concept card, **When** it is read standalone, **Then** the reader can explain the core loop, interaction, and failure state.

---

### User Story 2 - Real Playable Prototype (Priority: P1)

As a reviewer, I need `prototype.html` to contain an actual interaction loop with win/lose states, not a moving placeholder.

**Why this priority**: The factory requirement is playable prototypes, not visual stubs.

**Independent Test**: Open the generated prototype and complete or fail the puzzle through player actions.

**Acceptance Scenarios**:

1. **Given** a generated prototype, **When** the player interacts with it, **Then** game state changes according to puzzle rules.
2. **Given** the prototype, **When** the player satisfies the objective, **Then** a win state is shown.
3. **Given** the prototype, **When** the player exhausts legal progress, **Then** a lose state is shown.

---

### User Story 3 - Source Library Driven Runtime (Priority: P1)

As an operator, I need cells to reference a game library so the runtime can reason from specific source mechanics.

**Why this priority**: Specificity must come from structured input, not hardcoded prose guesses.

**Independent Test**: Validate run config requires `source_game_ids` and runtime resolves them from the game library.

**Acceptance Scenarios**:

1. **Given** missing `source_game_ids`, **When** config validation runs, **Then** it fails.
2. **Given** unknown source game ids, **When** wave runner executes, **Then** it fails with a concrete error.

## Edge Cases

- A cell references fewer than two source games.
- A source game id is missing from the library.
- A playable prototype becomes unwinnable due to bad level data.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST load source game data from `factory/references/game_library.json`.
- **FR-001A**: Game library entries MUST retain store-link provenance and remain human-editable in place.
- **FR-002**: System MUST require `source_game_ids` on every cell.
- **FR-003**: System MUST generate artifact content that names and describes the configured source games.
- **FR-004**: System MUST produce a playable `prototype.html` with click/tap interaction, reset, win state, and lose state.
- **FR-005**: System MUST preserve deterministic behavior for repeatable evaluation.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Generated concept and spec artifacts mention concrete source titles for every cell.
- **SC-002**: Prototype can be won and lost without external tooling.
- **SC-003**: Config validation rejects cells without concrete source grounding.
