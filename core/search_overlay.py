"""Nautilus Search Overlay — Ctrl+Space launcher + local search + web handoff."""

import subprocess

from PySide6.QtCore import Qt
from PySide6.QtGui import QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QVBoxLayout,
)

from core import search as search_index
from core.launcher import APP_MANIFEST
from core.theme import COLORS, FONTS, SPACING

APP_TAG = "[APP] "
FILE_TAG = "[FILE] "
WEB_TAG = "[WEB] "


def _item_style():
    return f"""
        QFrame#searchOverlay {{
            background-color: {COLORS['slate_navy']};
            border: 1px solid {COLORS['seafoam_deep']};
            border-radius: 4px;
        }}
        QLineEdit {{
            background-color: {COLORS['void_black']};
            color: {COLORS['hd_white']};
            border: 1px solid {COLORS['border']};
            border-radius: 4px;
            padding: 8px 12px;
            font-family: "{FONTS['ui']}";
            font-size: {FONTS['size_xl']}px;
        }}
        QListWidget {{
            background-color: transparent;
            color: {COLORS['hd_white']};
            border: none;
            font-family: "{FONTS['ui']}";
            font-size: {FONTS['size_md']}px;
        }}
        QListWidget::item {{
            padding: 6px 10px;
            border-radius: 4px;
        }}
        QListWidget::item:selected {{
            background-color: {COLORS['seafoam_deep']};
            color: {COLORS['hd_white']};
        }}
        QLabel {{ color: {COLORS['text_muted']}; }}
    """


class SearchOverlay(QFrame):
    def __init__(self, launcher, parent=None):
        super().__init__(parent)
        self._launcher = launcher
        self._results = []

        self.setObjectName("searchOverlay")
        self.setStyleSheet(_item_style())
        self.setFixedSize(680, 480)
        self.hide()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(SPACING["lg"], SPACING["lg"], SPACING["lg"], SPACING["lg"])
        layout.setSpacing(SPACING["md"])

        header = QHBoxLayout()
        title = QLabel("Search")
        title.setStyleSheet(
            f"color: {COLORS['seafoam']}; font-weight: bold; "
            f"font-size: {FONTS['size_xl']}px; letter-spacing: 1px;"
        )
        hint = QLabel(
            f"engine: {search_index.SEARCH_ENGINES[search_index.get_engine()][0]}"
        )
        hint.setStyleSheet(f"font-size: {FONTS['size_xs']}px;")
        self._hint = hint
        header.addWidget(title)
        header.addStretch()
        header.addWidget(hint)
        layout.addLayout(header)

        self._input = QLineEdit()
        self._input.setPlaceholderText(
            "Search apps, files, and the web  ·  Enter to open  ·  Esc to close"
        )
        self._input.textChanged.connect(self._on_text_changed)
        layout.addWidget(self._input)

        self._list = QListWidget()
        layout.addWidget(self._list, 1)

        self._list.itemActivated.connect(self._activate)
        self._input.returnPressed.connect(self._activate_selected)

        close_shortcut = QShortcut(QKeySequence("Escape"), self)
        close_shortcut.activated.connect(self.hide)

    # ── behaviour ────────────────────────────────────

    def show_overlay(self):
        self._list.clear()
        self._results = []
        self._input.clear()
        self.show()
        self.raise_()
        self._input.setFocus()

    def _on_text_changed(self, text: str):
        results = search_index.search_all(text.strip(), APP_MANIFEST) if text.strip() else []
        if text.strip() and not any(r["kind"] == "web" for r in results):
            results.append(search_index.web_result(text.strip()))
        self._results = results

        self._list.blockSignals(True)
        self._list.clear()
        for r in results:
            tag = {"app": APP_TAG, "file": FILE_TAG, "web": WEB_TAG}[r["kind"]]
            item = QListWidgetItem(f"{tag}{r['title']}")
            item.setData(Qt.ItemDataRole.UserRole, r)
            item.setToolTip(r.get("detail", r.get("url", "")))
            self._list.addItem(item)
        self._list.blockSignals(False)
        if self._list.count():
            self._list.setCurrentRow(0)

    def _activate_selected(self):
        row = self._list.currentRow()
        if row < 0 and self._list.count():
            row = 0
        item = self._list.item(row)
        if item:
            self._activate(item)

    def _activate(self, item):
        data = item.data(Qt.ItemDataRole.UserRole)
        if not data:
            return
        self.hide()
        kind = data["kind"]
        if kind == "app":
            self._launcher.launch(data["app_id"])
        elif kind == "file":
            self._open_path(data["path"])
        elif kind == "web":
            self._open_web(data["url"])

    def _open_path(self, path: str):
        try:
            subprocess.Popen(
                ["xdg-open", path],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            )
        except OSError:
            pass

    def _open_web(self, url: str):
        self._launcher.launch("surfline", [url])
