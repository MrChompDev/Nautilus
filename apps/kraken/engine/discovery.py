"""
Kraken AI — local model + cloud endpoint discovery.

Scans the machine for models that are already downloaded or reachable:

  * Ollama        — running server (/api/tags) and on-disk manifest store
  * LM Studio     — GGUF files under the LM Studio model cache
  * llama.cpp     — GGUF files in common model directories

Plus one-shot recommendations for `kraken setup` and remote model listings
for API providers. Everything is best-effort and never blocks long.
"""

import json
import os
import urllib.request
from typing import Any

from apps.kraken.engine.config import CLOUD_PROVIDERS, DEFAULT_CLOUD_MODELS, DEFAULT_PROVIDERS
from apps.kraken.engine.keys import load_keys

LMSTUDIO_DIRS = (
    os.path.expanduser("~/.cache/lm-studio/models"),
    os.path.expanduser("~/.lmstudio/models"),
    os.path.expanduser("~/.lmstudio/.cache/lm-studio/models"),
)

GGUF_DIRS = (
    os.path.expanduser("~/.local/share/models"),
    os.path.expanduser("~/.cache/gguf"),
    os.path.expanduser("~/models"),
    os.path.expanduser("~/Downloads/models"),
    os.path.expanduser("~/.cache/llama.cpp"),
    "/opt/models",
)

OLLAMA_MANIFESTS = os.path.expanduser("~/.ollama/models/manifests")

_MAX_WALK_DEPTH = 4
_MAX_MODELS_PER_SOURCE = 200


def _walk_guffs(root: str) -> list[str]:
    """Find *.gguf files under root, bounded depth and count."""
    out: list[str] = []
    if not root or not os.path.isdir(root):
        return out
    stack = [(root, 0)]
    while stack and len(out) < _MAX_MODELS_PER_SOURCE:
        current, depth = stack.pop()
        if depth > _MAX_WALK_DEPTH:
            continue
        try:
            entries = os.listdir(current)
        except OSError:
            continue
        for entry in sorted(entries):
            full = os.path.join(current, entry)
            if os.path.isdir(full):
                if depth < _MAX_WALK_DEPTH:
                    stack.append((full, depth + 1))
            elif entry.lower().endswith(".gguf"):
                out.append(full)
    return out


def _ollama_disk_models() -> list[dict[str, Any]]:
    """Read model names from Ollama's manifest store without a server."""
    out: list[dict[str, Any]] = []
    if not os.path.isdir(OLLAMA_MANIFESTS):
        return out
    for dirpath, _dirnames, filenames in os.walk(OLLAMA_MANIFESTS):
        for fn in sorted(filenames):
            if not fn.endswith(".json"):
                continue
            rel = os.path.relpath(os.path.join(dirpath, fn), OLLAMA_MANIFESTS)
            parts = rel.replace(os.sep, "/").split("/")
            # registry.ollama.ai/namespace/model/tag.json
            if len(parts) < 3:
                continue
            model = parts[-2] if len(parts) >= 3 else parts[-1]
            tag = parts[-1][: -len(".json")]
            name = f"{model}:{tag}"
            if not name.startswith("."):
                out.append({
                    "provider": "ollama",
                    "name": name,
                    "path": os.path.join(dirpath, fn),
                    "source": "disk",
                })
            if len(out) >= _MAX_MODELS_PER_SOURCE:
                break
    return out


def find_local_models(base_url: str = "http://localhost:11434",
                      gguf_dirs: tuple[str, ...] | None = None,
                      lmstudio_dirs: tuple[str, ...] | None = None) -> list[dict[str, Any]]:
    """Discover downloaded / reachable local models on this machine."""
    from apps.kraken.engine.providers import list_ollama_models

    results: list[dict[str, Any]] = []
    seen: set[str] = set()

    def _add(provider: str, name: str, path: str = "", source: str = ""):
        key = f"{provider}:{name}"
        if key in seen:
            return
        seen.add(key)
        results.append({"provider": provider, "name": name, "path": path, "source": source})

    for m in list_ollama_models(base_url):
        _add("ollama", m, source="server")
    for m in _ollama_disk_models():
        _add(m["provider"], m["name"], m.get("path", ""), m.get("source", "disk"))

    for root in lmstudio_dirs or LMSTUDIO_DIRS:
        for gguf in _walk_guffs(root):
            name = os.path.splitext(os.path.basename(gguf))[0]
            _add("lmstudio", name, path=gguf, source="disk")

    for root in gguf_dirs or GGUF_DIRS:
        for gguf in _walk_guffs(root):
            name = os.path.splitext(os.path.basename(gguf))[0]
            _add("llamacpp", name, path=gguf, source="disk")

    return results


def recommend_backend(home_dir: str, base_url: str = "http://localhost:11434") -> dict[str, Any] | None:
    """Pick the most promising backend for `kraken setup`.

    Priority: a reachable Ollama server with models → any downloaded local
    model (Ollama/LM Studio/llama.cpp) → any cloud API key found.
    """
    keys = load_keys(home_dir)
    models = find_local_models(base_url)

    for m in models:
        if m["provider"] == "ollama" and m["source"] == "server":
            return {"provider": "ollama", "base_url": base_url,
                    "model": m["name"], "api_key": None, "hint": "running Ollama server"}

    if models:
        m = models[0]
        meta = DEFAULT_PROVIDERS.get(m["provider"], {})
        return {"provider": m["provider"], "base_url": meta.get("base_url", base_url),
                "model": m["name"], "api_key": None, "hint": f"model on disk ({m['source']})"}

    for provider in CLOUD_PROVIDERS:
        if keys.get(provider):
            meta = DEFAULT_PROVIDERS[provider]
            return {
                "provider": provider,
                "base_url": meta["base_url"],
                "model": DEFAULT_CLOUD_MODELS.get(provider, ""),
                "api_key": keys[provider],
                "hint": f"{meta['label']} API key found",
            }
    return None


def list_api_models(provider: str, base_url: str, api_key: str) -> list[str]:
    """List available models for an API provider (best-effort, short timeout)."""
    if not api_key:
        return []
    meta = DEFAULT_PROVIDERS.get(provider, {})
    try:
        if meta.get("kind") == "anthropic":
            url = f"{base_url.rstrip('/')}/v1/models"
            headers = {"x-api-key": api_key, "anthropic-version": "2023-06-01"}
        else:
            url = f"{base_url.rstrip('/')}/models"
            headers = {"Authorization": f"Bearer {api_key}"}
        with urllib.request.urlopen(urllib.request.Request(url, headers=headers), timeout=6) as resp:
            data = json.loads(resp.read().decode("utf-8", "replace"))
        entries = data.get("data") or []
        return sorted(e.get("id", "") for e in entries if e.get("id"))
    except Exception:
        return []


def detect_provider_health(base_url: str = "http://localhost:11434") -> dict[str, dict]:
    """TCP ping every known local server; returns {provider: {'alive': bool}}."""
    from apps.kraken.engine.providers import ping_provider

    out: dict[str, dict] = {}
    for name in ("ollama", "lmstudio", "vllm", "llamacpp"):
        meta = DEFAULT_PROVIDERS[name]
        out[name] = {"alive": ping_provider(name, meta["base_url"])}
    return out
