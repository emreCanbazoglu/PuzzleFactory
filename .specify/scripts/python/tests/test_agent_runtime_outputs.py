import unittest
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[4]
SYS_PATH = ROOT / ".specify" / "scripts" / "python"
if str(SYS_PATH) not in sys.path:
    sys.path.append(str(SYS_PATH))

from agent_runtime import generate_prototype_html, generate_text_artifact  # noqa: E402


class TestAgentRuntimeOutputs(unittest.TestCase):
    def test_template_fallback_contains_required_markers(self):
        context = {
            "wave_id": "wave_001",
            "cell_id": "cell_x",
            "discovery_domain": "sort",
            "prototype_domain": "sort",
            "concept_count": 3,
            "reference_game": "seed_game",
        }
        content, fallback, template_name = generate_text_artifact(
            repo_root=ROOT,
            role="prototype_spec_writer",
            artifact_type="prototype_spec",
            context=context,
            profile={"provider": "mock", "model": "mock", "name": "cloud"},
            config={"execution": {"allow_mock_fallback": True}},
        )
        self.assertTrue(fallback)
        self.assertEqual(template_name, "prototype_spec.md")
        self.assertIn("Core Loop:", content)
        self.assertIn("Win Condition:", content)
        self.assertIn("Lose Condition:", content)

    def test_source_pair_is_named_in_concept_output(self):
        context = {
            "wave_id": "wave_001",
            "cell_id": "cell_a",
            "discovery_domain": "sort",
            "prototype_domain": "sort",
            "concept_count": 3,
            "source_games": [
                {"id": "ios-6751056652-pixel-flow", "name": "Pixel Flow!", "core_verb": "route packets", "board_topology": "lanes", "pressure": "queue pressure", "failure_mode": "jam", "depth_source": "route timing", "mechanics": ["queue_sort"], "notes": "lane pressure"},
                {"id": "ios-6471490579-screw-jam", "name": "Screw Jam", "core_verb": "remove exposed blockers", "board_topology": "stacked blockers", "pressure": "access order", "failure_mode": "deadlock", "depth_source": "unlock planning", "mechanics": ["sequence_constraint"], "notes": "exposure order"},
            ],
        }
        content, _, _ = generate_text_artifact(
            repo_root=ROOT,
            role="fusion_designer_conservative",
            artifact_type="concept_card",
            context=context,
            profile={"provider": "mock", "model": "mock", "name": "cloud"},
            config={"execution": {"allow_mock_fallback": True}},
        )
        self.assertIn("Pixel Flow!", content)
        self.assertIn("Screw Jam", content)
        self.assertIn("Click exposed screws", content)

    def test_generated_prototype_is_not_step_placeholder(self):
        html = generate_prototype_html(
            {
                "cell_id": "cell_a",
                "source_games": [
                    {"id": "ios-6751056652-pixel-flow", "name": "Pixel Flow!"},
                    {"id": "ios-6471490579-screw-jam", "name": "Screw Jam"},
                ],
            }
        )
        self.assertIn("All three packets can now flow", html)
        self.assertIn("Remove exposed screws only", html)
        self.assertNotIn("Deterministic prototype placeholder", html)
        self.assertNotIn("id=\"step\"", html)


if __name__ == "__main__":
    unittest.main()
