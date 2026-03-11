#!/usr/bin/env python3
import json
import sys
from pathlib import Path

from decision_register import append_records

METRICS = [
    "clarity",
    "depth",
    "level_scalability",
    "production_feasibility",
    "retention_potential",
    "novelty",
]


def classify(score_100: float, thresholds: dict, playable: bool, min_clarity: float, clarity: float) -> str:
    if not playable:
        return "Kill"
    if clarity < min_clarity:
        return "Kill"
    if score_100 >= thresholds["expand_min"]:
        return "Escalate"
    if score_100 >= thresholds["iterate_min"]:
        return "Iterate"
    return "Kill"


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: decision_engine.py <run_config.json>")
        return 1

    config_path = Path(sys.argv[1]).resolve()
    repo_root = config_path.parents[2]
    cfg = json.loads(config_path.read_text(encoding="utf-8"))
    wave_id = cfg["wave_id"]
    policy = cfg["decision_policy"]
    weights = policy["weights"]
    thresholds = policy["thresholds"]
    min_clarity = policy["hard_gates"]["min_clarity"]

    records = []
    for cell in cfg["cells"]:
        scorecard_path = repo_root / "factory" / "scorecards" / wave_id / cell["cell_id"] / "scorecard.json"
        if not scorecard_path.exists():
            continue
        row = json.loads(scorecard_path.read_text(encoding="utf-8"))
        scores = row["scores"]
        normalized = sum((scores[m] / 5.0) * weights[m] for m in METRICS)
        score_100 = round(normalized * 100.0, 2)
        auto = classify(score_100, thresholds, row.get("playable", False), min_clarity, scores.get("clarity", 0))
        records.append(
            {
                "concept_id": row["concept_id"],
                "cell_id": row["cell_id"],
                "auto_score": score_100,
                "auto_decision": auto,
                "final_decision": auto,
                "mode": cfg["human_feedback"]["mode"],
                "override": None,
                "finalized_at": None,
                "rationale": "Auto decision from weighted policy",
            }
        )

    out_path = repo_root / "runs" / wave_id / "auto_decisions.json"
    out_path.write_text(json.dumps(records, indent=2) + "\n", encoding="utf-8")

    register_path = repo_root / "runs" / wave_id / "decision_register.json"
    append_records(register_path, records)
    print(f"OK: decisions computed -> {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
