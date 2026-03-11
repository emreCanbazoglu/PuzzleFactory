import json
import subprocess
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[4]
CFG = ROOT / "runs" / "wave_001" / "run_config.json"


class TestDecisionScores(unittest.TestCase):
    def test_decisions_created(self):
        subprocess.run(["python3", str(ROOT / ".specify/scripts/python/decision_engine.py"), str(CFG)], check=True)
        out = ROOT / "runs/wave_001/auto_decisions.json"
        self.assertTrue(out.exists())
        rows = json.loads(out.read_text(encoding="utf-8"))
        self.assertGreater(len(rows), 0)
        for row in rows:
            self.assertGreaterEqual(row["auto_score"], 0)
            self.assertLessEqual(row["auto_score"], 100)


if __name__ == "__main__":
    unittest.main()
