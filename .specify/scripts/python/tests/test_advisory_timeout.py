import json
import os
import subprocess
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[4]
CFG = ROOT / "runs" / "wave_001" / "run_config.json"


class TestAdvisoryTimeout(unittest.TestCase):
    def test_advisory_without_override_uses_auto(self):
        override = ROOT / "runs/wave_001/human_overrides.json"
        if override.exists():
            os.remove(override)

        subprocess.run(["python3", str(ROOT / ".specify/scripts/python/human_feedback.py"), str(CFG)], check=True)
        final_rows = json.loads((ROOT / "runs/wave_001/final_decisions.json").read_text(encoding="utf-8"))
        for row in final_rows:
            self.assertEqual(row["final_decision"], row["auto_decision"])


if __name__ == "__main__":
    unittest.main()
