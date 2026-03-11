#!/usr/bin/env python3
import json
from pathlib import Path


def load_game_library(repo_root: Path) -> dict[str, dict]:
    path = repo_root / "factory" / "references" / "game_library.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    return {entry["id"]: entry for entry in data}


def resolve_games(repo_root: Path, source_game_ids: list[str]) -> list[dict]:
    library = load_game_library(repo_root)
    resolved = []
    for game_id in source_game_ids:
        if game_id not in library:
            raise KeyError(f"unknown source game id: {game_id}")
        resolved.append(library[game_id])
    return resolved
