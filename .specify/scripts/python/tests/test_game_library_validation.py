import json
import tempfile
import unittest
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[4]
SYS_PATH = ROOT / ".specify" / "scripts" / "python"
if str(SYS_PATH) not in sys.path:
    sys.path.append(str(SYS_PATH))

from validate_game_library import render_markdown, validate_entry, validate_library  # noqa: E402


class TestGameLibraryValidation(unittest.TestCase):
    def test_ready_entry_passes_without_questions(self):
        entry = {
            "id": "game-1",
            "name": "Example Game",
            "board_type": "grid",
            "mechanics": ["queue_sort", "path_creation"],
            "description": "Players route colored boxes around a perimeter conveyor to collect blockers in the right order before the dock fills.",
            "detail_text": "The board has a central stack of blockers and a surrounding conveyor. Players dispatch color-coded carriers with limited capacity, route them past slots, and clear the stack before move budget or dock lockout ends the level.",
            "store_links": {"app_store": "https://example.com/game"},
            "source_metadata": {
                "source": "store_ingestion",
                "provider": "app_store",
                "source_link": "https://example.com/game",
                "ingested_at": "2026-03-01",
            },
            "last_verified_at": "2026-03-09",
            "human_notes": {
                "winning_points": ["Unlocking a blocked route", "Clearing a full color set"],
                "adopt": ["Perimeter conveyor pressure", "Clear reveal order"],
                "avoid": ["Busy meta layers"],
                "main_goal": "Clear the blocker board by dispatching the right carriers in the correct order.",
                "stress_points": ["Limited dock space"],
                "fun_points": ["Watching a planned route resolve cleanly"],
            },
        }

        result = validate_entry(entry)

        self.assertEqual(result["status"], "ready")
        self.assertEqual(result["schema_issues"], [])
        self.assertEqual(result["quality_issues"], [])
        self.assertEqual(result["questions_for_human"], [])

    def test_missing_design_understanding_requires_human_clarification(self):
        entry = {
            "id": "game-2",
            "name": "Weakly Described Game",
            "board_type": "grid",
            "mechanics": ["restricted_space"],
            "description": "",
            "detail_text": "",
            "store_links": {"app_store": "https://example.com/game-2"},
            "source_metadata": {
                "source": "store_ingestion",
                "provider": "app_store",
                "source_link": "https://example.com/game-2",
                "ingested_at": "2026-03-01",
            },
            "last_verified_at": "2026-03-09",
            "human_notes": {
                "winning_points": [],
                "adopt": [],
                "avoid": [],
                "main_goal": "",
                "stress_points": [],
                "fun_points": [],
            },
        }

        result = validate_entry(entry)

        self.assertEqual(result["status"], "needs_human_clarification")
        self.assertEqual(result["schema_issues"], [])
        self.assertGreater(len(result["quality_issues"]), 0)
        self.assertTrue(any("winning points" in question.lower() for question in result["questions_for_human"]))

    def test_invalid_entry_reports_schema_and_date_issues(self):
        entry = {
            "id": "game-3",
            "name": "Broken Game",
            "board_type": "",
            "mechanics": [],
            "description": "Short",
            "detail_text": "Too short",
            "store_links": {},
            "source_metadata": {"source": "", "provider": "", "source_link": "", "ingested_at": "2026-13-40"},
            "last_verified_at": "not-a-date",
            "human_notes": {},
        }

        result = validate_entry(entry)

        self.assertEqual(result["status"], "invalid")
        self.assertTrue(any("board_type" in issue for issue in result["schema_issues"]))
        self.assertTrue(any("last_verified_at" in issue for issue in result["schema_issues"]))

    def test_validate_library_and_markdown_report(self):
        with tempfile.TemporaryDirectory() as tmp:
            library_path = Path(tmp) / "game_library.json"
            library_path.write_text(
                json.dumps(
                    [
                        {
                            "id": "game-1",
                            "name": "Example Game",
                            "board_type": "grid",
                            "mechanics": ["queue_sort"],
                            "description": "Players route carriers around a track to clear blockers before the dock jams.",
                            "detail_text": "A loop conveyor surrounds a central board. Players dispatch limited carriers from docks, collect matching blockers, and solve the board before losing their move budget.",
                            "store_links": {"app_store": "https://example.com"},
                            "source_metadata": {
                                "source": "store_ingestion",
                                "provider": "app_store",
                                "source_link": "https://example.com",
                                "ingested_at": "2026-03-01",
                            },
                            "last_verified_at": "2026-03-09",
                            "human_notes": {
                                "winning_points": ["Reveal order", "Board cleanup"],
                                "adopt": ["Conveyor pressure", "Small capacity carriers"],
                                "avoid": ["Noisy progression"],
                                "main_goal": "Clear the board using the right carriers before the dock jams.",
                                "stress_points": ["Dock lockout"],
                                "fun_points": ["Clean board resolution"],
                            },
                        }
                    ]
                ),
                encoding="utf-8",
            )

            report = validate_library(library_path)
            markdown = render_markdown(report)

            self.assertEqual(report["summary"]["entries_checked"], 1)
            self.assertIn("Entries Ready", markdown)
            self.assertIn("Example Game", markdown)


if __name__ == "__main__":
    unittest.main()
