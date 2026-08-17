"""Leviathan — writing model engine.

Uses the NumPy GPT backend for prose generation with style awareness.
"""

from __future__ import annotations

import os
from collections.abc import Callable

from apps.kraken.core.engine import BaseEngine, EngineResponse


class LeviathanEngine(BaseEngine):
    model_id = "leviathan"

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
            "models", "trained", "leviathan",
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

        system = (
            "You are Leviathan, a writing assistant with deep command of language. "
            "You write clear, engaging prose. Match the tone requested. "
            "Be thorough when depth is needed, terse when brevity is asked for."
        )
        full_messages = [{"role": "system", "content": system}] + list(messages)

        lm = self._get_lm()
        if lm:
            return self._respond_local(lm, full_messages, temperature, max_tokens, stream, t0)

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

        text = (
            "[Leviathan — no trained model loaded]\n\n"
            "To use Leviathan at full capacity, train the model:\n"
            "  python models/lm/train.py --id leviathan --data models/data/leviathan --smoke\n\n"
            f"Your message: {user_msg[:200]}"
        )

        if stream:
            for ch in text:
                stream(ch)
            stream("\x00")
        return EngineResponse(text=text, elapsed=self._done(t0), model_id=self.model_id)
