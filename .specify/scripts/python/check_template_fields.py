#!/usr/bin/env python3
from pathlib import Path

REQUIRED = {
    "templates/mechanic_sheet.md": [
        "Core Verb:",
        "Primary Decision:",
        "Failure Mode:",
        "Depth Source:",
    ],
    "templates/concept_card.md": [
        "Concept Name:",
        "Main Interaction:",
        "Objective:",
        "Prototype Scope:",
    ],
    "templates/prototype_spec.md": [
        "Core Loop:",
        "Win Condition:",
        "Lose Condition:",
        "Success Criteria:",
    ],
    "templates/evaluation_report.md": [
        "Clarity:",
        "Depth:",
        "Recommendation:",
    ],
}


def main() -> int:
    failed = False
    for rel_path, markers in REQUIRED.items():
        path = Path(rel_path)
        if not path.exists():
            print(f"ERROR: missing template {rel_path}")
            failed = True
            continue
        content = path.read_text(encoding="utf-8")
        for marker in markers:
            if marker not in content:
                print(f"ERROR: {rel_path} missing marker: {marker}")
                failed = True
    if failed:
        return 1
    print("OK: template fields complete")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
