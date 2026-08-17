"""Kraken AI — ChatGPT-style chat panel.

Message bubbles, streaming, markdown-ish rendering, input bar at bottom.
"""

from __future__ import annotations

import time

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

try:
    from core.theme import COLORS, FONTS, glass_bg, glass_bg_dark, glass_edge, glass_sheen
except ImportError:
    COLORS = {
        "abyss_navy": "#081626", "slate_navy": "#0E2238", "deep_navy": "#050D14",
        "seafoam": "#00F2C2", "coral": "#FF7F50", "amber": "#FFA502",
        "hd_white": "#EEF4F8", "text_secondary": "#8BA4B8", "text_muted": "#506070",
    }
    FONTS = {"mono": "JetBrains Mono", "ui": "Segoe UI", "size_sm": 11, "size_md": 12, "size_lg": 13}

    def glass_bg(a=180): return f"rgba(14, 34, 56, {a})"
    def glass_bg_dark(a=140): return f"rgba(5, 13, 20, {a})"
    def glass_edge(a=48): return f"rgba(0, 242, 194, {a})"
    def glass_sheen(): return "rgba(238, 244, 248, 26)"


class MessageBubble(QWidget):
    """A single chat message bubble."""

    def __init__(self, role: str, text: str, color: str = "#EEF4F8", creature_color: str = "#00F2C2", parent=None):
        super().__init__(parent)
        self._role = role
        self._build(role, text, color, creature_color)

    def _build(self, role: str, text: str, color: str, creature_color: str):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 4, 0, 4)

        if role == "user":
            lay.addStretch(1)
            container = QWidget()
            container.setStyleSheet(f"background: {creature_color}18; border: 1px solid {creature_color}30; border-radius: 12px; padding: 2px;")
            container_lay = QVBoxLayout(container)
            container_lay.setContentsMargins(12, 10, 12, 10)
        else:
            container = QWidget()
            container.setStyleSheet("background: transparent; padding: 2px;")
            container_lay = QVBoxLayout(container)
            container_lay.setContentsMargins(0, 6, 0, 6)

        # Label
        if role == "user":
            lbl = QLabel("You")
            lbl.setStyleSheet(f"color: {creature_color}; font-size: 10px; font-weight: bold; background: transparent; border: none; padding-bottom: 4px;")
        else:
            lbl = QLabel("Kraken")
            lbl.setStyleSheet(f"color: {creature_color}; font-size: 10px; font-weight: bold; background: transparent; border: none; padding-bottom: 4px;")
        container_lay.addWidget(lbl)

        # Body
        body = QLabel(text)
        body.setWordWrap(True)
        body.setTextInteractionFlags(Qt.TextSelectableByMouse)
        body.setStyleSheet(f"color: {color}; font-size: 13px; line-height: 1.5; background: transparent; border: none;")
        container_lay.addWidget(body)

        # Timestamp
        ts = QLabel(time.strftime("%H:%M"))
        ts.setStyleSheet("color: #506070; font-size: 9px; background: transparent; border: none;")
        if role == "user":
            ts.setAlignment(Qt.AlignRight)
        container_lay.addWidget(ts)

        if role == "user":
            row = QHBoxLayout()
            row.setContentsMargins(60, 0, 0, 0)
            row.addStretch(1)
            row.addWidget(container, 3)
            lay.addLayout(row)
        else:
            lay.addWidget(container)

    def append_text(self, text: str):
        """Append text to the body label (for streaming)."""
        labels = self.findChildren(QLabel)
        if len(labels) >= 2:
            body = labels[1]
            current = body.text()
            body.setText(current + text)


class ChatPanel(QWidget):
    """Full chat panel with scroll area + input bar."""

    submitted = Signal(str)
    stop_clicked = Signal()

    def __init__(self, creature_color: str = "#00F2C2", parent=None):
        super().__init__(parent)
        self._creature_color = creature_color
        self._streaming = False
        self._current_bubble: MessageBubble | None = None
        self._build_ui()

    def _build_ui(self):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)

        # Scroll area for messages
        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        self._scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self._scroll.setStyleSheet("QScrollArea { background: transparent; border: none; }")

        self._messages = QWidget()
        self._messages.setStyleSheet("background: transparent;")
        self._msg_lay = QVBoxLayout(self._messages)
        self._msg_lay.setContentsMargins(20, 20, 20, 20)
        self._msg_lay.setSpacing(4)
        self._msg_lay.addStretch(1)

        self._scroll.setWidget(self._messages)
        lay.addWidget(self._scroll, 1)

        # Welcome text
        self._welcome = QLabel("What can I help you with?")
        self._welcome.setAlignment(Qt.AlignCenter)
        self._welcome.setStyleSheet("color: #8BA4B8; font-size: 24px; padding: 80px 40px; background: transparent;")
        self._msg_lay.insertWidget(0, self._welcome)

        # Input bar
        input_frame = QWidget()
        input_frame.setStyleSheet(f"background: {glass_bg_dark(220)}; border-top: 1px solid {glass_edge()};")
        input_lay = QHBoxLayout(input_frame)
        input_lay.setContentsMargins(20, 12, 20, 12)
        input_lay.setSpacing(10)

        self._input = QLineEdit()
        self._input.setPlaceholderText("Send a message...")
        self._input.setMinimumHeight(44)
        self._input.setStyleSheet(f"""
            QLineEdit {{
                background: {glass_bg(120)};
                color: {COLORS['hd_white']};
                border: 1px solid {glass_edge(60)};
                border-radius: 22px;
                padding: 10px 18px;
                font-size: 14px;
                font-family: '{FONTS.get('ui', 'sans-serif')}';
            }}
            QLineEdit:focus {{
                border: 1px solid {self._creature_color};
            }}
        """)
        self._input.returnPressed.connect(self._on_submit)
        input_lay.addWidget(self._input, 1)

        self._send_btn = QPushButton("\u27a4")
        self._send_btn.setFixedSize(44, 44)
        self._send_btn.setCursor(Qt.PointingHandCursor)
        self._send_btn.setStyleSheet(f"""
            QPushButton {{
                background: {self._creature_color};
                color: #050D14;
                border: none;
                border-radius: 22px;
                font-size: 18px;
                font-weight: bold;
            }}
            QPushButton:hover {{ background: {self._creature_color}cc; }}
            QPushButton:disabled {{ background: #506070; color: #1A3352; }}
        """)
        self._send_btn.clicked.connect(self._on_submit)
        input_lay.addWidget(self._send_btn)

        self._stop_btn = QPushButton("\u25a0")
        self._stop_btn.setFixedSize(44, 44)
        self._stop_btn.setCursor(Qt.PointingHandCursor)
        self._stop_btn.setVisible(False)
        self._stop_btn.setStyleSheet("""
            QPushButton {
                background: #FF4444;
                color: #ffffff;
                border: none;
                border-radius: 22px;
                font-size: 16px;
                font-weight: bold;
            }
            QPushButton:hover { background: #FF6666; }
        """)
        self._stop_btn.clicked.connect(self._on_stop)
        input_lay.addWidget(self._stop_btn)

        lay.addWidget(input_frame)

    def _on_submit(self):
        text = self._input.text().strip()
        if not text or self._streaming:
            return
        self._input.clear()
        self.submitted.emit(text)

    def _on_stop(self):
        self.stop_clicked.emit()

    def set_creature_color(self, color: str):
        self._creature_color = color
        self._send_btn.setStyleSheet(f"""
            QPushButton {{
                background: {color};
                color: #050D14;
                border: none;
                border-radius: 22px;
                font-size: 18px;
                font-weight: bold;
            }}
            QPushButton:hover {{ background: {color}cc; }}
            QPushButton:disabled {{ background: #506070; color: #1A3352; }}
        """)

    # ── Message helpers ──────────────────────────────────────────

    def user_message(self, text: str):
        if self._welcome.isVisible():
            self._welcome.hide()
        bubble = MessageBubble("user", text, creature_color=self._creature_color)
        # Insert before the stretch
        self._msg_lay.insertWidget(self._msg_lay.count() - 1, bubble)
        self._scroll_to_bottom()

    def assistant_begin(self):
        if self._welcome.isVisible():
            self._welcome.hide()
        self._streaming = True
        self._send_btn.setVisible(False)
        self._stop_btn.setVisible(True)
        self._current_bubble = MessageBubble("assistant", "", creature_color=self._creature_color)
        self._msg_lay.insertWidget(self._msg_lay.count() - 1, self._current_bubble)
        self._scroll_to_bottom()

    def assistant_delta(self, text: str):
        if self._current_bubble:
            self._current_bubble.append_text(text)
            self._scroll_to_bottom()

    def assistant_end(self):
        self._streaming = False
        self._current_bubble = None
        self._send_btn.setVisible(True)
        self._stop_btn.setVisible(False)

    def error_message(self, text: str):
        bubble = MessageBubble("assistant", f"[Error] {text}", color="#FF7F50", creature_color="#FF7F50")
        self._msg_lay.insertWidget(self._msg_lay.count() - 1, bubble)
        self._scroll_to_bottom()

    def status_message(self, text: str):
        lbl = QLabel(text)
        lbl.setAlignment(Qt.AlignCenter)
        lbl.setStyleSheet("color: #506070; font-size: 10px; padding: 4px; background: transparent;")
        self._msg_lay.insertWidget(self._msg_lay.count() - 1, lbl)
        self._scroll_to_bottom()

    def clear(self):
        while self._msg_lay.count() > 1:
            item = self._msg_lay.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()
        self._welcome.show()
        self._current_bubble = None
        self._streaming = False

    def focus_input(self):
        self._input.setFocus()

    def _scroll_to_bottom(self):
        sb = self._scroll.verticalScrollBar()
        sb.setValue(sb.maximum())
