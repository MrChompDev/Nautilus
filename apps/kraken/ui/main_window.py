"""Kraken AI — main desktop window.

Clean layout: top bar + full-width chat with model dropdown in input bar.
No sidebar — model selection is a dropdown next to the send button.
"""

from __future__ import annotations

import json
import os
import queue
import threading
import time

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QSlider,
    QVBoxLayout,
    QWidget,
)

from apps.kraken.core.config import CREATURES, KrakenConfig
from apps.kraken.core.memory import MemoryStore
from apps.kraken.core.models import ModelRegistry
from apps.kraken.ui.chat_panel import ChatPanel

try:
    from core.theme import COLORS, FONTS, glass_bg, glass_bg_dark, glass_edge
except ImportError:
    COLORS = {
        "abyss_navy": "#081626", "slate_navy": "#0E2238", "deep_navy": "#050D14",
        "void_black": "#02060A", "seafoam": "#00F2C2", "seafoam_deep": "#004D40",
        "coral": "#FF7F50", "amber": "#FFA502", "emerald": "#00C853",
        "hd_white": "#EEF4F8", "text_secondary": "#8BA4B8", "text_muted": "#506070",
        "border": "#152D44", "surface_selected": "#1A3352",
    }
    FONTS = {"mono": "JetBrains Mono", "ui": "Segoe UI", "size_sm": 11, "size_xs": 10, "size_md": 12}

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
    """Kraken AI desktop app — model dropdown in input bar, no sidebar."""

    def __init__(self, cfg: KrakenConfig):
        super().__init__()
        self.cfg = cfg
        self.registry = ModelRegistry(cfg)
        self.memory = MemoryStore(cfg.memory_path, enabled=cfg.get("memory_enabled", True))
        self.worker = EngineWorker(cfg, self.registry)

        self._current_creature = cfg.get("creature", "kraken")
        self._chat_history: list[dict] = []
        self._conversations: list[dict] = []
        self._conv_index = -1

        self.setWindowTitle("Kraken AI")
        self.resize(1100, 780)
        self.setMinimumSize(700, 500)
        self.setStyleSheet(f"background: {COLORS['abyss_navy']}; color: {COLORS['hd_white']};")

        self._build_ui()
        self._bind_shortcuts()

        self._poll = QTimer(self)
        self._poll.timeout.connect(self._drain_events)
        self._poll.start(80)

        self._status_timer = QTimer(self)
        self._status_timer.timeout.connect(self._update_status)
        self._status_timer.start(2000)

        self._select_creature(self._current_creature, init=True)

    def _build_ui(self):
        root = QWidget()
        self.setCentralWidget(root)
        lay = QVBoxLayout(root)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)

        # Top bar
        self._top_bar = self._build_top_bar()
        lay.addWidget(self._top_bar)

        # Chat panel (includes input bar with model dropdown)
        self._chat = ChatPanel(creatures=CREATURES, creature_id=self._current_creature)
        self._chat.submitted.connect(self._on_submit)
        self._chat.stop_clicked.connect(self.worker.stop)
        self._chat.creature_changed.connect(self._select_creature)
        lay.addWidget(self._chat, 1)

        # Status bar
        self.statusBar().setStyleSheet(
            f"color: {COLORS.get('text_secondary', '#8BA4B8')}; "
            f"background: {glass_bg_dark(220)}; "
            f"border-top: 1px solid {glass_edge()}; "
            f"font-family: '{FONTS.get('mono', 'monospace')}'; "
            f"font-size: {FONTS.get('size_xs', 10)}px; "
            f"padding: 2px 8px;"
        )
        self._update_status()

    def _build_top_bar(self) -> QWidget:
        bar = QWidget()
        bar.setFixedHeight(54)
        bar.setStyleSheet(f"background: {glass_bg_dark(240)}; border-bottom: 1px solid {glass_edge()};")
        lay = QHBoxLayout(bar)
        lay.setContentsMargins(20, 0, 20, 0)

        # Creature icon circle
        self._icon_frame = QLabel()
        self._icon_frame.setFixedSize(36, 36)
        self._icon_frame.setAlignment(Qt.AlignCenter)
        self._update_icon()
        lay.addWidget(self._icon_frame)

        # Name + subtitle
        text_col = QVBoxLayout()
        text_col.setSpacing(0)
        text_col.setContentsMargins(0, 0, 0, 0)
        self._creature_name = QLabel("Kraken")
        self._creature_name.setStyleSheet(
            f"color: {COLORS['seafoam']}; font-size: 16px; font-weight: bold; "
            f"background: transparent; border: none;"
        )
        text_col.addWidget(self._creature_name)
        self._creature_subtitle = QLabel("Code from the Deep")
        self._creature_subtitle.setStyleSheet(
            f"color: {COLORS['text_secondary']}; font-size: 10px; "
            f"background: transparent; border: none;"
        )
        text_col.addWidget(self._creature_subtitle)
        lay.addLayout(text_col)

        lay.addStretch(1)

        # Shortcut hints
        hints = QLabel("Ctrl+L Clear  |  Esc Stop  |  Ctrl+N New  |  Ctrl+E Export")
        hints.setStyleSheet(
            f"color: {COLORS['text_muted']}; font-size: 9px; "
            f"background: transparent; border: none;"
        )
        lay.addWidget(hints)

        lay.addSpacing(12)

        # Settings button
        settings_btn = QPushButton("\u2699")
        settings_btn.setToolTip("Settings")
        settings_btn.setFixedSize(32, 32)
        settings_btn.setCursor(Qt.PointingHandCursor)
        settings_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent; color: {COLORS['text_secondary']};
                border: 1px solid transparent; border-radius: 6px; font-size: 14px;
            }}
            QPushButton:hover {{
                background: {glass_bg(100)}; border: 1px solid {glass_edge(40)};
                color: {COLORS['hd_white']};
            }}
        """)
        settings_btn.clicked.connect(self._open_settings)
        lay.addWidget(settings_btn)

        return bar

    def _update_icon(self):
        color = CREATURES.get(self._current_creature, {}).get("color", "#00F2C2")
        letter = CREATURES.get(self._current_creature, {}).get("name", "?")[0]
        self._icon_frame.setText(letter)
        self._icon_frame.setStyleSheet(f"""
            QLabel {{
                background: {color}22; border: 1.5px solid {color}66;
                border-radius: 18px; color: {color}; font-size: 16px; font-weight: bold;
            }}
        """)

    def _select_creature(self, creature_id: str, init: bool = False):
        if not init and creature_id == self._current_creature:
            return

        self._current_creature = creature_id
        meta = CREATURES.get(creature_id, {})
        color = meta.get("color", "#00F2C2")

        self._creature_name.setText(meta.get("name", creature_id))
        self._creature_name.setStyleSheet(
            f"color: {color}; font-size: 16px; font-weight: bold; "
            f"background: transparent; border: none;"
        )
        self._creature_subtitle.setText(meta.get("subtitle", ""))
        self._chat.set_creature_color(color)
        self._update_icon()

        if not init:
            self._chat.status_message(
                f"Switched to {meta.get('name', creature_id)} \u2014 "
                f"{meta.get('description', '')[:80]}"
            )

        self.cfg.set("creature", creature_id)
        self._update_status()

    def _on_submit(self, text: str):
        if self.worker.running:
            self._chat.error_message("Engine busy \u2014 stop the current run first.")
            return

        self._chat.user_message(text)
        self._chat_history.append({"role": "user", "content": text})
        self.memory.remember("user", text, creature=self._current_creature)

        self.worker.run(self._current_creature, list(self._chat_history))

    def _bind_shortcuts(self):
        QShortcut(QKeySequence("Ctrl+L"), self, self._chat.clear)
        QShortcut(QKeySequence("Escape"), self, self.worker.stop)
        QShortcut(QKeySequence("Ctrl+N"), self, self._new_conversation)
        QShortcut(QKeySequence("Ctrl+E"), self, self._export_chat)
        QShortcut(QKeySequence("Ctrl+,"), self, self._open_settings)
        QShortcut(QKeySequence("Ctrl+1"), self, lambda: self._select_creature("kraken"))
        QShortcut(QKeySequence("Ctrl+2"), self, lambda: self._select_creature("leviathan"))
        QShortcut(QKeySequence("Ctrl+3"), self, lambda: self._select_creature("charybdis"))
        QShortcut(QKeySequence("Ctrl+4"), self, lambda: self._select_creature("megalodon"))

    def _new_conversation(self):
        if self._chat_history:
            self._conversations.append({
                "name": self._chat_history[0]["content"][:40] if self._chat_history else "New Chat",
                "creature": self._current_creature,
                "messages": list(self._chat_history),
                "ts": time.time(),
            })
        self._chat_history = []
        self._chat.clear()
        meta = CREATURES.get(self._current_creature, {})
        self._chat.status_message(f"New conversation with {meta.get('name', self._current_creature)}")

    def _export_chat(self):
        if not self._chat_history:
            self._chat.status_message("Nothing to export yet.")
            return

        path, _ = QFileDialog.getSaveFileName(
            self, "Export Chat", f"kraken_{self._current_creature}_{int(time.time())}.md",
            "Markdown (*.md);;JSON (*.json);;Text (*.txt)"
        )
        if not path:
            return

        meta = CREATURES.get(self._current_creature, {})
        if path.endswith(".json"):
            with open(path, "w", encoding="utf-8") as f:
                json.dump({
                    "creature": self._current_creature,
                    "creature_name": meta.get("name", ""),
                    "messages": self._chat_history,
                    "exported": time.strftime("%Y-%m-%d %H:%M:%S"),
                }, f, indent=2)
        else:
            with open(path, "w", encoding="utf-8") as f:
                f.write(f"# Kraken AI \u2014 {meta.get('name', self._current_creature)} Chat\n\n")
                f.write(f"Exported: {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n---\n\n")
                for msg in self._chat_history:
                    role = "You" if msg["role"] == "user" else meta.get("name", "Kraken")
                    f.write(f"### {role}\n\n{msg['content']}\n\n---\n\n")

        self._chat.status_message(f"Chat exported to {os.path.basename(path)}")

    def _open_settings(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Settings")
        dialog.resize(440, 400)
        dialog.setStyleSheet(f"""
            QDialog {{ background: {COLORS['deep_navy']}; color: {COLORS['hd_white']};
                       border: 1px solid {glass_edge()}; border-radius: 12px; }}
        """)

        lay = QVBoxLayout(dialog)
        lay.setContentsMargins(20, 20, 20, 20)
        lay.setSpacing(12)

        title = QLabel("Settings")
        title.setStyleSheet(
            f"color: {COLORS['seafoam']}; font-size: 18px; font-weight: bold; "
            f"background: transparent; border: none;"
        )
        lay.addWidget(title)

        # Temperature
        temp_label = QLabel(f"Temperature: {self.cfg.get('temperature', 0.7):.1f}")
        temp_label.setStyleSheet(f"color: {COLORS['hd_white']}; font-size: 12px; background: transparent; border: none;")
        lay.addWidget(temp_label)
        temp_slider = QSlider(Qt.Horizontal)
        temp_slider.setRange(0, 100)
        temp_slider.setValue(int(self.cfg.get("temperature", 0.7) * 100))
        temp_slider.setStyleSheet(
            f"QSlider::groove:horizontal {{ background: {COLORS['border']}; height: 4px; border-radius: 2px; }} "
            f"QSlider::handle:horizontal {{ background: {COLORS['seafoam']}; width: 14px; margin: -5px 0; border-radius: 7px; }}"
        )
        def _on_temp(val):
            v = val / 100.0
            self.cfg.set("temperature", v)
            temp_label.setText(f"Temperature: {v:.1f}")
        temp_slider.valueChanged.connect(_on_temp)
        lay.addWidget(temp_slider)

        # Max tokens
        tokens_label = QLabel(f"Max tokens: {self.cfg.get('max_tokens', 4096)}")
        tokens_label.setStyleSheet(f"color: {COLORS['hd_white']}; font-size: 12px; background: transparent; border: none;")
        lay.addWidget(tokens_label)
        tokens_slider = QSlider(Qt.Horizontal)
        tokens_slider.setRange(256, 8192)
        tokens_slider.setSingleStep(256)
        tokens_slider.setValue(self.cfg.get("max_tokens", 4096))
        tokens_slider.setStyleSheet(temp_slider.styleSheet())
        def _on_tokens(val):
            self.cfg.set("max_tokens", val)
            tokens_label.setText(f"Max tokens: {val}")
        tokens_slider.valueChanged.connect(_on_tokens)
        lay.addWidget(tokens_slider)

        # Memory toggle
        mem_btn = QPushButton(f"Memory: {'ON' if self.cfg.get('memory_enabled', True) else 'OFF'}")
        mem_btn.setCursor(Qt.PointingHandCursor)
        mem_btn.setStyleSheet(
            f"QPushButton {{ background: {glass_bg(140)}; color: {COLORS['seafoam']}; border: 1px solid {glass_edge(60)}; border-radius: 6px; padding: 6px 12px; font-size: 11px; }} "
            f"QPushButton:hover {{ background: {glass_bg(180)}; }}"
        )
        def _toggle_mem():
            current = self.cfg.get("memory_enabled", True)
            self.cfg.set("memory_enabled", not current)
            mem_btn.setText(f"Memory: {'ON' if not current else 'OFF'}")
        mem_btn.clicked.connect(_toggle_mem)
        lay.addWidget(mem_btn)

        # Clear memory
        clear_mem_btn = QPushButton("Clear Memory")
        clear_mem_btn.setCursor(Qt.PointingHandCursor)
        clear_mem_btn.setStyleSheet(
            f"QPushButton {{ background: {COLORS['coral']}22; color: {COLORS['coral']}; border: 1px solid {COLORS['coral']}44; border-radius: 6px; padding: 6px 12px; font-size: 11px; }} "
            f"QPushButton:hover {{ background: {COLORS['coral']}44; }}"
        )
        def _clear_mem():
            self.memory.clear()
            self._chat.status_message("Memory cleared.")
        clear_mem_btn.clicked.connect(_clear_mem)
        lay.addWidget(clear_mem_btn)

        lay.addStretch(1)

        close_btn = QPushButton("Close")
        close_btn.setCursor(Qt.PointingHandCursor)
        close_btn.setStyleSheet(
            f"QPushButton {{ background: {COLORS['seafoam']}; color: {COLORS['deep_navy']}; border: none; border-radius: 6px; padding: 8px; font-size: 12px; font-weight: bold; }} "
            f"QPushButton:hover {{ background: {COLORS['seafoam']}cc; }}"
        )
        close_btn.clicked.connect(dialog.close)
        lay.addWidget(close_btn)

        dialog.exec()

    def _update_status(self):
        meta = CREATURES.get(self._current_creature, {})
        status = (
            f"{meta.get('name', '?')} \u00b7 "
            f"{self.cfg.get('provider', 'kraken-native')} \u00b7 "
            f"temp {self.cfg.get('temperature', 0.7):.1f} \u00b7 "
            f"{'ON' if self.cfg.get('memory_enabled') else 'OFF'} memory"
        )
        self.statusBar().showMessage(status)

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
