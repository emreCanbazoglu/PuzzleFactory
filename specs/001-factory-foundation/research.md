# Research: Factory Foundation

## Decisions

1. Use root `specs/` as canonical feature lifecycle location.
2. Use `.specify/` for constitution, templates, scripts, and checklists.
3. Use JSON run config for wave/cell/routing/decision settings.
4. Keep validators dependency-free (Python stdlib) for portability.

## Rejected Options

- `.specify/specs/` as canonical specs path: rejected to align with standard spec-kit root `specs/` flow.
- Hardcoded domain cells: rejected because domains must remain editable presets.
- Mandatory human approval: rejected for baseline automation throughput.
