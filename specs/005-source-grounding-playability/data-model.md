# Data Model: Source Grounding and Playability

## GameLibraryEntry

- `id`
- `name`
- `primary_domains`
- `mechanics`
- `core_verb`
- `board_topology`
- `pressure`
- `failure_mode`
- `depth_source`

## Cell Grounding

- `source_game_ids`
- resolved `source_games[]`

## Prototype State

- `moves`
- `screws[]`
- `packets[]`
- win/lose derived state
