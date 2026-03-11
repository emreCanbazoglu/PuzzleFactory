#!/usr/bin/env python3
from pathlib import Path

ALLOWED_FACTORY_AREAS = {
    "references",
    "mechanics",
    "concepts",
    "specs",
    "prototypes",
    "evaluations",
    "scorecards",
    "portfolio",
}


def cell_output_path(repo_root: Path, area: str, wave_id: str, cell_id: str, filename: str) -> Path:
    if area not in ALLOWED_FACTORY_AREAS:
        raise ValueError(f"invalid factory area: {area}")
    if not wave_id or not cell_id:
        raise ValueError("wave_id and cell_id are required")

    path = repo_root / "factory" / area / wave_id / cell_id / filename
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def portfolio_output_path(repo_root: Path, wave_id: str, filename: str) -> Path:
    path = repo_root / "factory" / "portfolio" / wave_id / filename
    path.parent.mkdir(parents=True, exist_ok=True)
    return path
