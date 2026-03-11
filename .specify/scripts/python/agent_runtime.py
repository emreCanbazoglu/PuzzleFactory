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
        "core_verb": "remove exposed screws to open matching flow lanes",
        "primary_decision": "which exposed screw unlocks the most useful lane progress without wasting a move",
        "main_interaction": "Click exposed screws to open lane segments so queued pixels can reach matching exits.",
        "objective": "Clear the minimum blocker set needed to connect all three pixel lanes before moves run out.",
        "core_loop": "inspect exposed screws -> remove one -> lanes recalculate -> newly opened packets flow",
        "failure_pressure": "wasting removals on visible but non-critical screws",
        "why_it_works": "It combines lane-routing pressure with exposure-order pressure, so every removal changes both access and flow.",
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
    },
    "ios-6471490579-screw-jam": {
        "core_verb": "remove blockers in a legal exposure order",
        "board_topology": "stacked blockers on a compact grid",
        "pressure": "unlock order and blocked access",
        "failure_mode": "deadlock from removing the wrong exposed blocker",
        "depth_source": "planning future accessibility before committing",
        "notes": "exposed-order removal and deadlock risk",
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
    }


def _source_names(context: dict[str, Any]) -> str:
    return " + ".join(game["name"] for game in _source_games(context)) or "Unknown Sources"


def _pair_preset(context: dict[str, Any]) -> dict[str, str]:
    ids = tuple(sorted(game["id"] for game in _source_games(context)))
    return PAIR_PRESETS.get(ids, {})


def _fusion_summary(context: dict[str, Any]) -> dict[str, str]:
    sources = [_normalize_game(game) for game in _source_games(context)]
    preset = _pair_preset(context)
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
        }

    first, second = sources[0], sources[1]
    source_names = _source_names(context)
    concept_name = preset.get("concept_name", f"{first['name']} x {second['name']}")
    main_interaction = preset.get(
        "main_interaction",
        f"Fuse {first['core_verb']} with {second['core_verb']} in one deterministic board state.",
    )
    objective = preset.get(
        "objective",
        f"Use {first['mechanics'][0]} pressure and {second['mechanics'][0]} pressure to solve a single board cleanly.",
    )
    core_loop = preset.get(
        "core_loop",
        f"read board -> apply {first['core_verb']} -> resolve {second['failure_mode']} risk -> check objective",
    )
    failure_pressure = preset.get(
        "failure_pressure",
        f"{first['pressure']} plus {second['pressure']}",
    )

    return {
        "concept_name": concept_name,
        "source_names": source_names,
        "main_interaction": main_interaction,
        "objective": objective,
        "core_loop": core_loop,
        "failure_pressure": failure_pressure,
        "game_line": source_names,
        "genre": "Hybrid casual puzzle",
        "core_verb": preset.get("core_verb", f"{first['core_verb']} while respecting {second['core_verb']}"),
        "board_topology": f"{first['board_topology']} fused with {second['board_topology']}",
        "object_types": "colored packets, exits, screws, blockers, move budget",
        "primary_decision": preset.get(
            "primary_decision",
            f"how to apply {second['core_verb']} so {first['core_verb']} remains possible",
        ),
        "skill_type": "forward planning with board readability",
        "pressure_type": failure_pressure,
        "failure_mode": f"{first['failure_mode']}; {second['failure_mode']}",
        "depth_source": f"{first['depth_source']} combined with {second['depth_source']}",
        "player_emotion": "clarity under pressure",
        "why_it_works": preset.get(
            "why_it_works",
            f"It combines {first['notes']} with {second['notes']} in one readable move loop.",
        ),
        "why_it_fails": "If the board state stops telegraphing which action is critical, the fusion collapses into guesswork.",
        "why_fresh": f"{first['name']} creates forward movement while {second['name']} makes access order the main tension.",
        "why_understandable": f"Both sources have visible cause-effect: remove blocker, path opens; clear path, packet moves.",
        "likely_obstacles": "Over-complex states if too many blocker layers are introduced too early.",
        "production_risk": "Tuning puzzle readability without trivializing optimal order.",
        "prototype_scope": "One mechanic slice, two handcrafted levels, no progression layer.",
        "reasons_fail": "If legal removals do not meaningfully change flow, the fusion feels stapled together.",
        "board_setup": "Three horizontal lanes feed matching exits on the right. Screws occupy lane cells and can be removed only when exposed in their column.",
        "object_rules": "Packets auto-claim a lane once every blocker in that lane is removed. Clicking an exposed screw removes it and spends one move.",
        "win_condition": "All packets reach matching exits before the move budget is exhausted.",
        "lose_condition": "Move budget hits zero before all lanes are opened.",
        "level1_goal": "Teach exposed-screw removal and show that only some screws matter to opening flow.",
        "level2_goal": "Introduce decoy screws so removal order creates real planning pressure.",
        "ui_notes": "Show moves remaining, lane status, source names, and a visible win or lose banner.",
        "debug_controls": "Reset level only. No step control in the player-facing loop.",
        "non_goals": "Theme, economy, meta progression, animation polish.",
        "success_criteria": "A new reader can predict the consequences of a removal before clicking it.",
        "strengths": "High readability and clear fusion of route pressure with exposure order.",
        "weaknesses": "Current prototype depth is narrow and depends on handcrafted layouts.",
        "key_risks": "If layouts are too linear, the game becomes a lock-and-key exercise instead of a puzzle.",
        "recommendation": "Iterate",
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
        "Input Behavior": "Click an exposed screw to remove it. The board immediately recomputes which lanes are open.",
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


def _stage_prompt(role_text: str, template_text: str, context: dict[str, Any], artifact_type: str) -> str:
    director_brief = context.get("director_brief", "").strip()
    return (
        "You are an execution agent in PuzzleFusionFactory.\n"
        "Follow the role instructions exactly and output only markdown.\n\n"
        f"Role instructions:\n{role_text}\n\n"
        f"Artifact type: {artifact_type}\n"
        f"Cell context JSON: {json.dumps(context, ensure_ascii=True)}\n\n"
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
    cid = context.get("cell_id", "cell")
    source_names = _source_names(context)
    title = _fusion_summary(context)["concept_name"]
    return f"""<!doctype html>
<html>
<head>
  <meta charset=\"utf-8\" />
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />
  <title>{title}</title>
  <style>
    :root {{ --bg: #0d1418; --panel: #162229; --ink: #f2efe4; --muted: #9eb2b7; --accent: #f06b47; --good: #3ac17e; --bad: #ef5350; }}
    * {{ box-sizing: border-box; }}
    body {{ margin: 0; background:
      radial-gradient(circle at top left, rgba(240,107,71,0.18), transparent 30%),
      linear-gradient(180deg, #0f171c 0%, #0a1014 100%);
      color: var(--ink); font-family: Georgia, 'Times New Roman', serif; }}
    .wrap {{ max-width: 1100px; margin: 0 auto; padding: 24px; }}
    .header {{ display: grid; gap: 8px; margin-bottom: 18px; }}
    .eyebrow {{ color: var(--muted); text-transform: uppercase; letter-spacing: 0.14em; font-size: 12px; }}
    h1 {{ margin: 0; font-size: clamp(28px, 4vw, 46px); }}
    .sub {{ color: var(--muted); max-width: 760px; line-height: 1.4; }}
    .panel {{ background: rgba(22,34,41,0.92); border: 1px solid rgba(255,255,255,0.08); border-radius: 18px; box-shadow: 0 20px 60px rgba(0,0,0,0.35); }}
    .hud {{ display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 12px; padding: 14px; margin-bottom: 16px; }}
    .stat {{ padding: 12px; border-radius: 12px; background: rgba(255,255,255,0.04); }}
    .stat .label {{ display: block; color: var(--muted); font-size: 11px; text-transform: uppercase; letter-spacing: 0.14em; }}
    .stat .value {{ display: block; margin-top: 6px; font-size: 20px; }}
    .board {{ padding: 20px; }}
    .lane {{ display: grid; grid-template-columns: 100px repeat(4, 90px) 100px; gap: 12px; align-items: center; margin-bottom: 14px; }}
    .endpoint, .exit {{ padding: 14px; border-radius: 14px; text-align: center; font-weight: 700; }}
    .endpoint {{ background: rgba(255,255,255,0.06); }}
    .exit {{ border: 2px solid rgba(255,255,255,0.12); }}
    .cell {{ height: 78px; border-radius: 16px; display: grid; place-items: center; background: rgba(255,255,255,0.05); border: 1px solid rgba(255,255,255,0.08); position: relative; overflow: hidden; }}
    .open::after {{ content: 'FLOW'; font-size: 12px; color: rgba(255,255,255,0.35); letter-spacing: 0.16em; }}
    .screw {{ width: 62px; height: 62px; border-radius: 50%; border: 0; cursor: pointer; color: #0b1014; font-weight: 700; font-size: 12px; box-shadow: inset 0 -6px 0 rgba(0,0,0,0.18); }}
    .screw:disabled {{ cursor: not-allowed; opacity: 0.45; }}
    .row-packet {{ width: 50px; height: 50px; border-radius: 14px; display: grid; place-items: center; font-weight: 700; color: #081014; }}
    .controls {{ display: flex; gap: 12px; padding: 0 20px 20px; }}
    button.action {{ background: var(--accent); color: #fff; border: 0; padding: 12px 16px; border-radius: 999px; font-weight: 700; cursor: pointer; }}
    .message {{ margin-top: 14px; padding: 14px; border-radius: 14px; }}
    .win {{ background: rgba(58,193,126,0.14); color: #baf1d1; }}
    .lose {{ background: rgba(239,83,80,0.14); color: #ffd0cf; }}
    .rules {{ margin-top: 18px; padding: 18px; line-height: 1.45; color: var(--muted); }}
    @media (max-width: 900px) {{
      .hud {{ grid-template-columns: repeat(2, minmax(0, 1fr)); }}
      .lane {{ grid-template-columns: 70px repeat(4, 1fr) 70px; gap: 8px; }}
      .cell {{ height: 64px; }}
      .screw {{ width: 48px; height: 48px; }}
    }}
  </style>
</head>
<body>
  <div class=\"wrap\">
    <div class=\"header\">
      <div class=\"eyebrow\">Playable Fusion Prototype</div>
      <h1>{title}</h1>
      <div class=\"sub\">{source_names}. Remove only exposed screws. Each removal costs one move. A lane starts flowing once every screw in that lane is gone. Open all three lanes before moves run out.</div>
    </div>
    <div class=\"panel hud\">
      <div class=\"stat\"><span class=\"label\">Cell</span><span class=\"value\">{cid}</span></div>
      <div class=\"stat\"><span class=\"label\">Moves Left</span><span class=\"value\" id=\"moves\"></span></div>
      <div class=\"stat\"><span class=\"label\">Open Lanes</span><span class=\"value\" id=\"lanesOpen\"></span></div>
      <div class=\"stat\"><span class=\"label\">State</span><span class=\"value\" id=\"stateLabel\">Running</span></div>
    </div>
    <div class=\"panel board\">
      <div id=\"board\"></div>
      <div class=\"controls\">
        <button class=\"action\" id=\"reset\">Reset</button>
      </div>
      <div id=\"message\"></div>
    </div>
    <div class=\"panel rules\">
      Source influence: Pixel Flow style lane completion plus Screw Jam style exposed-order removal. The correct play is not \"remove everything\". It is \"remove the few screws that unlock the three packet lanes inside the move budget\".
    </div>
  </div>
  <script>
    const COLORS = {{
      red: '#f06b47',
      blue: '#46a6ff',
      green: '#62c97f',
      brass: '#d9b15d',
      steel: '#a8b6c1'
    }};
    const INITIAL = {{
      moves: 5,
      screws: [
        {{ id: 's1', lane: 0, col: 0, color: 'brass' }},
        {{ id: 's2', lane: 1, col: 0, color: 'steel' }},
        {{ id: 's3', lane: 2, col: 0, color: 'brass' }},
        {{ id: 's4', lane: 1, col: 1, color: 'steel' }},
        {{ id: 's5', lane: 0, col: 2, color: 'brass' }},
        {{ id: 's6', lane: 2, col: 3, color: 'steel' }}
      ],
      packets: [
        {{ lane: 0, color: 'red', label: 'R' }},
        {{ lane: 1, color: 'blue', label: 'B' }},
        {{ lane: 2, color: 'green', label: 'G' }}
      ]
    }};
    let state = structuredClone(INITIAL);
    function exposed(screw) {{
      return !state.screws.some(other => other.col === screw.col && other.lane < screw.lane);
    }}
    function laneOpen(lane) {{
      return !state.screws.some(s => s.lane === lane);
    }}
    function stateKind() {{
      const openCount = state.packets.filter(p => laneOpen(p.lane)).length;
      if (openCount === state.packets.length) return 'win';
      if (state.moves <= 0) return 'lose';
      const hasMove = state.screws.some(exposed);
      return hasMove ? 'running' : 'lose';
    }}
    function removeScrew(id) {{
      const screw = state.screws.find(s => s.id === id);
      if (!screw || !exposed(screw) || stateKind() !== 'running') return;
      state.screws = state.screws.filter(s => s.id !== id);
      state.moves -= 1;
      render();
    }}
    function laneRow(packet) {{
      const cells = [];
      for (let col = 0; col < 4; col += 1) {{
        const screw = state.screws.find(s => s.lane === packet.lane && s.col === col);
        if (screw) {{
          cells.push(`<div class="cell"><button class="screw" data-id="${{screw.id}}" style="background:${{COLORS[screw.color]}};" ${{exposed(screw) ? '' : 'disabled'}}>${{exposed(screw) ? 'EXPOSED' : 'LOCKED'}}</button></div>`);
        }} else {{
          cells.push('<div class="cell open"></div>');
        }}
      }}
      return `<div class="lane">
        <div class="endpoint" style="background:${{COLORS[packet.color]}}22;border:1px solid ${{COLORS[packet.color]}};"><div class="row-packet" style="background:${{COLORS[packet.color]}};">${{packet.label}}</div></div>
        ${{cells.join('')}}
        <div class="exit" style="background:${{laneOpen(packet.lane) ? COLORS[packet.color] + '22' : 'rgba(255,255,255,0.05)'}};border-color:${{COLORS[packet.color]}};">${{laneOpen(packet.lane) ? 'FLOWING' : 'EXIT'}}</div>
      </div>`;
    }}
    function render() {{
      document.getElementById('moves').textContent = String(state.moves);
      document.getElementById('lanesOpen').textContent = String(state.packets.filter(p => laneOpen(p.lane)).length) + '/3';
      document.getElementById('board').innerHTML = state.packets.map(laneRow).join('');
      document.querySelectorAll('.screw').forEach(btn => btn.addEventListener('click', () => removeScrew(btn.dataset.id)));
      const kind = stateKind();
      const stateLabel = document.getElementById('stateLabel');
      const message = document.getElementById('message');
      if (kind === 'win') {{
        stateLabel.textContent = 'Win';
        message.className = 'message win';
        message.textContent = 'All three packets can now flow. This board is solved.';
      }} else if (kind === 'lose') {{
        stateLabel.textContent = 'Lose';
        message.className = 'message lose';
        message.textContent = 'You ran out of useful removals before opening every lane.';
      }} else {{
        stateLabel.textContent = 'Running';
        message.className = 'message';
        message.textContent = 'Remove exposed screws only. Hidden screws become exposed after blockers above them are cleared.';
      }}
    }}
    document.getElementById('reset').addEventListener('click', () => {{
      state = structuredClone(INITIAL);
      render();
    }});
    render();
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
        f"{fusion['concept_name']} should use {fusion['board_topology']} and center the turn around {fusion['primary_decision']}.\n\n"
        "Board Promise:\n"
        f"{fusion['board_setup']}\n\n"
        "Turn Action:\n"
        f"{fusion['main_interaction']}\n\n"
        "Failure Pressure:\n"
        f"{fusion['failure_pressure']}\n\n"
        "Guardrails:\n"
        "- Do not describe the game as abstract domains only.\n"
        "- Preserve a visible cause-effect chain after every move.\n"
        "- Keep the first prototype limited to one clear mechanic slice.\n"
    )


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
