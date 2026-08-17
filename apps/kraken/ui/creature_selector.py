"""Kraken AI — creature selector cards.

Card-based model picker with logos, names, and descriptions.
"""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
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
        self.setFixedHeight(76)
        self.setStyleSheet(self._base_style())
        self._build_ui()

    def _base_style(self):
        c = self.meta.get("color", "#00F2C2")
        return f"""
            QFrame {{
                background: rgba(14, 34, 56, 140);
                border: 1px solid rgba(255,255,255, 20);
                border-radius: 12px;
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
            }}
        """

    def _build_ui(self):
        lay = QHBoxLayout(self)
        lay.setContentsMargins(10, 8, 10, 8)
        lay.setSpacing(10)

        c = self.meta.get("color", "#00F2C2")

        # Logo circle
        logo_frame = QFrame()
        logo_frame.setFixedSize(44, 44)
        logo_frame.setStyleSheet(f"""
            QFrame {{
                background: {c}22;
                border: 1.5px solid {c}66;
                border-radius: 22px;
            }}
        """)
        logo_lay = QVBoxLayout(logo_frame)
        logo_lay.setContentsMargins(0, 0, 0, 0)
        logo_label = QLabel(self.meta.get("name", "?")[0])
        logo_label.setAlignment(Qt.AlignCenter)
        logo_label.setStyleSheet(f"color: {c}; font-size: 18px; font-weight: bold; background: transparent; border: none;")
        logo_lay.addWidget(logo_label)
        lay.addWidget(logo_frame)

        # Text
        text_lay = QVBoxLayout()
        text_lay.setSpacing(1)
        text_lay.setContentsMargins(0, 2, 0, 2)

        name_label = QLabel(self.meta.get("name", self.creature_id))
        name_label.setStyleSheet(f"color: {c}; font-size: 13px; font-weight: bold; background: transparent; border: none;")
        text_lay.addWidget(name_label)

        sub_label = QLabel(self.meta.get("subtitle", ""))
        sub_label.setStyleSheet("color: #8BA4B8; font-size: 10px; background: transparent; border: none;")
        text_lay.addWidget(sub_label)

        lay.addLayout(text_lay, 1)

    def set_active(self, active: bool):
        self._active = active
        self.setStyleSheet(self._active_style() if active else self._base_style())

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit(self.creature_id)
        super().mousePressEvent(event)


class CreatureSelector(QWidget):
    """Widget listing all four creature cards vertically."""

    creature_selected = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._cards: dict[str, CreatureCard] = {}
        self.setStyleSheet("background: transparent;")
        self._build_ui()

    def _build_ui(self):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(6)

        for creature_id, meta in CREATURES.items():
            card = CreatureCard(creature_id, meta)
            card.clicked.connect(self._on_card_clicked)
            self._cards[creature_id] = card
            lay.addWidget(card)

        lay.addStretch(1)

    def _on_card_clicked(self, creature_id: str):
        for cid, card in self._cards.items():
            card.set_active(cid == creature_id)
        self.creature_selected.emit(creature_id)

    def set_active(self, creature_id: str):
        for cid, card in self._cards.items():
            card.set_active(cid == creature_id)
