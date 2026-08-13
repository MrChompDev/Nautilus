"""Riptide Audio - PySide6 SFX Board View"""
from __future__ import annotations

import os

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFileDialog,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from apps.RipTide.database.db import Database
from apps.RipTide.ui.styles import Colors

C = Colors


class SFXBoardView(QWidget):
    def __init__(self, db: Database, sfx_engine, parent=None):
        super().__init__(parent)
        self._db = db
        self._sfx = sfx_engine
        self._setup_ui()
        self.refresh()

    def _setup_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(16, 12, 16, 12)
        root.setSpacing(8)

        header = QHBoxLayout()
        title = QLabel("SFX Board")
        title.setObjectName("page_title")
        header.addWidget(title)
        header.addStretch()

        self._import_btn = QPushButton("+ Add SFX")
        self._import_btn.setObjectName("accent_btn")
        self._import_btn.clicked.connect(self._import_clip)
        header.addWidget(self._import_btn)
        root.addLayout(header)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        content = QWidget()
        self._grid = QGridLayout(content)
        self._grid.setContentsMargins(8, 8, 8, 8)
        self._grid.setSpacing(10)
        scroll.setWidget(content)
        root.addWidget(scroll, 1)

        self._empty = QLabel(
            "No sound effects yet.\nClick '+ Add SFX' to load audio clips you can "
            "fire instantly while you play music.")
        self._empty.setAlignment(Qt.AlignCenter)
        self._empty.setMinimumHeight(180)
        self._empty.setStyleSheet(f"color: {C.TEXT_MUTED}; font-size: 13px; background: transparent;")
        root.addWidget(self._empty)

    def refresh(self) -> None:
        self._clear_grid()
        clips = self._db.get_sfx_clips()
        self._empty.setVisible(not clips)
        cols = 4
        for i, clip in enumerate(clips):
            btn = self._clip_button(clip)
            self._grid.addWidget(btn, i // cols, i % cols)

    def _clip_button(self, clip) -> QPushButton:
        name = clip.name
        btn = QPushButton(name[:18] + ("..." if len(name) > 18 else ""))
        btn.setObjectName("accent_btn")
        btn.setFixedSize(150, 90)
        btn.setToolTip(clip.file_path)
        btn.clicked.connect(lambda _, cid=clip.id: self._trigger(cid))
        return btn

    def _trigger(self, clip_id: int) -> None:
        clip = next((c for c in self._db.get_sfx_clips() if c.id == clip_id), None)
        if clip:
            self._sfx.trigger_clip(clip)

    def _import_clip(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self, "Import Sound Effect", "",
            "Audio Files (*.wav *.mp3 *.ogg *.flac);;All Files (*)")
        if not path:
            return
        try:
            from apps.RipTide.models import SFXClip
            self._db.add_sfx_clip(SFXClip(name=os.path.basename(path), file_path=path))
        except Exception as e:
            print(f"Failed to import SFX: {e}")
            return
        self.refresh()

    def _clear_grid(self) -> None:
        while self._grid.count():
            item = self._grid.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()
