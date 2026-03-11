#!/usr/bin/env python3
import json
import sys
from pathlib import Path


def fail(msg: str) -> None:
    print(f"ERROR: {msg}")
    raise SystemExit(1)


def validate(path: Path) -> None:
    if not path.exists():
        fail(f"run config not found: {path}")

    data = json.loads(path.read_text(encoding="utf-8"))

    if not isinstance(data.get("wave_id"), str) or not data["wave_id"].strip():
        fail("wave_id must be a non-empty string")

    cells = data.get("cells")
    if not isinstance(cells, list) or not cells:
        fail("cells must be a non-empty array")

    cell_ids = set()
    for idx, cell in enumerate(cells):
        if not isinstance(cell, dict):
            fail(f"cells[{idx}] must be an object")
        for key in ("cell_id", "discovery_domain", "prototype_domain"):
            if not isinstance(cell.get(key), str) or not cell[key].strip():
                fail(f"cells[{idx}].{key} must be a non-empty string")
        source_game_ids = cell.get("source_game_ids")
        if not isinstance(source_game_ids, list) or len(source_game_ids) < 2:
            fail(f"cells[{idx}].source_game_ids must be an array with at least 2 game ids")
        if any(not isinstance(game_id, str) or not game_id.strip() for game_id in source_game_ids):
            fail(f"cells[{idx}].source_game_ids must contain non-empty strings")
        concept_count = cell.get("concept_count")
        if not isinstance(concept_count, int) or concept_count < 1:
            fail(f"cells[{idx}].concept_count must be integer >= 1")
        if cell["cell_id"] in cell_ids:
            fail(f"duplicate cell_id: {cell['cell_id']}")
        cell_ids.add(cell["cell_id"])

    routing = data.get("routing")
    if not isinstance(routing, dict):
        fail("routing must be an object")
    for key in ("cloud_roles", "local_roles"):
        arr = routing.get(key)
        if not isinstance(arr, list):
            fail(f"routing.{key} must be an array")
        if any(not isinstance(x, str) or not x.strip() for x in arr):
            fail(f"routing.{key} must contain non-empty strings")

    decision = data.get("decision_policy")
    if not isinstance(decision, dict):
        fail("decision_policy must be an object")

    models = data.get("models")
    if models is not None:
        if not isinstance(models, dict):
            fail("models must be an object when provided")
        for key in ("cloud", "local"):
            if key in models:
                profile = models[key]
                if not isinstance(profile, dict):
                    fail(f"models.{key} must be an object")
                provider = profile.get("provider")
                if provider is not None and provider not in {"openai", "ollama", "mock"}:
                    fail(f"models.{key}.provider must be one of openai|ollama|mock")
                model = profile.get("model")
                if model is not None and (not isinstance(model, str) or not model.strip()):
                    fail(f"models.{key}.model must be a non-empty string when provided")

    execution = data.get("execution")
    if execution is not None:
        if not isinstance(execution, dict):
            fail("execution must be an object when provided")
        if "allow_mock_fallback" in execution and not isinstance(execution["allow_mock_fallback"], bool):
            fail("execution.allow_mock_fallback must be boolean")

    human = data.get("human_feedback")
    if human is not None:
        if not isinstance(human, dict):
            fail("human_feedback must be an object when provided")
        mode = human.get("mode")
        allowed = {"advisory_window", "hard_approval", "off"}
        if mode not in allowed:
            fail(f"human_feedback.mode must be one of {sorted(allowed)}")
        timeout = human.get("timeout_hours")
        if not isinstance(timeout, int) or timeout < 0:
            fail("human_feedback.timeout_hours must be integer >= 0")

    print(f"OK: run config valid -> {path}")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        fail("usage: validate_run_config.py <run_config.json>")
    validate(Path(sys.argv[1]))
