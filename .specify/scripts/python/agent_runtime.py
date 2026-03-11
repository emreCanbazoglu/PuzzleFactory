#!/usr/bin/env python3
import hashlib
import json
import os
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from model_router import allow_mock_fallback

TEMPLATE_MAP = {
    "mechanic_sheet": "mechanic_sheet.md",
    "concept_card": "concept_card.md",
    "prototype_spec": "prototype_spec.md",
    "evaluation_report": "evaluation_report.md",
}

PAIR_PRESETS = {
    ("ios-1617391485-block-blast", "ios-6751056652-pixel-flow"): {
        "concept_name": "Shape Current",
        "main_interaction": "Place or clear rigid blockers to keep a packet route open across a cramped board.",
        "objective": "Deliver all packets to exits before the footprint grid chokes future routes.",
        "core_loop": "read board pressure -> free or reserve space -> watch packets advance -> reassess exits",
        "failure_pressure": "space denial from poor footprint timing",
    },
    ("ios-1617391485-block-blast", "ios-6471490579-screw-jam"): {
        "concept_name": "Bolt Fit",
        "main_interaction": "Remove exposed bolts to free footprint cells that a rigid block pattern needs next.",
        "objective": "Create exact placement windows for upcoming shapes without sealing future removals.",
        "core_loop": "inspect exposed bolts -> remove one -> open footprint space -> place next shape",
        "failure_pressure": "locking the board before the next shape fits",
    },
    ("ios-6471490579-screw-jam", "ios-6751056652-pixel-flow"): {
        "concept_name": "Pixel Jam Flow",
        "core_verb": "dispatch colored boxes onto a conveyor to collect exposed matching screws",
        "primary_decision": "which top-of-queue box color and capacity best clears the current exposed screw layer without clogging future turns",
        "main_interaction": "Send colored screwboxes from dock queues onto a surrounding conveyor so they orbit the layered board and collect matching exposed screws automatically.",
        "objective": "Clear the layered screw board by dispatching the right boxes in the right order before queue and overflow pressure collapses the run.",
        "core_loop": "read exposed screws and top queue colors -> dispatch one box -> orbit and collect matching screws -> plates collapse and reveal new screws -> reassess",
        "failure_pressure": "sending the wrong box wastes a full orbit, preserves bad exposure order, and builds queue or overflow pressure",
        "why_it_works": "It preserves Screw Jam's reveal-order payoff and Pixel Flow's conveyor dispatch pressure inside one unified box-dispatch interaction.",
        "input_behavior": "Tap only the front box in a dock lane to send it around the conveyor; the box auto-collects exposed matching screws during its lap.",
        "board_setup": "A layered Screw Jam-style plate board sits inside a Pixel Flow-style surrounding conveyor. Top-only dock queues feed colored boxes onto the loop while exposed screws wait on the current outer layer of each plate.",
        "object_rules": "Boxes have a color and capacity. During one full lap they collect only exposed matching screws. Clearing all screws from a plate collapses it and reveals the next layer. Returned boxes or unmatched pickups create pressure in the dock or overflow system.",
        "win_condition": "Every screw is collected and every plate collapses off the board.",
        "lose_condition": "Queue or overflow pressure locks the system before the board is cleared.",
        "level1_goal": "Teach that only exposed screws are collectible and that dispatch order matters more than raw speed.",
        "level2_goal": "Introduce a tempting wrong-color queue front so the player must clear for future access before sending the ideal collector.",
        "variation_1": "Dispatch colored boxes from top-only dock queues onto the conveyor to collect exposed screws from a static layered board.",
        "variation_2": "Use the conveyor as a rotating assignment system where each dispatched box commits to one plate, so plate-collapse order matters more than immediate collection count.",
        "variation_3": "Focus on queue-clearing decisions: sometimes the right move is to send a weak front box only to surface the high-value color needed for the next reveal state.",
        "variations": [
            {
                "id": "variation_01",
                "label": "Collector Loop",
                "role": "conservative",
                "core_verb": "dispatch colored boxes onto a conveyor to collect exposed matching screws",
                "main_interaction": "Send colored screwboxes from dock queues onto a surrounding conveyor so they orbit the layered board and collect matching exposed screws automatically.",
                "objective": "Clear the layered screw board by dispatching the right boxes in the right order before queue and overflow pressure collapses the run.",
                "core_loop": "read exposed screws and top queue colors -> dispatch one box -> orbit and collect matching screws -> plates collapse and reveal new screws -> reassess",
                "failure_pressure": "sending the wrong box wastes a full orbit, preserves bad exposure order, and builds queue or overflow pressure",
                "board_setup": "A layered Screw Jam-style plate board sits inside a Pixel Flow-style surrounding conveyor. Top-only dock queues feed colored boxes onto the loop while exposed screws wait on the current outer layer of each plate.",
                "object_rules": "Boxes have a color and capacity. During one full lap they collect only exposed matching screws. Clearing all screws from a plate collapses it and reveals the next layer. Returned boxes or unmatched pickups create pressure in the dock or overflow system.",
                "input_behavior": "Tap only the front box in a dock lane to send it around the conveyor; the box auto-collects exposed matching screws during its lap.",
            },
            {
                "id": "variation_02",
                "label": "Plate Claim Loop",
                "role": "conservative",
                "core_verb": "assign one moving box to one plate and commit to its collapse route",
                "main_interaction": "Dispatch a colored box that commits to one chosen plate for the whole lap, collecting only that plate's exposed screws while giving up other opportunities.",
                "objective": "Collapse the layered plates in the right order so committed laps unlock better future plates instead of trapping the queue.",
                "core_loop": "read exposed screws and plate priorities -> assign a box to one plate -> resolve one committed lap -> collapsed plate reveals new route -> reassess next commitment",
                "failure_pressure": "a wrong commitment spends a full lap on low-value screws and delays the plate whose collapse would have opened the board",
                "board_setup": "A layered plate board sits inside a conveyor, but each dispatched box visibly locks onto one plate for its trip rather than roaming freely across all exposed screws.",
                "object_rules": "A box can collect only from its assigned plate during that lap. Finishing a plate collapses it and reconfigures access. Queue pressure rises because each wrong commitment costs an entire circuit.",
                "input_behavior": "Tap a front-box, then tap one eligible plate to assign that lap before the box enters the conveyor.",
            },
            {
                "id": "variation_03",
                "label": "Queue Prep Loop",
                "role": "novelty",
                "core_verb": "sacrifice short-term collection to prepare the next ideal box order",
                "main_interaction": "Sometimes dispatch a low-value front box mainly to cycle the dock and surface the color-capacity combo needed for the next exposed screws.",
                "objective": "Clear the board by managing future queue state as aggressively as current plate state.",
                "core_loop": "inspect exposed screws and future queue -> dispatch current front box for setup or value -> resolve one lap -> next queue front changes -> exploit the prepared board state",
                "failure_pressure": "greedy immediate collection can bury the only future color-capacity match and force overflow later",
                "board_setup": "The layered board and surrounding conveyor remain the same, but the main challenge shifts toward managing the top-only queue order instead of just matching current exposures.",
                "object_rules": "Every dispatched box changes both the board and the future queue. Some boxes are sent mainly to surface the next correct collector rather than to maximize the current lap's screw count.",
                "input_behavior": "Tap only the front box in a dock lane, knowing the real purpose of the move may be queue preparation rather than immediate collection.",
            },
        ],
    },
    ("ios-1482155847-royal-match", "ios-1514542157-water-sort-puzzle"): {
        "concept_name": "Cascade Decant",
        "main_interaction": "Trigger color groups that pour stacked colors into temporary tubes after every cascade.",
        "objective": "Set up cascades that also improve tube purity instead of scrambling it.",
        "core_loop": "plan swap -> resolve cascade -> auto-pour overflow colors -> restore clean containers",
        "failure_pressure": "cascades create unusable mixed storage",
    },
}

PROFILE_OVERRIDES = {
    "ios-6751056652-pixel-flow": {
        "core_verb": "route colored units through constrained paths",
        "board_topology": "grid lanes with path blockers",
        "pressure": "queue buildup and lane blocking",
        "failure_mode": "packets jam before reaching correct exits",
        "depth_source": "route sequencing under limited space",
        "notes": "lane routing and path reveal pressure",
        "surface_form": [
            "tap front shooters from dock queues",
            "shoot colored bullets from a conveyor loop",
            "pixel board theme and cube targets",
        ],
        "system_functions": [
            "surrounding conveyor delivery loop",
            "top-of-queue dispatch restriction",
            "progressive clearance of currently reachable perimeter targets",
            "color and quantity matching against exposed targets",
            "slot or overflow pressure from returning units",
        ],
        "replaceable_elements": [
            "literal shooter object",
            "bullet shooting presentation",
            "pixel art theme",
        ],
    },
    "ios-6471490579-screw-jam": {
        "core_verb": "remove blockers in a legal exposure order",
        "board_topology": "stacked blockers on a compact grid",
        "pressure": "unlock order and blocked access",
        "failure_mode": "deadlock from removing the wrong exposed blocker",
        "depth_source": "planning future accessibility before committing",
        "notes": "exposed-order removal and deadlock risk",
        "surface_form": [
            "tap exposed screws directly",
            "screw theme and shaped plates",
            "target boxes that auto-sort collected screws",
        ],
        "system_functions": [
            "exposed-only interaction order",
            "layer reveal through plate collapse",
            "target-box capacity pressure",
            "overflow risk for unmatched colors",
            "clear-the-board progression through legal removal order",
        ],
        "replaceable_elements": [
            "direct screw tapping",
            "literal screw theme",
            "target boxes as passive UI instead of active movers",
        ],
    },
    "ios-1514542157-water-sort-puzzle": {
        "core_verb": "pour color stacks between containers",
        "board_topology": "vertical containers with free slots",
        "pressure": "temporary storage exhaustion",
        "failure_mode": "mixed stacks trap critical colors",
        "depth_source": "sacrifice and recovery planning",
        "notes": "reversible sorting with temporary storage pressure",
    },
    "ios-1482155847-royal-match": {
        "core_verb": "swap to create color groups and cascades",
        "board_topology": "grid with cascading refill",
        "pressure": "limited moves with objective gating",
        "failure_mode": "board stalls before objective completion",
        "depth_source": "combo setup and cascade leverage",
        "notes": "color grouping with cascade reward",
    },
    "ios-1617391485-block-blast": {
        "core_verb": "place rigid shapes into shrinking free space",
        "board_topology": "compact grid with footprint constraints",
        "pressure": "space denial from poor placement",
        "failure_mode": "future shapes cannot fit",
        "depth_source": "foresight around future footprint demand",
        "notes": "space reservation and footprint planning",
    },
}


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _source_games(context: dict[str, Any]) -> list[dict[str, Any]]:
    return list(context.get("source_games", []))


def _normalize_game(game: dict[str, Any]) -> dict[str, Any]:
    override = PROFILE_OVERRIDES.get(game.get("id", ""), {})
    human_notes = dict(game.get("human_notes", {}))
    return {
        "id": game.get("id", "unknown-game"),
        "name": game.get("name", "Unknown Game"),
        "core_verb": game.get("core_verb") or override.get("core_verb", "manipulate constrained board pieces"),
        "board_topology": game.get("board_topology") or override.get("board_topology", "compact puzzle board"),
        "pressure": game.get("pressure") or override.get("pressure", "limited move pressure"),
        "failure_mode": game.get("failure_mode") or override.get("failure_mode", "board deadlock"),
        "depth_source": game.get("depth_source") or override.get("depth_source", "forward planning"),
        "mechanics": list(game.get("mechanics", ["objective_variation"])),
        "notes": game.get("notes") or override.get("notes", "a readable mechanical loop"),
        "main_goal": human_notes.get("main_goal", ""),
        "winning_points": list(human_notes.get("winning_points", [])),
        "adopt": list(human_notes.get("adopt", [])),
        "avoid": list(human_notes.get("avoid", [])),
        "stress_points": list(human_notes.get("stress_points", [])),
        "fun_points": list(human_notes.get("fun_points", [])),
        "surface_form": list(game.get("surface_form") or override.get("surface_form", [])),
        "system_functions": list(game.get("system_functions") or override.get("system_functions", [])),
        "replaceable_elements": list(game.get("replaceable_elements") or override.get("replaceable_elements", [])),
    }


def _source_names(context: dict[str, Any]) -> str:
    return " + ".join(game["name"] for game in _source_games(context)) or "Unknown Sources"


def _pair_preset(context: dict[str, Any]) -> dict[str, str]:
    ids = tuple(sorted(game["id"] for game in _source_games(context)))
    return PAIR_PRESETS.get(ids, {})


def _variation_specs(context: dict[str, Any]) -> list[dict[str, Any]]:
    preset = _pair_preset(context)
    return list(preset.get("variations", []))


def _selected_variation(context: dict[str, Any]) -> dict[str, Any] | None:
    selected_id = context.get("selected_variation_id")
    if not selected_id:
        return None
    for variation in _variation_specs(context):
        if variation.get("id") == selected_id:
            return variation
    return None


def _joined(items: list[str], fallback: str) -> str:
    clean = [item for item in items if item]
    return ", ".join(clean) if clean else fallback


def _pick(items: list[str], fallback: str) -> str:
    return items[0] if items else fallback


def _fusion_summary(context: dict[str, Any]) -> dict[str, str]:
    sources = [_normalize_game(game) for game in _source_games(context)]
    preset = _pair_preset(context)
    selected_variation = _selected_variation(context)
    if len(sources) < 2:
        return {
            "concept_name": preset.get("concept_name", f"{context.get('cell_id', 'cell')} Fusion"),
            "source_names": _source_names(context),
            "main_interaction": preset.get("main_interaction", "Combine two readable puzzle pressures in one board."),
            "objective": preset.get("objective", "Solve the board inside the move budget."),
            "core_loop": preset.get("core_loop", "inspect -> act -> resolve -> reassess"),
            "failure_pressure": preset.get("failure_pressure", "limited moves"),
            "game_line": _source_names(context),
            "genre": "Hybrid casual puzzle",
            "core_verb": "make one meaningful move at a time",
            "board_topology": "compact deterministic board",
            "object_types": "packets, blockers, exits",
            "primary_decision": "which move changes the board state most productively",
            "skill_type": "planning",
            "pressure_type": "limited moves",
            "failure_mode": "board stalls before objective completion",
            "depth_source": "visible cause and effect",
            "player_emotion": "clarity under pressure",
            "why_it_works": "The loop is readable and deterministic.",
            "why_it_fails": "If each action has weak consequence, the puzzle becomes flat.",
            "why_fresh": "It merges two puzzle tensions instead of reskinning one.",
            "why_understandable": "The board state shows why actions matter.",
            "likely_obstacles": "Difficulty balancing.",
            "production_risk": "Content pipeline depth.",
            "prototype_scope": "Single mechanic slice.",
            "reasons_fail": "Not enough interaction between the source mechanics.",
            "board_setup": "Small board with visible blockers and exits.",
            "object_rules": "Every click changes board accessibility.",
            "win_condition": "Open every required route.",
            "lose_condition": "Run out of moves.",
            "level1_goal": "Teach the core interaction.",
            "level2_goal": "Add one new pressure layer.",
            "ui_notes": "Keep state and objective visible.",
            "debug_controls": "Reset only.",
            "non_goals": "Theme and polish.",
            "success_criteria": "A reader can explain the puzzle after one pass.",
            "strengths": "Readable state changes.",
            "weaknesses": "Limited depth in the current prototype slice.",
            "key_risks": "Overly linear boards.",
            "recommendation": "Iterate",
            "surface_form": "visible puzzle pieces",
            "system_functions": "clear board state change, deterministic pressure, readable cause and effect",
            "replaceable_surface": "visual theme and literal object identity",
            "source_a_functions": "readable board change",
            "source_b_functions": "failure pressure",
            "new_unified_verb": "make one meaningful move that advances the board",
            "literal_fusion_why_weaker": "literal side-by-side copying would create two competing interaction models",
            "input_behavior": "Click the primary puzzle piece to make one meaningful deterministic move.",
            "variation_1": "Variation 1 should keep source A's board promise and source B's pressure source.",
            "variation_2": "Variation 2 should keep source B's board promise and source A's pressure source.",
            "variation_3": "Variation 3 should reassign one source object's role to perform the other source's function.",
        }

    first, second = sources[0], sources[1]
    source_names = _source_names(context)
    concept_name = preset.get("concept_name", f"{first['name']} x {second['name']}")
    source_a_functions = _joined(first["system_functions"], first["notes"])
    source_b_functions = _joined(second["system_functions"], second["notes"])
    replaceable_surface = _joined(first["replaceable_elements"] + second["replaceable_elements"], "source presentation details")
    new_unified_verb = (selected_variation or {}).get("core_verb") or preset.get(
        "core_verb",
        f"apply {first['name']}'s board pressure through {second['name']}'s access logic",
    )
    main_interaction = (selected_variation or {}).get("main_interaction") or preset.get(
        "main_interaction",
        f"Use one interaction model that preserves {first['name']}'s { _pick(first['system_functions'], first['core_verb']) } and {second['name']}'s { _pick(second['system_functions'], second['core_verb']) }.",
    )
    objective = (selected_variation or {}).get("objective") or preset.get(
        "objective",
        f"Preserve {first['name']}'s {_pick(first['winning_points'], first['main_goal'] or first['notes'])} while also preserving {second['name']}'s {_pick(second['winning_points'], second['main_goal'] or second['notes'])}.",
    )
    core_loop = (selected_variation or {}).get("core_loop") or preset.get(
        "core_loop",
        f"read exposed state -> commit the unified action -> resolve board update and pressure -> reassess the next layer",
    )
    failure_pressure = (selected_variation or {}).get("failure_pressure") or preset.get(
        "failure_pressure",
        f"{first['pressure']} plus {second['pressure']}",
    )
    input_behavior = (selected_variation or {}).get("input_behavior") or preset.get(
        "input_behavior",
        "Use a single unified input that preserves both source games' strategic functions instead of copying both source verbs.",
    )
    variation_1 = preset.get(
        "variation_1",
        f"Variation 1: Keep {first['name']}'s board promise but let {second['name']}'s pressure source drive the fail state.",
    )
    variation_2 = preset.get(
        "variation_2",
        f"Variation 2: Keep {second['name']}'s board promise but let {first['name']}'s pressure source drive the fail state.",
    )
    variation_3 = preset.get(
        "variation_3",
        f"Variation 3: Reassign one of {first['name']}'s objects so it performs {second['name']}'s gameplay job inside a unified loop.",
    )
    why_it_works = preset.get(
        "why_it_works",
        f"It preserves {first['name']}'s {_pick(first['fun_points'], first['notes'])} and {second['name']}'s {_pick(second['fun_points'], second['notes'])} inside one interaction loop.",
    )
    why_it_fails = (
        "If the fusion keeps both source verbs literally, the player will learn two competing games instead of one coherent system."
        + (
            f" It must also avoid {first['avoid'][0].lower()} and {second['avoid'][0].lower()}."
            if first["avoid"] and second["avoid"]
            else ""
        )
    )
    why_fresh = preset.get(
        "why_fresh",
        f"It reassigns source roles instead of copying source verbs: {first['name']} contributes {_pick(first['system_functions'], first['notes'])} while {second['name']} contributes {_pick(second['system_functions'], second['notes'])}.",
    )
    why_understandable = preset.get(
        "why_understandable",
        "The board still communicates one clear action, one clear update, and one clear failure channel after every turn.",
    )
    board_setup = (selected_variation or {}).get("board_setup") or preset.get(
        "board_setup",
        f"A compact board combines {first['board_topology']} with {second['board_topology']} while keeping a single readable objective.",
    )
    object_rules = (selected_variation or {}).get("object_rules") or preset.get(
        "object_rules",
        "Every action must advance both source functions at once; if a rule only expresses one source superficially, it should be removed.",
    )
    win_condition = preset.get("win_condition", "Clear the board before the pressure system locks the run.")
    lose_condition = preset.get("lose_condition", "The board pressure system blocks further productive play before the objective is complete.")

    return {
        "concept_name": concept_name,
        "source_names": source_names,
        "main_interaction": main_interaction,
        "objective": objective,
        "core_loop": core_loop,
        "failure_pressure": failure_pressure,
        "game_line": source_names,
        "genre": "Hybrid casual puzzle",
        "core_verb": new_unified_verb,
        "board_topology": f"{first['board_topology']} fused with {second['board_topology']}",
        "object_types": preset.get("object_types", "fused board pieces that preserve source functions without copying every source object"),
        "primary_decision": preset.get(
            "primary_decision",
            f"which unified action best preserves {first['name']}'s {_pick(first['system_functions'], first['core_verb'])} and {second['name']}'s {_pick(second['system_functions'], second['core_verb'])}",
        ),
        "skill_type": "forward planning with board readability",
        "pressure_type": failure_pressure,
        "failure_mode": f"{first['failure_mode']}; {second['failure_mode']}",
        "depth_source": f"{first['depth_source']} combined with {second['depth_source']}",
        "player_emotion": "clarity under pressure",
        "why_it_works": why_it_works,
        "why_it_fails": why_it_fails,
        "why_fresh": why_fresh,
        "why_understandable": why_understandable,
        "likely_obstacles": "Over-complex states if too many blocker layers are introduced too early.",
        "production_risk": "Tuning puzzle readability without trivializing optimal order.",
        "prototype_scope": "One mechanic slice, two handcrafted levels, no progression layer.",
        "reasons_fail": "If the fusion cannot explain why replacing the source verb creates a better unified loop, it will collapse into a stapled-together design.",
        "board_setup": board_setup,
        "object_rules": object_rules,
        "win_condition": win_condition,
        "lose_condition": lose_condition,
        "level1_goal": preset.get("level1_goal", "Teach the unified interaction and show how both source functions appear through that one action."),
        "level2_goal": preset.get("level2_goal", "Add a second pressure layer that forces role reassignment or future planning."),
        "ui_notes": "Show moves remaining, lane status, source names, and a visible win or lose banner.",
        "debug_controls": "Reset level only. No step control in the player-facing loop.",
        "non_goals": "Theme, economy, meta progression, animation polish.",
        "success_criteria": "A new reader can predict the consequence of the next dispatch before committing it.",
        "strengths": f"It preserves source functions instead of copying source verbs. It also protects {_pick(first['winning_points'], first['notes']).lower()} and {_pick(second['winning_points'], second['notes']).lower()}.",
        "weaknesses": "Current prototype depth is narrow and depends on handcrafted layouts.",
        "key_risks": "If layouts are too linear, the game becomes a lock-and-key exercise instead of a puzzle.",
        "recommendation": "Iterate",
        "surface_form": _joined(first["surface_form"] + second["surface_form"], "literal source presentation"),
        "system_functions": _joined(first["system_functions"] + second["system_functions"], "reusable puzzle functions"),
        "replaceable_surface": replaceable_surface,
        "source_a_functions": source_a_functions,
        "source_b_functions": source_b_functions,
        "new_unified_verb": new_unified_verb,
        "literal_fusion_why_weaker": "literal side-by-side copying would preserve two separate interaction models instead of one coherent loop",
        "input_behavior": input_behavior,
        "variation_1": variation_1,
        "variation_2": variation_2,
        "variation_3": variation_3,
    }


def _http_post_json(url: str, payload: dict[str, Any], headers: dict[str, str], timeout: float = 45.0) -> dict[str, Any]:
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json", **headers},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def call_provider(profile: dict[str, str], prompt: str) -> str:
    provider = profile.get("provider", "mock")
    model = profile.get("model", "")

    if provider == "openai":
        api_key = os.getenv(profile.get("api_key_env", "OPENAI_API_KEY"), "").strip()
        if not api_key:
            raise RuntimeError("OPENAI_API_KEY missing")
        base = profile.get("base_url") or "https://api.openai.com/v1"
        url = base.rstrip("/") + "/chat/completions"
        payload = {
            "model": model or "gpt-5-mini",
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.4,
        }
        data = _http_post_json(url, payload, {"Authorization": f"Bearer {api_key}"})
        return data["choices"][0]["message"]["content"]

    if provider == "ollama":
        base = profile.get("base_url") or "http://localhost:11434/api"
        url = base.rstrip("/") + "/chat"
        payload = {
            "model": model or "qwen3:14b",
            "stream": False,
            "messages": [{"role": "user", "content": prompt}],
        }
        data = _http_post_json(url, payload, {})
        return data.get("message", {}).get("content", "")

    raise RuntimeError(f"provider not available: {provider}")


def _value_for_key(key: str, context: dict[str, Any]) -> str:
    fusion = _fusion_summary(context)
    defaults = {
        "Game": fusion["game_line"],
        "Genre": fusion["genre"],
        "Core Verb": fusion["core_verb"],
        "Board Topology": fusion["board_topology"],
        "Object Types": fusion["object_types"],
        "Primary Decision": fusion["primary_decision"],
        "Skill Type": fusion["skill_type"],
        "Pressure Type": fusion["pressure_type"],
        "Failure Mode": fusion["failure_mode"],
        "Depth Source": fusion["depth_source"],
        "Player Emotion": fusion["player_emotion"],
        "Why it works": fusion["why_it_works"],
        "Why it fails": fusion["why_it_fails"],
        "Concept Name": fusion["concept_name"],
        "Fused Sources": fusion["source_names"],
        "Core Player Verb": fusion["core_verb"],
        "Main Interaction": fusion["main_interaction"],
        "Objective": fusion["objective"],
        "Why It Feels Fresh": fusion["why_fresh"],
        "Why It Is Understandable": fusion["why_understandable"],
        "Failure Pressure": fusion["failure_pressure"],
        "Likely Obstacles": fusion["likely_obstacles"],
        "Production Risk": fusion["production_risk"],
        "Prototype Scope": fusion["prototype_scope"],
        "Reasons It May Fail": fusion["reasons_fail"],
        "Core Loop": fusion["core_loop"],
        "Input Behavior": fusion["input_behavior"],
        "Board Setup": fusion["board_setup"],
        "Object Rules": fusion["object_rules"],
        "Win Condition": fusion["win_condition"],
        "Lose Condition": fusion["lose_condition"],
        "Level 1 Goal": fusion["level1_goal"],
        "Level 2 Goal": fusion["level2_goal"],
        "UI Notes": fusion["ui_notes"],
        "Debug Controls": fusion["debug_controls"],
        "Non-Goals": fusion["non_goals"],
        "Success Criteria": fusion["success_criteria"],
        "Clarity": "4.0",
        "Novelty": "3.7",
        "Depth": "3.5",
        "Level Scalability": "3.4",
        "Retention Potential": "3.1",
        "Production Feasibility": "4.0",
        "Strengths": fusion["strengths"],
        "Weaknesses": fusion["weaknesses"],
        "Key Risks": fusion["key_risks"],
        "Recommendation": fusion["recommendation"],
    }
    return defaults.get(key, "TBD")


def fill_template(template_text: str, context: dict[str, Any]) -> str:
    lines = template_text.splitlines()
    out: list[str] = []
    for line in lines:
        stripped = line.strip()
        if stripped.endswith(":") and not stripped.startswith("#"):
            key = stripped[:-1]
            out.append(f"{stripped} {_value_for_key(key, context)}")
        else:
            out.append(line)
    return "\n".join(out).rstrip() + "\n"


def generate_director_plan(context: dict[str, Any]) -> dict[str, Any]:
    fusion = _fusion_summary(context)
    variations = _variation_specs(context)
    return {
        "wave_id": context.get("wave_id", ""),
        "cell_id": context.get("cell_id", ""),
        "sources": [
            {"id": game["id"], "name": game["name"]}
            for game in _source_games(context)
        ],
        "new_unified_verb": fusion["new_unified_verb"],
        "source_a_functions": fusion["source_a_functions"],
        "source_b_functions": fusion["source_b_functions"],
        "replaceable_surface": fusion["replaceable_surface"],
        "literal_fusion_why_weaker": fusion["literal_fusion_why_weaker"],
        "variation_targets": variations if variations else [
            {"id": "variation_01", "label": "Primary variation", "role": "conservative", "summary": fusion["variation_1"]},
            {"id": "variation_02", "label": "Secondary variation", "role": "conservative", "summary": fusion["variation_2"]},
            {"id": "variation_03", "label": "Tertiary variation", "role": "novelty", "summary": fusion["variation_3"]},
        ],
    }


def render_director_plan(plan: dict[str, Any]) -> str:
    lines = [
        "# Director Plan",
        "",
        f"Wave: {plan['wave_id']}",
        f"Cell: {plan['cell_id']}",
        f"Sources: {', '.join(source['name'] for source in plan['sources'])}",
        "",
        "Pre-Ideation Guardrails:",
        f"- New Unified Player Verb: {plan['new_unified_verb']}",
        f"- Source A Functions To Preserve: {plan['source_a_functions']}",
        f"- Source B Functions To Preserve: {plan['source_b_functions']}",
        f"- Replaceable Surface Elements: {plan['replaceable_surface']}",
        f"- Why Literal Fusion Is Weaker: {plan['literal_fusion_why_weaker']}",
        "",
        "Variation Targets:",
    ]
    for idx, variation in enumerate(plan["variation_targets"], start=1):
        lines.append(f"{idx}. {variation.get('label', variation.get('id', 'variation'))}")
        if "summary" in variation:
            lines.append(f"   - Summary: {variation['summary']}")
        for key in ("core_verb", "main_interaction", "objective", "failure_pressure"):
            if variation.get(key):
                label = key.replace("_", " ").title()
                lines.append(f"   - {label}: {variation[key]}")
    lines.append("")
    return "\n".join(lines)


def _stage_prompt(role_text: str, template_text: str, context: dict[str, Any], artifact_type: str) -> str:
    director_brief = context.get("director_brief", "").strip()
    director_plan = context.get("director_plan_markdown", "").strip()
    return (
        "You are an execution agent in PuzzleFusionFactory.\n"
        "Follow the role instructions exactly and output only markdown.\n\n"
        f"Role instructions:\n{role_text}\n\n"
        f"Artifact type: {artifact_type}\n"
        f"Cell context JSON: {json.dumps(context, ensure_ascii=True)}\n\n"
        + (f"Director plan:\n{director_plan}\n\n" if director_plan else "")
        + (f"Director brief:\n{director_brief}\n\n" if director_brief else "")
        +
        "Fill this template with concrete content and keep all headings/fields:\n"
        f"{template_text}\n"
    )


def generate_text_artifact(
    *,
    repo_root: Path,
    role: str,
    artifact_type: str,
    context: dict[str, Any],
    profile: dict[str, str],
    config: dict[str, Any],
) -> tuple[str, bool, str]:
    template_name = TEMPLATE_MAP[artifact_type]
    role_path = repo_root / "agents" / f"{role}.md"
    template_path = repo_root / "templates" / template_name

    if not role_path.exists():
        raise FileNotFoundError(f"missing role file: {role_path}")
    if not template_path.exists():
        raise FileNotFoundError(f"missing template file: {template_path}")

    role_text = read_text(role_path)
    template_text = read_text(template_path)
    prompt = _stage_prompt(role_text, template_text, context, artifact_type)

    fallback = False
    output = ""
    if profile.get("provider") != "mock":
        try:
            output = call_provider(profile, prompt).strip() + "\n"
        except (RuntimeError, urllib.error.URLError, TimeoutError, KeyError, IndexError):
            if not allow_mock_fallback(config):
                raise
            fallback = True

    if profile.get("provider") == "mock" or fallback or not output.strip():
        output = fill_template(template_text, context)
        fallback = True

    return output, fallback, template_name


def generate_prototype_html(context: dict[str, Any]) -> str:
    ids = tuple(sorted(game["id"] for game in _source_games(context)))
    if ids != ("ios-6471490579-screw-jam", "ios-6751056652-pixel-flow"):
        title = _fusion_summary(context)["concept_name"]
        return f"""<!doctype html>
<html>
<head><meta charset=\"utf-8\" /><meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" /><title>{title}</title></head>
<body style=\"margin:0;background:#111;color:#fff;font-family:monospace;\">
<div style=\"max-width:920px;margin:0 auto;padding:24px;\">
<h1>{title}</h1>
<p>Fallback prototype. This fusion does not yet have a handcrafted playable loop.</p>
</div>
</body>
</html>
"""

    cid = context.get("cell_id", "cell")
    title = _fusion_summary(context)["concept_name"]
    source_names = _source_names(context)
    return f"""<!doctype html>
<html>
<head>
  <meta charset=\"utf-8\" />
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />
  <title>{title}</title>
  <style>
    :root {{ --bg:#0d1418; --panel:#162229; --ink:#f2efe4; --muted:#9eb2b7; --accent:#f06b47; --good:#3ac17e; --bad:#ef5350; }}
    * {{ box-sizing:border-box; }}
    body {{ margin:0; background:radial-gradient(circle at top left, rgba(240,107,71,0.18), transparent 30%), linear-gradient(180deg, #0f171c 0%, #0a1014 100%); color:var(--ink); font-family:Georgia, 'Times New Roman', serif; }}
    .wrap {{ max-width:1120px; margin:0 auto; padding:24px; }}
    .header {{ display:grid; gap:8px; margin-bottom:18px; }}
    .eyebrow {{ color:var(--muted); text-transform:uppercase; letter-spacing:0.14em; font-size:12px; }}
    h1 {{ margin:0; font-size:clamp(28px, 4vw, 46px); }}
    .sub {{ color:var(--muted); max-width:760px; line-height:1.45; }}
    .panel {{ background:rgba(22,34,41,0.92); border:1px solid rgba(255,255,255,0.08); border-radius:18px; box-shadow:0 20px 60px rgba(0,0,0,0.35); }}
    .hud {{ display:grid; grid-template-columns:repeat(4, minmax(0,1fr)); gap:12px; padding:14px; margin-bottom:16px; }}
    .stat {{ padding:12px; border-radius:12px; background:rgba(255,255,255,0.04); }}
    .label {{ display:block; color:var(--muted); font-size:11px; text-transform:uppercase; letter-spacing:0.14em; }}
    .value {{ display:block; margin-top:6px; font-size:20px; }}
    .board {{ padding:18px; }}
    .dock {{ display:grid; grid-template-columns:repeat(3, minmax(0,1fr)); gap:12px; margin-bottom:16px; }}
    .dock-slot {{ min-height:80px; border-radius:16px; background:rgba(255,255,255,0.04); border:1px solid rgba(255,255,255,0.06); padding:10px; display:grid; gap:8px; }}
    .dock-slot button {{ border:0; border-radius:12px; padding:12px; font-weight:700; cursor:pointer; }}
    .dock-slot button:disabled {{ opacity:0.35; cursor:not-allowed; }}
    .arena {{ position:relative; min-height:640px; overflow:hidden; }}
    .frame {{ position:absolute; inset:46px; border-radius:34px; border:16px solid rgba(217,177,93,0.22); box-shadow:inset 0 0 0 1px rgba(255,255,255,0.08); }}
    .center-board {{ position:absolute; left:50%; top:50%; transform:translate(-50%, -50%); width:360px; height:360px; border-radius:28px; background:rgba(255,255,255,0.04); border:1px solid rgba(255,255,255,0.07); display:grid; grid-template-columns:repeat(3, 1fr); gap:18px; padding:28px; }}
    .stack {{ border-radius:18px; background:rgba(0,0,0,0.18); border:1px solid rgba(255,255,255,0.06); display:flex; flex-direction:column-reverse; align-items:center; padding:18px 8px 10px; gap:8px; position:relative; }}
    .stack-label {{ position:absolute; top:8px; left:10px; color:var(--muted); font-size:11px; text-transform:uppercase; letter-spacing:0.12em; }}
    .screw-chip {{ width:56px; height:56px; border-radius:50%; display:grid; place-items:center; font-size:11px; font-weight:700; color:#091014; box-shadow:inset 0 -6px 0 rgba(0,0,0,0.18); }}
    .screw-chip.hidden {{ opacity:0.24; filter:grayscale(0.45); }}
    .boxes {{ position:absolute; inset:0; }}
    .box {{ width:54px; height:54px; border-radius:16px; position:absolute; display:grid; place-items:center; font-weight:700; color:#091014; box-shadow:0 14px 24px rgba(0,0,0,0.28), inset 0 -6px 0 rgba(0,0,0,0.18); }}
    .cap {{ position:absolute; bottom:-18px; font-size:11px; color:var(--ink); }}
    .legend {{ display:grid; grid-template-columns:repeat(3, minmax(0,1fr)); gap:10px; margin-bottom:16px; }}
    .legend-item {{ padding:12px; border-radius:14px; background:rgba(255,255,255,0.04); color:var(--muted); line-height:1.35; }}
    .controls {{ display:flex; gap:12px; padding:0 0 20px; }}
    button.action {{ background:var(--accent); color:#fff; border:0; padding:12px 16px; border-radius:999px; font-weight:700; cursor:pointer; }}
    button.secondary {{ background:rgba(255,255,255,0.08); color:var(--ink); }}
    .message {{ margin-top:14px; padding:14px; border-radius:14px; }}
    .win {{ background:rgba(58,193,126,0.14); color:#baf1d1; }}
    .lose {{ background:rgba(239,83,80,0.14); color:#ffd0cf; }}
    .rules {{ margin-top:18px; padding:18px; line-height:1.45; color:var(--muted); }}
    @media (max-width:900px) {{
      .hud {{ grid-template-columns:repeat(2, minmax(0,1fr)); }}
      .dock {{ grid-template-columns:1fr; }}
      .legend {{ grid-template-columns:1fr; }}
      .arena {{ min-height:760px; }}
      .center-board {{ width:292px; height:292px; }}
    }}
  </style>
</head>
<body>
  <div class=\"wrap\">
    <div class=\"header\">
      <div class=\"eyebrow\">Playable Fusion Prototype</div>
      <h1>{title}</h1>
      <div class=\"sub\">{source_names}. Send colored screwboxes from the dock onto the surrounding conveyor. Boxes collect matching exposed screws from layered stacks. Clear every stack before you run out of dispatches.</div>
    </div>
    <div class=\"panel hud\">
      <div class=\"stat\"><span class=\"label\">Cell</span><span class=\"value\">{cid}</span></div>
      <div class=\"stat\"><span class=\"label\">Dispatches Left</span><span class=\"value\" id=\"dispatches\"></span></div>
      <div class=\"stat\"><span class=\"label\">Stacks Cleared</span><span class=\"value\" id=\"stacksCleared\"></span></div>
      <div class=\"stat\"><span class=\"label\">State</span><span class=\"value\" id=\"stateLabel\">Running</span></div>
    </div>
    <div class=\"panel board\">
      <div class=\"dock\" id=\"dock\"></div>
      <div class=\"legend\">
        <div class=\"legend-item\">Dispatch order matters. A box does one full conveyor lap, then exits.</div>
        <div class=\"legend-item\">Only the top screw in each stack is exposed and collectible.</div>
        <div class=\"legend-item\">Each box can hold up to 3 matching screws before it returns to dock.</div>
      </div>
      <div class=\"arena\">
        <div class=\"frame\"></div>
        <div class=\"center-board\" id=\"board\"></div>
        <div class=\"boxes\" id=\"boxes\"></div>
      </div>
      <div class=\"controls\">
        <button class=\"action\" id=\"reset\">Reset</button>
        <button class=\"action secondary\" id=\"nextLevel\" style=\"display:none;\">Next Level</button>
      </div>
      <div id=\"message\"></div>
    </div>
    <div class=\"panel rules\">Source influence: Screw Jam gives the layered exposed-order stacks. Pixel Flow gives the surrounding conveyor, dock queue, and route pressure. The intended feeling is sending the right box at the right moment and watching the board unlock cleanly.</div>
  </div>
  <script>
    const COLORS = {{ red:'#f06b47', blue:'#46a6ff', green:'#62c97f' }};
    const LEVELS = [
      {{ dispatches:4, dockQueue:['red','blue','green','red','blue'], stacks:[{{ id:'A', screws:['blue','red'] }}, {{ id:'B', screws:['green','blue'] }}, {{ id:'C', screws:['red','green'] }}] }},
      {{ dispatches:5, dockQueue:['blue','red','green','blue','red','green'], stacks:[{{ id:'A', screws:['green','blue','red'] }}, {{ id:'B', screws:['red','green','blue'] }}, {{ id:'C', screws:['blue','red','green'] }}] }}
    ];
    const PATH = [{{x:220,y:44}},{{x:380,y:44}},{{x:540,y:44}},{{x:636,y:140}},{{x:636,y:300}},{{x:636,y:460}},{{x:540,y:556}},{{x:380,y:556}},{{x:220,y:556}},{{x:124,y:460}},{{x:124,y:300}},{{x:124,y:140}}];
    const STACK_VISITS = {{ A:[1,7], B:[3,9], C:[5,11] }};
    let levelIndex = 0;
    let state = createLevelState(levelIndex);
    let lastTime = 0;
    function createLevelState(index) {{
      const level = LEVELS[index];
      return {{ dispatchesLeft: level.dispatches, dockQueue: level.dockQueue.slice(), activeBox: null, delivered: {{red:0, blue:0, green:0}}, stacks: level.stacks.map(s => ({{ id:s.id, screws:s.screws.slice() }})), message: 'Dispatch a box from the dock. Matching top screws are collected automatically as the box passes.', finished: 'running' }};
    }}
    function topScrew(stack) {{ return stack.screws.length ? stack.screws[stack.screws.length - 1] : null; }}
    function stackClearedCount() {{ return state.stacks.filter(stack => stack.screws.length === 0).length; }}
    function stateKind() {{
      if (stackClearedCount() === state.stacks.length) return 'win';
      if (state.dispatchesLeft <= 0 && !state.activeBox) return 'lose';
      return 'running';
    }}
    function dispatchBox(slotIndex) {{
      if (state.activeBox || state.dispatchesLeft <= 0 || state.finished !== 'running') return;
      if (slotIndex < 0 || slotIndex >= Math.min(3, state.dockQueue.length)) return;
      const color = state.dockQueue.splice(slotIndex, 1)[0];
      state.activeBox = {{ color, pathIndex:0, progress:0, collected:0, capacity:3, visited:new Set() }};
      state.dispatchesLeft -= 1;
      state.message = color.toUpperCase() + ' box launched. Watch which exposed screws it can collect this lap.';
      render();
    }}
    function collectAtVisit(visitIndex) {{
      if (!state.activeBox) return;
      for (const stack of state.stacks) {{
        if (!STACK_VISITS[stack.id].includes(visitIndex)) continue;
        const key = stack.id + ':' + visitIndex;
        if (state.activeBox.visited.has(key)) continue;
        state.activeBox.visited.add(key);
        const top = topScrew(stack);
        if (top && top === state.activeBox.color && state.activeBox.collected < state.activeBox.capacity) {{
          stack.screws.pop();
          state.activeBox.collected += 1;
          state.message = state.activeBox.color.toUpperCase() + ' box collected a screw from stack ' + stack.id + '.';
        }}
      }}
    }}
    function update(dt) {{
      if (!state.activeBox || state.finished !== 'running') return;
      state.activeBox.progress += dt * 0.0006;
      while (state.activeBox.progress >= 1) {{
        state.activeBox.progress -= 1;
        state.activeBox.pathIndex += 1;
        if (state.activeBox.pathIndex >= PATH.length) {{
          state.delivered[state.activeBox.color] += state.activeBox.collected;
          state.message = state.activeBox.color.toUpperCase() + ' box returned to dock carrying ' + state.activeBox.collected + ' screw(s).';
          state.activeBox = null;
          state.finished = stateKind();
          render();
          return;
        }}
        collectAtVisit(state.activeBox.pathIndex);
      }}
      state.finished = stateKind();
    }}
    function boxPosition() {{
      if (!state.activeBox) return null;
      const a = PATH[state.activeBox.pathIndex % PATH.length];
      const b = PATH[(state.activeBox.pathIndex + 1) % PATH.length];
      const t = state.activeBox.progress;
      return {{ x: a.x + (b.x - a.x) * t, y: a.y + (b.y - a.y) * t }};
    }}
    function renderDock() {{
      const dock = document.getElementById('dock');
      dock.innerHTML = [0,1,2].map(index => {{
        const color = state.dockQueue[index];
        if (!color) return `<div class="dock-slot"><div class="label">Dock Slot ${{index + 1}}</div><div>Empty</div></div>`;
        return `<div class="dock-slot"><div class="label">Dock Slot ${{index + 1}}</div><button data-dispatch="${{index}}" style="background:${{COLORS[color]}}; color:#091014;" ${{state.activeBox || state.finished !== 'running' ? 'disabled' : ''}}>Dispatch ${{color.toUpperCase()}} box</button></div>`;
      }}).join('');
      dock.querySelectorAll('button[data-dispatch]').forEach(btn => btn.addEventListener('click', () => dispatchBox(Number(btn.dataset.dispatch))));
    }}
    function renderBoard() {{
      document.getElementById('board').innerHTML = state.stacks.map(stack => {{
        const chips = stack.screws.map((color, idx) => `<div class="screw-chip ${{idx === stack.screws.length - 1 ? '' : 'hidden'}}" style="background:${{COLORS[color]}};">${{idx === stack.screws.length - 1 ? color.toUpperCase() : ''}}</div>`).join('');
        return `<div class="stack"><div class="stack-label">Stack ${{stack.id}}</div>${{chips || '<div class="screw-chip hidden" style="background:rgba(255,255,255,0.06);color:var(--muted);">CLEAR</div>'}}</div>`;
      }}).join('');
    }}
    function renderBoxes() {{
      const root = document.getElementById('boxes');
      if (!state.activeBox) {{ root.innerHTML = ''; return; }}
      const pos = boxPosition();
      root.innerHTML = `<div class="box" style="left:${{pos.x}}px; top:${{pos.y}}px; background:${{COLORS[state.activeBox.color]}}; transform:translate(-50%, -50%);">${{state.activeBox.color.slice(0,1).toUpperCase()}}<div class="cap">${{state.activeBox.collected}}/${{state.activeBox.capacity}}</div></div>`;
    }}
    function render() {{
      document.getElementById('dispatches').textContent = String(state.dispatchesLeft);
      document.getElementById('stacksCleared').textContent = String(stackClearedCount()) + '/' + state.stacks.length;
      renderDock();
      renderBoard();
      renderBoxes();
      const message = document.getElementById('message');
      const stateLabel = document.getElementById('stateLabel');
      const nextLevel = document.getElementById('nextLevel');
      if (state.finished === 'win') {{
        stateLabel.textContent = 'Win';
        message.className = 'message win';
        message.textContent = 'Board cleared. You sent the right boxes in the right order and the layered screws collapsed cleanly.';
        nextLevel.style.display = levelIndex < LEVELS.length - 1 ? 'inline-flex' : 'none';
      }} else if (state.finished === 'lose') {{
        stateLabel.textContent = 'Lose';
        message.className = 'message lose';
        message.textContent = 'You ran out of dispatches before clearing every stack. Retry and change the box order.';
        nextLevel.style.display = 'none';
      }} else {{
        stateLabel.textContent = state.activeBox ? 'Conveyor Running' : 'Awaiting Dispatch';
        message.className = 'message';
        message.textContent = state.message;
        nextLevel.style.display = 'none';
      }}
    }}
    function tick(ts) {{
      const dt = lastTime ? (ts - lastTime) : 16;
      lastTime = ts;
      update(dt);
      renderBoxes();
      requestAnimationFrame(tick);
    }}
    function resetLevel() {{ state = createLevelState(levelIndex); lastTime = 0; render(); }}
    document.getElementById('reset').addEventListener('click', resetLevel);
    document.getElementById('nextLevel').addEventListener('click', () => {{ if (levelIndex < LEVELS.length - 1) {{ levelIndex += 1; resetLevel(); }} }});
    render();
    requestAnimationFrame(tick);
  </script>
</body>
</html>
"""


def generate_director_brief(context: dict[str, Any]) -> str:
    fusion = _fusion_summary(context)
    return (
        "# Director Brief\n\n"
        f"Sources: {fusion['source_names']}\n\n"
        "Fusion Hypothesis:\n"
        f"{fusion['concept_name']} should preserve source functions, not source verbs. Use this board promise: {fusion['board_setup']} The central turn question is {fusion['primary_decision']}.\n\n"
        "Source A Functions To Preserve:\n"
        f"{fusion['source_a_functions']}\n\n"
        "Source B Functions To Preserve:\n"
        f"{fusion['source_b_functions']}\n\n"
        "Replaceable Surface Elements:\n"
        f"{fusion['replaceable_surface']}\n\n"
        "New Unified Player Verb:\n"
        f"{fusion['new_unified_verb']}\n\n"
        "Why Literal Fusion Is Weaker:\n"
        f"{fusion['literal_fusion_why_weaker']}\n\n"
        "Variation Targets For This Cell:\n"
        f"- {fusion['variation_1']}\n"
        f"- {fusion['variation_2']}\n"
        f"- {fusion['variation_3']}\n\n"
        "Board Promise:\n"
        f"{fusion['board_setup']}\n\n"
        "Turn Action:\n"
        f"{fusion['main_interaction']}\n\n"
        "Failure Pressure:\n"
        f"{fusion['failure_pressure']}\n\n"
        "Guardrails:\n"
        "- Do not describe the game as abstract domains only.\n"
        "- Preserve system functions and winning points even when the source verb changes.\n"
        "- Prefer one unified interaction model over two literal copied source loops.\n"
        "- Preserve a visible cause-effect chain after every move.\n"
        "- Keep the first prototype limited to one clear mechanic slice.\n"
    )


def generate_human_review_stub(repo_root: Path, context: dict[str, Any]) -> tuple[str, str]:
    template_path = repo_root / "templates" / "human_review.md"
    template_text = read_text(template_path)
    fusion = _fusion_summary(context)
    content = (
        template_text.replace("Wave:", f"Wave: {context.get('wave_id', '')}")
        .replace("Cell:", f"Cell: {context.get('cell_id', '')}")
        .replace("Concept Name:", f"Concept Name: {fusion['concept_name']}")
    )
    return content, "human_review.md"


def deterministic_scores(cell_id: str, domain: str) -> dict[str, float]:
    seed = int(hashlib.sha256(f"{cell_id}:{domain}".encode("utf-8")).hexdigest()[:8], 16)

    def score(offset: int) -> float:
        value = 3.0 + ((seed >> offset) % 13) * 0.1
        return round(min(value, 4.2), 1)

    return {
        "clarity": score(0),
        "depth": score(4),
        "level_scalability": score(8),
        "production_feasibility": score(12),
        "retention_potential": score(16),
        "novelty": score(20),
    }


def write_metadata(
    *,
    metadata_path: Path,
    wave_id: str,
    cell_id: str,
    role: str,
    template_name: str,
    profile: dict[str, str],
    artifact_path: Path,
    fallback_used: bool,
) -> None:
    payload = {
        "wave_id": wave_id,
        "cell_id": cell_id,
        "role": role,
        "template": template_name,
        "profile": profile,
        "artifact_path": str(artifact_path),
        "generated_at": now_iso(),
        "fallback_used": fallback_used,
    }
    metadata_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
