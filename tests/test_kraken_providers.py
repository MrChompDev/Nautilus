#!/usr/bin/env python3
"""
Kraken AI — provider / key / model-discovery tests (no backend required).

Covers API key resolution (keys.json / ~/.env / env vars), local model
discovery (Ollama manifests, LM Studio, GGUF dirs), the Anthropic + Gemini
wire formats, `kraken setup` backend recommendation, and CLI dispatch for the
`keys`/`setup` subcommands.

Usage:  python3 tests/test_kraken_providers.py
"""

import json
import os
import stat
import sys
import tempfile

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from apps.kraken.cli import _dispatch, build_client  # noqa: E402
from apps.kraken.engine.config import DEFAULT_PROVIDERS, KrakenConfig  # noqa: E402
from apps.kraken.engine.discovery import (  # noqa: E402
    _ollama_disk_models,
    find_local_models,
    list_api_models,
    recommend_backend,
)
from apps.kraken.engine.keys import get_key, load_keys, mask_key, save_keys  # noqa: E402
from apps.kraken.engine.providers import ChatClient  # noqa: E402

PASS = 0


def check(name: str, condition: bool):
    global PASS
    if not condition:
        print(f"[FAIL] {name}")
        raise SystemExit(1)
    PASS += 1
    print(f"[ ok ] {name}")


def _write(path: str, content: str):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)


def test_keys_precedence(tmp):
    keys_file = os.path.join(tmp, "keys.json")
    env_file = os.path.join(tmp, ".env")
    _write(keys_file, json.dumps({"openai": "file-key", "groq": "file-groq"}))
    _write(env_file, "# comment\nANTHROPIC_API_KEY=envfile-claude\nGROQ_API_KEY=envfile-groq\nMISTRAL_API_KEY=envfile-mistral\n")

    keys = load_keys(tmp, env={"OPENAI_API_KEY": "env-key"}, env_file=env_file)
    check("keys.json wins over env", keys["openai"] == "file-key")
    check("env-file key read", keys["anthropic"] == "envfile-claude")
    check("keys.json wins over env-file", keys["groq"] == "file-groq")
    check("env-file wins over process env", load_keys(tmp, env={"MISTRAL_API_KEY": "proc"}, env_file=env_file)["mistral"] == "envfile-mistral")
    check("process env fills empty", load_keys(tmp, env={"MISTRAL_API_KEY": "proc"}, env_file=os.path.join(tmp, "nope.env"))["mistral"] == "proc")
    check("get_key", get_key(tmp, "openai") == "file-key")
    check("get_key missing", get_key(tmp, "deepseek") is None)

    path = save_keys(tmp, {"openai": "abc123", "x": ""})
    check("save writes json", load_keys(tmp, env={}, env_file="")["openai"] == "abc123")
    check("save writes 0600", oct(stat.S_IMODE(os.stat(path).st_mode)) == "0o600")
    check("empty keys filtered", "x" not in load_keys(tmp, env={}, env_file=""))


def test_mask_key():
    check("mask long key", mask_key("sk-test1234567890") == "sk-t…7890")
    check("mask short key", mask_key("abc") == "***")


def test_local_model_discovery(tmp):
    lm_dir = os.path.join(tmp, "lmstudio")
    _write(os.path.join(lm_dir, "mistral", "mistral-7b.Q4_K_M.gguf"), "")
    gguf_dir = os.path.join(tmp, "gguf")
    _write(os.path.join(gguf_dir, "nested", "llama-3.Q8_0.gguf"), "")

    found = find_local_models(gguf_dirs=(gguf_dir,), lmstudio_dirs=(lm_dir,))
    names = {(m["provider"], m["name"]) for m in found}
    check("lmstudio gguf found", ("lmstudio", "mistral-7b.Q4_K_M") in names)
    check("llamacpp gguf found", ("llamacpp", "llama-3.Q8_0") in names)
    check("gguf paths recorded", all(
        m["path"] for m in found if m["provider"] in ("lmstudio", "llamacpp")))

    manifests = os.path.join(tmp, "manifests")
    _write(os.path.join(manifests, "registry.ollama.ai", "library", "qwen2.5-coder", "14b.json"), "{}")
    old = _ollama_disk_models.__globals__["OLLAMA_MANIFESTS"]
    _ollama_disk_models.__globals__["OLLAMA_MANIFESTS"] = manifests
    try:
        disk = _ollama_disk_models()
    finally:
        _ollama_disk_models.__globals__["OLLAMA_MANIFESTS"] = old
    check("offline ollama manifests", any(m["name"] == "qwen2.5-coder:14b" for m in disk))


def test_recommend_backend(tmp):
    from apps.kraken.engine import providers as prov_mod

    lm_dir = os.path.join(tmp, "lmstudio")
    _write(os.path.join(lm_dir, "mistral", "mistral-7b.Q4_K_M.gguf"), "")
    save_keys(tmp, {"openai": "sk-abc"})

    import apps.kraken.engine.discovery as disc
    original = disc.find_local_models

    def fake_local(base_url=""):
        return [{"provider": "lmstudio", "name": "mistral-7b", "path": "", "source": "disk"}]

    disc.find_local_models = fake_local
    try:
        rec = recommend_backend(tmp)
    finally:
        disc.find_local_models = original
    check("local model beats key", rec["provider"] == "lmstudio" and rec["model"] == "mistral-7b")

    disc.find_local_models = lambda base_url="": []
    try:
        rec = recommend_backend(tmp)
    finally:
        disc.find_local_models = original
    check("key fallback", rec["provider"] == "openai" and rec["api_key"] == "sk-abc")
    check("suggested cloud model", rec["model"] == "gpt-4o-mini")


def test_list_api_models():
    check("no key -> empty", list_api_models("openai", "http://x", "") == [])
    check("unknown provider kind openai", list_api_models("deepseek", "http://x", "k") == [])


def test_anthropic_wire_format():
    c = ChatClient(provider="anthropic", model="claude-3-5-haiku-latest", api_key="sk-ant-test123")
    check("anthropic url", c._chat_url() == "https://api.anthropic.com/v1/messages")
    h = c._headers()
    check("anthropic headers", h.get("x-api-key") == "sk-ant-test123" and h.get("anthropic-version") == "2023-06-01")
    p = c._payload([{"role": "system", "content": "Be brief."}, {"role": "user", "content": "hi"}])
    check("anthropic system split", p["system"] == "Be brief.")
    check("anthropic max_tokens", p["max_tokens"] == 4096)
    check("anthropic chat only", p["messages"] == [{"role": "user", "content": "hi"}])
    check("anthropic sse delta", ChatClient._parse_chunk(
        '{"type":"content_block_delta","delta":{"type":"text_delta","text":"Hello"}}') == "Hello")
    check("anthropic sse ignore", ChatClient._parse_chunk('{"type":"message_stop"}') == "")
    check("anthropic non-stream", ChatClient._parse_single(
        '{"content":[{"type":"text","text":"A"},{"type":"text","text":"B"}]}') == "AB")


def test_openai_and_gemini_wire_format():
    o = ChatClient(provider="openai", model="gpt-4o-mini", api_key="sk-abc")
    check("openai url", o._chat_url() == "https://api.openai.com/v1/chat/completions")
    check("openai auth header", o._headers()["Authorization"] == "Bearer sk-abc")
    msg = [{"role": "system", "content": "s"}, {"role": "user", "content": "u"}]
    check("openai payload keeps system", o._payload(msg)["messages"] == msg)
    check("openai sse", ChatClient._parse_chunk(
        '{"choices":[{"delta":{"content":"X"}}]}') == "X")

    g = ChatClient(provider="gemini", model="gemini-2.5-flash", api_key="AIza-test")
    check("gemini openai-compat kind", g.kind == "openai")
    check("gemini base url", "generativelanguage" in g.base_url and "/openai" in g.base_url)

    om = ChatClient(provider="ollama", model="qwen2.5-coder:7b")
    check("ollama native url", om._chat_url() == "http://localhost:11434/api/chat")
    check("ollama native payload", om._payload(msg).get("options", {}).get("num_ctx") == 8192)

    check("provider presets exist", all(p in DEFAULT_PROVIDERS for p in
        ("openai", "anthropic", "gemini", "groq", "openrouter", "mistral", "deepseek", "together")))


def test_build_client_key_resolution(tmp):
    save_keys(tmp, {"openai": "file-key"})
    cfg = KrakenConfig.load(tmp)
    cfg.update(provider="openai", base_url=DEFAULT_PROVIDERS["openai"]["base_url"])
    client = build_client(cfg)
    check("build_client uses keys store", client.api_key == "file-key")

    cfg.update(api_key="cfg-key")
    check("cfg api_key wins", build_client(cfg).api_key == "cfg-key")


def test_stream_ndjson_and_no_deadlock():
    import io
    import urllib.request
    import apps.kraken.engine.providers as prov_mod

    raw_lines = [
        b'{"model":"m","message":{"content":"Hel"}}\n',
        b'{"model":"m","message":{"content":"lo!"}}\n',
        b'{"model":"m","done":true}\n',
    ]

    class FakeResp:
        def __init__(self):
            self.headers = {"Content-Type": "application/x-ndjson"}

        def __enter__(self):
            return self

        def __exit__(self, *exc):
            return False

        def __iter__(self):
            return iter(raw_lines)

    class FakeRespJson:
        def __init__(self):
            self.headers = {"Content-Type": "application/json"}

        def __enter__(self):
            return self

        def __exit__(self, *exc):
            return False

        def read(self):
            return b'{"model":"m","message":{"content":"single"}}'

    calls = []
    mode = {"value": "ndjson"}
    orig = prov_mod.urllib.request.urlopen

    def fake_urlopen(req, timeout=None):
        calls.append(req)
        return FakeRespJson() if mode["value"] == "single" else FakeResp()

    prov_mod.urllib.request.urlopen = fake_urlopen
    try:
        c = ChatClient(provider="ollama", model="m")
        streamed = "".join(c.stream([{"role": "user", "content": "hi"}]))
        check("ndjson lines parsed without data: prefix", streamed == "Hello!")
        check("stats streams counted", c.stats["streams"] == 1)
        check("stats tokens counted", c.stats["tokens"] > 0)

        mode["value"] = "single"
        once = c.chat([{"role": "user", "content": "hi"}])
        check("single json path", once == "single")
        check("reentrant lock survives stream loop", calls[0].data is not None)
    finally:
        prov_mod.urllib.request.urlopen = orig


def test_dispatch():
    check("keys list routes", _dispatch(["keys"]) == ("keys", []))
    check("keys add routes", _dispatch(["keys", "add", "openai", "sk-x"]) == ("keys", ["add", "openai", "sk-x"]))
    check("keys remove routes", _dispatch(["keys", "rm", "openai"]) == ("keys", ["rm", "openai"]))
    check("setup routes", _dispatch(["setup"]) == ("setup", []))
    check("keys as task stays task", _dispatch(["keys", "in", "the", "safe"]) == (None, ["keys", "in", "the", "safe"]))
    check("setup as task stays task", _dispatch(["setup", "a", "tent"]) == (None, ["setup", "a", "tent"]))
    check("models routes", _dispatch(["models"]) == ("models", []))


def main():
    tmp = tempfile.mkdtemp(prefix="kraken-providers-")
    test_keys_precedence(tmp)
    test_mask_key()
    test_local_model_discovery(tmp)
    test_recommend_backend(tmp)
    test_list_api_models()
    test_anthropic_wire_format()
    test_openai_and_gemini_wire_format()
    test_build_client_key_resolution(tmp)
    test_stream_ndjson_and_no_deadlock()
    test_dispatch()
    print(f"\n{PASS} checks passed.")


if __name__ == "__main__":
    main()
