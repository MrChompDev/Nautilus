"""Kraken AI — creature selector sidebar.

Card-based model picker with logos, names, and descriptions.
Each card highlights when active.
"""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from apps.kraken.core.config import CREATURES


class CreatureCard(QFrame):
    """A single creature selection card."""

    clicked = Signal(str)

    def __init__(self, creature_id: str, meta: dict, parent=None):
        super().__init__(parent)
        self.creature_id = creature_id
        self.meta = meta
        self._active = False
        self.setCursor(Qt.PointingHandCursor)
        self.setFixedHeight(80)
        self.setStyleSheet(self._base_style())
        self._build_ui()

    def _base_style(self):
        c = self.meta.get("color", "#00F2C2")
        return f"""
            QFrame {{
                background: rgba(14, 34, 56, 140);
                border: 1px solid rgba(255,255,255, 20);
                border-radius: 12px;
                padding: 8px;
            }}
            QFrame:hover {{
                background: rgba(14, 34, 56, 200);
                border: 1px solid {c}44;
            }}
        """

    def _active_style(self):
        c = self.meta.get("color", "#00F2C2")
        return f"""
            QFrame {{
                background: rgba(14, 34, 56, 220);
                border: 2px solid {c};
                border-radius: 12px;
                padding: 8px;
            }}
        """

    def _build_ui(self):
        lay = QHBoxLayout(self)
        lay.setContentsMargins(10, 8, 10, 8)
        lay.setSpacing(10)

        # Logo placeholder (colored circle with first letter)
        logo_frame = QFrame()
        logo_frame.setFixedSize(48, 48)
        c = self.meta.get("color", "#00F2C2")
        logo_frame.setStyleSheet(f"""
            QFrame {{
                background: {c}22;
                border: 1.5px solid {c}66;
                border-radius: 24px;
            }}
        """)
        logo_lay = QVBoxLayout(logo_frame)
        logo_lay.setContentsMargins(0, 0, 0, 0)
        logo_label = QLabel(self.meta.get("name", "?")[0])
        logo_label.setAlignment(Qt.AlignCenter)
        logo_label.setStyleSheet(f"color: {c}; font-size: 20px; font-weight: bold; background: transparent; border: none;")
        logo_lay.addWidget(logo_label)
        lay.addWidget(logo_frame)

        # Text
        text_lay = QVBoxLayout()
        text_lay.setSpacing(2)
        text_lay.setContentsMargins(0, 4, 0, 4)

        name_label = QLabel(self.meta.get("name", self.creature_id))
        name_label.setStyleSheet(f"color: {c}; font-size: 14px; font-weight: bold; background: transparent; border: none;")
        text_lay.addWidget(name_label)

        sub_label = QLabel(self.meta.get("subtitle", ""))
        sub_label.setStyleSheet("color: #8BA4B8; font-size: 10px; background: transparent; border: none;")
        text_lay.addWidget(sub_label)

        desc_label = QLabel(self.meta.get("description", "")[:60])
        desc_label.setStyleSheet("color: #506070; font-size: 9px; background: transparent; border: none;")
        desc_label.setWordWrap(True)
        text_lay.addWidget(desc_label)

        lay.addLayout(text_lay, 1)

    def set_active(self, active: bool):
        self._active = active
        self.setStyleSheet(self._active_style() if active else self._base_style())

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit(self.creature_id)
        super().mousePressEvent(event)


class CreatureSelector(QWidget):
    """Sidebar listing all four creature models."""

    creature_selected = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumWidth(240)
        self.setMaximumWidth(280)
        self.setStyleSheet("background: rgba(5, 13, 20, 220); border-right: 1px solid rgba(0, 242, 194, 30);")
        self._cards: dict[str, CreatureCard] = {}
        self._build_ui()

    def _build_ui(self):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(12, 16, 12, 12)
        lay.setSpacing(8)

        # Header
        header = QLabel("MODELS")
        header.setStyleSheet(
            "color: #00F2C2; font-size: 11px; font-weight: bold; letter-spacing: 2px; "
            "padding: 4px 0; background: transparent; border: none;"
        )
        lay.addWidget(header)

        # Scroll area for cards
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setStyleSheet("QScrollArea { background: transparent; border: none; }")

        container = QWidget()
        container.setStyleSheet("background: transparent;")
        self._card_lay = QVBoxLayout(container)
        self._card_lay.setContentsMargins(0, 0, 0, 0)
        self._card_lay.setSpacing(8)

        for creature_id, meta in CREATURES.items():
            card = CreatureCard(creature_id, meta)
            card.clicked.connect(self._on_card_clicked)
            self._cards[creature_id] = card
            self._card_lay.addWidget(card)

        self._card_lay.addStretch(1)
        scroll.setWidget(container)
        lay.addWidget(scroll, 1)

        # Footer
        footer = QLabel("Deep Sea AI")
        footer.setAlignment(Qt.AlignCenter)
        footer.setStyleSheet("color: #506070; font-size: 9px; padding: 8px; background: transparent; border: none;")
        lay.addWidget(footer)

    def _on_card_clicked(self, creature_id: str):
        for cid, card in self._cards.items():
            card.set_active(cid == creature_id)
        self.creature_selected.emit(creature_id)

    def set_active(self, creature_id: str):
        for cid, card in self._cards.items():
            card.set_active(cid == creature_id)
