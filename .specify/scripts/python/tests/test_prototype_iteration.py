#!/usr/bin/env python3
"""Tests for the prototype iteration loop (spec 014)."""
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from prototype_iteration_runner import (
    BrowserResult,
    CritiqueResult,
    run_iteration_loop,
)

MINIMAL_HTML = "<!doctype html><html><body><button>tap</button></body></html>"

PROFILE = {"provider": "mock", "model": "mock"}
CONFIG = {"execution": {"allow_mock_fallback": True}}

DOM_PASS = {
    "board_visible": "pass",
    "elements_present": "pass",
    "interactive_hint": "pass",
    "readable": "pass",
}


def _make_html(tmp: Path, content: str = MINIMAL_HTML) -> Path:
    p = tmp / "prototype.html"
    p.write_text(content, encoding="utf-8")
    return p


def _clean_browser() -> BrowserResult:
    return BrowserResult(errors=[], dom_checks=DOM_PASS,
                         state_changed="pass", playwright_available=True)


def _clean_critique(pass_count: int = 5) -> CritiqueResult:
    return CritiqueResult(
        criteria={k: "pass" for k in ["board_visible", "elements_present",
                                       "interactive_hint", "state_changed", "readable"]},
        pass_count=pass_count,
        notes="looks good",
        available=True,
    )


ITER_CFG = {"enabled": True, "max_rounds": 4, "levels": ["errors", "visual"],
            "budget_seconds": 300, "pass_threshold": 4}


class TestPrototypeIteration(unittest.TestCase):

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())

    # Case 1: clean pass on round 1 — no patching needed
    @patch("prototype_iteration_runner._run_code_review_critique")
    @patch("prototype_iteration_runner._run_browser_check")
    def test_clean_pass_on_round_1(self, mock_browser, mock_critique):
        mock_browser.return_value = _clean_browser()
        mock_critique.return_value = _clean_critique(pass_count=5)

        html = _make_html(self.tmp)
        result = run_iteration_loop(
            html_path=html, repo_root=self.tmp, wave_id="wave_test",
            cell_id="cell_a", iteration_config=ITER_CFG,
            profile=PROFILE, config=CONFIG,
        )

        self.assertTrue(result["passed"])
        self.assertEqual(result["rounds_run"], 1)
        mock_browser.assert_called_once()
        mock_critique.assert_called_once()

    # Case 2: fails round 1, fixed on round 2
    @patch("prototype_iteration_runner._patch_prototype")
    @patch("prototype_iteration_runner._run_code_review_critique")
    @patch("prototype_iteration_runner._run_browser_check")
    def test_error_fixed_on_round_2(self, mock_browser, mock_critique, mock_patch):
        mock_browser.side_effect = [
            BrowserResult(errors=["[error] Uncaught TypeError"],
                          dom_checks={"board_visible": "fail"}, state_changed="fail",
                          playwright_available=True),
            _clean_browser(),
        ]
        mock_critique.side_effect = [
            _clean_critique(pass_count=2),
            _clean_critique(pass_count=5),
        ]
        mock_patch.return_value = MINIMAL_HTML

        html = _make_html(self.tmp)
        result = run_iteration_loop(
            html_path=html, repo_root=self.tmp, wave_id="wave_test",
            cell_id="cell_a", iteration_config=ITER_CFG,
            profile=PROFILE, config=CONFIG,
        )

        self.assertTrue(result["passed"])
        self.assertEqual(result["rounds_run"], 2)
        mock_patch.assert_called_once()

    # Case 3: max_rounds respected — never passes
    @patch("prototype_iteration_runner._patch_prototype")
    @patch("prototype_iteration_runner._run_code_review_critique")
    @patch("prototype_iteration_runner._run_browser_check")
    def test_max_rounds_respected(self, mock_browser, mock_critique, mock_patch):
        mock_browser.return_value = BrowserResult(
            errors=["[error] always broken"], dom_checks={"board_visible": "fail"},
            state_changed="fail", playwright_available=True,
        )
        mock_critique.return_value = _clean_critique(pass_count=1)
        mock_patch.return_value = MINIMAL_HTML

        html = _make_html(self.tmp)
        result = run_iteration_loop(
            html_path=html, repo_root=self.tmp, wave_id="wave_test",
            cell_id="cell_a", iteration_config={**ITER_CFG, "max_rounds": 3},
            profile=PROFILE, config=CONFIG,
        )

        self.assertFalse(result["passed"])
        self.assertEqual(result["rounds_run"], 3)
        self.assertEqual(mock_patch.call_count, 2)

    # Case 4: playwright unavailable — loop skips gracefully
    @patch("prototype_iteration_runner._run_browser_check")
    def test_playwright_unavailable_skips_gracefully(self, mock_browser):
        mock_browser.return_value = BrowserResult(
            errors=[], dom_checks={}, state_changed="unclear", playwright_available=False,
        )

        html = _make_html(self.tmp)
        result = run_iteration_loop(
            html_path=html, repo_root=self.tmp, wave_id="wave_test",
            cell_id="cell_a", iteration_config=ITER_CFG,
            profile=PROFILE, config=CONFIG,
        )

        self.assertEqual(result["rounds_run"], 1)

    # Case 5: iteration_log.md written with correct columns
    @patch("prototype_iteration_runner._run_code_review_critique")
    @patch("prototype_iteration_runner._run_browser_check")
    def test_iteration_log_written(self, mock_browser, mock_critique):
        mock_browser.return_value = _clean_browser()
        mock_critique.return_value = _clean_critique(pass_count=5)

        html = _make_html(self.tmp)
        result = run_iteration_loop(
            html_path=html, repo_root=self.tmp, wave_id="wave_test",
            cell_id="cell_a", iteration_config=ITER_CFG,
            profile=PROFILE, config=CONFIG,
        )

        log = Path(result["log_path"])
        self.assertTrue(log.exists())
        content = log.read_text(encoding="utf-8")
        self.assertIn("Round", content)
        self.assertIn("L1 Errors", content)
        self.assertIn("L2 Pass Count", content)
        self.assertIn("Decision", content)


if __name__ == "__main__":
    unittest.main()
