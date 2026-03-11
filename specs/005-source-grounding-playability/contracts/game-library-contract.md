# Game Library Contract

## Source of truth

- Library file: `factory/references/game_library.json`
- Entries are imported from store-link based ingestion and may be manually edited afterward.

## Required provenance

- `id`
- `name`
- `mechanics`
- `board_type`
- `store_links`
- `source_metadata`
- `last_verified_at`

## Editable fields

- `mechanics`
- `description`
- `detail_text`
- any added design notes used to improve fusion quality

The file remains the canonical editable library used by the runtime.
