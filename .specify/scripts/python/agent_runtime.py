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


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


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
    cell_id = context.get("cell_id", "cell")
    discovery_domain = context.get("discovery_domain", "hybrid")
    prototype_domain = context.get("prototype_domain", "hybrid")
    concept_name = f"{cell_id}_{prototype_domain}_fusion"

    defaults = {
        "Game": context.get("reference_game", "Library sample"),
        "Genre": "Hybrid puzzle",
        "Core Verb": "route and sort",
        "Board Topology": "grid",
        "Object Types": "tiles, containers, blockers",
        "Primary Decision": "choose order of moves under slot pressure",
        "Skill Type": "planning",
        "Pressure Type": "limited space and queue pressure",
        "Failure Mode": "deadlock",
        "Depth Source": "state-space branching",
        "Player Emotion": "control under pressure",
        "Why it works": "clear goals with compounding consequences",
        "Why it fails": "if states become unreadable",
        "Concept Name": concept_name,
        "Fused Sources": f"{discovery_domain} + {prototype_domain}",
        "Core Player Verb": "route",
        "Main Interaction": "assign moves that reorder constrained objects",
        "Objective": "clear target sets without overflow",
        "Why It Feels Fresh": "cross-domain pressure combination",
        "Why It Is Understandable": "single-turn cause-effect visibility",
        "Failure Pressure": "queue overflow",
        "Likely Obstacles": "early complexity spikes",
        "Production Risk": "tuning challenge curves",
        "Prototype Scope": "2 levels, deterministic",
        "Reasons It May Fail": "insufficient differentiation",
        "Core Loop": "observe -> choose move -> resolve -> check goals",
        "Input Behavior": "single click/tap selects action",
        "Board Setup": "compact board with constrained slots",
        "Object Rules": "deterministic movement and collisions",
        "Win Condition": "all targets completed",
        "Lose Condition": "no legal moves or overflow",
        "Level 1 Goal": "teach primary verb",
        "Level 2 Goal": "add second pressure axis",
        "UI Notes": "minimal readable HUD",
        "Debug Controls": "reset, step, seed display",
        "Non-Goals": "theme polish, monetization",
        "Success Criteria": "players can clear both levels consistently",
        "Clarity": "3.6",
        "Novelty": "3.3",
        "Depth": "3.5",
        "Level Scalability": "3.7",
        "Retention Potential": "3.2",
        "Production Feasibility": "3.8",
        "Strengths": "clear feedback and deterministic outcomes",
        "Weaknesses": "novelty risk",
        "Key Risks": "late-level combinatorial explosion",
        "Recommendation": "Iterate",
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
    return (
        "You are an execution agent in PuzzleFusionFactory.\n"
        "Follow the role instructions exactly and output only markdown.\n\n"
        f"Role instructions:\n{role_text}\n\n"
        f"Artifact type: {artifact_type}\n"
        f"Cell context JSON: {json.dumps(context, ensure_ascii=True)}\n\n"
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
    domain = context.get("prototype_domain", "hybrid")
    return f"""<!doctype html>
<html>
<head>
  <meta charset=\"utf-8\" />
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />
  <title>{cid} prototype</title>
  <style>
    body {{ margin: 0; background: #111; color: #fff; font-family: monospace; }}
    #hud {{ padding: 10px; display: flex; gap: 10px; align-items: center; }}
    button {{ background: #2a2a2a; color: #fff; border: 1px solid #666; padding: 6px 10px; }}
    canvas {{ border-top: 1px solid #444; width: 100%; height: calc(100vh - 52px); }}
  </style>
</head>
<body>
  <div id=\"hud\">
    <span>Cell: {cid}</span>
    <span>Domain: {domain}</span>
    <button id=\"reset\">Reset</button>
    <button id=\"step\">Step</button>
  </div>
  <canvas id=\"c\" width=\"900\" height=\"520\"></canvas>
  <script>
    const c = document.getElementById('c');
    const ctx = c.getContext('2d');
    let t = 0;
    function draw() {{
      ctx.fillStyle = '#111';
      ctx.fillRect(0, 0, c.width, c.height);
      ctx.fillStyle = '#39a';
      ctx.fillRect(120 + (t % 200), 120, 80, 80);
      ctx.fillStyle = '#fff';
      ctx.fillText('Deterministic prototype placeholder', 20, 24);
      ctx.fillText('Use Step/Reset debug controls', 20, 44);
    }}
    function step() {{ t += 16; draw(); }}
    document.getElementById('step').onclick = step;
    document.getElementById('reset').onclick = () => {{ t = 0; draw(); }};
    draw();
  </script>
</body>
</html>
"""


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
