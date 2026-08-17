"""Kraken AI — persistent configuration.

Stores all settings as JSON in ~/.kraken/config.json.
Fully offline, auditable, zero lock-in.
"""

import json
import os
from dataclasses import dataclass, field
from typing import Any

KRAKEN_HOME = os.path.join(os.path.expanduser("~"), ".kraken")

# ── Sea-creature model catalogue ──────────────────────────────────

CREATURES = {
    "kraken": {
        "name": "Kraken",
        "subtitle": "Code from the Deep",
        "description": "General-purpose coding assistant. Reads your project, writes code, fixes bugs.",
        "color": "#00F2C2",
        "accent": "#004D40",
        "icon": "kraken",
        "specialties": ["code", "debug", "refactor", "architecture"],
        "system_prompt": (
            "You are Kraken, a coding assistant embedded in a project. "
            "You have access to the project file tree and can read/write files "
            "and run terminal commands. Be precise, concise, and always verify "
            "your changes compile or pass lint before suggesting them."
        ),
    },
    "leviathan": {
        "name": "Leviathan",
        "subtitle": "Prose from the Abyss",
        "description": "Writing assistant. READMEs, docs, prose, copy, and creative writing.",
        "color": "#7B68EE",
        "accent": "#2E1A6E",
        "icon": "leviathan",
        "specialties": ["write", "docs", "prose", "copy"],
        "system_prompt": (
            "You are Leviathan, a writing assistant with a deep command of language. "
            "You write clear, engaging prose. Match the tone requested. Be thorough "
            "when depth is needed, terse when brevity is asked for."
        ),
    },
    "charybdis": {
        "name": "Charybdis",
        "subtitle": "Visions from the Vortex",
        "description": "Image and video generation. Creates visuals from text descriptions.",
        "color": "#FF6B9D",
        "accent": "#6B1A3A",
        "icon": "charybdis",
        "specialties": ["image", "video", "visual", "art"],
        "system_prompt": (
            "You are Charybdis, a visual creation engine. You generate images and "
            "video concepts from text descriptions. Describe what you create in "
            "detail. When generating, specify dimensions, style, palette, and mood."
        ),
    },
    "megalodon": {
        "name": "Megalodon",
        "subtitle": "Hunt in the Dark",
        "description": "Security and pentest assistant. Scans, analyzes, and hardens systems.",
        "color": "#FF4444",
        "accent": "#6B1A1A",
        "icon": "megalodon",
        "specialties": ["pentest", "security", "audit", "harden"],
        "system_prompt": (
            "You are Megalodon, a security specialist. You analyze systems for "
            "vulnerabilities, suggest hardening measures, and write security-focused "
            "code. Always explain the risk level and potential impact of findings."
        ),
    },
}

DEFAULT_CREATURE = "kraken"

# ── Provider presets (for external APIs) ──────────────────────────

PROVIDERS = {
    "kraken-native": {"label": "Kraken Native", "kind": "native"},
    "ollama": {"label": "Ollama", "base_url": "http://localhost:11434", "kind": "ollama"},
    "lmstudio": {"label": "LM Studio", "base_url": "http://localhost:1234/v1", "kind": "openai"},
    "openai": {"label": "OpenAI", "base_url": "https://api.openai.com/v1", "kind": "openai"},
    "anthropic": {"label": "Anthropic", "base_url": "https://api.anthropic.com", "kind": "anthropic"},
}

DEFAULT_TOOLS = ("file_read", "file_write", "terminal_exec")


def _defaults() -> dict:
    return {
        "version": 2,
        "creature": DEFAULT_CREATURE,
        "provider": "kraken-native",
        "base_url": "",
        "model": "",
        "api_key": "",
        "temperature": 0.7,
        "max_tokens": 4096,
        "auto_approve": False,
        "memory_enabled": True,
        "workspace": os.getcwd(),
        "tools": list(DEFAULT_TOOLS),
    }


@dataclass
class KrakenConfig:
    home: str
    data: dict = field(default_factory=_defaults)

    @classmethod
    def load(cls, home: str | None = None) -> "KrakenConfig":
        h = home or KRAKEN_HOME
        cfg = cls(home=h, data=_defaults())
        path = os.path.join(h, "config.json")
        try:
            with open(path, encoding="utf-8") as f:
                stored = json.load(f)
            if isinstance(stored, dict):
                cfg.data.update(stored)
        except (OSError, ValueError):
            pass
        os.makedirs(h, exist_ok=True)
        return cfg

    def save(self):
        os.makedirs(self.home, exist_ok=True)
        path = os.path.join(self.home, "config.json")
        fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(self.data, f, indent=2)

    def get(self, key: str, default: Any = None) -> Any:
        return self.data.get(key, default)

    def set(self, key: str, value: Any):
        self.data[key] = value
        self.save()

    def __getattr__(self, name: str) -> Any:
        if name.startswith("_"):
            raise AttributeError(name)
        data = self.__dict__.get("data", {})
        if name in data:
            return data[name]
        raise AttributeError(name)

    @property
    def creature_info(self) -> dict:
        return CREATURES.get(self.data.get("creature", DEFAULT_CREATURE), CREATURES[DEFAULT_CREATURE])

    @property
    def memory_path(self) -> str:
        return os.path.join(self.home, "memory.db")

    @property
    def agents_dir(self) -> str:
        return os.path.join(self.home, "agents")
