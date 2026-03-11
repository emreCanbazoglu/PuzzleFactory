#!/usr/bin/env python3
import json
from datetime import datetime, timezone
from pathlib import Path


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_or_init_state(path: Path, wave_id: str, cell_ids: list[str]) -> dict:
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    state = {
        "wave_id": wave_id,
        "status": "initialized",
        "started_at": now_iso(),
        "finished_at": None,
        "cell_states": [
            {
                "cell_id": cid,
                "status": "pending",
                "stage": "initialize",
                "artifacts": [],
                "error": None,
            }
            for cid in cell_ids
        ],
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")
    return state


def write_state(path: Path, state: dict) -> None:
    path.write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")


def set_cell_status(state: dict, cell_id: str, status: str, stage: str, error: str | None = None) -> None:
    for cell in state.get("cell_states", []):
        if cell.get("cell_id") == cell_id:
            cell["status"] = status
            cell["stage"] = stage
            cell["error"] = error
            return
    raise ValueError(f"unknown cell_id: {cell_id}")


def add_cell_artifact(state: dict, cell_id: str, artifact_path: str) -> None:
    for cell in state.get("cell_states", []):
        if cell.get("cell_id") == cell_id:
            cell.setdefault("artifacts", []).append(artifact_path)
            return
    raise ValueError(f"unknown cell_id: {cell_id}")
