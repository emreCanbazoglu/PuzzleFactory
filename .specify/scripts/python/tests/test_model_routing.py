import unittest
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[4]
SYS_PATH = ROOT / ".specify" / "scripts" / "python"
if str(SYS_PATH) not in sys.path:
    sys.path.append(str(SYS_PATH))

from model_router import resolve_profile_for_role  # noqa: E402


class TestModelRouting(unittest.TestCase):
    def test_local_role_routes_to_local_profile(self):
        cfg = {
            "routing": {
                "cloud_roles": ["prototype_critic"],
                "local_roles": ["prototype_builder_web"],
            },
            "models": {
                "cloud": {"provider": "openai", "model": "gpt-5-mini"},
                "local": {"provider": "ollama", "model": "qwen3:14b"},
            },
        }
        profile = resolve_profile_for_role(cfg, "prototype_builder_web")
        self.assertEqual(profile["name"], "local")
        self.assertEqual(profile["provider"], "ollama")

    def test_unknown_role_defaults_to_cloud(self):
        cfg = {
            "routing": {"cloud_roles": ["prototype_critic"], "local_roles": []},
            "models": {"cloud": {"provider": "mock", "model": "mock-cloud"}},
        }
        profile = resolve_profile_for_role(cfg, "unknown_role")
        self.assertEqual(profile["name"], "cloud")


if __name__ == "__main__":
    unittest.main()
