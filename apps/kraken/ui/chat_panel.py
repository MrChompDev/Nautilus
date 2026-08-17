"""Kraken AI — ChatGPT-style chat panel.

Message bubbles, streaming, typing indicator, markdown-ish rendering.
"""

from __future__ import annotations

import html
import time

from PySide6.QtCore import Qt, Signal, QTimer, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import QTextCursor
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
    from core.theme import COLORS, FONTS, glass_bg, glass_bg_dark, glass_edge
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


class TypingIndicator(QWidget):
    """Animated typing indicator dots."""

    def __init__(self, color: str = "#00F2C2", parent=None):
        super().__init__(parent)
        self._color = color
        self._dots = []
        self._phase = 0
        self.setFixedHeight(24)

        lay = QHBoxLayout(self)
        lay.setContentsMargins(40, 0, 0, 0)
        lay.setSpacing(4)

        for _ in range(3):
            dot = QLabel("\u25cf")
            dot.setStyleSheet(f"color: {color}; font-size: 8px; background: transparent; border: none;")
            self._dots.append(dot)
            lay.addWidget(dot)
        lay.addStretch(1)

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._animate)
        self._timer.start(400)

    def _animate(self):
        self._phase = (self._phase + 1) % 4
        for i, dot in enumerate(self._dots):
            if i == self._phase % 3:
                dot.setStyleSheet(f"color: {self._color}; font-size: 10px; background: transparent; border: none;")
            else:
                dot.setStyleSheet(f"color: {self._color}44; font-size: 8px; background: transparent; border: none;")

    def set_color(self, color: str):
        self._color = color


class MessageBubble(QWidget):
    """A single chat message bubble."""

    def __init__(self, role: str, text: str, color: str = "#EEF4F8", creature_color: str = "#00F2C2", parent=None):
        super().__init__(parent)
        self._role = role
        self._creature_color = creature_color
        self._build(role, text, color, creature_color)

    def _build(self, role: str, text: str, color: str, creature_color: str):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 2, 0, 2)

        if role == "user":
            # User message — right-aligned bubble
            lay.addStretch(1)
            container = QWidget()
            container.setStyleSheet(f"""
                background: {creature_color}15;
                border: 1px solid {creature_color}25;
                border-radius: 16px 16px 4px 16px;
            """)
            container_lay = QVBoxLayout(container)
            container_lay.setContentsMargins(16, 12, 16, 10)

            body = QLabel(text)
            body.setWordWrap(True)
            body.setTextInteractionFlags(Qt.TextSelectableByMouse)
            body.setStyleSheet(f"color: {color}; font-size: 13px; background: transparent; border: none; line-height: 1.4;")
            container_lay.addWidget(body)

            ts = QLabel(time.strftime("%H:%M"))
            ts.setAlignment(Qt.AlignRight)
            ts.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: 9px; background: transparent; border: none; padding-top: 4px;")
            container_lay.addWidget(ts)

            row = QHBoxLayout()
            row.setContentsMargins(80, 0, 16, 0)
            row.addStretch(1)
            row.addWidget(container, 4)
            lay.addLayout(row)

        else:
            # Assistant message — left-aligned
            header_lay = QHBoxLayout()
            header_lay.setContentsMargins(40, 0, 0, 2)
            header_lay.setSpacing(6)

            # Avatar circle
            avatar = QLabel(creature_color[1].upper() if creature_color.startswith("#") else "?")
            avatar.setFixedSize(24, 24)
            avatar.setAlignment(Qt.AlignCenter)
            avatar.setStyleSheet(f"""
                background: {creature_color}22; border: 1px solid {creature_color}44;
                border-radius: 12px; color: {creature_color}; font-size: 11px; font-weight: bold;
            """)
            header_lay.addWidget(avatar)

            name = QLabel("Kraken")
            name.setStyleSheet(f"color: {creature_color}; font-size: 11px; font-weight: bold; background: transparent; border: none;")
            header_lay.addWidget(name)
            header_lay.addStretch(1)

            lay.addLayout(header_lay)

            container = QWidget()
            container.setStyleSheet("background: transparent;")
            container_lay = QVBoxLayout(container)
            container_lay.setContentsMargins(40, 0, 60, 0)

            body = QLabel(text)
            body.setWordWrap(True)
            body.setTextInteractionFlags(Qt.TextSelectableByMouse)
            body.setStyleSheet(f"color: {color}; font-size: 13px; background: transparent; border: none; line-height: 1.5;")
            container_lay.addWidget(body)

            ts = QLabel(time.strftime("%H:%M"))
            ts.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: 9px; background: transparent; border: none; padding-top: 2px;")
            container_lay.addWidget(ts)

            lay.addWidget(container)

    def append_text(self, text: str):
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
        self._typing: TypingIndicator | None = None
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

        # Welcome screen
        self._welcome = self._build_welcome()
        self._msg_lay.insertWidget(0, self._welcome)

        # Typing indicator
        self._typing = TypingIndicator(self._creature_color)
        self._typing.hide()

        # Input bar
        input_frame = QWidget()
        input_frame.setStyleSheet(f"background: {glass_bg_dark(220)}; border-top: 1px solid {glass_edge()};")
        input_lay = QHBoxLayout(input_frame)
        input_lay.setContentsMargins(24, 14, 24, 14)
        input_lay.setSpacing(10)

        self._input = QLineEdit()
        self._input.setPlaceholderText("Send a message...")
        self._input.setMinimumHeight(46)
        self._input.setStyleSheet(f"""
            QLineEdit {{
                background: {glass_bg(120)};
                color: {COLORS['hd_white']};
                border: 1px solid {glass_edge(60)};
                border-radius: 23px;
                padding: 11px 20px;
                font-size: 14px;
                font-family: '{FONTS.get('ui', 'sans-serif')}';
            }}
            QLineEdit:focus {{
                border: 1px solid {self._creature_color};
                background: {glass_bg(150)};
            }}
        """)
        self._input.returnPressed.connect(self._on_submit)
        input_lay.addWidget(self._input, 1)

        self._send_btn = QPushButton("\u27a4")
        self._send_btn.setFixedSize(46, 46)
        self._send_btn.setCursor(Qt.PointingHandCursor)
        self._send_btn.setStyleSheet(self._send_style(self._creature_color))
        self._send_btn.clicked.connect(self._on_submit)
        input_lay.addWidget(self._send_btn)

        self._stop_btn = QPushButton("\u25a0")
        self._stop_btn.setFixedSize(46, 46)
        self._stop_btn.setCursor(Qt.PointingHandCursor)
        self._stop_btn.setVisible(False)
        self._stop_btn.setStyleSheet(f"""
            QPushButton {{
                background: #FF4444; color: #ffffff; border: none;
                border-radius: 23px; font-size: 16px; font-weight: bold;
            }}
            QPushButton:hover {{ background: #FF6666; }}
        """)
        self._stop_btn.clicked.connect(self._on_stop)
        input_lay.addWidget(self._stop_btn)

        lay.addWidget(input_frame)

    def _send_style(self, color: str) -> str:
        return f"""
            QPushButton {{
                background: {color}; color: #050D14; border: none;
                border-radius: 23px; font-size: 18px; font-weight: bold;
            }}
            QPushButton:hover {{ background: {color}cc; }}
            QPushButton:disabled {{ background: #506070; color: #1A3352; }}
        """

    def _build_welcome(self) -> QWidget:
        welcome = QWidget()
        lay = QVBoxLayout(welcome)
        lay.setAlignment(Qt.AlignCenter)

        # Logo
        logo = QLabel("?")
        logo.setFixedSize(80, 80)
        logo.setAlignment(Qt.AlignCenter)
        color = self._creature_color
        logo.setStyleSheet(f"""
            background: {color}15; border: 2px solid {color}30;
            border-radius: 40px; color: {color}; font-size: 36px; font-weight: bold;
        """)
        lay.addWidget(logo, alignment=Qt.AlignCenter)
        lay.addSpacing(16)

        title = QLabel("What can I help you with?")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet(f"color: {COLORS['hd_white']}; font-size: 26px; font-weight: bold; background: transparent; border: none;")
        lay.addWidget(title)

        subtitle = QLabel("Choose a model on the left, then type your message below.")
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 13px; background: transparent; border: none;")
        lay.addWidget(subtitle)

        lay.addSpacing(24)

        # Quick action cards
        cards_lay = QHBoxLayout()
        cards_lay.setSpacing(12)
        cards_lay.setAlignment(Qt.AlignCenter)

        for label, hint in [("Code", "Write or debug code"), ("Write", "Draft prose or docs"), ("Visual", "Generate an image"), ("Scan", "Security audit")]:
            card = QPushButton(f"{label}\n{hint}")
            card.setFixedSize(120, 60)
            card.setCursor(Qt.PointingHandCursor)
            card.setStyleSheet(f"""
                QPushButton {{
                    background: {glass_bg(80)}; color: {COLORS['text_secondary']};
                    border: 1px solid {glass_edge(30)}; border-radius: 10px;
                    font-size: 10px; padding: 8px;
                }}
                QPushButton:hover {{
                    background: {glass_bg(120)}; border: 1px solid {glass_edge(50)};
                    color: {COLORS['hd_white']};
                }}
            """)
            cards_lay.addWidget(card)

        lay.addLayout(cards_lay)

        return welcome

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
        self._send_btn.setStyleSheet(self._send_style(color))
        if self._typing:
            self._typing.set_color(color)
        # Update welcome logo
        if hasattr(self, "_welcome"):
            logos = self._welcome.findChildren(QLabel)
            if logos:
                logos[0].setStyleSheet(f"""
                    background: {color}15; border: 2px solid {color}30;
                    border-radius: 40px; color: {color}; font-size: 36px; font-weight: bold;
                """)

    # ── Message helpers ──────────────────────────────────────────

    def user_message(self, text: str):
        if self._welcome.isVisible():
            self._welcome.hide()
        bubble = MessageBubble("user", text, creature_color=self._creature_color)
        self._msg_lay.insertWidget(self._msg_lay.count() - 1, bubble)
        self._scroll_to_bottom()

    def assistant_begin(self):
        if self._welcome.isVisible():
            self._welcome.hide()
        self._streaming = True
        self._send_btn.setVisible(False)
        self._stop_btn.setVisible(True)
        # Show typing indicator briefly
        self._typing.set_color(self._creature_color)
        self._msg_lay.insertWidget(self._msg_lay.count() - 1, self._typing)
        self._typing.show()
        self._scroll_to_bottom()
        # Replace with bubble after a short delay
        QTimer.singleShot(300, self._start_bubble)

    def _start_bubble(self):
        self._typing.hide()
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
        self._typing.hide()

    def error_message(self, text: str):
        bubble = MessageBubble("assistant", f"[Error] {text}", color="#FF7F50", creature_color="#FF7F50")
        self._msg_lay.insertWidget(self._msg_lay.count() - 1, bubble)
        self._scroll_to_bottom()

    def status_message(self, text: str):
        lbl = QLabel(text)
        lbl.setAlignment(Qt.AlignCenter)
        lbl.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: 10px; padding: 6px; background: transparent; border: none;")
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
        self._typing.hide()

    def focus_input(self):
        self._input.setFocus()

    def _scroll_to_bottom(self):
        sb = self._scroll.verticalScrollBar()
        sb.setValue(sb.maximum())
