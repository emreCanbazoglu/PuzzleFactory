# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**PuzzeFactory** is an AI-driven batch factory for generating, prototyping, and evaluating hybrid puzzle game concepts. It runs in configurable **waves**, each containing parallel **cells** that independently produce a full artifact chain: mechanic sheet → concept card → prototype spec → playable HTML prototype → evaluation report → scored decision.

It is the evolved successor to PuzzleFusionEngine. Where PuzzleFusionEngine is a real-time web API for quick ideation, PuzzeFactory is a batch research pipeline with strict process governance, cell-parallel execution, human advisory gates, and a configurable decision policy engine.

## Development Commands

```bash
# Install Python dependencies (includes Playwright for prototype iteration)
pip install -r .specify/scripts/python/requirements.txt
playwright install chromium   # one-time: downloads headless Chromium

# Run a wave (from repo root)
cd .specify/scripts/python
python3 wave_runner.py ../../../runs/wave_001/run_config.json

# Run all tests
cd .specify/scripts/python
python -m pytest tests/ -v

# Run a single test file
python -m pytest tests/test_model_routing.py -v

# Validate run config before a wave
python validate_run_config.py ../../../runs/wave_001/run_config.json

# Validate game library health
python validate_game_library.py ../../../factory/references/game_library.json

# Prepare a single-game library review brief
python prepare_game_library_review.py ../../../factory/references/game_library.json <game-id>
```

All scripts must be run from `.specify/scripts/python/` so relative imports resolve correctly.

## Architecture

### Execution Pipeline (per cell)

```
run_config.json
    ↓
wave_runner.py  ──── ThreadPoolExecutor (one thread per cell)
    ↓
run_cell()
    ├── 1. fusion_director      → director_plan.json + director_brief.md
    ├── 2. deconstructor        → mechanic_sheet.md
    ├── 3. fusion_designer_*    → concept_card_NN.md  (one per variation)
    ├── 4. prototype_spec_writer → prototype_spec.md
    ├── 5. prototype_builder_web → prototype.html
    ├── 6. prototype_critic     → evaluation_report.md
    └── 7. scorecard            → scorecard.json
         ↓
decision_engine.py  → auto_decisions.json → decision_register.json
```

### Key Scripts (`.specify/scripts/python/`)

| File | Role |
|---|---|
| `wave_runner.py` | Orchestrator — runs cells in parallel, writes state |
| `agent_runtime.py` | LLM invocation, template rendering, mock fallback, artifact construction |
| `model_router.py` | Resolves cloud/local profile per agent role from `run_config.json` |
| `decision_engine.py` | Weighted scorecard scoring → Escalate / Iterate / Kill |
| `game_library.py` | Loads and resolves source games from `game_library.json` |
| `run_state.py` | Session state — resumable from `runs/wave_001/run_state.json` |
| `path_guard.py` | Enforces cell ownership — prevents cross-cell writes |
| `validate_run_config.py` | Schema-validates `run_config.json` before execution |
| `validate_game_library.py` | Checks library readiness, flags missing `human_notes` |

### Output Structure (`factory/`)

```
factory/
├── references/
│   └── game_library.json          ← source game database
├── mechanics/wave_001/cell_*/     ← mechanic_sheet.md
├── concepts/wave_001/cell_*/      ← director_plan.md/json, concept_card_NN.md
├── specs/wave_001/cell_*/         ← prototype_spec.md
├── prototypes/wave_001/cell_*/    ← prototype.html
├── evaluations/wave_001/cell_*/   ← evaluation_report.md, human_review.md
├── scorecards/wave_001/cell_*/    ← scorecard.json
└── portfolio/wave_001/            ← cross-cell ranking
```

Every artifact has a sibling `.metadata.json` file recording the role, template, model profile, and whether mock fallback was used.

### Agent Roles (`agents/`)

Roles define how each stage behaves. The two designer roles are the most important:

- **`fusion_designer_conservative`** — preserves source game system functions, reassigns roles for a unified verb. High clarity, low learning friction.
- **`fusion_designer_novelty`** — replaces verbs/objects aggressively if it creates a stronger loop. High novelty, accepts more risk.
- **`fusion_director`** — plans variation targets (conservative vs novelty) from source games before designers run.
- **`deconstructor`** — extracts player verbs, system functions, failure modes, depth sources from game library entries.
- **`prototype_spec_writer`** — converts concept cards to exact buildable specs (board, win/lose, level goals).
- **`prototype_builder_web`** — produces playable HTML/JS/Canvas prototype with deterministic win/lose.
- **`prototype_critic`** — evaluates the prototype on 6 dimensions: clarity, depth, level_scalability, production_feasibility, retention_potential, novelty.

### Game Library (`factory/references/game_library.json`)

Each entry extends the PuzzleFusionEngine schema with `human_notes` — the key differentiator:

```json
{
  "id": "ios-...",
  "name": "...",
  "mechanics": ["queue_sort", "path_creation"],
  "description": "...",        // full prose description
  "detail_text": "...",        // extended mechanical detail
  "human_notes": {
    "winning_points": [...],   // what makes it satisfying
    "adopt": [...],            // system functions to carry forward
    "avoid": [...],            // surface elements to drop
    "main_goal": "...",        // one-sentence player goal
    "stress_points": [...],    // where the loop creates pressure
    "fun_points": [...]        // where reward is delivered
  }
}
```

`human_notes` is consumed directly by `agent_runtime.py`'s `_normalize_game()` and injected into agent prompts. **Never leave `human_notes` empty for a source game that will be used in a cell** — it degrades concept quality significantly.

### Model Routing

Each agent role maps to either the `cloud` or `local` profile via `run_config.json`'s `routing` section. Profiles are resolved at runtime by `model_router.py`:

```json
"routing": {
  "cloud_roles": ["fusion_director", "fusion_designer_conservative", ...],
  "local_roles": ["prototype_builder_web"]
},
"models": {
  "cloud": { "provider": "openai", "model": "gpt-4o-mini" },
  "local": { "provider": "ollama", "model": "qwen3:14b" }
}
```

Supported providers:

| Provider | How it works | Requires |
|---|---|---|
| `openai` | HTTP to OpenAI chat/completions | `OPENAI_API_KEY` |
| `ollama` | HTTP to local Ollama server | Ollama running locally |
| `claude` | Shells out to `claude -p …` (Claude Code CLI) | `claude` in PATH, logged-in session — **no API key** |
| `codex` | Shells out to `codex exec …` (OpenAI Codex CLI) | `codex` in PATH + valid Codex session |
| `mock` | Fills templates deterministically — no LLM | Nothing |

`mock` is the default. Enable `allow_mock_fallback: true` in `run_config.json` to fall back to mock when a real provider fails, rather than aborting.

### Prototype Iteration Loop (spec 014)

After `prototype_builder_web` generates `prototype.html`, an optional closed feedback loop runs:

1. **Run** — load HTML in headless Playwright Chromium, capture JS errors + two screenshots
2. **Critique** — Claude vision CLI evaluates screenshots against a 5-point rubric (`board_visible`, `elements_present`, `interactive_hint`, `state_changed`, `readable`)
3. **Patch** — Claude CLI rewrites the HTML targeting failed criteria
4. **Repeat** — up to `max_rounds`, or until `pass_threshold` criteria pass

Enable in `run_config.json`:
```json
"prototype_iteration": {
  "enabled": true,
  "max_rounds": 4,
  "levels": ["errors", "visual"],
  "budget_seconds": 300,
  "pass_threshold": 4
}
```

Artifacts land in `factory/prototypes/<wave>/<cell>/iterations/round_NN/`. The loop is skipped gracefully if Playwright is not installed (install with `pip install playwright && playwright install chromium`).

### Decision Policy

Configured entirely in `run_config.json` — no code changes needed to retune:

```json
"decision_policy": {
  "weights": { "clarity": 0.25, "depth": 0.2, ... },
  "thresholds": { "expand_min": 80, "iterate_min": 60, "kill_max": 59 },
  "hard_gates": { "playable_required": true, "min_clarity": 3.5 }
}
```

Scores 0-5 per dimension → weighted to 0-100 → classified as **Escalate** / **Iterate** / **Kill**. Hard gates can override the weighted score (e.g. a non-playable prototype is always killed regardless of score).

Human feedback integrates via `runs/wave_001/human_overrides.json`. Mode `advisory_window` auto-finalises after `timeout_hours` if no override is provided.

## Environment Configuration

Create `.env` at the repo root (loaded manually — see scripts):

```bash
# Cloud LLM provider for reasoning roles
PF_CLOUD_PROVIDER=claude          # openai | ollama | claude | codex | mock
PF_CLOUD_MODEL=claude-sonnet-4    # ignored for claude/codex CLI providers

# Local LLM provider for builder roles (usually lighter)
PF_LOCAL_PROVIDER=ollama
PF_LOCAL_MODEL=qwen3:14b

# OpenAI (when PF_CLOUD_PROVIDER=openai)
OPENAI_API_KEY=sk-...
OPENAI_BASE_URL=https://api.openai.com/v1

# Ollama (when using ollama)
OLLAMA_BASE_URL=http://localhost:11434/api

# CLI provider paths & timeouts (when using claude or codex)
# CLAUDE_CLI_PATH=claude
# PF_CLAUDE_CLI_TIMEOUT_SECONDS=120
# CODEX_CLI_PATH=codex
# PF_CODEX_CLI_MODEL=gpt-5.3-codex
# PF_CODEX_CLI_TIMEOUT_SECONDS=120

# Safety
PF_ALLOW_MOCK_FALLBACK=true       # fall back to mock instead of aborting on provider error
```

## Spec-Kit Process (Mandatory)

Every non-trivial change must follow this order before implementation:

1. `specs/<NNN>-<slug>/spec.md` — problem, solution, acceptance criteria
2. `specs/<NNN>-<slug>/plan.md` — implementation approach and trade-offs
3. `specs/<NNN>-<slug>/tasks.md` — ordered task list

Work follows task order unless a blocker is explicitly documented. See existing `specs/` for examples.

## Constitution

Non-negotiable rules in `.specify/memory/constitution.md`:

1. **Structure is contract** — `factory/*` folder layout is mandatory and stable
2. **Spec before implementation** — spec → plan → tasks before any code
3. **Role and template compliance** — behavior from `agents/*.md`, output shape from `templates/*.md`
4. **Cell isolation** — cells write only to their own subdirectory; cross-cell sync only at evaluation stage
5. **Playability gate** — a concept is not evaluable without a prototype with deterministic win/lose
6. **Decisioning is tunable and auditable** — policy in run_config, human override trail preserved
7. **Session continuity** — full state recoverable from repo files alone

## Agentic Implementation Workflow

For non-trivial features or fixes, use a subagent-based workflow where Codex subagents implement and Claude Code orchestrates review and merge.

### Roles

| Role | Tool | Responsibility |
|---|---|---|
| **Orchestrator** | Claude Code (this session) | Task decomposition, PR review, merge |
| **Implementor** | OpenAI Codex CLI subagent | Code changes in an isolated worktree branch |

### Step-by-step

1. **Spawn a Codex subagent** with model `gpt-5.3-codex` in an isolated worktree:
   ```bash
   codex exec -m gpt-5.3-codex --full-auto \
     -C /path/to/PuzzeFactory \
     "<full task description with acceptance criteria>"
   ```
   - Each subagent works in its own `git worktree` branch so `main` is never touched.
   - Multiple independent tasks can be parallelised by spawning multiple subagents simultaneously.

2. **Subagent creates a PR** when done:
   ```bash
   gh pr create --title "<title>" --body "<summary + test plan>"
   ```

3. **Claude Code reviews the PR**:
   - `gh pr diff <number>` / `gh pr checks <number>`
   - `gh pr review <number> --comment -b "<feedback>"`
   - If changes needed, re-invoke subagent with PR URL and feedback.

4. **Claude Code merges** once approved:
   ```bash
   gh pr merge <number> --squash --delete-branch
   ```

### Subagent invocation template

```bash
codex exec \
  -m gpt-5.3-codex \
  --full-auto \
  -C /path/to/PuzzeFactory \
  "Branch: feat/<task-slug>  (create as a git worktree from main)

Task: <description>

Acceptance criteria:
- <criterion 1>
- <criterion 2>

When done: run python -m pytest .specify/scripts/python/tests/ -v, fix any failures, then push the branch and open a PR to main with a summary and test plan."
```

### Guidelines

- **One subagent per independent concern.** Follow the spec-kit: each concern should already have a `specs/` entry.
- **Subagents must not touch `main` directly.**
- **Iterate at most 2 rounds** of review per PR. If still failing, redesign the task.
- Subagents must run `python -m pytest .specify/scripts/python/tests/ -v` before opening the PR.
