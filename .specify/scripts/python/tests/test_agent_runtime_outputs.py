import unittest
from pathlib import Path
import sys
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[4]
SYS_PATH = ROOT / ".specify" / "scripts" / "python"
if str(SYS_PATH) not in sys.path:
    sys.path.append(str(SYS_PATH))

from agent_runtime import generate_director_brief, generate_director_plan, generate_director_plan_with_model, generate_prototype_html, generate_text_artifact, render_director_plan, validate_director_plan  # noqa: E402


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
        self.assertIn("dispatch colored boxes", content.lower())
        self.assertNotIn("Click exposed screws", content)

    def test_director_brief_includes_function_first_handoff(self):
        context = {
            "wave_id": "wave_001",
            "cell_id": "cell_a",
            "source_games": [
                {"id": "ios-6751056652-pixel-flow", "name": "Pixel Flow!", "mechanics": ["queue_sort"], "human_notes": {}},
                {"id": "ios-6471490579-screw-jam", "name": "Screw Jam", "mechanics": ["sequence_constraint"], "human_notes": {}},
            ],
        }

        brief = generate_director_brief(context)

        self.assertIn("Source A Functions To Preserve", brief)
        self.assertIn("Replaceable Surface Elements", brief)
        self.assertIn("New Unified Player Verb", brief)
        self.assertIn("Why Literal Fusion Is Weaker", brief)
        self.assertIn("Variation Targets For This Cell", brief)

    def test_director_plan_persists_ranked_variations(self):
        context = {
            "wave_id": "wave_001",
            "cell_id": "cell_a",
            "concept_count": 3,
            "source_games": [
                {"id": "ios-6751056652-pixel-flow", "name": "Pixel Flow!", "mechanics": ["queue_sort"], "human_notes": {}},
                {"id": "ios-6471490579-screw-jam", "name": "Screw Jam", "mechanics": ["sequence_constraint"], "human_notes": {}},
            ],
        }
        plan = generate_director_plan(context)
        markdown = render_director_plan(plan)

        self.assertEqual(len(plan["variation_targets"]), 3)
        self.assertIn("Collector Loop", markdown)
        self.assertIn("Plate Claim Loop", markdown)
        self.assertIn("Queue Prep Loop", markdown)

    def test_validate_director_plan_accepts_materially_different_variations(self):
        context = {
            "wave_id": "wave_001",
            "cell_id": "cell_a",
            "concept_count": 3,
            "source_games": [
                {"id": "ios-6751056652-pixel-flow", "name": "Pixel Flow!", "mechanics": ["queue_sort"], "human_notes": {}},
                {"id": "ios-6471490579-screw-jam", "name": "Screw Jam", "mechanics": ["sequence_constraint"], "human_notes": {}},
            ],
        }
        plan = {
            "new_unified_verb": "dispatch boxes to collect exposed screws",
            "source_a_functions": "conveyor loop and queue pressure",
            "source_b_functions": "layered reveal and collapse",
            "replaceable_surface": "shooters and direct screw tapping",
            "literal_fusion_why_weaker": "two interaction models would compete",
            "selected_build_variation_id": "variation_01",
            "variation_targets": [
                {
                    "id": "variation_01",
                    "label": "Collector Loop",
                    "role": "conservative",
                    "core_verb": "dispatch boxes to collect screws",
                    "main_interaction": "Send a box around the loop to collect exposed screws.",
                    "objective": "Clear the board before pressure collapses the run.",
                    "core_loop": "read -> dispatch -> collect -> reassess",
                    "failure_pressure": "wrong box wastes a lap",
                    "board_setup": "Layered plate board inside a conveyor.",
                    "object_rules": "Boxes collect only exposed matching screws.",
                    "input_behavior": "Tap a front box to dispatch.",
                    "difference_note": "Free collection across all exposed plates.",
                },
                {
                    "id": "variation_02",
                    "label": "Plate Claim",
                    "role": "conservative",
                    "core_verb": "assign a box to one plate",
                    "main_interaction": "Commit one box to one plate for a full lap.",
                    "objective": "Collapse plates in the correct order.",
                    "core_loop": "read -> assign -> resolve -> reassess",
                    "failure_pressure": "wrong plate commitment costs a full lap",
                    "board_setup": "Layered plate board with one-plate assignment per lap.",
                    "object_rules": "Assigned boxes collect only from their target plate.",
                    "input_behavior": "Tap a box, then tap a plate.",
                    "difference_note": "Commitment changes the board-update logic.",
                },
                {
                    "id": "variation_03",
                    "label": "Queue Prep",
                    "role": "novelty",
                    "core_verb": "sacrifice current value to set future queue order",
                    "main_interaction": "Dispatch low-value boxes to surface the next ideal box.",
                    "objective": "Win by managing future queue state.",
                    "core_loop": "read queue -> dispatch prep box -> next front changes -> exploit",
                    "failure_pressure": "greedy present play buries the needed future box",
                    "board_setup": "Same board, but queue order is the main problem.",
                    "object_rules": "Every dispatch changes both board and future queue.",
                    "input_behavior": "Tap the front box for either value or setup.",
                    "difference_note": "Future queue preparation is the primary challenge.",
                },
            ],
        }

        validated = validate_director_plan(plan, context)
        self.assertEqual(validated["plan_source"], "model")
        self.assertEqual(validated["selected_build_variation_id"], "variation_01")

    @patch("agent_runtime.call_provider")
    def test_model_director_plan_falls_back_when_invalid(self, mock_call_provider):
        context = {
            "wave_id": "wave_001",
            "cell_id": "cell_a",
            "concept_count": 3,
            "source_games": [
                {"id": "ios-6751056652-pixel-flow", "name": "Pixel Flow!", "mechanics": ["queue_sort"], "human_notes": {}},
                {"id": "ios-6471490579-screw-jam", "name": "Screw Jam", "mechanics": ["sequence_constraint"], "human_notes": {}},
            ],
        }
        mock_call_provider.return_value = '{"bad":"shape"}'
        plan, fallback_used = generate_director_plan_with_model(
            repo_root=ROOT,
            context=context,
            profile={"provider": "openai", "model": "test-model", "name": "cloud"},
            config={"execution": {"allow_mock_fallback": True}},
        )

        self.assertTrue(fallback_used)
        self.assertEqual(plan["plan_source"], "scripted_fallback")

    @patch("agent_runtime.call_provider")
    def test_model_director_plan_uses_valid_json(self, mock_call_provider):
        context = {
            "wave_id": "wave_001",
            "cell_id": "cell_a",
            "concept_count": 3,
            "source_games": [
                {"id": "ios-6751056652-pixel-flow", "name": "Pixel Flow!", "mechanics": ["queue_sort"], "human_notes": {}},
                {"id": "ios-6471490579-screw-jam", "name": "Screw Jam", "mechanics": ["sequence_constraint"], "human_notes": {}},
            ],
        }
        mock_call_provider.return_value = """
        {
          "new_unified_verb": "dispatch boxes to collect exposed screws",
          "source_a_functions": "conveyor loop, queue pressure",
          "source_b_functions": "layer reveal, plate collapse",
          "replaceable_surface": "shooters, direct tapping",
          "literal_fusion_why_weaker": "two interaction models would compete",
          "selected_build_variation_id": "variation_02",
          "variation_targets": [
            {
              "id": "variation_01",
              "label": "Collector Loop",
              "role": "conservative",
              "core_verb": "dispatch boxes to collect screws",
              "main_interaction": "Send a box around the loop to collect exposed screws.",
              "objective": "Clear the board before pressure collapses the run.",
              "core_loop": "read -> dispatch -> collect -> reassess",
              "failure_pressure": "wrong box wastes a lap",
              "board_setup": "Layered plate board inside a conveyor.",
              "object_rules": "Boxes collect only exposed matching screws.",
              "input_behavior": "Tap a front box to dispatch.",
              "difference_note": "Free collection across all exposed plates."
            },
            {
              "id": "variation_02",
              "label": "Plate Claim",
              "role": "conservative",
              "core_verb": "assign a box to one plate",
              "main_interaction": "Commit one box to one plate for a full lap.",
              "objective": "Collapse plates in the correct order.",
              "core_loop": "read -> assign -> resolve -> reassess",
              "failure_pressure": "wrong plate commitment costs a full lap",
              "board_setup": "Layered plate board with one-plate assignment per lap.",
              "object_rules": "Assigned boxes collect only from their target plate.",
              "input_behavior": "Tap a box, then tap a plate.",
              "difference_note": "Commitment changes the board-update logic."
            },
            {
              "id": "variation_03",
              "label": "Queue Prep",
              "role": "novelty",
              "core_verb": "sacrifice current value to set future queue order",
              "main_interaction": "Dispatch low-value boxes to surface the next ideal box.",
              "objective": "Win by managing future queue state.",
              "core_loop": "read queue -> dispatch prep box -> next front changes -> exploit",
              "failure_pressure": "greedy present play buries the needed future box",
              "board_setup": "Same board, but queue order is the main problem.",
              "object_rules": "Every dispatch changes both board and future queue.",
              "input_behavior": "Tap the front box for either value or setup.",
              "difference_note": "Future queue preparation is the primary challenge."
            }
          ]
        }
        """
        plan, fallback_used = generate_director_plan_with_model(
            repo_root=ROOT,
            context=context,
            profile={"provider": "openai", "model": "test-model", "name": "cloud"},
            config={"execution": {"allow_mock_fallback": True}},
        )

        self.assertFalse(fallback_used)
        self.assertEqual(plan["plan_source"], "model")
        self.assertEqual(plan["selected_build_variation_id"], "variation_02")

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
        self.assertIn("Dispatch a box from the dock", html)
        self.assertIn("Each box can hold up to 3 matching screws", html)
        self.assertIn("Next Level", html)
        self.assertNotIn("Deterministic prototype placeholder", html)
        self.assertNotIn("id=\"step\"", html)

    def test_prototype_spec_uses_translated_input_model(self):
        context = {
            "wave_id": "wave_001",
            "cell_id": "cell_a",
            "selected_variation_id": "variation_01",
            "source_games": [
                {"id": "ios-6751056652-pixel-flow", "name": "Pixel Flow!", "mechanics": ["queue_sort"], "human_notes": {}},
                {"id": "ios-6471490579-screw-jam", "name": "Screw Jam", "mechanics": ["sequence_constraint"], "human_notes": {}},
            ],
        }
        content, _, _ = generate_text_artifact(
            repo_root=ROOT,
            role="prototype_spec_writer",
            artifact_type="prototype_spec",
            context=context,
            profile={"provider": "mock", "model": "mock", "name": "cloud"},
            config={"execution": {"allow_mock_fallback": True}},
        )

        self.assertIn("Tap only the front box in a dock lane", content)
        self.assertNotIn("Click an exposed screw", content)

    def test_variation_selection_changes_concept_output(self):
        base = {
            "wave_id": "wave_001",
            "cell_id": "cell_a",
            "source_games": [
                {"id": "ios-6751056652-pixel-flow", "name": "Pixel Flow!", "mechanics": ["queue_sort"], "human_notes": {}},
                {"id": "ios-6471490579-screw-jam", "name": "Screw Jam", "mechanics": ["sequence_constraint"], "human_notes": {}},
            ],
        }
        context_a = dict(base, selected_variation_id="variation_01")
        context_b = dict(base, selected_variation_id="variation_02")

        content_a, _, _ = generate_text_artifact(
            repo_root=ROOT,
            role="fusion_designer_conservative",
            artifact_type="concept_card",
            context=context_a,
            profile={"provider": "mock", "model": "mock", "name": "cloud"},
            config={"execution": {"allow_mock_fallback": True}},
        )
        content_b, _, _ = generate_text_artifact(
            repo_root=ROOT,
            role="fusion_designer_conservative",
            artifact_type="concept_card",
            context=context_b,
            profile={"provider": "mock", "model": "mock", "name": "cloud"},
            config={"execution": {"allow_mock_fallback": True}},
        )

        self.assertIn("collect exposed matching screws", content_a)
        self.assertIn("commits to one chosen plate", content_b)


if __name__ == "__main__":
    unittest.main()
