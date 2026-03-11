#!/usr/bin/env python3
import os
from typing import Any


def _env_bool(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def allow_mock_fallback(config: dict[str, Any]) -> bool:
    if isinstance(config.get("execution"), dict) and "allow_mock_fallback" in config["execution"]:
        return bool(config["execution"]["allow_mock_fallback"])
    return _env_bool("PF_ALLOW_MOCK_FALLBACK", True)


def _default_profile(kind: str) -> dict[str, str]:
    provider_env = f"PF_{kind.upper()}_PROVIDER"
    model_env = f"PF_{kind.upper()}_MODEL"
    base_url_env = "OPENAI_BASE_URL" if kind == "cloud" else "OLLAMA_BASE_URL"

    provider = os.getenv(provider_env, "mock").strip().lower()
    if provider not in {"openai", "ollama", "mock"}:
        provider = "mock"

    model_default = "gpt-5-mini" if provider == "openai" else "qwen3:14b"
    model = os.getenv(model_env, model_default).strip()
    base_url = os.getenv(base_url_env, "").strip()
    api_key_env = "OPENAI_API_KEY" if provider == "openai" else ""

    return {
        "provider": provider,
        "model": model,
        "base_url": base_url,
        "api_key_env": api_key_env,
    }


def get_profile(config: dict[str, Any], profile_name: str) -> dict[str, str]:
    configured = {}
    if isinstance(config.get("models"), dict):
        if isinstance(config["models"].get(profile_name), dict):
            configured = dict(config["models"][profile_name])

    profile = _default_profile(profile_name)
    profile.update({k: str(v) for k, v in configured.items() if v is not None})
    profile["name"] = profile_name
    return profile


def resolve_profile_for_role(config: dict[str, Any], role: str) -> dict[str, str]:
    routing = config.get("routing", {}) if isinstance(config.get("routing"), dict) else {}
    cloud_roles = set(routing.get("cloud_roles", [])) if isinstance(routing.get("cloud_roles"), list) else set()
    local_roles = set(routing.get("local_roles", [])) if isinstance(routing.get("local_roles"), list) else set()

    if role in local_roles:
        return get_profile(config, "local")
    if role in cloud_roles:
        return get_profile(config, "cloud")
    return get_profile(config, "cloud")
