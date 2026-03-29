# Data Model: Agent Runtime Integration

## ModelProfile

- `provider`: `openai | ollama | mock`
- `model`: string
- `base_url`: optional string
- `api_key_env`: optional string

## AgentTask

- `wave_id`
- `cell_id`
- `role`
- `artifact_type`
- `template_name`
- `profile`

## ArtifactEnvelope

- `content`
- `metadata.role`
- `metadata.template`
- `metadata.profile`
- `metadata.generated_at`
