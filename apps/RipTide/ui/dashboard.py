"""Riptide Audio - PySide6 Dashboard View"""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from apps.RipTide.ui.styles import Colors
from apps.RipTide.ui.widgets import ArtistCard, PlaylistCard, TrackRow

C = Colors


def _title(text: str) -> QLabel:
    lbl = QLabel(text)
    lbl.setObjectName("page_title")
    return lbl


def _section(text: str) -> QLabel:
    lbl = QLabel(text)
    lbl.setObjectName("section_title")
    return lbl


class DashboardView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._play_track_callback = None
        self._play_artist_callback = None
        self._play_playlist_callback = None
        self._setup_ui()

    def _setup_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(16, 12, 16, 12)
        root.setSpacing(8)

        header = QHBoxLayout()
        header.addWidget(_title("Dashboard"))
        header.addStretch()
        self._status = QLabel("")
        self._status.setObjectName("muted")
        header.addWidget(self._status)
        root.addLayout(header)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        content = QWidget()
        self._content_layout = QVBoxLayout(content)
        self._content_layout.setContentsMargins(8, 8, 8, 8)
        self._content_layout.setSpacing(4)
        self._content_layout.addStretch()
        scroll.setWidget(content)
        root.addWidget(scroll, 1)

        self._welcome = QLabel(
            "Welcome to Riptide Audio\nConnect your accounts in Settings to get started.")
        self._welcome.setAlignment(Qt.AlignCenter)
        self._welcome.setMinimumHeight(200)
        self._welcome.setStyleSheet(f"color: {C.TEXT_MUTED}; font-size: 14px; background: transparent;")
        self._content_layout.insertWidget(0, self._welcome)

        # Sections (inserted above the stretch at the end)
        self._artists_label = _section("Your Top Artists")
        self._artists_label.hide()
        self._content_layout.insertWidget(0, self._artists_label)
        self._artists_row = QHBoxLayout()
        self._artists_wrap = QWidget()
        self._artists_wrap.setLayout(self._artists_row)
        self._artists_wrap.hide()
        self._content_layout.insertWidget(0, self._artists_wrap)

        self._playlists_label = _section("Your Playlists")
        self._playlists_label.hide()
        self._content_layout.insertWidget(0, self._playlists_label)
        self._playlists_box = QVBoxLayout()
        self._playlists_wrap = QWidget()
        self._playlists_wrap.setLayout(self._playlists_box)
        self._playlists_wrap.hide()
        self._content_layout.insertWidget(0, self._playlists_wrap)

        self._recent_label = _section("Recently Played")
        self._recent_label.hide()
        self._content_layout.insertWidget(0, self._recent_label)
        self._recent_box = QVBoxLayout()
        self._recent_wrap = QWidget()
        self._recent_wrap.setLayout(self._recent_box)
        self._recent_wrap.hide()
        self._content_layout.insertWidget(0, self._recent_wrap)

        self._top_label = _section("Your Top Tracks")
        self._top_label.hide()
        self._content_layout.insertWidget(0, self._top_label)
        self._top_box = QVBoxLayout()
        self._top_wrap = QWidget()
        self._top_wrap.setLayout(self._top_box)
        self._top_wrap.hide()
        self._content_layout.insertWidget(0, self._top_wrap)

    # ── Callbacks ──

    def set_play_track_callback(self, cb):
        self._play_track_callback = cb

    def set_play_artist_callback(self, cb):
        self._play_artist_callback = cb

    def set_play_playlist_callback(self, cb):
        self._play_playlist_callback = cb

    # ── Updates ──

    def update_status(self, text: str) -> None:
        self._status.setText(text)

    def update_dashboard(self, data: dict) -> None:
        self._welcome.hide()
        self.clear()

        top_artists = data.get("top_artists", [])
        if top_artists:
            self._show_artists(top_artists)

        playlists = data.get("playlists", [])
        if playlists:
            self._show_playlists(playlists)

        recently_played = data.get("recently_played", [])
        if recently_played:
            self._show_tracks(recently_played, self._recent_label, self._recent_wrap, self._recent_box)

        top_tracks = data.get("top_tracks", [])
        if top_tracks:
            self._show_tracks(top_tracks, self._top_label, self._top_wrap, self._top_box)

    def _show_artists(self, artists) -> None:
        self._clear_layout(self._artists_row)
        self._artists_label.show()
        self._artists_wrap.show()
        for artist in artists[:10]:
            card = ArtistCard(artist)
            if self._play_artist_callback:
                card.clicked.connect(self._play_artist_callback)
            self._artists_row.addWidget(card)
        self._artists_row.addStretch()

    def _show_playlists(self, playlists) -> None:
        self._clear_layout(self._playlists_box)
        self._playlists_label.show()
        self._playlists_wrap.show()
        cols = 5
        row = None
        for i, pl in enumerate(playlists[:12]):
            if i % cols == 0:
                row = QHBoxLayout()
                row.addStretch()
                self._playlists_box.addLayout(row)
            card = PlaylistCard(pl)
            if self._play_playlist_callback:
                card.clicked.connect(self._play_playlist_callback)
            row.addWidget(card)
            row.addStretch()

    def _show_tracks(self, tracks, label, wrap, box) -> None:
        self._clear_layout(box)
        label.show()
        wrap.show()
        for i, track in enumerate(tracks[:10]):
            row = TrackRow(track, i)
            if self._play_track_callback:
                row.play_clicked.connect(self._play_track_callback)
                row.activated.connect(lambda t, idx: self._play_track_callback(t))
            box.addWidget(row)

    def clear(self) -> None:
        self._artists_label.hide()
        self._artists_wrap.hide()
        self._playlists_label.hide()
        self._playlists_wrap.hide()
        self._recent_label.hide()
        self._recent_wrap.hide()
        self._top_label.hide()
        self._top_wrap.hide()
        self._clear_layout(self._artists_row)
        self._clear_layout(self._playlists_box)
        self._clear_layout(self._recent_box)
        self._clear_layout(self._top_box)
        self._welcome.show()

    @staticmethod
    def _clear_layout(layout) -> None:
        while layout.count():
            item = layout.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()
