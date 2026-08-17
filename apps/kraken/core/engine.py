"""Kraken AI — shared base engine interface.

Every sea-creature model implements this interface so the UI and agent
loop can treat them uniformly.
"""

from __future__ import annotations

import time
from collections.abc import Callable


class EngineResponse:
    """Standard response from any model engine."""

    __slots__ = ("text", "tokens", "elapsed", "model_id")

    def __init__(self, text: str, tokens: int = 0, elapsed: float = 0.0, model_id: str = ""):
        self.text = text
        self.tokens = tokens
        self.elapsed = elapsed
        self.model_id = model_id

    @property
    def tok_per_sec(self) -> float:
        return self.tokens / self.elapsed if self.elapsed > 0 else 0.0

    def __repr__(self):
        return f"EngineResponse({self.model_id!r}, {self.tokens} tok, {self.elapsed:.2f}s)"


class BaseEngine:
    """Abstract base for all sea-creature engines.

    Subclasses must implement respond().
    """

    model_id: str = ""

    def respond(
        self,
        messages: list[dict],
        temperature: float = 0.7,
        max_tokens: int = 4096,
        stream: Callable[[str], None] | None = None,
        workspace: str | None = None,
    ) -> EngineResponse:
        raise NotImplementedError

    def _tick(self) -> float:
        return time.time()

    def _done(self, start: float) -> float:
        return time.time() - start
