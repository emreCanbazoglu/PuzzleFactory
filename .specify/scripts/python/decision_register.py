#!/usr/bin/env python3
import json
from pathlib import Path


def append_records(register_path: Path, records: list[dict]) -> None:
    register = {"wave_id": "unknown", "mode": "advisory_window", "records": []}
    if register_path.exists():
        register = json.loads(register_path.read_text(encoding="utf-8"))

    register.setdefault("records", []).extend(records)
    register_path.write_text(json.dumps(register, indent=2) + "\n", encoding="utf-8")
