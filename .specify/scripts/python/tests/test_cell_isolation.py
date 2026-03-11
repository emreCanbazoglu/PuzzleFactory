import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[4]


class TestCellIsolation(unittest.TestCase):
    def test_artifacts_are_cell_scoped(self):
        state = json.loads((ROOT / "runs/wave_001/run_state.json").read_text(encoding="utf-8"))
        for cell in state["cell_states"]:
            cid = cell["cell_id"]
            for artifact in cell["artifacts"]:
                self.assertIn(f"/wave_001/{cid}/", artifact)


if __name__ == "__main__":
    unittest.main()
