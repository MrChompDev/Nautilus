"""Kraken providers — pluggable model backends.

Two provider types:
  * "local"  — the trained NumPy models (text LMs + the diffusion image model)
  * "openai" — any OpenAI-compatible /chat/completions API (OpenAI, Ollama,
               llama.cpp, LM Studio, vLLM, Groq, OpenRouter, ...) with SSE
               streaming and native function-calling.

Configure providers/models in ~/.config/kraken/config.json; see `kraken config init`.
"""

from __future__ import annotations

import json
import os
import re
import time
import urllib.error
import urllib.request
from dataclasses import dataclass, field

from models.kraken.config import Auth, Config

# ✓ opencode-style in-spec tool call marker for models without native function calling.
TOOL_CALL_RE = re.compile(r"\[\[tool:([A-Za-z0-9_.-]+)(?:\s+(\{.*?\}))?\]\]", re.S)

System = "system"
User = "user"
Assistant = "assistant"
Tool = "tool"


@dataclass
class ToolCall:
    name: str
    arguments: dict = field(default_factory=dict)


@dataclass
class ChatMsg:
    role: str
    content: str = ""
    tool_calls: list[ToolCall] | None = None
    tool_call_id: str | None = None

    def to_dict(self) -> dict:
        d: dict = {"role": self.role}
        if self.content:
            d["content"] = self.content
        if self.tool_calls:
            d["tool_calls"] = [
                {"id": f"call_{i}", "type": "function",
                 "function": {"name": c.name, "arguments": json.dumps(c.arguments)}}
                for i, c in enumerate(self.tool_calls)
            ]
        if self.tool_call_id is not None:
            d["tool_call_id"] = self.tool_call_id
        return d


@dataclass
class ChatResult:
    content: str = ""
    tool_calls: list[ToolCall] | None = None
    tokens: int = 0
    seconds: float = 0.0
    tok_s: float = 0.0
    model: str = ""


@dataclass
class ModelRef:
    provider: str
    model_id: str
    remote: str | None
    kind: str = "text"
    entry: dict = field(default_factory=dict)

    def display(self) -> str:
        return f"{self.provider}/{self.model_id}"


class Provider:
    id = "base"

    def models(self) -> list[str]:
        raise NotImplementedError

    def chat(self, model: ModelRef, messages: list[ChatMsg], *, tools: list[dict] | None = None,
             temperature: float = 0.7, max_tokens: int = 200, top_k: int = 40,
             on_token: object | None = None) -> ChatResult:
        raise NotImplementedError

    def image(self, model: ModelRef, prompt: str) -> str:
        raise NotImplementedError(f"provider '{self.id}' has no image model")

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Provider {self.id}>"


# ───────────────────────── Local ───────────────────────────────────
class LocalProvider(Provider):
    """Runs the trained NumPy models (text + image) from models/trained."""

    def __init__(self, trained_dir: str):
        self.id = "local"
        self.trained_dir = trained_dir
        self._lms: dict[str, object] = {}
        self._imggen = None

    def models(self) -> list[str]:
        names = []
        if os.path.isdir(self.trained_dir):
            for name in sorted(os.listdir(self.trained_dir)):
                if os.path.isfile(os.path.join(self.trained_dir, name, "weights.npz")):
                    names.append(name)
        return names

    def is_image(self, model_id: str) -> bool:
        return model_id == "imggen" and os.path.isfile(os.path.join(self.trained_dir, "imggen", "weights.npz"))

    def _lm(self, model_id: str):
        if model_id not in self._lms:
            from models.lm.engine import LM

            self._lms[model_id] = LM(os.path.join(self.trained_dir, model_id))
        return self._lms[model_id]

    def _imggen(self):
        if self._imggen is None:
            from models.imggen.engine import ImageGen

            self._imggen = ImageGen(os.path.join(self.trained_dir, "imggen"))
        return self._imggen

    def _with_tools(self, system: str, tools: list[dict] | None) -> str:
        if not tools:
            return system
        block = 'If you need to call a tool, output exactly one line: [[tool:NAME {"arg": "value"}]]. '
        block += "After a tool result is provided, continue with your answer using that result."
        schema = json.dumps(tools, indent=1)
        return f"{system}\n\n## Available tools\n{schema}\n## Tool instructions\n{block}"

    def chat(self, model: ModelRef, messages: list[ChatMsg], *, tools: list[dict] | None = None,
             temperature: float = 0.7, max_tokens: int = 200, top_k: int = 40,
             on_token: object | None = None) -> ChatResult:
        lm = self._lm(model.model_id)
        parts = []
        for i, m in enumerate(messages):
            if m.role == System:
                parts.append(f"### system\n{self._with_tools(m.content, tools if i == 0 else None)}")
            else:
                parts.append(f"### {m.role}\n{m.content}")
        prompt = "\n\n".join(parts)

        acc: list[str] = []

        def sink(tok, _acc=acc, _on=on_token, _lm=lm):
            ch = _lm.decode([tok])
            _acc.append(ch)
            if _on is not None:
                _on(ch)

        t0 = time.time()
        out_ids = lm.model.generate(
            lm.tok.encode(prompt), max_new_tokens=max_tokens,
            temperature=temperature, top_k=top_k, stream=sink,
        )
        dt = time.time() - t0
        text = "".join(acc)
        tool_calls = None
        if _check_tools(text, tools):
            tool_calls = []
            for m in TOOL_CALL_RE.finditer(text):
                name, raw = m.group(1), m.group(2)
                args: dict = {}
                if raw:
                    try:
                        args = json.loads(raw)
                    except ValueError:
                        pass
                tool_calls.append(ToolCall(name=name, arguments=args))
            text = TOOL_CALL_RE.sub("", text).strip()
        n = len(out_ids)
        return ChatResult(content=text, tool_calls=tool_calls, tokens=n,
                          seconds=dt, tok_s=n / dt if dt > 0 else 0.0, model=f"local/{model.model_id}")

    def image(self, model: ModelRef, prompt: str) -> str:
        from models.imggen.engine import save_png

        gen = self._imggen()
        img = gen.generate(prompt, size=512, steps=40)
        path = os.path.join(os.getcwd(), f"kraken_art_{int(time.time())}.png")
        save_png(path, img)
        return path


# ───────────────────────── OpenAI-compatible ───────────────────────
class OpenAIProvider(Provider):
    def __init__(self, name: str, base_url: str, api_key: str | None = None):
        self.id = name
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key or ""

    def models(self) -> list[str]:
        # Model names come from config entry "remote" for each configured model.
        return []

    def _headers(self) -> dict:
        h = {"Content-Type": "application/json", "Accept": "text/event-stream"}
        if self.api_key:
            h["Authorization"] = f"Bearer {self.api_key}"
        return h

    def chat(self, model: ModelRef, messages: list[ChatMsg], *, tools: list[dict] | None = None,
             temperature: float = 0.7, max_tokens: int = 200, top_k: int = 40,
             on_token: object | None = None) -> ChatResult:
        payload = {
            "model": model.remote or model.model_id,
            "messages": [m.to_dict() for m in messages],
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": True,
        }
        if tools:
            payload["tools"] = tools
        body = json.dumps(payload).encode()
        req = urllib.request.Request(
            f"{self.base_url}/chat/completions", data=body,
            headers=self._headers(), method="POST",
        )
        t0 = time.time()
        try:
            resp = urllib.request.urlopen(req, timeout=300)
        except urllib.error.HTTPError as e:
            detail = e.read().decode(errors="replace")[:400]
            raise RuntimeError(f"[{self.id}] HTTP {e.code}: {detail}") from e
        except urllib.error.URLError as e:
            raise RuntimeError(f"[{self.id}] connection error: {e.reason}") from e

        text_parts: list[str] = []
        idx_calls: dict[int, dict] = {}
        completion_tokens = 0
        with resp:
            for raw in resp:
                line = raw.decode("utf-8", errors="replace").strip()
                if not line.startswith("data:"):
                    continue
                data = line[5:].strip()
                if data == "[DONE]":
                    break
                try:
                    obj = json.loads(data)
                except ValueError:
                    continue
                if "usage" in obj and obj["usage"]:
                    completion_tokens = obj["usage"].get("completion_tokens") or 0
                choices = obj.get("choices") or []
                if not choices:
                    continue
                delta = choices[0].get("delta") or {}
                if delta.get("content"):
                    text_parts.append(delta["content"])
                    if on_token is not None:
                        on_token(delta["content"])
                for tc in delta.get("tool_calls") or []:
                    slot = idx_calls.setdefault(tc.get("index", 0), {})
                    fn = tc.get("function") or {}
                    slot["name"] = slot.get("name", "") + (fn.get("name") or "")
                    slot["args"] = slot.get("args", "") + (fn.get("arguments") or "")

        dt = time.time() - t0
        content = "".join(text_parts)
        tool_calls = None
        if idx_calls:
            tool_calls = []
            for i in sorted(idx_calls):
                slot = idx_calls[i]
                name = slot.get("name", "")
                args: dict = {}
                if slot.get("args"):
                    try:
                        args = json.loads(slot["args"])
                    except ValueError:
                        args = {"raw": slot["args"]}
                tool_calls.append(ToolCall(name=name, arguments=args))
        if not completion_tokens:
            completion_tokens = max(1, len(content.split()))
        return ChatResult(content=content, tool_calls=tool_calls, tokens=completion_tokens,
                          seconds=dt, tok_s=completion_tokens / dt if dt > 0 else 0.0,
                          model=f"{self.id}/{model.remote or model.model_id}")


# ───────────────────────── registry ────────────────────────────────
_PROVIDERS: dict[str, Provider] = {}


def register_provider(provider: Provider) -> None:
    _PROVIDERS[provider.id] = provider


def get_provider(pid: str) -> Provider | None:
    return _PROVIDERS.get(pid)


def provider_ids() -> list[str]:
    return sorted(_PROVIDERS)


def _check_tools(text: str, tools: list[dict] | None) -> bool:
    if not tools:
        return False
    return bool(TOOL_CALL_RE.search(text))


def bootstrap(config: Config, trained_dir: str) -> None:
    """Register the local provider + every configured remote provider."""
    _PROVIDERS.clear()
    register_provider(LocalProvider(trained_dir))
    auth = Auth.load()
    for name, entry in (config.providers or {}).items():
        type_ = entry.get("type", "openai")
        if type_ != "openai":
            continue
        key = entry.get("api_key")
        if not key and entry.get("env_key"):
            key = os.environ.get(entry["env_key"]) or None
        if not key:
            key = auth.get(name)
        register_provider(OpenAIProvider(name, entry.get("base_url", ""), key or None))


def _local_catalog(trained_dir: str) -> dict:
    catalog: dict[str, dict] = {}
    if os.path.isdir(trained_dir):
        for name in sorted(os.listdir(trained_dir)):
            if os.path.isfile(os.path.join(trained_dir, name, "weights.npz")):
                catalog[name] = {"provider": "local", "remote": None,
                                 "kind": "image" if name == "imggen" else "text"}
    return catalog


def model_catalog(config: Config, trained_dir: str) -> dict:
    """model_id -> entry. Config models override discovered local ones."""
    catalog = _local_catalog(trained_dir)
    for mid, entry in (config.models or {}).items():
        catalog[mid] = {"provider": entry.get("provider", "openai"),
                        "remote": entry.get("remote"), "kind": entry.get("kind", "text")}
    return catalog


class UnknownModelError(KeyError):
    pass


def resolve_model(spec: str, config: Config, trained_dir: str) -> ModelRef:
    """Resolve opencode-style 'provider/model' or a bare model id."""
    catalog = model_catalog(config, trained_dir)
    provider_id = None
    model_id = spec
    if "/" in spec:
        provider_id, model_id = spec.split("/", 1)

    entry = catalog.get(model_id)
    if entry is None:
        raise UnknownModelError(f"unknown model '{spec}' — see `kraken models`")
    if provider_id and entry["provider"] != provider_id:
        raise UnknownModelError(f"'{spec}' is provided by '{entry['provider']}', not '{provider_id}'")
    if get_provider(entry["provider"]) is None:
        raise UnknownModelError(f"provider '{entry['provider']}' not configured — see `kraken providers`")
    cfg_entry = (config.models or {}).get(model_id, {})
    return ModelRef(
        provider=entry["provider"], model_id=model_id, remote=entry.get("remote"),
        kind=entry.get("kind", "text"), entry=cfg_entry,
    )