import json
import subprocess
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[4]
CFG = ROOT / "runs" / "wave_001" / "run_config.json"


class TestParallelCells(unittest.TestCase):
    def test_wave_runner_completes_cells(self):
        subprocess.run(["python3", str(ROOT / ".specify/scripts/python/wave_runner.py"), str(CFG)], check=True)
        state = json.loads((ROOT / "runs/wave_001/run_state.json").read_text(encoding="utf-8"))
        self.assertEqual(state["status"], "completed")
        for cell in state["cell_states"]:
            self.assertEqual(cell["status"], "completed")
            self.assertGreater(len(cell["artifacts"]), 0)
            self.assertTrue(any(path.endswith("human_review.md") for path in cell["artifacts"]))


if __name__ == "__main__":
    unittest.main()
