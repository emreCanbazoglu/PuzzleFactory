#!/usr/bin/env python3
import json
import sys
from datetime import datetime, timezone
from pathlib import Path


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: human_feedback.py <run_config.json>")
        return 1

    config_path = Path(sys.argv[1]).resolve()
    repo_root = config_path.parents[2]
    cfg = json.loads(config_path.read_text(encoding="utf-8"))
    wave_id = cfg["wave_id"]
    mode = cfg["human_feedback"]["mode"]

    auto_path = repo_root / "runs" / wave_id / "auto_decisions.json"
    if not auto_path.exists():
        print("ERROR: auto decisions not found")
        return 1

    decisions = json.loads(auto_path.read_text(encoding="utf-8"))
    override_path = repo_root / "runs" / wave_id / "human_overrides.json"
    overrides = {}
    if override_path.exists():
        raw = json.loads(override_path.read_text(encoding="utf-8"))
        overrides = {row["concept_id"]: row for row in raw}

    for row in decisions:
        concept_id = row["concept_id"]
        if mode == "off":
            row["final_decision"] = row["auto_decision"]
            row["rationale"] = "Human feedback mode off"
        elif mode == "hard_approval":
            if concept_id in overrides:
                row["final_decision"] = overrides[concept_id]["decision"]
                row["override"] = overrides[concept_id]
                row["rationale"] = "Finalized by hard approval"
            else:
                row["final_decision"] = "PendingApproval"
                row["rationale"] = "Awaiting required human approval"
        else:  # advisory_window
            if concept_id in overrides:
                row["final_decision"] = overrides[concept_id]["decision"]
                row["override"] = overrides[concept_id]
                row["rationale"] = "Finalized by advisory override"
            else:
                row["final_decision"] = row["auto_decision"]
                row["rationale"] = "Advisory timeout fallback to auto decision"

        row["finalized_at"] = now_iso()

    out_path = repo_root / "runs" / wave_id / "final_decisions.json"
    out_path.write_text(json.dumps(decisions, indent=2) + "\n", encoding="utf-8")
    print(f"OK: decision finalization complete -> {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
