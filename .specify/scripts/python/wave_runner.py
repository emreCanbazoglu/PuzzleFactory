#!/usr/bin/env python3
import json
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from agent_runtime import (
    deterministic_scores,
    generate_director_brief,
    generate_human_review_stub,
    generate_prototype_html,
    generate_text_artifact,
    write_metadata,
)
from game_library import resolve_games
from model_router import resolve_profile_for_role
from path_guard import cell_output_path
from run_state import add_cell_artifact, load_or_init_state, now_iso, set_cell_status, write_state


def _write_text(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8")


def _metadata_path_for(artifact_path: Path) -> Path:
    return artifact_path.with_suffix(artifact_path.suffix + ".metadata.json")


def _generate_stage_text(
    *,
    repo_root: Path,
    cfg: dict,
    wave_id: str,
    cell: dict,
    role: str,
    artifact_type: str,
    area: str,
    filename: str,
    context: dict,
) -> tuple[str, str]:
    profile = resolve_profile_for_role(cfg, role)
    content, fallback_used, template_name = generate_text_artifact(
        repo_root=repo_root,
        role=role,
        artifact_type=artifact_type,
        context=context,
        profile=profile,
        config=cfg,
    )

    artifact_path = cell_output_path(repo_root, area, wave_id, cell["cell_id"], filename)
    _write_text(artifact_path, content)

    meta_path = _metadata_path_for(artifact_path)
    write_metadata(
        metadata_path=meta_path,
        wave_id=wave_id,
        cell_id=cell["cell_id"],
        role=role,
        template_name=template_name,
        profile=profile,
        artifact_path=artifact_path,
        fallback_used=fallback_used,
    )
    return str(artifact_path), str(meta_path)


def run_cell(repo_root: Path, cfg: dict, wave_id: str, cell: dict) -> list[str]:
    cid = cell["cell_id"]
    source_games = resolve_games(repo_root, cell.get("source_game_ids", []))
    context = {
        "wave_id": wave_id,
        "cell_id": cid,
        "discovery_domain": cell.get("discovery_domain", "hybrid"),
        "prototype_domain": cell.get("prototype_domain", "hybrid"),
        "concept_count": cell.get("concept_count", 3),
        "source_games": source_games,
    }

    outputs: list[str] = []

    director_brief = generate_director_brief(context)
    context["director_brief"] = director_brief
    director_path = cell_output_path(repo_root, "concepts", wave_id, cid, "director_brief.md")
    _write_text(director_path, director_brief)
    outputs.append(str(director_path))
    director_meta = _metadata_path_for(director_path)
    write_metadata(
        metadata_path=director_meta,
        wave_id=wave_id,
        cell_id=cid,
        role="fusion_director",
        template_name="director_brief_builtin",
        profile=resolve_profile_for_role(cfg, "fusion_director"),
        artifact_path=director_path,
        fallback_used=True,
    )
    outputs.append(str(director_meta))

    # Stage 1: mechanic extraction
    ap, mp = _generate_stage_text(
        repo_root=repo_root,
        cfg=cfg,
        wave_id=wave_id,
        cell=cell,
        role="deconstructor",
        artifact_type="mechanic_sheet",
        area="mechanics",
        filename="mechanic_sheet.md",
        context=context,
    )
    outputs.extend([ap, mp])

    review_content, review_template = generate_human_review_stub(repo_root, context)
    review_path = cell_output_path(repo_root, "evaluations", wave_id, cid, "human_review.md")
    _write_text(review_path, review_content)
    outputs.append(str(review_path))
    review_meta = _metadata_path_for(review_path)
    write_metadata(
        metadata_path=review_meta,
        wave_id=wave_id,
        cell_id=cid,
        role="human_feedback",
        template_name=review_template,
        profile={"name": "human", "provider": "human", "model": "n/a"},
        artifact_path=review_path,
        fallback_used=True,
    )
    outputs.append(str(review_meta))

    # Stage 2: concept design (conservative + novelty then merge)
    ap1, mp1 = _generate_stage_text(
        repo_root=repo_root,
        cfg=cfg,
        wave_id=wave_id,
        cell=cell,
        role="fusion_designer_conservative",
        artifact_type="concept_card",
        area="concepts",
        filename="concept_card_conservative.md",
        context=context,
    )
    ap2, mp2 = _generate_stage_text(
        repo_root=repo_root,
        cfg=cfg,
        wave_id=wave_id,
        cell=cell,
        role="fusion_designer_novelty",
        artifact_type="concept_card",
        area="concepts",
        filename="concept_card_novelty.md",
        context=context,
    )
    outputs.extend([ap1, mp1, ap2, mp2])

    chosen_path = cell_output_path(repo_root, "concepts", wave_id, cid, "concept_card.md")
    chosen_content = Path(ap1).read_text(encoding="utf-8")
    _write_text(chosen_path, chosen_content)
    outputs.append(str(chosen_path))

    # Stage 3: prototype spec
    ap, mp = _generate_stage_text(
        repo_root=repo_root,
        cfg=cfg,
        wave_id=wave_id,
        cell=cell,
        role="prototype_spec_writer",
        artifact_type="prototype_spec",
        area="specs",
        filename="prototype_spec.md",
        context=context,
    )
    outputs.extend([ap, mp])

    # Stage 4: prototype build (web)
    prototype_path = cell_output_path(repo_root, "prototypes", wave_id, cid, "prototype.html")
    _write_text(prototype_path, generate_prototype_html(context))
    outputs.append(str(prototype_path))
    prototype_meta = _metadata_path_for(prototype_path)
    write_metadata(
        metadata_path=prototype_meta,
        wave_id=wave_id,
        cell_id=cid,
        role="prototype_builder_web",
        template_name="prototype_html_builtin",
        profile=resolve_profile_for_role(cfg, "prototype_builder_web"),
        artifact_path=prototype_path,
        fallback_used=True,
    )
    outputs.append(str(prototype_meta))

    # Stage 5: evaluation
    ap, mp = _generate_stage_text(
        repo_root=repo_root,
        cfg=cfg,
        wave_id=wave_id,
        cell=cell,
        role="prototype_critic",
        artifact_type="evaluation_report",
        area="evaluations",
        filename="evaluation_report.md",
        context=context,
    )
    outputs.extend([ap, mp])

    # Scorecard for decision engine
    score_seed = "-".join(game["id"] for game in source_games)
    scores = deterministic_scores(cid, score_seed)
    scorecard_path = cell_output_path(repo_root, "scorecards", wave_id, cid, "scorecard.json")
    scorecard_path.write_text(
        json.dumps(
            {
                "wave_id": wave_id,
                "cell_id": cid,
                "concept_id": f"{cid}_concept_01",
                "scores": scores,
                "prototype_domain": context["prototype_domain"],
                "source_games": [game["name"] for game in source_games],
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

    futures: dict = {}
    with ThreadPoolExecutor(max_workers=len(cells)) as ex:
        for cell in cells:
            cid = cell["cell_id"]
            set_cell_status(state, cid, "running", "cell_generation")
            write_state(state_path, state)
            futures[ex.submit(run_cell, repo_root, cfg, wave_id, cell)] = cid

        for future in as_completed(futures):
            cid = futures[future]
            try:
                artifact_paths = future.result()
                for artifact_path in artifact_paths:
                    add_cell_artifact(state, cid, artifact_path)
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
