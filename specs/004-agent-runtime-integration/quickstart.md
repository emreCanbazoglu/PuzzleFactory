# Quickstart: Agent Runtime Integration

## Run

```bash
python3 .specify/scripts/python/wave_runner.py runs/wave_001/run_config.json
```

## Optional live providers

- Set cloud provider env vars (example OpenAI):
  - `PF_CLOUD_PROVIDER=openai`
  - `OPENAI_API_KEY=...`
- Set local provider env vars (example Ollama):
  - `PF_LOCAL_PROVIDER=ollama`
  - `OLLAMA_BASE_URL=http://localhost:11434/api`

## Deterministic fallback

If provider access is unavailable, set:

- `PF_ALLOW_MOCK_FALLBACK=1` (default)
