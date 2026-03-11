import json
import tempfile
import unittest
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[4]
SYS_PATH = ROOT / ".specify" / "scripts" / "python"
if str(SYS_PATH) not in sys.path:
    sys.path.append(str(SYS_PATH))

from prepare_game_library_review import render_review_brief  # noqa: E402
from validate_game_library import validate_entry  # noqa: E402


class TestGameLibraryReviewBrief(unittest.TestCase):
    def test_review_brief_includes_questions_for_unclear_game(self):
        entry = {
            "id": "game-weak",
            "name": "Weak Game",
            "board_type": "grid",
            "mechanics": ["queue_sort"],
            "description": "",
            "detail_text": "",
            "store_links": {"app_store": "https://example.com"},
            "source_metadata": {
                "source": "store_ingestion",
                "provider": "app_store",
                "source_link": "https://example.com",
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

        validation = validate_entry(entry)
        brief = render_review_brief(entry, validation)

        self.assertIn("Questions For Human:", brief)
        self.assertIn("What are the top 2-3 winning points", brief)
        self.assertIn("Answers / Decisions:", brief)

    def test_review_brief_marks_ready_game_as_not_requiring_review(self):
        entry = {
            "id": "game-ready",
            "name": "Ready Game",
            "board_type": "grid",
            "mechanics": ["queue_sort"],
            "description": "Players route carriers around a conveyor to collect blockers in the right order and clear the board before the dock jams.",
            "detail_text": "The board has a central blocker stack and a surrounding conveyor. Players choose a carrier from the dock, dispatch it onto the loop, collect matching blockers with limited capacity, and solve the level before the move budget or dock lockout ends the run.",
            "store_links": {"app_store": "https://example.com"},
            "source_metadata": {
                "source": "store_ingestion",
                "provider": "app_store",
                "source_link": "https://example.com",
                "ingested_at": "2026-03-01",
            },
            "last_verified_at": "2026-03-09",
            "human_notes": {
                "winning_points": ["Reveal order", "Cleanup payoff"],
                "adopt": ["Conveyor pressure", "Capacity-limited carriers"],
                "avoid": ["Meta clutter"],
                "main_goal": "Clear the blocker board by dispatching the right carriers in the right order.",
                "stress_points": ["Dock space"],
                "fun_points": ["Watching a plan resolve cleanly"],
            },
        }

        validation = validate_entry(entry)
        brief = render_review_brief(entry, validation)

        self.assertIn("Status: ready", brief)
        self.assertIn("If status is `ready`, no review is required", brief)


if __name__ == "__main__":
    unittest.main()
