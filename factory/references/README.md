# Game Library

`game_library.json` is the canonical source-game library.

Rules:

- Base records come from store-link ingestion.
- Humans may edit entries after import.
- `human_notes` is the place to record:
  - winning points
  - what to adopt
  - what to avoid
  - main goal
  - stress points
  - fun points

The runtime should treat these notes as first-class guidance for deconstruction and fusion.

## Validation

Validate the library before using entries in a wave:

```bash
python3 .specify/scripts/python/validate_game_library.py
```

Outputs:

- `factory/references/validation/game_library_validation.md`
- `factory/references/validation/game_library_validation.json`

Statuses:

- `ready`: factual record and design interpretation are strong enough for deconstruction/fusion.
- `needs_human_clarification`: schema is usable, but the design understanding is too weak.
- `invalid`: required factual data is missing or malformed.

## Human Review Loop

Use validation as the gate, then review one game at a time with the review agent.

Prepare a review brief:

```bash
python3 .specify/scripts/python/prepare_game_library_review.py ios-6751056652-pixel-flow
```

Outputs:

- `factory/references/reviews/<game_id>/review_session.md`
- `factory/references/reviews/<game_id>/review_session.json`

Recommended flow:

1. Run `validate_game_library.py`
2. Pick one entry with `needs_human_clarification`
3. Generate its review brief
4. Discuss that single game with the review agent
5. Update `game_library.json`
6. Re-run validation
