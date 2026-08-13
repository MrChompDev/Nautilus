"""Riptide Audio - PySide6 Search View"""
from __future__ import annotations

from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from apps.RipTide.models import Platform
from apps.RipTide.ui.styles import Colors
from apps.RipTide.ui.widgets import TrackRow

C = Colors


class SearchView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._search_callback = None
        self._play_callback = None
        self._debounce = QTimer(self)
        self._debounce.setSingleShot(True)
        self._debounce.setInterval(400)
        self._debounce.timeout.connect(self._trigger_search)
        self._setup_ui()

    def _setup_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(16, 12, 16, 12)
        root.setSpacing(8)

        bar = QHBoxLayout()
        self._query = QLineEdit()
        self._query.setPlaceholderText("Search songs, artists, albums...")
        self._query.textChanged.connect(lambda _: self._debounce.start())
        self._query.returnPressed.connect(self._trigger_search)
        bar.addWidget(self._query, 1)

        self._platform = QComboBox()
        self._platform.addItem("All Platforms", None)
        for platform in Platform:
            self._platform.addItem(platform.display_name, platform)
        self._platform.currentIndexChanged.connect(lambda _: self._debounce.start())
        bar.addWidget(self._platform)
        root.addLayout(bar)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        content = QWidget()
        self._results_layout = QVBoxLayout(content)
        self._results_layout.setContentsMargins(8, 8, 8, 8)
        self._results_layout.setSpacing(4)
        self._results_layout.addStretch()
        scroll.setWidget(content)
        root.addWidget(scroll, 1)

        self._placeholder = QLabel(
            "Search across Spotify, YouTube and SoundCloud.\n"
            "Type a query above - results appear instantly.")
        self._placeholder.setAlignment(Qt.AlignCenter)
        self._placeholder.setMinimumHeight(200)
        self._placeholder.setStyleSheet(f"color: {C.TEXT_MUTED}; font-size: 13px; background: transparent;")
        self._results_layout.insertWidget(0, self._placeholder)

        self._status = QLabel("")
        self._status.setObjectName("muted")
        root.addWidget(self._status)

    # ── Callbacks ──

    def set_search_callback(self, cb):
        self._search_callback = cb

    def set_play_callback(self, cb):
        self._play_callback = cb

    # ── Search ──

    def _trigger_search(self) -> None:
        query = self._query.text().strip()
        if not query:
            return
        if not self._search_callback:
            return
        self._status.setText("Searching...")
        self._search_callback(query)

    def display_results(self, results: list) -> None:
        self._status.setText(f"{len(results)} result(s)")
        self._placeholder.hide()
        self._clear_results()
        for i, track in enumerate(results):
            row = TrackRow(track, i)
            if self._play_callback:
                row.play_clicked.connect(self._play_callback)
                row.activated.connect(lambda t, idx: self._play_callback(t))
            self._results_layout.insertWidget(self._results_layout.count() - 1, row)

    def display_error(self, message: str) -> None:
        self._status.setText("")
        self._placeholder.setText(message)
        self._placeholder.show()
        self._clear_results()

    def _clear_results(self) -> None:
        while self._results_layout.count() > 1:
            item = self._results_layout.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()
