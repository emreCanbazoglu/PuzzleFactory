#!/usr/bin/env python3
import json
import sys
from datetime import date, datetime
from pathlib import Path


REQUIRED_NOTE_LISTS = {
    "winning_points": 2,
    "adopt": 2,
    "avoid": 1,
    "stress_points": 1,
    "fun_points": 1,
}

REQUIRED_NOTE_TEXT = {
    "main_goal": 20,
}


def fail(message: str) -> None:
    print(f"ERROR: {message}")
    raise SystemExit(1)


def parse_iso_date(value: str | None, field_name: str, issues: list[str], *, stale_days: int | None = None) -> date | None:
    if not isinstance(value, str) or not value.strip():
        issues.append(f"{field_name} must be a non-empty YYYY-MM-DD string")
        return None

    try:
        parsed = datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError:
        issues.append(f"{field_name} must use YYYY-MM-DD format")
        return None

    if parsed > date.today():
        issues.append(f"{field_name} cannot be in the future")
        return parsed

    if stale_days is not None and (date.today() - parsed).days > stale_days:
        issues.append(f"{field_name} is older than {stale_days} days")

    return parsed


def is_meaningful_text(value: object, minimum_length: int) -> bool:
    if not isinstance(value, str):
        return False
    return len(" ".join(value.split())) >= minimum_length


def normalize_string_list(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    items = []
    for item in value:
        if isinstance(item, str):
            text = " ".join(item.split())
            if text:
                items.append(text)
    return items


def build_question(field_name: str, game_name: str) -> str:
    prompts = {
        "description": f"What is the clearest 1-2 sentence player-facing description of {game_name}, including the core action and objective?",
        "detail_text": f"Describe {game_name} in enough detail for fusion work: board layout, input, turn loop, pressure, failure mode, and why a good move feels good.",
        "winning_points": f"What are the top 2-3 winning points of {game_name}: the moments or systems that make players want one more try?",
        "adopt": f"For {game_name}, which 2-3 mechanics or presentation patterns should the factory actively adopt into fusions?",
        "avoid": f"For {game_name}, which mechanic patterns or UX traits should the factory avoid copying because they are weak, noisy, or too derivative?",
        "main_goal": f"What is the exact main goal the player is pursuing in {game_name} on a typical level?",
        "stress_points": f"What creates tension in {game_name}: queue pressure, move limits, deadlock risk, blocked access, or something else?",
        "fun_points": f"What is satisfying in {game_name}: reveal order, combo payoff, cleanup, route completion, etc.?",
        "store_links": f"Which store or source link should be kept as the canonical reference for {game_name}?",
        "source_metadata": f"What is the trusted provenance for {game_name}: source, provider, source link, and ingestion date?",
        "last_verified_at": f"What is the correct last verification date for {game_name} in YYYY-MM-DD format?",
    }
    return prompts[field_name]


def validate_entry(entry: dict) -> dict:
    schema_issues: list[str] = []
    quality_issues: list[str] = []
    questions: list[str] = []

    game_id = entry.get("id")
    game_name = entry.get("name") or str(game_id or "Unknown Game")

    if not isinstance(game_id, str) or not game_id.strip():
        schema_issues.append("id must be a non-empty string")
    if not isinstance(entry.get("name"), str) or not entry["name"].strip():
        schema_issues.append("name must be a non-empty string")
    if not isinstance(entry.get("board_type"), str) or not entry["board_type"].strip():
        schema_issues.append("board_type must be a non-empty string")

    mechanics = normalize_string_list(entry.get("mechanics"))
    if not mechanics:
        schema_issues.append("mechanics must contain at least one non-empty mechanic tag")

    store_links = entry.get("store_links")
    if not isinstance(store_links, dict) or not any(isinstance(v, str) and v.strip() for v in store_links.values()):
        schema_issues.append("store_links must contain at least one non-empty link")
        questions.append(build_question("store_links", game_name))

    source_metadata = entry.get("source_metadata")
    if not isinstance(source_metadata, dict):
        schema_issues.append("source_metadata must be an object")
        questions.append(build_question("source_metadata", game_name))
    else:
        for key in ("source", "provider"):
            if not isinstance(source_metadata.get(key), str) or not source_metadata[key].strip():
                schema_issues.append(f"source_metadata.{key} must be a non-empty string")
        if not isinstance(source_metadata.get("source_link"), str) or not source_metadata["source_link"].strip():
            schema_issues.append("source_metadata.source_link must be a non-empty string")
        parse_iso_date(source_metadata.get("ingested_at"), "source_metadata.ingested_at", schema_issues)

    verification_issues: list[str] = []
    parse_iso_date(entry.get("last_verified_at"), "last_verified_at", verification_issues, stale_days=180)
    if verification_issues:
        if any("older than" in issue for issue in verification_issues):
            quality_issues.extend(verification_issues)
        else:
            schema_issues.extend(verification_issues)
        questions.append(build_question("last_verified_at", game_name))

    if not is_meaningful_text(entry.get("description"), 50):
        quality_issues.append("description is missing or too weak for deconstruction")
        questions.append(build_question("description", game_name))

    if not is_meaningful_text(entry.get("detail_text"), 100):
        quality_issues.append("detail_text is missing or too weak for fusion/prototyping")
        questions.append(build_question("detail_text", game_name))

    notes = entry.get("human_notes")
    if not isinstance(notes, dict):
        quality_issues.append("human_notes is missing")
        for field_name in list(REQUIRED_NOTE_LISTS) + list(REQUIRED_NOTE_TEXT):
            questions.append(build_question(field_name, game_name))
    else:
        for field_name, minimum_items in REQUIRED_NOTE_LISTS.items():
            items = normalize_string_list(notes.get(field_name))
            if len(items) < minimum_items:
                quality_issues.append(f"human_notes.{field_name} must contain at least {minimum_items} useful item(s)")
                questions.append(build_question(field_name, game_name))
        for field_name, minimum_length in REQUIRED_NOTE_TEXT.items():
            if not is_meaningful_text(notes.get(field_name), minimum_length):
                quality_issues.append(f"human_notes.{field_name} must explain the game objective clearly")
                questions.append(build_question(field_name, game_name))

    deduped_questions: list[str] = []
    seen = set()
    for question in questions:
        if question not in seen:
            deduped_questions.append(question)
            seen.add(question)

    if schema_issues:
        status = "invalid"
    elif quality_issues:
        status = "needs_human_clarification"
    else:
        status = "ready"

    return {
        "game_id": game_id,
        "game_name": game_name,
        "status": status,
        "schema_issues": schema_issues,
        "quality_issues": quality_issues,
        "questions_for_human": deduped_questions,
    }


def render_markdown(report: dict) -> str:
    lines = [
        "# Game Library Validation",
        "",
        f"Generated At: {report['generated_at']}",
        f"Library Path: {report['library_path']}",
        "",
        "Summary:",
        f"- Entries Checked: {report['summary']['entries_checked']}",
        f"- Entries Ready: {report['summary']['ready']}",
        f"- Entries Needing Human Clarification: {report['summary']['needs_human_clarification']}",
        f"- Entries Invalid: {report['summary']['invalid']}",
        "",
        "## Per Game",
        "",
    ]

    for entry in report["entries"]:
        lines.append(f"Game: {entry['game_name']} ({entry['game_id']})")
        lines.append(f"Status: {entry['status']}")
        lines.append("Schema Issues:")
        if entry["schema_issues"]:
            lines.extend(f"- {issue}" for issue in entry["schema_issues"])
        else:
            lines.append("- None")
        lines.append("Quality Issues:")
        if entry["quality_issues"]:
            lines.extend(f"- {issue}" for issue in entry["quality_issues"])
        else:
            lines.append("- None")
        lines.append("Questions For Human:")
        if entry["questions_for_human"]:
            lines.extend(f"- {question}" for question in entry["questions_for_human"])
        else:
            lines.append("- None")
        lines.append("")

    return "\n".join(lines).strip() + "\n"


def validate_library(path: Path) -> dict:
    if not path.exists():
        fail(f"game library not found: {path}")

    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        fail("game library must be a JSON array")

    entries = []
    for idx, entry in enumerate(data):
        if not isinstance(entry, dict):
            fail(f"game library entry at index {idx} must be an object")
        entries.append(validate_entry(entry))

    summary = {"entries_checked": len(entries), "ready": 0, "needs_human_clarification": 0, "invalid": 0}
    for entry in entries:
        summary[entry["status"]] += 1

    return {
        "generated_at": datetime.now().replace(microsecond=0).isoformat(),
        "library_path": str(path),
        "summary": summary,
        "entries": entries,
    }


def write_report(repo_root: Path, report: dict) -> Path:
    output_dir = repo_root / "factory" / "references" / "validation"
    output_dir.mkdir(parents=True, exist_ok=True)

    markdown_path = output_dir / "game_library_validation.md"
    json_path = output_dir / "game_library_validation.json"

    markdown_path.write_text(render_markdown(report), encoding="utf-8")
    json_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    return markdown_path


def main() -> None:
    repo_root = Path(__file__).resolve().parents[3]
    library_path = repo_root / "factory" / "references" / "game_library.json"
    report = validate_library(library_path)
    markdown_path = write_report(repo_root, report)
    print(f"OK: game library validation report -> {markdown_path}")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        fail("usage: validate_game_library.py")
    main()
