"""
Kraken AI — Model providers.

Provider-agnostic streaming chat client over plain HTTP. Two wire formats:

  * OpenAI-compatible (`/chat/completions` SSE) — Ollama, LM Studio, vLLM,
    llama.cpp, OpenAI, Groq, OpenRouter, Mistral, DeepSeek, Together, and
    Gemini via its OpenAI-compat endpoint.
  * Anthropic native (`/v1/messages` SSE) — claude models.

Cloud providers are presets in `config.DEFAULT_PROVIDERS`; API keys resolve
through `engine.keys` (keys.json → ~/.env → environment) or `api_key=` on the
client. Any OpenAI-compatible URL is supported via `--provider custom`.
"""

import json
import os
import threading
import urllib.error
import urllib.request
from collections.abc import Callable, Iterator

from apps.kraken.engine.config import DEFAULT_PROVIDERS

TIMEOUT = 300

# Shell-safe env vars we forward to local model servers (optional keys).
_ENV_KEYS = ("OLLAMA_HOST", "OPENAI_API_KEY")


class ProviderError(Exception):
    """Raised when a model backend cannot be reached or returns an error."""


class ChatClient:
    """Streaming OpenAI-compatible chat client for local or custom backends."""

    def __init__(
        self,
        provider: str = "ollama",
        base_url: str | None = None,
        model: str = "qwen2.5-coder:14b",
        temperature: float = 0.2,
        max_tokens: int = 4096,
        num_ctx: int = 8192,
        api_key: str | None = None,
        timeout: int = TIMEOUT,
        on_chunk: Callable[[str], None] | None = None,
        on_status: Callable[[str], None] | None = None,
    ):
        self.provider = (provider or "ollama").lower()
        meta = DEFAULT_PROVIDERS.get(self.provider, {"kind": "openai"})
        self.kind = meta["kind"]
        self.base_url = (base_url or meta.get("base_url") or "").rstrip("/")
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.num_ctx = num_ctx
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")
        self.timeout = timeout
        self._on_chunk = on_chunk
        self._on_status = on_status
        self._lock = threading.RLock()
        self.stats = {"tokens": 0, "streams": 0}

    # ── Endpoint helpers ───────────────────────────────────────
    def _chat_url(self) -> str:
        if self.kind == "anthropic":
            return f"{self.base_url}/v1/messages"
        if self.kind == "ollama" and "/v1" not in self.base_url:
            return f"{self.base_url}/api/chat"
        return f"{self.base_url}/chat/completions"

    def _headers(self) -> dict:
        headers = {"Content-Type": "application/json"}
        if self.kind == "anthropic":
            if self.api_key:
                headers["x-api-key"] = self.api_key
            headers["anthropic-version"] = "2023-06-01"
        elif self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers

    def _payload(self, messages: list[dict]) -> dict:
        if self.kind == "anthropic":
            system_text = "\n".join(
                m["content"] for m in messages if m.get("role") == "system" and m.get("content")
            ).strip()
            chat = [m for m in messages if m.get("role") != "system"]
            payload: dict = {
                "model": self.model,
                "max_tokens": self.max_tokens,
                "messages": chat,
                "stream": True,
                "temperature": self.temperature,
            }
            if system_text:
                payload["system"] = system_text
            return payload
        if self.kind == "ollama" and "/v1" not in self.base_url:
            return {
                "model": self.model,
                "messages": messages,
                "stream": True,
                "options": {
                    "temperature": self.temperature,
                    "num_predict": self.max_tokens,
                    "num_ctx": self.num_ctx,
                },
            }
        payload: dict = {
            "model": self.model,
            "messages": messages,
            "stream": True,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
        }
        return payload

    # ── Public API ─────────────────────────────────────────────
    def chat(self, messages: list[dict]) -> str:
        """Non-streaming convenience wrapper over stream()."""
        return "".join(self.stream(messages))

    def stream(self, messages: list[dict]) -> Iterator[str]:
        """Yield text deltas as they arrive from the backend."""
        url = self._chat_url()
        payload = self._payload(messages)
        data = json.dumps(payload).encode("utf-8")

        if self._on_status:
            self._on_status(f"POST {url} · {self.model}")

        try:
            with self._lock, urllib.request.urlopen(
                urllib.request.Request(
                    url,
                    data=data,
                    headers=self._headers(),
                    method="POST",
                ),
                timeout=self.timeout,
            ) as resp:
                content_type = resp.headers.get("Content-Type", "")
                if "application/json" in content_type:
                    body = resp.read().decode("utf-8", "replace")
                    text = self._parse_single(body)
                    if text:
                        with self._lock:
                            self.stats["streams"] += 1
                            self.stats["tokens"] += self._estimate_tokens(text)
                        if self._on_chunk:
                            self._on_chunk(text)
                        yield text
                    return

                with self._lock:
                    self.stats["streams"] += 1
                for raw in resp:
                    line = raw.decode("utf-8", "replace").strip()
                    if not line:
                        continue
                    if line.startswith("data:"):
                        chunk = line[5:].strip()
                        if chunk == "[DONE]":
                            break
                    else:
                        chunk = line
                    text = self._parse_chunk(chunk)
                    if text:
                        with self._lock:
                            self.stats["tokens"] += self._estimate_tokens(text)
                        if self._on_chunk:
                            self._on_chunk(text)
                        yield text

        except urllib.error.HTTPError as e:
            if e.code == 404:
                raise ProviderError(
                    f"{self.provider} is running but has no model named {self.model!r} — "
                    f"pull it (e.g. `ollama pull {self.model}`) or set a model that exists "
                    f"(`kraken models`, `kraken config model <name>`)"
                ) from e
            if e.code in (401, 403):
                raise ProviderError(
                    f"{self.provider} rejected the request (HTTP {e.code}) — check the API key "
                    f"(`kraken keys add {self.provider} <key>` or set an OPENAI_API_KEY env var)"
                ) from e
            raise ProviderError(
                f"{self.provider} at {self.base_url} returned HTTP {e.code} ({e.reason})"
            ) from e
        except urllib.error.URLError as e:
            raise ProviderError(
                f"Cannot reach {self.provider} at {self.base_url} — is the model server running? "
                f"({e.reason})"
            ) from e
        except OSError as e:
            raise ProviderError(
                f"Network error talking to {self.provider}: {e}"
            ) from e
        except (ValueError, KeyError) as e:
            raise ProviderError(f"Malformed response from {self.provider}: {e}") from e

    # ── Response parsing ───────────────────────────────────────
    @staticmethod
    def _parse_chunk(chunk: str) -> str:
        try:
            obj = json.loads(chunk)
        except ValueError:
            return ""
        # Anthropic SSE: {"type":"content_block_delta","delta":{"type":"text_delta","text":"..."}}
        if obj.get("type") == "content_block_delta":
            delta = obj.get("delta") or {}
            if delta.get("type") == "text_delta":
                return delta.get("text") or ""
            return ""
        # Ollama native
        if "message" in obj and isinstance(obj["message"], dict):
            return obj["message"].get("content", "")
        # OpenAI compatible
        choices = obj.get("choices")
        if choices:
            delta = choices[0].get("delta") or {}
            return delta.get("content") or choices[0].get("text") or ""
        return ""

    @staticmethod
    def _parse_single(body: str) -> str:
        try:
            obj = json.loads(body)
        except ValueError:
            return ""
        if "message" in obj and isinstance(obj["message"], dict):
            return obj["message"].get("content", "")
        # Anthropic non-stream: {"content":[{"type":"text","text":"..."}]}
        content = obj.get("content")
        if isinstance(content, list):
            return "".join(b.get("text", "") for b in content if isinstance(b, dict) and b.get("type") == "text")
        choices = obj.get("choices")
        if choices:
            return (choices[0].get("message") or {}).get("content") or ""
        return ""

    @staticmethod
    def _estimate_tokens(text: str) -> int:
        # Cheap heuristic: ~4 chars per token.
        return max(1, len(text) // 4)


def list_ollama_models(base_url: str = "http://localhost:11434") -> list[str]:
    """Query a running Ollama server for installed models (best-effort)."""
    try:
        with urllib.request.urlopen(
            f"{base_url}/api/tags", timeout=5
        ) as resp:
            data = json.loads(resp.read().decode("utf-8", "replace"))
        return [m.get("name", "") for m in data.get("models", []) if m.get("name")]
    except Exception:
        return []


def ping_provider(provider: str, base_url: str) -> bool:
    """Best-effort TCP reachability probe for the configured backend."""
    import socket
    from urllib.parse import urlparse

    parsed = urlparse(base_url)
    host = parsed.hostname or "localhost"
    port = parsed.port or 80
    try:
        with socket.create_connection((host, port), timeout=4):
            return True
    except OSError:
        return False
