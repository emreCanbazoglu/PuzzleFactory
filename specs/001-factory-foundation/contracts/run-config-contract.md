# Run Config Contract

## Required Sections

- `wave_id`
- `cells[]` with required `cell_id`, `discovery_domain`, `prototype_domain`, `concept_count`
- `routing` (`cloud_roles`, `local_roles`)
- `decision_policy` (`weights`, `thresholds`, `hard_gates`)
- `human_feedback` (`enabled`, `mode`, `timeout_hours`, `override_scope`)

## Mandatory Behavior

- `cells[]` is editable and not limited to the initial domain example.
- `prototype_domain` is required for every cell.
- Decision policy must be tunable from config without code edits.
- Human feedback supports advisory mode with timeout fallback.
