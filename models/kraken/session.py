"""Kraken — conversation session. Keeps multi-turn context within block limits."""

from __future__ import annotations

import os
import time


class Session:
    """Bounded conversation context using the `### system/user/assistant` format."""

    def __init__(self, system_prompt: str | None = None, max_tokens: int = 800):
        self.system = system_prompt or (
            "You are Kraken, a local-first AI assistant. Answer clearly and directly."
        )
        self.max_tokens = max_tokens
        self.turns: list[tuple[str, str]] = []
        self.started = time.time()

    def add(self, role: str, text: str):
        self.turns.append((role, text))
        self._trim()

    def _trim(self):
        # drop oldest turns until we fit the budget (rough char-based estimate)
        budget = self.max_tokens * 4
        used = sum(len(t) for _, t in self.turns) + len(self.system)
        while self.turns and used > budget:
            removed = self.turns.pop(0)
            used -= len(removed[1])

    def to_prompt(self, user_text: str) -> str:
        parts = [f"### system\n{self.system}"]
        for role, text in self.turns:
            parts.append(f"### {role}\n{text}")
        parts.append(f"### user\n{user_text}")
        return "\n\n".join(parts)

    def to_messages(self):
        """Conversation as provider ChatMsg list (system first, then turns)."""
        from models.kraken.providers import ChatMsg, System

        msgs = [ChatMsg(role=System, content=self.system)]
        for role, text in self.turns:
            msgs.append(ChatMsg(role=role, content=text))
        return msgs

    def append_turns(self, msgs) -> None:
        """Append assistant/tool messages produced during a turn."""
        for m in msgs:
            if m.role in ("user", "assistant", "tool") and m.content:
                self.turns.append((m.role, m.content))
        self._trim()

    def reset(self):
        self.turns.clear()
        self.started = time.time()

    def export(self) -> str:
        lines = [f"# Kraken session — {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(self.started))}"]
        for role, text in self.turns:
            lines.append(f"### {role}\n{text}")
        return "\n\n".join(lines)

    def save(self, path: str):
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(self.export())

    @property
    def turn_count(self) -> int:
        return len(self.turns)