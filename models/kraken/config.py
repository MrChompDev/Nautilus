"""Kraken configuration — opencode-style: providers, models, MCP, commands, theme.

Lives at ~/.config/kraken/config.json (override with KRAKEN_CONFIG_DIR or KRAKEN_CONFIG).
API keys are kept separately in ~/.config/kraken/auth.json (chmod 600).
"""

from __future__ import annotations

import json
import os

DEFAULTS: dict = {
    "defaults": {"model": "auto"},
    "theme": {"blue": [32, 58, 108], "cyan": [0, 242, 194]},
    "providers": {},
    "models": {},
    "mcp": {},
    "command": {},
}

EXAMPLES = {
    "defaults": {"model": "auto"},
    "theme": {"blue": [32, 58, 108], "cyan": [0, 242, 194]},
    "providers": {
        "openai": {"type": "openai", "base_url": "https://api.openai.com/v1", "env_key": "OPENAI_API_KEY"},
        "ollama": {"type": "openai", "base_url": "http://localhost:11434/v1"},
    },
    "models": {
        "gpt": {"provider": "openai", "remote": "gpt-4o-mini", "kind": "text", "temperature": 0.7, "max_tokens": 600},
        "llama3": {"provider": "ollama", "remote": "llama3.1", "kind": "text", "temperature": 0.7, "max_tokens": 600},
    },
    "mcp": {
        "filesystem": {
            "command": "npx",
            "args": ["-y", "@modelcontextprotocol/server-filesystem", "/tmp"],
        }
    },
    "command": {
        "tldr": {"template": "Give a concise 5-bullet summary of $ARGUMENTS.", "description": "Concise summary"},
    },
}


def config_dir() -> str:
    return os.environ.get("KRAKEN_CONFIG_DIR", os.path.expanduser("~/.config/kraken"))


def config_path() -> str:
    return os.environ.get("KRAKEN_CONFIG", os.path.join(config_dir(), "config.json"))


def auth_path() -> str:
    return os.path.join(config_dir(), "auth.json")


def _deep_merge(base: dict, extra: dict) -> dict:
    out = dict(base)
    for k, v in (extra or {}).items():
        if isinstance(v, dict) and isinstance(out.get(k), dict):
            out[k] = _deep_merge(out[k], v)
        else:
            out[k] = v
    return out


class Config:
    """Load/save ~/.config/kraken/config.json with sane defaults."""

    def __init__(self, data: dict | None = None):
        self.data = _deep_merge(DEFAULTS, data or {})

    # ── load / save ────────────────────────────────────────────────
    @classmethod
    def load(cls, path: str | None = None) -> Config:
        path = path or config_path()
        try:
            with open(path, encoding="utf-8") as f:
                return cls(json.load(f))
        except (OSError, ValueError):
            return cls()

    def save(self, path: str | None = None) -> str:
        path = path or config_path()
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.data, f, indent=2, sort_keys=True)
            f.write("\n")
        return path

    # ── accessors ──────────────────────────────────────────────────
    @property
    def defaults(self) -> dict:
        return self.data["defaults"]

    @property
    def theme(self) -> dict:
        return self.data["theme"]

    @property
    def providers(self) -> dict:
        return self.data["providers"]

    @property
    def models(self) -> dict:
        return self.data["models"]

    @property
    def mcp(self) -> dict:
        return self.data["mcp"]

    @property
    def commands(self) -> dict:
        return self.data["command"]

    # ── mutators ───────────────────────────────────────────────────
    def add_provider(self, name: str, *, base_url: str, api_key: str | None = None,
                     env_key: str | None = None, type_: str = "openai") -> None:
        entry = {"type": type_, "base_url": base_url}
        if api_key:
            entry["api_key"] = api_key
        if env_key:
            entry["env_key"] = env_key
        self.providers[name] = entry

    def add_model(self, model_id: str, provider: str, *, remote: str | None = None,
                  kind: str = "text", temperature: float | None = None,
                  top_k: int | None = None, max_tokens: int | None = None) -> None:
        entry: dict = {"provider": provider, "kind": kind}
        if remote:
            entry["remote"] = remote
        if temperature is not None:
            entry["temperature"] = temperature
        if top_k is not None:
            entry["top_k"] = top_k
        if max_tokens is not None:
            entry["max_tokens"] = max_tokens
        self.models[model_id] = entry

    def add_mcp(self, name: str, *, command: str | None = None, args: list[str] | None = None,
                url: str | None = None, env: dict | None = None) -> None:
        entry: dict = {}
        if command:
            entry["command"] = command
        if args:
            entry["args"] = args
        if url:
            entry["url"] = url
        if env:
            entry["env"] = env
        self.mcp[name] = entry


class Auth:
    """API-key store; keys resolve as: config api_key > auth.json > KRAKEN_<PROVIDER>_API_KEY."""

    def __init__(self, keys: dict | None = None):
        self.keys = keys or {}

    @classmethod
    def load(cls) -> Auth:
        try:
            with open(auth_path(), encoding="utf-8") as f:
                return cls(json.load(f))
        except (OSError, ValueError):
            return cls()

    def save(self) -> str:
        path = auth_path()
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.keys, f, indent=2)
            f.write("\n")
        os.chmod(path, 0o600)
        return path

    def get(self, provider: str) -> str | None:
        env = os.environ.get(f"KRAKEN_{provider.upper()}_API_KEY")
        if env:
            return env
        return self.keys.get(provider)

    def set(self, provider: str, key: str) -> None:
        self.keys[provider] = key

    def rm(self, provider: str) -> bool:
        return self.keys.pop(provider, None) is not None