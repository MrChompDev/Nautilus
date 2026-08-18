"""Kraken AI — Chat panel with model dropdown in input bar.

Message bubbles, streaming, typing indicator, model selector combo.
Layout follows Claude/ChatGPT pattern: full-width messages that wrap.
"""

from __future__ import annotations

import time

from PySide6.QtCore import Qt, Signal, QTimer, QSize
from PySide6.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QSizePolicy,
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
    """A single chat message bubble — Claude-style full-width layout."""

    def __init__(self, role: str, text: str, color: str = "#EEF4F8",
                 creature_color: str = "#00F2C2", creature_name: str = "Kraken",
                 parent=None):
        super().__init__(parent)
        self._role = role
        self._creature_color = creature_color
        self._body_label: QLabel | None = None
        self._build(role, text, color, creature_color, creature_name)

    def _build(self, role: str, text: str, color: str, creature_color: str, creature_name: str):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 4, 0, 4)
        lay.setSpacing(0)

        if role == "user":
            # User message — right-aligned, colored bubble
            row = QHBoxLayout()
            row.setContentsMargins(0, 0, 0, 0)
            row.addStretch(1)

            container = QWidget()
            container.setStyleSheet(f"""
                background: {creature_color}15;
                border: 1px solid {creature_color}25;
                border-radius: 16px 16px 4px 16px;
            """)
            container.setMaximumWidth(520)
            cl = QVBoxLayout(container)
            cl.setContentsMargins(16, 12, 16, 10)

            body = QLabel(text)
            body.setWordWrap(True)
            body.setTextInteractionFlags(Qt.TextSelectableByMouse)
            body.setStyleSheet(f"color: #FFFFFF; font-size: 13px; background: transparent; border: none;")
            cl.addWidget(body)

            ts = QLabel(time.strftime("%H:%M"))
            ts.setAlignment(Qt.AlignRight)
            ts.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: 9px; background: transparent; border: none; padding-top: 4px;")
            cl.addWidget(ts)

            row.addWidget(container)
            row.addStretch(1)
            lay.addLayout(row)

        else:
            # Assistant message — full width, left-aligned, like Claude
            header = QHBoxLayout()
            header.setContentsMargins(40, 0, 20, 4)
            header.setSpacing(8)

            avatar = QLabel(creature_name[0] if creature_name else "?")
            avatar.setFixedSize(26, 26)
            avatar.setAlignment(Qt.AlignCenter)
            avatar.setStyleSheet(f"""
                background: {creature_color}22; border: 1px solid {creature_color}44;
                border-radius: 13px; color: {creature_color}; font-size: 12px; font-weight: bold;
            """)
            header.addWidget(avatar)

            name_lbl = QLabel(creature_name)
            name_lbl.setStyleSheet(f"color: {creature_color}; font-size: 12px; font-weight: bold; background: transparent; border: none;")
            header.addWidget(name_lbl)
            header.addStretch(1)
            lay.addLayout(header)

            # Body — full width, text wraps naturally like Claude
            body = QLabel(text)
            body.setWordWrap(True)
            body.setTextInteractionFlags(Qt.TextSelectableByMouse)
            body.setStyleSheet(
                f"color: #FFFFFF; font-size: 13px; "
                f"background: transparent; border: none; padding: 0 40px 0 40px;"
            )
            lay.addWidget(body, 1)
            self._body_label = body

            ts = QLabel(time.strftime("%H:%M"))
            ts.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: 9px; background: transparent; border: none; padding: 4px 40px 0 40px;")
            lay.addWidget(ts)

    def append_text(self, text: str):
        if self._body_label:
            self._body_label.setText(self._body_label.text() + text)


class ChatPanel(QWidget):
    """Full chat panel with scroll area + input bar with model dropdown."""

    submitted = Signal(str)
    stop_clicked = Signal()
    creature_changed = Signal(str)

    def __init__(self, creatures: dict | None = None,
                 creature_id: str = "kraken", parent=None):
        super().__init__(parent)
        self._creatures = creatures or {}
        self._creature_id = creature_id
        self._creature_color = self._creatures.get(creature_id, {}).get("color", "#00F2C2")
        self._streaming = False
        self._current_bubble: MessageBubble | None = None
        self._typing: TypingIndicator | None = None
        self._build_ui()

    def _build_ui(self):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)

        # Scroll area for messages — fills the entire chat area
        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        self._scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self._scroll.setStyleSheet("QScrollArea { background: transparent; border: none; }")

        self._messages = QWidget()
        self._messages.setStyleSheet("background: transparent;")
        self._msg_lay = QVBoxLayout(self._messages)
        self._msg_lay.setContentsMargins(0, 0, 0, 0)
        self._msg_lay.setSpacing(0)
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
        input_lay.setContentsMargins(20, 14, 20, 14)
        input_lay.setSpacing(8)

        # Model dropdown
        self._model_combo = QComboBox()
        self._model_combo.setFixedWidth(160)
        self._model_combo.setFixedHeight(40)
        for cid, meta in self._creatures.items():
            self._model_combo.addItem(meta.get("name", cid), cid)
        idx = self._model_combo.findData(self._creature_id)
        if idx >= 0:
            self._model_combo.setCurrentIndex(idx)
        self._model_combo.setStyleSheet(self._combo_style(self._creature_color))
        self._model_combo.currentIndexChanged.connect(self._on_creature_changed)
        input_lay.addWidget(self._model_combo)

        # Text input
        self._input = QLineEdit()
        self._input.setPlaceholderText("Send a message...")
        self._input.setMinimumHeight(46)
        self._input.setStyleSheet(self._input_style(self._creature_color))
        self._input.returnPressed.connect(self._on_submit)
        input_lay.addWidget(self._input, 1)

        # Send button
        self._send_btn = QPushButton("\u27a4")
        self._send_btn.setFixedSize(46, 46)
        self._send_btn.setCursor(Qt.PointingHandCursor)
        self._send_btn.setStyleSheet(self._send_style(self._creature_color))
        self._send_btn.clicked.connect(self._on_submit)
        input_lay.addWidget(self._send_btn)

        # Stop button
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

    def _combo_style(self, color: str) -> str:
        return f"""
            QComboBox {{
                background: {glass_bg(120)}; color: {color};
                border: 1px solid {color}66; border-radius: 8px;
                padding: 6px 12px; font-size: 12px; font-weight: bold;
                font-family: '{FONTS.get('ui', 'sans-serif')}';
            }}
            QComboBox:hover {{ border: 1px solid {color}; }}
            QComboBox::drop-down {{ border: none; width: 24px; }}
            QComboBox::down-arrow {{
                image: none; border-left: 4px solid transparent;
                border-right: 4px solid transparent; border-top: 6px solid {color};
                margin-right: 8px;
            }}
            QComboBox QAbstractItemView {{
                background: {COLORS['deep_navy']}; color: {COLORS['hd_white']};
                border: 1px solid {color}44; border-radius: 6px;
                selection-background-color: {color}22; padding: 4px;
            }}
        """

    def _input_style(self, color: str) -> str:
        return f"""
            QLineEdit {{
                background: {glass_bg(120)}; color: {COLORS['hd_white']};
                border: 1px solid {glass_edge(60)}; border-radius: 23px;
                padding: 11px 20px; font-size: 14px;
                font-family: '{FONTS.get('ui', 'sans-serif')}';
            }}
            QLineEdit:focus {{ border: 1px solid {color}; background: {glass_bg(150)}; }}
        """

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

        color = self._creature_color
        logo = QLabel("?")
        logo.setFixedSize(80, 80)
        logo.setAlignment(Qt.AlignCenter)
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

        subtitle = QLabel("Select a model from the dropdown below, then type your message.")
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 13px; background: transparent; border: none;")
        lay.addWidget(subtitle)

        return welcome

    def _on_creature_changed(self, index: int):
        cid = self._model_combo.currentData()
        if cid and cid != self._creature_id:
            self._creature_id = cid
            self._creature_color = self._creatures.get(cid, {}).get("color", "#00F2C2")
            self._apply_color()
            self.creature_changed.emit(cid)

    def _apply_color(self):
        c = self._creature_color
        self._send_btn.setStyleSheet(self._send_style(c))
        self._input.setStyleSheet(self._input_style(c))
        self._model_combo.setStyleSheet(self._combo_style(c))
        if self._typing:
            self._typing.set_color(c)
        if hasattr(self, "_welcome"):
            logos = self._welcome.findChildren(QLabel)
            if logos:
                logos[0].setStyleSheet(f"""
                    background: {c}15; border: 2px solid {c}30;
                    border-radius: 40px; color: {c}; font-size: 36px; font-weight: bold;
                """)

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
        self._apply_color()

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
        # Create bubble immediately — no timer delay
        self._typing.set_color(self._creature_color)
        name = self._creatures.get(self._creature_id, {}).get("name", "Kraken")
        self._current_bubble = MessageBubble(
            "assistant", "", creature_color=self._creature_color, creature_name=name,
        )
        self._msg_lay.insertWidget(self._msg_lay.count() - 1, self._current_bubble)
        self._scroll_to_bottom()

    def _start_bubble(self):
        pass  # kept for compatibility — bubble is created in assistant_begin now

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
        # Double-buffer: ensure scroll reaches bottom after layout updates
        QTimer.singleShot(10, lambda: sb.setValue(sb.maximum()))
        QTimer.singleShot(50, lambda: sb.setValue(sb.maximum()))
