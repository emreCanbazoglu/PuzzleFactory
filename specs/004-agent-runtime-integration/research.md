# Research: Agent Runtime Integration

## Decisions

1. Use config-driven profiles (`cloud`, `local`) with role mapping from existing `routing` keys.
2. Keep external model calls optional; default to deterministic mock fallback for local development continuity.
3. Record per-artifact runtime metadata to support audits and resume workflows.

## Rejected

- Hard dependency on remote APIs: rejected due to fragility in fresh local sessions.
- Single-provider routing: rejected because hybrid model routing is a stated requirement.
