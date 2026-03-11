import json
import subprocess
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[4]
CFG = ROOT / "runs" / "wave_001" / "run_config.json"


class TestEvaluationSyncBoundary(unittest.TestCase):
    def test_sync_after_cells(self):
        subprocess.run(["python3", str(ROOT / ".specify/scripts/python/evaluation_sync.py"), str(CFG)], check=True)
        out = ROOT / "factory/portfolio/wave_001/portfolio_summary.json"
        self.assertTrue(out.exists())
        data = json.loads(out.read_text(encoding="utf-8"))
        cfg = json.loads(CFG.read_text(encoding="utf-8"))
        self.assertEqual(data["aggregated_cells"], len(cfg["cells"]))


if __name__ == "__main__":
    unittest.main()
