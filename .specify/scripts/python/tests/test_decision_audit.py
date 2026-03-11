import json
import subprocess
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[4]
CFG = ROOT / "runs" / "wave_001" / "run_config.json"


class TestDecisionAudit(unittest.TestCase):
    def test_override_is_recorded(self):
        auto = json.loads((ROOT / "runs/wave_001/auto_decisions.json").read_text(encoding="utf-8"))
        concept = auto[0]["concept_id"]
        override = [{"concept_id": concept, "decision": "Iterate", "author": "human"}]
        (ROOT / "runs/wave_001/human_overrides.json").write_text(json.dumps(override, indent=2) + "\n", encoding="utf-8")

        subprocess.run(["python3", str(ROOT / ".specify/scripts/python/human_feedback.py"), str(CFG)], check=True)
        final_rows = json.loads((ROOT / "runs/wave_001/final_decisions.json").read_text(encoding="utf-8"))

        target = [r for r in final_rows if r["concept_id"] == concept][0]
        self.assertEqual(target["final_decision"], "Iterate")
        self.assertIsNotNone(target["override"])


if __name__ == "__main__":
    unittest.main()
