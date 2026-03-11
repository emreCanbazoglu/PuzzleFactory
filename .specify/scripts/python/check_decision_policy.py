#!/usr/bin/env python3
import json
import math
import sys
from pathlib import Path


def fail(msg: str) -> None:
    print(f"ERROR: {msg}")
    raise SystemExit(1)


def validate(path: Path) -> None:
    data = json.loads(path.read_text(encoding="utf-8"))
    policy = data.get("decision_policy", {})
    weights = policy.get("weights", {})
    thresholds = policy.get("thresholds", {})

    required_weights = [
        "clarity",
        "depth",
        "level_scalability",
        "production_feasibility",
        "retention_potential",
        "novelty",
    ]
    for key in required_weights:
        val = weights.get(key)
        if not isinstance(val, (int, float)):
            fail(f"missing numeric decision_policy.weights.{key}")

    total = sum(float(weights[k]) for k in required_weights)
    if not math.isclose(total, 1.0, rel_tol=1e-6, abs_tol=1e-6):
        fail(f"decision_policy.weights must sum to 1.0; got {total}")

    expand_min = thresholds.get("expand_min")
    iterate_min = thresholds.get("iterate_min")
    kill_max = thresholds.get("kill_max")

    for name, value in [("expand_min", expand_min), ("iterate_min", iterate_min), ("kill_max", kill_max)]:
        if not isinstance(value, (int, float)):
            fail(f"decision_policy.thresholds.{name} must be numeric")

    if not (expand_min > iterate_min and iterate_min > kill_max):
        fail("thresholds must satisfy expand_min > iterate_min > kill_max")

    print(f"OK: decision policy valid -> {path}")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        fail("usage: check_decision_policy.py <run_config.json>")
    validate(Path(sys.argv[1]))
