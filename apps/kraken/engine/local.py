"""
Kraken AI — local custom model runtime.

Loads the sea-creature named models (kraken / leviathan / megalodon / charybdis)
and serves them through the same streaming ChatClient interface as every other
provider, so the GUI, CLI, and agents treat them uniformly.  No network, no API
keys.
"""

import os
import threading

_TRAINED_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))),
    "models",
    "trained",
)

_LOCK = threading.RLock()
_CACHE: dict[str, object] = {}


def trained_dir() -> str:
    return _TRAINED_DIR


def list_local_models() -> list[dict]:
    out = []
    if not os.path.isdir(_TRAINED_DIR):
        return out
    for name in sorted(os.listdir(_TRAINED_DIR)):
        path = os.path.join(_TRAINED_DIR, name)
        if os.path.isfile(os.path.join(path, "weights.npz")):
            size = sum(
                os.path.getsize(os.path.join(path, f)) for f in os.listdir(path)
            ) // (1024 * 1024)
            out.append({"id": name, "path": path, "size_mb": size})
    return out


def is_available(model_id: str) -> bool:
    return os.path.isfile(os.path.join(_TRAINED_DIR, model_id, "weights.npz"))


def load_lm(model_id: str):
    """Load (and cache) a local model by id."""
    with _LOCK:
        if model_id in _CACHE:
            return _CACHE[model_id]
        path = os.path.join(_TRAINED_DIR, model_id)
        if not os.path.isfile(os.path.join(path, "weights.npz")):
            raise FileNotFoundError(f"local model {model_id!r} not trained (see models/lm/train.py)")
        from apps.kraken.core.lm_loader import load_lm as _load_lm
        lm = _load_lm(path)
        _CACHE[model_id] = lm
        return lm


def format_messages(messages: list[dict]) -> str:
    """Render a chat history in the Nautilus `### role` prompt format."""
    parts = []
    for m in messages:
        role = m.get("role", "user")
        content = (m.get("content") or "").strip()
        if not content:
            continue
        if role == "system":
            parts.append(f"### system\n{content}")
        elif role == "assistant":
            parts.append(f"### assistant\n{content}")
        else:
            parts.append(f"### user\n{content}")
    parts.append("### assistant\n")
    return "\n\n".join(parts)


def brain_context(query: str, workspace: str | None = None, max_chars: int = 1400) -> str:
    """Compact project-brain context for the coding model's system prompt.

    Uses the persisted SQLite index (built once by `brain scan`) so the model
    answers questions about the project without re-reading the file tree.
    """
    try:
        from apps.kraken.engine.brain import ProjectBrain
    except Exception:
        return ""
    if not workspace:
        try:
            from apps.kraken.engine.config import KrakenConfig

            workspace = KrakenConfig.load().workspace
        except Exception:
            return ""
    if not os.path.isdir(workspace):
        return ""
    brain = ProjectBrain(workspace)
    if not os.path.exists(brain.db_path):
        try:
            brain.scan()
        except Exception:
            return ""
    try:
        relevant = brain.context(query, k=5)
        tree = brain.file_map()
    except Exception:
        return ""
    lines = tree.splitlines()[:90]
    tree = "\n".join(lines)
    body = f"# Project files (workspace: {workspace})\n{tree}\n\n# Relevant to this question\n{relevant}"
    return body[:max_chars]


def with_brain_system(messages: list[dict], workspace: str | None = None) -> list[dict]:
    """Prepend a brain system message for coding-model chats."""
    query = ""
    for m in reversed(messages):
        if m.get("role") == "user":
            query = (m.get("content") or "")[:400]
            break
    ctx = brain_context(query, workspace)
    if not ctx:
        return messages
    return [{"role": "system", "content": ctx}] + list(messages)


def local_stream(
    model_id: str,
    messages: list[dict],
    temperature: float = 0.6,
    max_new_tokens: int = 256,
    top_k: int = 40,
    on_chunk=None,
    workspace: str | None = None,
):
    """Generate a response from a local model, yielding text deltas."""
    lm = load_lm(model_id)
    if model_id == "kraken" and workspace is not None:
        messages = with_brain_system(messages, workspace)
    prompt = format_messages(messages)

    def sink(tok: int):
        text = lm.decode([tok])
        if on_chunk:
            on_chunk(text)

    out_ids = lm.model.generate(
        lm.encode(prompt),
        max_new_tokens=max_new_tokens,
        temperature=temperature,
        top_k=top_k,
        stop=None,
        stream=sink,
    )
    text = lm.decode(out_ids)
    # Trim a trailing "### " the model may start emitting for the next turn.
    for marker in ("\n### ", "### "):
        if marker in text:
            text = text.split(marker, 1)[0]
    if on_chunk:
        on_chunk("\x00")  # sentinel: done
    yield text
