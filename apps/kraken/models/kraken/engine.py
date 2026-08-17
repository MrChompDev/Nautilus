"""Kraken — coding model engine.

Uses the NumPy GPT backend for code generation with project-brain context.
Also provides file/terminal tools for autonomous coding tasks.
"""

from __future__ import annotations

import os
from collections.abc import Callable

from apps.kraken.core.engine import BaseEngine, EngineResponse
from apps.kraken.core.tools import execute_tool


def _brain_context(query: str, workspace: str | None, max_chars: int = 2000) -> str:
    """Compact project-brain context for the coding system prompt."""
    try:
        from apps.kraken.engine.brain import ProjectBrain
    except Exception:
        return ""
    if not workspace:
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
    lines = tree.splitlines()[:100]
    tree_str = "\n".join(lines)
    body = f"# Project files ({workspace})\n{tree_str}\n\n# Relevant\n{relevant}"
    return body[:max_chars]


class KrakenEngine(BaseEngine):
    model_id = "kraken"

    def __init__(self, cfg):
        self.cfg = cfg
        self._lm = None

    def _get_lm(self):
        if self._lm is not None:
            return self._lm
        trained = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(
                os.path.dirname(os.path.abspath(__file__))
            )))),
            "models", "trained", "kraken",
        )
        if os.path.isfile(os.path.join(trained, "weights.npz")):
            from models.lm.engine import LM
            self._lm = LM(trained)
            return self._lm
        return None

    def respond(
        self,
        messages: list[dict],
        temperature: float = 0.7,
        max_tokens: int = 4096,
        stream: Callable[[str], None] | None = None,
        workspace: str | None = None,
    ) -> EngineResponse:
        t0 = self._tick()

        # Build system prompt with brain context
        query = ""
        for m in reversed(messages):
            if m.get("role") == "user":
                query = (m.get("content") or "")[:400]
                break
        brain = _brain_context(query, workspace)
        system = "You are Kraken, a coding assistant. You write precise, working code."
        if brain:
            system += f"\n\n{brain}"

        full_messages = [{"role": "system", "content": system}] + list(messages)

        # Try local GPT
        lm = self._get_lm()
        if lm:
            return self._respond_local(lm, full_messages, temperature, max_tokens, stream, t0)

        # Fallback: tool-augmented echo (for when no trained model exists)
        return self._respond_fallback(messages, stream, t0)

    def _respond_local(self, lm, messages, temperature, max_tokens, stream, t0):
        prompt_parts = []
        for m in messages:
            role = m.get("role", "user")
            content = (m.get("content") or "").strip()
            if role == "system":
                prompt_parts.append(f"### system\n{content}")
            elif role == "assistant":
                prompt_parts.append(f"### assistant\n{content}")
            else:
                prompt_parts.append(f"### user\n{content}")
        prompt_parts.append("### assistant\n")
        prompt = "\n\n".join(prompt_parts)

        out_ids = lm.model.generate(
            lm.encode(prompt),
            max_new_tokens=min(max_tokens, 2048),
            temperature=temperature,
            top_k=40,
            stream=lambda tok: stream(lm.decode([tok])) if stream else None,
        )
        text = lm.decode(out_ids)
        for marker in ("\n### ", "### "):
            if marker in text:
                text = text.split(marker, 1)[0]
        if stream:
            stream("\x00")
        return EngineResponse(text=text, tokens=len(out_ids), elapsed=self._done(t0), model_id=self.model_id)

    def _respond_fallback(self, messages, stream, t0):
        user_msg = ""
        for m in reversed(messages):
            if m.get("role") == "user":
                user_msg = m.get("content", "")
                break

        # Tool-augmented responses for common coding tasks
        if user_msg.lower().startswith(("list files", "show files", "ls")):
            workspace = self.cfg.workspace if hasattr(self.cfg, "workspace") else os.getcwd()
            result = execute_tool("file_list", {"path": workspace})
            text = result.output if result.ok else f"Error: {result.error}"
        elif user_msg.lower().startswith(("read ", "cat ")):
            path = user_msg.split(None, 1)[1].strip().strip('"').strip("'")
            result = execute_tool("file_read", {"path": path})
            text = result.output if result.ok else f"Error: {result.error}"
        else:
            text = (
                "[Kraken — no trained model loaded]\n\n"
                "To use Kraken at full capacity, train the model:\n"
                "  python models/lm/train.py --id kraken --data models/data/kraken --smoke\n\n"
                f"Your message: {user_msg[:200]}"
            )

        if stream:
            for ch in text:
                stream(ch)
            stream("\x00")
        return EngineResponse(text=text, elapsed=self._done(t0), model_id=self.model_id)
