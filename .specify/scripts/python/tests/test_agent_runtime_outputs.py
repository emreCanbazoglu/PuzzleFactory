import unittest
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[4]
SYS_PATH = ROOT / ".specify" / "scripts" / "python"
if str(SYS_PATH) not in sys.path:
    sys.path.append(str(SYS_PATH))

from agent_runtime import generate_text_artifact  # noqa: E402


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


if __name__ == "__main__":
    unittest.main()
