# Model Routing Contract

## Inputs

- `routing.cloud_roles[]`
- `routing.local_roles[]`
- optional `models.cloud`
- optional `models.local`

## Rules

- Role in `cloud_roles` routes to cloud profile.
- Role in `local_roles` routes to local profile.
- Unknown role defaults to cloud profile.
- If provider call fails and mock fallback is enabled, runtime uses deterministic mock output.
