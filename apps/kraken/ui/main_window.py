"""Kraken AI — main desktop window.

ChatGPT/Claude-style layout: creature selector sidebar on left,
streaming chat in center, status bar at bottom.
"""

from __future__ import annotations

import os
import queue
import threading

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QVBoxLayout,
    QWidget,
)

from apps.kraken.core.config import CREATURES, KrakenConfig
from apps.kraken.core.memory import MemoryStore
from apps.kraken.core.models import ModelRegistry
from apps.kraken.ui.chat_panel import ChatPanel
from apps.kraken.ui.creature_selector import CreatureSelector

try:
    from core.theme import COLORS, FONTS, glass_bg, glass_bg_dark, glass_edge
except ImportError:
    COLORS = {
        "abyss_navy": "#081626", "slate_navy": "#0E2238", "deep_navy": "#050D14",
        "seafoam": "#00F2C2", "hd_white": "#EEF4F8",
    }
    FONTS = {"mono": "JetBrains Mono", "ui": "Segoe UI", "size_sm": 11, "size_xs": 10}

    def glass_bg(a=180): return f"rgba(14, 34, 56, {a})"
    def glass_bg_dark(a=140): return f"rgba(5, 13, 20, {a})"
    def glass_edge(a=48): return f"rgba(0, 242, 194, {a})"


class EngineWorker:
    """Runs model inference off the Qt thread."""

    def __init__(self, cfg: KrakenConfig, registry: ModelRegistry):
        self.cfg = cfg
        self.registry = registry
        self.events: queue.Queue = queue.Queue()
        self.running = False
        self._stop = False

    def run(self, creature_id: str, messages: list[dict]):
        self._stop = False
        self.running = True

        def _target():
            try:
                handle = self.registry.get(creature_id)
                self.events.put({"kind": "stream_begin"})
                resp = handle.respond(
                    messages=messages,
                    temperature=self.cfg.get("temperature", 0.7),
                    max_tokens=self.cfg.get("max_tokens", 4096),
                    stream=self._on_chunk if not self._stop else None,
                    workspace=self.cfg.get("workspace", os.getcwd()),
                )
                self.events.put({"kind": "stream_end"})
                self.events.put({"kind": "done", "text": resp.text})
            except Exception as e:
                self.events.put({"kind": "error", "text": str(e)})
            finally:
                self.running = False

        threading.Thread(target=_target, daemon=True, name="kraken-engine").start()

    def stop(self):
        self._stop = True

    def _on_chunk(self, text: str):
        if self._stop:
            return
        if text == "\x00":
            self.events.put({"kind": "stream_end"})
        else:
            self.events.put({"kind": "stream_delta", "text": text})


class KrakenWindow(QMainWindow):
    """Kraken AI desktop app — deep sea creature themed."""

    def __init__(self, cfg: KrakenConfig):
        super().__init__()
        self.cfg = cfg
        self.registry = ModelRegistry(cfg)
        self.memory = MemoryStore(cfg.memory_path, enabled=cfg.get("memory_enabled", True))
        self.worker = EngineWorker(cfg, self.registry)

        self._current_creature = cfg.get("creature", "kraken")
        self._chat_history: list[dict] = []

        self.setWindowTitle("Kraken AI — Deep Sea Intelligence")
        self.resize(1200, 800)
        self.setMinimumSize(800, 600)
        self.setStyleSheet(f"background: {COLORS['abyss_navy']}; color: {COLORS['hd_white']};")

        self._build_ui()
        self._bind_shortcuts()

        # Event polling
        self._poll = QTimer(self)
        self._poll.timeout.connect(self._drain_events)
        self._poll.start(80)

        # Set initial creature
        self._select_creature(self._current_creature, init=True)

    def _build_ui(self):
        root = QWidget()
        self.setCentralWidget(root)
        lay = QHBoxLayout(root)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)

        # Left sidebar — creature selector
        self._selector = CreatureSelector()
        self._selector.creature_selected.connect(self._select_creature)
        lay.addWidget(self._selector)

        # Right — chat area
        right = QWidget()
        right_lay = QVBoxLayout(right)
        right_lay.setContentsMargins(0, 0, 0, 0)
        right_lay.setSpacing(0)

        # Top bar
        self._top_bar = self._build_top_bar()
        right_lay.addWidget(self._top_bar)

        # Chat
        self._chat = ChatPanel()
        self._chat.submitted.connect(self._on_submit)
        self._chat.stop_clicked.connect(self.worker.stop)
        right_lay.addWidget(self._chat, 1)

        lay.addWidget(right, 1)

        # Status bar
        self.statusBar().setStyleSheet(
            f"color: {COLORS.get('text_secondary', '#8BA4B8')}; "
            f"background: {glass_bg_dark(220)}; "
            f"border-top: 1px solid {glass_edge()}; "
            f"font-family: '{FONTS.get('mono', 'monospace')}'; "
            f"font-size: {FONTS.get('size_xs', 10)}px;"
        )
        self._update_status()

    def _build_top_bar(self) -> QWidget:
        bar = QWidget()
        bar.setFixedHeight(52)
        bar.setStyleSheet(f"background: {glass_bg_dark(240)}; border-bottom: 1px solid {glass_edge()};")
        lay = QHBoxLayout(bar)
        lay.setContentsMargins(20, 0, 20, 0)

        self._creature_icon = QLabel()
        self._creature_icon.setFixedSize(32, 32)
        self._creature_icon.setStyleSheet("background: transparent;")
        lay.addWidget(self._creature_icon)

        self._creature_name = QLabel("Kraken")
        self._creature_name.setStyleSheet("color: #00F2C2; font-size: 16px; font-weight: bold; background: transparent;")
        lay.addWidget(self._creature_name)

        self._creature_subtitle = QLabel("Code from the Deep")
        self._creature_subtitle.setStyleSheet("color: #8BA4B8; font-size: 11px; background: transparent;")
        lay.addWidget(self._creature_subtitle)

        lay.addStretch(1)

        # Clear button
        clear_btn = QLabel("Clear")
        clear_btn.setStyleSheet("color: #8BA4B8; font-size: 11px; padding: 4px 8px; background: transparent;")
        clear_btn.setCursor(Qt.PointingHandCursor)
        clear_btn.mousePressEvent = lambda _: self._chat.clear()
        lay.addWidget(clear_btn)

        return bar

    def _select_creature(self, creature_id: str, init: bool = False):
        if not init and creature_id == self._current_creature:
            return

        self._current_creature = creature_id
        meta = CREATURES.get(creature_id, {})
        color = meta.get("color", "#00F2C2")

        self._creature_name.setText(meta.get("name", creature_id))
        self._creature_name.setStyleSheet(f"color: {color}; font-size: 16px; font-weight: bold; background: transparent;")
        self._creature_subtitle.setText(meta.get("subtitle", ""))
        self._chat.set_creature_color(color)
        self._selector.set_active(creature_id)

        if not init:
            self._chat.status_message(f"Switched to {meta.get('name', creature_id)}")
            # Reset chat history for new creature
            self._chat_history = []

        self.cfg.set("creature", creature_id)
        self._update_status()

    def _on_submit(self, text: str):
        if self.worker.running:
            self._chat.error_message("Engine busy — stop the current run first.")
            return

        self._chat.user_message(text)
        self._chat_history.append({"role": "user", "content": text})
        self.memory.remember("user", text, creature=self._current_creature)

        self.worker.run(self._current_creature, list(self._chat_history))

    def _bind_shortcuts(self):
        QShortcut(QKeySequence("Ctrl+L"), self, self._chat.clear)
        QShortcut(QKeySequence("Escape"), self, self.worker.stop)

    def _update_status(self):
        meta = CREATURES.get(self._current_creature, {})
        status = (
            f"{meta.get('name', '?')} · "
            f"provider {self.cfg.get('provider', 'kraken-native')} · "
            f"memory {'ON' if self.cfg.get('memory_enabled') else 'OFF'}"
        )
        self.statusBar().showMessage(status)

    # ── Event drain ──────────────────────────────────────────────

    def _drain_events(self):
        try:
            while True:
                ev = self.worker.events.get_nowait()
                self._handle_event(ev)
        except queue.Empty:
            pass

    def _handle_event(self, ev: dict):
        kind = ev.get("kind", "")
        if kind == "stream_begin":
            self._chat.assistant_begin()
        elif kind == "stream_delta":
            self._chat.assistant_delta(ev.get("text", ""))
        elif kind == "stream_end":
            self._chat.assistant_end()
        elif kind == "error":
            self._chat.assistant_end()
            self._chat.error_message(ev.get("text", "unknown error"))
        elif kind == "done":
            text = ev.get("text", "")
            if text:
                self._chat_history.append({"role": "assistant", "content": text})
                self.memory.remember("assistant", text, creature=self._current_creature)
        self._update_status()
