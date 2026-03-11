#!/usr/bin/env python3
import json
import sys
from pathlib import Path

from path_guard import portfolio_output_path


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: evaluation_sync.py <run_config.json>")
        return 1

    config_path = Path(sys.argv[1]).resolve()
    repo_root = config_path.parents[2]
    cfg = json.loads(config_path.read_text(encoding="utf-8"))
    wave_id = cfg["wave_id"]

    rows = []
    for cell in cfg["cells"]:
        scorecard = repo_root / "factory" / "scorecards" / wave_id / cell["cell_id"] / "scorecard.json"
        if scorecard.exists():
            rows.append(json.loads(scorecard.read_text(encoding="utf-8")))

    out = {
        "wave_id": wave_id,
        "aggregated_cells": len(rows),
        "scorecards": rows,
    }
    out_path = portfolio_output_path(repo_root, wave_id, "portfolio_summary.json")
    out_path.write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8")
    print(f"OK: evaluation sync complete -> {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
