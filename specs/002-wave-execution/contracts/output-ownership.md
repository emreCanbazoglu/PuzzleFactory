# Output Ownership Contract

Each cell writes only to paths namespaced by `wave_id/cell_id` metadata.

Shared paths (`factory/portfolio`, run-level summaries) are writable only in global stages.
