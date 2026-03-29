#!/usr/bin/env python3
import json
import sys
from datetime import datetime
from pathlib import Path

from game_library import load_game_library
from validate_game_library import validate_entry


def fail(message: str) -> None:
    print(f"ERROR: {message}")
    raise SystemExit(1)


def summarize_game(entry: dict) -> list[str]:
    notes = entry.get("human_notes") or {}
    lines = [
        f"- Name: {entry.get('name', '')}",
        f"- Board Type: {entry.get('board_type', '')}",
        f"- Mechanics: {', '.join(entry.get('mechanics') or [])}",
        f"- Description: {entry.get('description') or '[missing]'}",
        f"- Detail Text: {entry.get('detail_text') or '[missing]'}",
        f"- Main Goal: {notes.get('main_goal') or '[missing]'}",
        f"- Winning Points: {', '.join(notes.get('winning_points') or []) or '[missing]'}",
        f"- Adopt: {', '.join(notes.get('adopt') or []) or '[missing]'}",
        f"- Avoid: {', '.join(notes.get('avoid') or []) or '[missing]'}",
        f"- Stress Points: {', '.join(notes.get('stress_points') or []) or '[missing]'}",
        f"- Fun Points: {', '.join(notes.get('fun_points') or []) or '[missing]'}",
        f"- Last Verified At: {entry.get('last_verified_at') or '[missing]'}",
    ]
    return lines


def render_review_brief(entry: dict, validation: dict) -> str:
    lines = [
        "# Game Library Review Session",
        "",
        f"Generated At: {datetime.now().replace(microsecond=0).isoformat()}",
        f"Game: {validation['game_name']}",
        f"Game ID: {validation['game_id']}",
        f"Status: {validation['status']}",
        "",
        "Current Summary:",
        *summarize_game(entry),
        "",
        "Open Issues:",
    ]

    issues = validation["schema_issues"] + validation["quality_issues"]
    if issues:
        lines.extend(f"- {issue}" for issue in issues)
    else:
        lines.append("- None")

    lines.extend(["", "Questions For Human:"])
    if validation["questions_for_human"]:
        for idx, question in enumerate(validation["questions_for_human"], start=1):
            lines.append(f"{idx}. {question}")
    else:
        lines.append("- None")

    lines.extend(
        [
            "",
            "Answers / Decisions:",
            "- Fill this section during the human-agent review conversation.",
            "",
            "Next Action:",
            "- If status is `ready`, no review is required unless the human wants to improve the entry.",
            "- If status is `needs_human_clarification`, answer the questions and update `factory/references/game_library.json`.",
            "- Re-run `python3 .specify/scripts/python/validate_game_library.py` after edits.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> None:
    if len(sys.argv) != 2:
        fail("usage: prepare_game_library_review.py <game_id>")

    game_id = sys.argv[1]
    repo_root = Path(__file__).resolve().parents[3]
    library = load_game_library(repo_root)
    entry = library.get(game_id)
    if entry is None:
        fail(f"unknown game id: {game_id}")

    validation = validate_entry(entry)
    output_dir = repo_root / "factory" / "references" / "reviews" / game_id
    output_dir.mkdir(parents=True, exist_ok=True)

    brief_path = output_dir / "review_session.md"
    json_path = output_dir / "review_session.json"

    brief_path.write_text(render_review_brief(entry, validation), encoding="utf-8")
    json_path.write_text(
        json.dumps(
            {
                "generated_at": datetime.now().replace(microsecond=0).isoformat(),
                "game_id": validation["game_id"],
                "game_name": validation["game_name"],
                "status": validation["status"],
                "schema_issues": validation["schema_issues"],
                "quality_issues": validation["quality_issues"],
                "questions_for_human": validation["questions_for_human"],
                "entry_snapshot": entry,
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    print(f"OK: review brief -> {brief_path}")


if __name__ == "__main__":
    main()
