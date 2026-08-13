"""
Kraken AI — Configuration store.

Persists user and session settings as plain JSON in the Kraken home
directory (~/.kraken/config.json) so the engine stays fully offline,
auditable, and free of any lock-in.
"""

import json
import os
from dataclasses import dataclass, field
from typing import Any

from apps.kraken.engine import __version__

DEFAULT_HOME = os.path.join(os.path.expanduser("~"), ".kraken")

DEFAULT_MODEL = "qwen2.5-coder:14b"

DEFAULT_PROVIDERS = {
    # Local servers
    "ollama": {"label": "Ollama", "base_url": "http://localhost:11434", "kind": "ollama"},
    "lmstudio": {"label": "LM Studio", "base_url": "http://localhost:1234/v1", "kind": "openai"},
    "vllm": {"label": "vLLM", "base_url": "http://localhost:8000/v1", "kind": "openai"},
    "llamacpp": {"label": "llama.cpp", "base_url": "http://localhost:8080/v1", "kind": "openai"},
    # Cloud APIs (OpenAI-compatible wire format, unless noted)
    "openai": {"label": "OpenAI", "base_url": "https://api.openai.com/v1", "kind": "openai"},
    "anthropic": {"label": "Anthropic", "base_url": "https://api.anthropic.com", "kind": "anthropic"},
    "gemini": {"label": "Google Gemini", "base_url": "https://generativelanguage.googleapis.com/v1beta/openai", "kind": "openai"},
    "groq": {"label": "Groq", "base_url": "https://api.groq.com/openai/v1", "kind": "openai"},
    "openrouter": {"label": "OpenRouter", "base_url": "https://openrouter.ai/api/v1", "kind": "openai"},
    "mistral": {"label": "Mistral", "base_url": "https://api.mistral.ai/v1", "kind": "openai"},
    "deepseek": {"label": "DeepSeek", "base_url": "https://api.deepseek.com/v1", "kind": "openai"},
    "together": {"label": "Together", "base_url": "https://api.together.xyz/v1", "kind": "openai"},
}

# Providers that talk to the cloud and want an API key.
CLOUD_PROVIDERS = (
    "openai", "anthropic", "gemini", "groq", "openrouter", "mistral", "deepseek", "together",
)

# A sensible default model per cloud provider (used by `kraken setup`).
DEFAULT_CLOUD_MODELS = {
    "openai": "gpt-4o-mini",
    "anthropic": "claude-3-5-haiku-latest",
    "gemini": "gemini-2.5-flash",
    "groq": "llama-3.3-70b-versatile",
    "openrouter": "meta-llama/llama-3.3-70b-instruct:free",
    "mistral": "mistral-small-latest",
    "deepseek": "deepseek-chat",
    "together": "meta-llama/Llama-3.3-70B-Instruct-Turbo",
}

DEFAULT_TOOLS = ("file_read", "file_write", "terminal_exec")


def _default_config() -> dict:
    return {
    "version": __version__,
    "provider": "ollama",
    "base_url": DEFAULT_PROVIDERS["ollama"]["base_url"],
    "model": DEFAULT_MODEL,
    "api_key": "",
    "temperature": 0.2,
        "max_tokens": 4096,
        "num_ctx": 8192,
        "auto_approve": False,
        "memory_enabled": True,
        "memory_top_k": 3,
        "max_agent_rounds": 12,
        "max_parallel_workers": 3,
        "workspace": os.getcwd(),
        "timeout": 300,
        "tools": list(DEFAULT_TOOLS),
    }


@dataclass
class KrakenConfig:
    """Loaded Kraken settings with attribute access + safe get/set."""

    home_dir: str
    data: dict = field(default_factory=_default_config)

    # ── Loading / saving ──────────────────────────────────────
    @classmethod
    def load(cls, home_dir: str | None = None) -> "KrakenConfig":
        home = home_dir or DEFAULT_HOME
        cfg = cls(home_dir=home, data=_default_config())
        path = os.path.join(home, "config.json")
        try:
            with open(path, encoding="utf-8") as f:
                stored = json.load(f)
            if isinstance(stored, dict):
                cfg.data.update(stored)
        except (OSError, ValueError, TypeError):
            pass
        cfg.ensure_home()
        return cfg

    def ensure_home(self):
        os.makedirs(self.home_dir, exist_ok=True)

    def save(self):
        self.ensure_home()
        path = os.path.join(self.home_dir, "config.json")
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(self.data, f, indent=2)
        except OSError:
            pass

    # ── Attribute access ──────────────────────────────────────
    def __getattr__(self, name: str) -> Any:
        if name.startswith("_"):
            raise AttributeError(name)
        data = self.__dict__.get("data", {})
        if name in data:
            return data[name]
        raise AttributeError(name)

    def get(self, key: str, default: Any = None) -> Any:
        return self.data.get(key, default)

    def set(self, key: str, value: Any):
        self.data[key] = value
        self.save()

    def update(self, **kwargs):
        self.data.update(kwargs)
        self.save()

    # ── Derived helpers ───────────────────────────────────────
    @property
    def config_path(self) -> str:
        return os.path.join(self.home_dir, "config.json")

    @property
    def memory_path(self) -> str:
        return os.path.join(self.home_dir, "memory.db")

    @property
    def agents_dir(self) -> str:
        return os.path.join(self.home_dir, "agents")
