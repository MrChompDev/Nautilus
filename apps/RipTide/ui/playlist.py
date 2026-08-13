"""Riptide Audio - PySide6 Playlist View"""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from apps.RipTide.database.db import Database
from apps.RipTide.ui.styles import Colors
from apps.RipTide.ui.widgets import TrackRow

C = Colors


class PlaylistView(QWidget):
    def __init__(self, db: Database, parent=None):
        super().__init__(parent)
        self._db = db
        self._play_callback = None
        self._play_playlist_callback = None
        self._playlist_id: int | None = None
        self._setup_ui()

    def _setup_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(16, 12, 16, 12)
        root.setSpacing(8)

        header = QHBoxLayout()
        self._title = QLabel("Playlists")
        self._title.setObjectName("page_title")
        header.addWidget(self._title)
        header.addStretch()

        self._play_all = QPushButton("Play All")
        self._play_all.setObjectName("accent_btn")
        self._play_all.clicked.connect(self._play_all_clicked)
        self._play_all.hide()
        header.addWidget(self._play_all)

        self._back = QPushButton("\u2190 Back")
        self._back.setObjectName("ghost_btn")
        self._back.clicked.connect(self._show_list)
        self._back.hide()
        header.addWidget(self._back)
        root.addLayout(header)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        content = QWidget()
        self._list_layout = QVBoxLayout(content)
        self._list_layout.setContentsMargins(8, 8, 8, 8)
        self._list_layout.setSpacing(4)
        self._list_layout.addStretch()
        scroll.setWidget(content)
        root.addWidget(scroll, 1)

        self._show_list()

    # ── Callbacks ──

    def set_play_callback(self, cb):
        self._play_callback = cb

    def set_play_playlist_callback(self, cb):
        self._play_playlist_callback = cb

    # ── UI helpers ──

    def refresh(self) -> None:
        if self._playlist_id is None:
            self._show_list()
        else:
            self._show_playlist(self._playlist_id)

    def _show_list(self) -> None:
        self._playlist_id = None
        self._title.setText("Playlists")
        self._back.hide()
        self._play_all.hide()
        self._clear_layout(self._list_layout)
        playlists = self._db.get_playlists()
        if not playlists:
            lbl = QLabel("No playlists yet.\nCreate one from the Search results (right-click / menu).")
            lbl.setStyleSheet(f"color: {C.TEXT_MUTED}; font-size: 13px; padding: 20px; background: transparent;")
            self._list_layout.addWidget(lbl)
            return
        for playlist in playlists:
            row = self._playlist_row(playlist)
            self._list_layout.addWidget(row)
        self._list_layout.addStretch()

    def _playlist_row(self, playlist) -> QWidget:
        frame = QFrame()
        frame.setObjectName("card")
        frame.setFixedHeight(56)
        frame.setCursor(Qt.PointingHandCursor)
        lay = QHBoxLayout(frame)
        lay.setContentsMargins(12, 6, 12, 6)

        name = QLabel(playlist.name)
        name.setStyleSheet(f"color: {C.TEXT_PRIMARY}; font-weight: bold; background: transparent;")
        lay.addWidget(name, 1)

        count = QLabel(f"{playlist.track_count} tracks")
        count.setStyleSheet(f"color: {C.TEXT_MUTED}; background: transparent;")
        lay.addWidget(count)

        open_btn = QPushButton("\U0001F4C2")
        open_btn.setObjectName("ghost_btn")
        open_btn.setToolTip("Open playlist")
        open_btn.clicked.connect(lambda _, pid=playlist.id: self._show_playlist(pid))
        lay.addWidget(open_btn)

        del_btn = QPushButton("\U0001F5D1")
        del_btn.setObjectName("danger_btn")
        del_btn.setToolTip("Delete playlist")
        del_btn.clicked.connect(lambda _, pid=playlist.id: self._delete_playlist(pid))
        lay.addWidget(del_btn)

        frame.mousePressEvent = lambda event, pid=playlist.id: self._show_playlist(pid)
        return frame

    def _show_playlist(self, playlist_id: int) -> None:
        self._playlist_id = playlist_id
        playlist = next((p for p in self._db.get_playlists() if p.id == playlist_id), None)
        self._title.setText(f"Playlist: {playlist.name if playlist else ''}")
        self._back.show()
        self._play_all.show()
        self._clear_layout(self._list_layout)

        tracks = self._db.get_playlist_tracks(playlist_id)
        if not tracks:
            lbl = QLabel("This playlist is empty.")
            lbl.setStyleSheet(f"color: {C.TEXT_MUTED}; font-size: 13px; padding: 20px; background: transparent;")
            self._list_layout.addWidget(lbl)
            return
        for i, track in enumerate(tracks):
            row = TrackRow(track, i)
            row.setFixedHeight(44)
            if self._play_callback:
                row.play_clicked.connect(self._play_callback)
                row.activated.connect(lambda t, idx: self._play_callback(t))
            self._list_layout.addWidget(row)
        self._list_layout.addStretch()

    def _play_all_clicked(self) -> None:
        if not self._playlist_id or not self._play_playlist_callback:
            return
        tracks = self._db.get_playlist_tracks(self._playlist_id)
        if tracks:
            self._play_playlist_callback(tracks)

    def _delete_playlist(self, playlist_id: int) -> None:
        answer = QMessageBox.question(
            self, "Delete playlist", "Delete this playlist?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if answer == QMessageBox.Yes:
            self._db.delete_playlist(playlist_id)
            self._show_list()

    @staticmethod
    def _clear_layout(layout) -> None:
        while layout.count():
            item = layout.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()
