"""Kraken AI — model registry.

Routes each sea-creature model to its engine.
All engines share the same .respond(prompt, stream=) interface.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from apps.kraken.core.config import KrakenConfig


class ModelHandle:
    """Lightweight handle returned by the registry."""

    def __init__(self, creature_id: str, engine: object, meta: dict):
        self.id = creature_id
        self.engine = engine
        self.meta = meta

    @property
    def name(self) -> str:
        return self.meta.get("name", self.id)

    @property
    def color(self) -> str:
        return self.meta.get("color", "#00F2C2")

    def respond(
        self,
        messages: list[dict],
        temperature: float = 0.7,
        max_tokens: int = 4096,
        stream: Callable[[str], None] | None = None,
        workspace: str | None = None,
    ) -> dict:
        return self.engine.respond(
            messages,
            temperature=temperature,
            max_tokens=max_tokens,
            stream=stream,
            workspace=workspace,
        )


class ModelRegistry:
    """Lazy-loading registry that maps creature IDs to engines."""

    def __init__(self, cfg: KrakenConfig):
        self.cfg = cfg
        self._engines: dict[str, ModelHandle] = {}

    def get(self, creature_id: str) -> ModelHandle:
        if creature_id in self._engines:
            return self._engines[creature_id]
        engine = self._build(creature_id)
        from apps.kraken.core.config import CREATURES
        handle = ModelHandle(creature_id, engine, CREATURES.get(creature_id, {}))
        self._engines[creature_id] = handle
        return handle

    def _build(self, creature_id: str):
        if creature_id == "kraken":
            from apps.kraken.models.kraken.engine import KrakenEngine
            return KrakenEngine(self.cfg)
        if creature_id == "leviathan":
            from apps.kraken.models.leviathan.engine import LeviathanEngine
            return LeviathanEngine(self.cfg)
        if creature_id == "charybdis":
            from apps.kraken.models.charybdis.engine import CharybdisEngine
            return CharybdisEngine(self.cfg)
        if creature_id == "megalodon":
            from apps.kraken.models.megalodon.engine import MegalodonEngine
            return MegalodonEngine(self.cfg)
        raise ValueError(f"unknown creature: {creature_id}")

    def all_creatures(self) -> list[dict]:
        from apps.kraken.core.config import CREATURES
        return [{"id": k, **v} for k, v in CREATURES.items()]
