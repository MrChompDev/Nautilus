"""Kraken AI — main desktop window.

ChatGPT/Claude-style layout with deep sea creature theming.
Features: creature selector, conversation history, settings, export.
"""

from __future__ import annotations

import json
import os
import queue
import threading
import time

from PySide6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import QKeySequence, QShortcut, QAction, QIcon
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QDialog,
    QFileDialog,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSlider,
    QSplitter,
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
    """Kraken AI desktop app — deep sea creature themed."""

    def __init__(self, cfg: KrakenConfig):
        super().__init__()
        self.cfg = cfg
        self.registry = ModelRegistry(cfg)
        self.memory = MemoryStore(cfg.memory_path, enabled=cfg.get("memory_enabled", True))
        self.worker = EngineWorker(cfg, self.registry)

        self._current_creature = cfg.get("creature", "kraken")
        self._chat_history: list[dict] = []
        self._conversations: list[dict] = []  # {name, creature, messages, ts}
        self._conv_index = -1

        self.setWindowTitle("Kraken AI")
        self.resize(1280, 820)
        self.setMinimumSize(900, 600)
        self.setStyleSheet(f"background: {COLORS['abyss_navy']}; color: {COLORS['hd_white']};")

        self._build_ui()
        self._bind_shortcuts()

        # Event polling
        self._poll = QTimer(self)
        self._poll.timeout.connect(self._drain_events)
        self._poll.start(80)

        # Status timer
        self._status_timer = QTimer(self)
        self._status_timer.timeout.connect(self._update_status)
        self._status_timer.start(2000)

        self._select_creature(self._current_creature, init=True)

    def _build_ui(self):
        root = QWidget()
        self.setCentralWidget(root)
        lay = QHBoxLayout(root)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)

        # Left sidebar — creature selector + history
        self._sidebar = self._build_sidebar()
        lay.addWidget(self._sidebar)

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
            f"font-size: {FONTS.get('size_xs', 10)}px; "
            f"padding: 2px 8px;"
        )
        self._update_status()

    def _build_sidebar(self) -> QWidget:
        sidebar = QWidget()
        sidebar.setMinimumWidth(240)
        sidebar.setMaximumWidth(280)
        sidebar.setStyleSheet("background: rgba(5, 13, 20, 220); border-right: 1px solid rgba(0, 242, 194, 30);")
        lay = QVBoxLayout(sidebar)
        lay.setContentsMargins(12, 12, 12, 8)
        lay.setSpacing(6)

        # New Chat button
        new_btn = QPushButton("+ New Chat")
        new_btn.setCursor(Qt.PointingHandCursor)
        new_btn.setFixedHeight(36)
        new_btn.setStyleSheet(f"""
            QPushButton {{
                background: {glass_bg(140)}; color: {COLORS['seafoam']};
                border: 1px solid {glass_edge(60)}; border-radius: 8px;
                font-size: 12px; font-weight: bold; padding: 0 12px;
            }}
            QPushButton:hover {{ background: {glass_bg(180)}; border: 1px solid {glass_edge(80)}; }}
        """)
        new_btn.clicked.connect(self._new_conversation)
        lay.addWidget(new_btn)

        # Model selector label
        models_label = QLabel("MODELS")
        models_label.setStyleSheet(
            f"color: {COLORS['seafoam']}; font-size: 10px; font-weight: bold; "
            f"letter-spacing: 2px; padding: 8px 0 4px 0; background: transparent; border: none;"
        )
        lay.addWidget(models_label)

        # Creature selector
        self._selector = CreatureSelector()
        self._selector.creature_selected.connect(self._select_creature)
        self._selector.setMaximumHeight(380)
        lay.addWidget(self._selector)

        # History label
        hist_label = QLabel("HISTORY")
        hist_label.setStyleSheet(
            f"color: {COLORS['text_muted']}; font-size: 10px; font-weight: bold; "
            f"letter-spacing: 2px; padding: 8px 0 4px 0; background: transparent; border: none;"
        )
        lay.addWidget(hist_label)

        # History list
        self._history_scroll = QScrollArea()
        self._history_scroll.setWidgetResizable(True)
        self._history_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self._history_scroll.setStyleSheet("QScrollArea { background: transparent; border: none; }")
        self._history_container = QWidget()
        self._history_container.setStyleSheet("background: transparent;")
        self._history_lay = QVBoxLayout(self._history_container)
        self._history_lay.setContentsMargins(0, 0, 0, 0)
        self._history_lay.setSpacing(2)
        self._history_lay.addStretch(1)
        self._history_scroll.setWidget(self._history_container)
        lay.addWidget(self._history_scroll, 1)

        # Footer
        footer = QLabel("Kraken AI v2.0")
        footer.setAlignment(Qt.AlignCenter)
        footer.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: 9px; padding: 4px; background: transparent; border: none;")
        lay.addWidget(footer)

        return sidebar

    def _build_top_bar(self) -> QWidget:
        bar = QWidget()
        bar.setFixedHeight(54)
        bar.setStyleSheet(f"background: {glass_bg_dark(240)}; border-bottom: 1px solid {glass_edge()};")
        lay = QHBoxLayout(bar)
        lay.setContentsMargins(20, 0, 20, 0)

        # Creature icon (colored circle)
        self._icon_frame = QLabel()
        self._icon_frame.setFixedSize(36, 36)
        self._icon_frame.setAlignment(Qt.AlignCenter)
        self._update_icon()
        lay.addWidget(self._icon_frame)

        # Creature name + subtitle
        text_col = QVBoxLayout()
        text_col.setSpacing(0)
        text_col.setContentsMargins(0, 0, 0, 0)
        self._creature_name = QLabel("Kraken")
        self._creature_name.setStyleSheet("color: #00F2C2; font-size: 16px; font-weight: bold; background: transparent; border: none;")
        text_col.addWidget(self._creature_name)
        self._creature_subtitle = QLabel("Code from the Deep")
        self._creature_subtitle.setStyleSheet("color: #8BA4B8; font-size: 10px; background: transparent; border: none;")
        text_col.addWidget(self._creature_subtitle)
        lay.addLayout(text_col)

        lay.addStretch(1)

        # Keyboard shortcut hints
        hints = QLabel("Ctrl+L Clear  /  Esc Stop  /  Ctrl+N New")
        hints.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: 9px; background: transparent; border: none;")
        lay.addWidget(hints)

        lay.addSpacing(12)

        # Export button
        export_btn = self._icon_button("Export", "\u2b07")
        export_btn.clicked.connect(self._export_chat)
        lay.addWidget(export_btn)

        # Settings button
        settings_btn = self._icon_button("Settings", "\u2699")
        settings_btn.clicked.connect(self._open_settings)
        lay.addWidget(settings_btn)

        return bar

    def _icon_button(self, tooltip: str, icon_text: str) -> QPushButton:
        btn = QPushButton(icon_text)
        btn.setToolTip(tooltip)
        btn.setFixedSize(32, 32)
        btn.setCursor(Qt.PointingHandCursor)
        btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent; color: {COLORS['text_secondary']};
                border: 1px solid transparent; border-radius: 6px; font-size: 14px;
            }}
            QPushButton:hover {{
                background: {glass_bg(100)}; border: 1px solid {glass_edge(40)};
                color: {COLORS['hd_white']};
            }}
        """)
        return btn

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
        self._creature_name.setStyleSheet(f"color: {color}; font-size: 16px; font-weight: bold; background: transparent; border: none;")
        self._creature_subtitle.setText(meta.get("subtitle", ""))
        self._chat.set_creature_color(color)
        self._selector.set_active(creature_id)
        self._update_icon()

        if not init:
            self._chat.status_message(f"Switched to {meta.get('name', creature_id)} — {meta.get('description', '')[:60]}")

        self.cfg.set("creature", creature_id)
        self._update_status()

    def _new_conversation(self):
        # Save current conversation if it has messages
        if self._chat_history:
            self._conversations.append({
                "name": self._chat_history[0]["content"][:40] if self._chat_history else "New Chat",
                "creature": self._current_creature,
                "messages": list(self._chat_history),
                "ts": time.time(),
            })
            self._refresh_history()

        self._chat_history = []
        self._chat.clear()
        meta = CREATURES.get(self._current_creature, {})
        self._chat.status_message(f"New conversation with {meta.get('name', self._current_creature)}")

    def _refresh_history(self):
        # Clear existing items
        while self._history_lay.count() > 1:
            item = self._history_lay.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()

        # Add history items (newest first)
        for i, conv in enumerate(reversed(self._conversations)):
            name = conv.get("name", "Chat")[:30]
            creature = conv.get("creature", "kraken")
            color = CREATURES.get(creature, {}).get("color", "#00F2C2")
            btn = QPushButton(f"  {name}")
            btn.setCursor(Qt.PointingHandCursor)
            btn.setFixedHeight(28)
            btn.setStyleSheet(f"""
                QPushButton {{
                    background: transparent; color: {COLORS['text_secondary']};
                    border: none; border-radius: 4px; text-align: left;
                    font-size: 10px; padding: 0 8px;
                }}
                QPushButton:hover {{ background: {glass_bg(80)}; color: {COLORS['hd_white']}; }}
            """)
            idx = len(self._conversations) - 1 - i
            btn.clicked.connect(lambda _, ii=idx: self._load_conversation(ii))
            self._history_lay.insertWidget(self._history_lay.count() - 1, btn)

    def _load_conversation(self, index: int):
        if 0 <= index < len(self._conversations):
            conv = self._conversations[index]
            self._chat_history = list(conv.get("messages", []))
            creature = conv.get("creature", self._current_creature)
            if creature != self._current_creature:
                self._select_creature(creature)
            self._chat.clear()
            for msg in self._chat_history:
                if msg["role"] == "user":
                    self._chat.user_message(msg["content"])
                elif msg["role"] == "assistant":
                    self._chat.assistant_begin()
                    self._chat.assistant_delta(msg["content"])
                    self._chat.assistant_end()

    def _on_submit(self, text: str):
        if self.worker.running:
            self._chat.error_message("Engine busy — stop the current run first.")
            return

        self._chat.user_message(text)
        self._chat_history.append({"role": "user", "content": text})
        self.memory.remember("user", text, creature=self._current_creature)

        self.worker.run(self._current_creature, list(self._chat_history))

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
                f.write(f"# Kraken AI — {meta.get('name', self._current_creature)} Chat\n\n")
                f.write(f"Exported: {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n---\n\n")
                for msg in self._chat_history:
                    role = "You" if msg["role"] == "user" else meta.get("name", "Kraken")
                    f.write(f"### {role}\n\n{msg['content']}\n\n---\n\n")

        self._chat.status_message(f"Chat exported to {os.path.basename(path)}")

    def _open_settings(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Kraken Settings")
        dialog.resize(480, 500)
        dialog.setStyleSheet(f"""
            QDialog {{ background: {COLORS['deep_navy']}; color: {COLORS['hd_white']};
                       border: 1px solid {glass_edge()}; border-radius: 12px; }}
        """)

        lay = QVBoxLayout(dialog)
        lay.setContentsMargins(20, 20, 20, 20)
        lay.setSpacing(12)

        # Title
        title = QLabel("Settings")
        title.setStyleSheet(f"color: {COLORS['seafoam']}; font-size: 18px; font-weight: bold; background: transparent; border: none;")
        lay.addWidget(title)

        # Temperature
        temp_label = QLabel(f"Temperature: {self.cfg.get('temperature', 0.7):.1f}")
        temp_label.setStyleSheet(f"color: {COLORS['hd_white']}; font-size: 12px; background: transparent; border: none;")
        lay.addWidget(temp_label)
        temp_slider = QSlider(Qt.Horizontal)
        temp_slider.setRange(0, 100)
        temp_slider.setValue(int(self.cfg.get("temperature", 0.7) * 100))
        temp_slider.setStyleSheet(f"QSlider::groove:horizontal {{ background: {COLORS['border']}; height: 4px; border-radius: 2px; }} "
                                  f"QSlider::handle:horizontal {{ background: {COLORS['seafoam']}; width: 14px; margin: -5px 0; border-radius: 7px; }}")
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

        # Workspace
        ws_label = QLabel(f"Workspace: {self.cfg.get('workspace', os.getcwd())}")
        ws_label.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 10px; background: transparent; border: none;")
        ws_label.setWordWrap(True)
        lay.addWidget(ws_label)
        ws_btn = QPushButton("Change Workspace")
        ws_btn.setCursor(Qt.PointingHandCursor)
        ws_btn.setStyleSheet(f"QPushButton {{ background: {glass_bg(140)}; color: {COLORS['seafoam']}; border: 1px solid {glass_edge(60)}; border-radius: 6px; padding: 6px 12px; font-size: 11px; }} "
                             f"QPushButton:hover {{ background: {glass_bg(180)}; }}")
        def _change_ws():
            d = QFileDialog.getExistingDirectory(self, "Workspace", self.cfg.get("workspace", os.getcwd()))
            if d:
                self.cfg.set("workspace", d)
                ws_label.setText(f"Workspace: {d}")
        ws_btn.clicked.connect(_change_ws)
        lay.addWidget(ws_btn)

        # Memory toggle
        mem_btn = QPushButton(f"Memory: {'ON' if self.cfg.get('memory_enabled', True) else 'OFF'}")
        mem_btn.setCursor(Qt.PointingHandCursor)
        mem_btn.setStyleSheet(f"QPushButton {{ background: {glass_bg(140)}; color: {COLORS['seafoam']}; border: 1px solid {glass_edge(60)}; border-radius: 6px; padding: 6px 12px; font-size: 11px; }} "
                              f"QPushButton:hover {{ background: {glass_bg(180)}; }}")
        def _toggle_mem():
            current = self.cfg.get("memory_enabled", True)
            self.cfg.set("memory_enabled", not current)
            mem_btn.setText(f"Memory: {'ON' if not current else 'OFF'}")
        mem_btn.clicked.connect(_toggle_mem)
        lay.addWidget(mem_btn)

        # Clear memory
        clear_mem_btn = QPushButton("Clear Memory")
        clear_mem_btn.setCursor(Qt.PointingHandCursor)
        clear_mem_btn.setStyleSheet(f"QPushButton {{ background: {COLORS['coral']}22; color: {COLORS['coral']}; border: 1px solid {COLORS['coral']}44; border-radius: 6px; padding: 6px 12px; font-size: 11px; }} "
                                    f"QPushButton:hover {{ background: {COLORS['coral']}44; }}")
        def _clear_mem():
            self.memory.clear()
            self._chat.status_message("Memory cleared.")
        clear_mem_btn.clicked.connect(_clear_mem)
        lay.addWidget(clear_mem_btn)

        lay.addStretch(1)

        # Close
        close_btn = QPushButton("Close")
        close_btn.setCursor(Qt.PointingHandCursor)
        close_btn.setStyleSheet(f"QPushButton {{ background: {COLORS['seafoam']}; color: {COLORS['deep_navy']}; border: none; border-radius: 6px; padding: 8px; font-size: 12px; font-weight: bold; }} "
                                f"QPushButton:hover {{ background: {COLORS['seafoam']}cc; }}")
        close_btn.clicked.connect(dialog.close)
        lay.addWidget(close_btn)

        dialog.exec()

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

    def _update_status(self):
        meta = CREATURES.get(self._current_creature, {})
        status = (
            f"{meta.get('name', '?')} · "
            f"{self.cfg.get('provider', 'kraken-native')} · "
            f"temp {self.cfg.get('temperature', 0.7):.1f} · "
            f"{'ON' if self.cfg.get('memory_enabled') else 'OFF'} memory"
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
