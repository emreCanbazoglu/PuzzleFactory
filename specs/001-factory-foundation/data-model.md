# Data Model: Factory Foundation

## RunConfig

- `wave_id`: string
- `cells`: array of `CellConfig`
- `routing`: `RoutingConfig`
- `decision_policy`: `DecisionPolicy`
- `human_feedback`: `HumanFeedbackConfig`

## CellConfig

- `cell_id`: string (unique)
- `discovery_domain`: string
- `prototype_domain`: string
- `concept_count`: integer >= 1

## RoutingConfig

- `cloud_roles`: string[]
- `local_roles`: string[]

## DecisionPolicy

- `weights`: object
  - clarity
  - depth
  - level_scalability
  - production_feasibility
  - retention_potential
  - novelty
- `thresholds`
  - expand_min
  - iterate_min
  - kill_max
- `hard_gates`
  - playable_required
  - min_clarity

## HumanFeedbackConfig

- `enabled`: boolean
- `mode`: `advisory_window | hard_approval | off`
- `timeout_hours`: integer >= 0
- `override_scope`: string
