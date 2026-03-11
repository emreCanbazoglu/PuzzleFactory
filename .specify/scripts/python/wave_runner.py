#!/usr/bin/env python3
import json
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from path_guard import cell_output_path
from run_state import add_cell_artifact, load_or_init_state, now_iso, set_cell_status, write_state


def write_text(path: Path, content: str) -> str:
    path.write_text(content, encoding="utf-8")
    return str(path)


def run_cell(repo_root: Path, wave_id: str, cell: dict) -> list[str]:
    cid = cell["cell_id"]
    domain = cell["prototype_domain"]

    outputs = []
    outputs.append(
        write_text(
            cell_output_path(repo_root, "mechanics", wave_id, cid, "mechanic_sheet.md"),
            f"# Mechanic Sheet\n\nGame: {cid}\nCore Verb: TBD\nFailure Mode: TBD\nDepth Source: TBD\n",
        )
    )
    outputs.append(
        write_text(
            cell_output_path(repo_root, "concepts", wave_id, cid, "concept_card.md"),
            f"# Concept Card\n\nConcept Name: {cid}_{domain}_concept\nMain Interaction: TBD\nObjective: TBD\n",
        )
    )
    outputs.append(
        write_text(
            cell_output_path(repo_root, "specs", wave_id, cid, "prototype_spec.md"),
            "# Prototype Spec\n\nCore Loop: TBD\nWin Condition: TBD\nLose Condition: TBD\n",
        )
    )
    outputs.append(
        write_text(
            cell_output_path(repo_root, "prototypes", wave_id, cid, "prototype_stub.html"),
            "<!doctype html><html><body><h1>Prototype Stub</h1></body></html>",
        )
    )
    outputs.append(
        write_text(
            cell_output_path(repo_root, "evaluations", wave_id, cid, "evaluation_report.md"),
            "# Evaluation Report\n\nClarity: 3.5\nDepth: 3.4\nRecommendation: Iterate\n",
        )
    )
    scorecard_path = cell_output_path(repo_root, "scorecards", wave_id, cid, "scorecard.json")
    scorecard_path.write_text(
        json.dumps(
            {
                "wave_id": wave_id,
                "cell_id": cid,
                "concept_id": f"{cid}_concept_01",
                "scores": {
                    "clarity": 3.5,
                    "depth": 3.4,
                    "level_scalability": 3.6,
                    "production_feasibility": 3.8,
                    "retention_potential": 3.2,
                    "novelty": 3.1,
                },
                "prototype_domain": domain,
                "playable": True,
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    outputs.append(str(scorecard_path))
    return outputs


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: wave_runner.py <run_config.json>")
        return 1

    config_path = Path(sys.argv[1]).resolve()
    repo_root = config_path.parents[2]
    cfg = json.loads(config_path.read_text(encoding="utf-8"))
    wave_id = cfg["wave_id"]
    cells = cfg["cells"]

    state_path = repo_root / "runs" / wave_id / "run_state.json"
    state = load_or_init_state(state_path, wave_id, [c["cell_id"] for c in cells])
    state["status"] = "running"
    write_state(state_path, state)

    futures = {}
    with ThreadPoolExecutor(max_workers=len(cells)) as ex:
        for cell in cells:
            cid = cell["cell_id"]
            set_cell_status(state, cid, "running", "cell_generation")
            write_state(state_path, state)
            futures[ex.submit(run_cell, repo_root, wave_id, cell)] = cid

        for future in as_completed(futures):
            cid = futures[future]
            try:
                artifact_paths = future.result()
                for ap in artifact_paths:
                    add_cell_artifact(state, cid, ap)
                set_cell_status(state, cid, "completed", "cell_evaluation")
            except Exception as exc:
                set_cell_status(state, cid, "failed", "cell_generation", str(exc))
            write_state(state_path, state)

    state["status"] = "completed"
    state["finished_at"] = now_iso()
    write_state(state_path, state)
    print(f"OK: wave run completed -> {wave_id}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
