"""Riptide Audio - PySide6 Main Window"""
from __future__ import annotations

from PySide6.QtCore import QObject, Qt, QTimer, Signal
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QSplitter,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from apps.RipTide import config
from apps.RipTide.api.soundcloud import SoundCloudAPI
from apps.RipTide.api.spotify import SpotifyAPI
from apps.RipTide.api.youtube import YouTubeAPI
from apps.RipTide.audio.engine import AudioEngine
from apps.RipTide.audio.sfx import SFXEngine
from apps.RipTide.database.db import Database
from apps.RipTide.models import Platform, PlaybackState, Track
from apps.RipTide.ui.dashboard import DashboardView
from apps.RipTide.ui.playlist import PlaylistView
from apps.RipTide.ui.search import SearchView
from apps.RipTide.ui.settings import SettingsView
from apps.RipTide.ui.sfx_board import SFXBoardView
from apps.RipTide.ui.styles import Colors
from apps.RipTide.ui.widgets import NowPlayingBar
from apps.RipTide.workers.api_workers import DashboardWorker, SearchWorker
from core.theme import glass_bg_heavy, glass_edge

NAV_ITEMS = [
    ("Dashboard", "\U0001f4ca"),
    ("Search", "\U0001f50d"),
    ("Playlists", "\U0001f3b6"),
    ("SFX Board", "\U0001f50a"),
    ("Settings", "\u2699\ufe0f"),
]


class _AudioBridge(QObject):
    """Marshals engine callbacks (any thread) onto the Qt event loop."""

    track_changed = Signal(object)
    state_changed = Signal(object)
    position_changed = Signal(int, int)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(config.WINDOW_TITLE)
        self.setMinimumSize(config.WINDOW_MIN_WIDTH, config.WINDOW_MIN_HEIGHT)
        self.resize(1440, 900)

        self._db = Database()
        self._audio = AudioEngine()
        self._sfx = SFXEngine()

        self._api_clients: dict[Platform, object] = {}
        self._init_api_clients()

        self._bridge = _AudioBridge()
        self._bridge.track_changed.connect(self._on_track_changed)
        self._bridge.state_changed.connect(self._on_state_changed)
        self._bridge.position_changed.connect(self._on_position_changed)

        self._audio.on_track_changed = self._bridge.track_changed.emit
        self._audio.on_state_changed = self._bridge.state_changed.emit
        self._audio.on_position_changed = self._bridge.position_changed.emit

        self._panels: list = []
        self._current_panel = 0

        self._setup_ui()
        self._setup_connections()

        self._refresh_timer = QTimer(self)
        self._refresh_timer.timeout.connect(self._refresh_dashboard)
        self._refresh_timer.start(60000)

        self._refresh_dashboard()

    # ── API clients ──

    def _init_api_clients(self) -> None:
        self._api_clients.clear()
        accounts = self._db.get_accounts()
        for account in accounts:
            if account.platform == Platform.SPOTIFY:
                client = SpotifyAPI(account)
            elif account.platform == Platform.YOUTUBE:
                client = YouTubeAPI(account)
            elif account.platform == Platform.SOUNDCLOUD:
                client = SoundCloudAPI(account)
            else:
                continue
            self._api_clients[account.platform] = client
            self._audio.register_api_client(account.platform, client)

    def refresh_accounts(self) -> None:
        """Re-read the DB and rebuild API clients after Settings changes."""
        self._init_api_clients()
        self._refresh_sidebar_accounts()
        self._settings.refresh_accounts()
        if self._api_clients:
            self._refresh_dashboard()

    # ── UI ──

    def _setup_ui(self) -> None:
        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        body = QSplitter(Qt.Horizontal)
        body.setHandleWidth(1)
        body.setChildrenCollapsible(False)

        sidebar = self._create_sidebar()
        body.addWidget(sidebar)

        right = QWidget()
        right_layout = QVBoxLayout(right)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(0)

        self._stack = QStackedWidget()
        self._dashboard = DashboardView()
        self._search = SearchView()
        self._playlists = PlaylistView(self._db)
        self._sfx_board = SFXBoardView(self._db, self._sfx)
        self._settings = SettingsView(self._db)
        self._settings.on_accounts_changed = self.refresh_accounts

        self._panels = [
            self._dashboard, self._search, self._playlists,
            self._sfx_board, self._settings,
        ]
        for panel in self._panels:
            self._stack.addWidget(panel)

        right_layout.addWidget(self._stack, 1)

        self._player_bar = NowPlayingBar()
        right_layout.addWidget(self._player_bar)

        body.addWidget(right)
        body.setStretchFactor(1, 1)
        body.setSizes([220, 1220])
        root.addWidget(body, 1)

    def _create_sidebar(self) -> QWidget:
        side = QWidget()
        side.setFixedWidth(220)
        side.setStyleSheet(f"background: {glass_bg_heavy(210)}; border-right: 1px solid {glass_edge()};")
        lay = QVBoxLayout(side)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)

        logo = QLabel("  Riptide Audio")
        logo.setFixedHeight(56)
        logo.setStyleSheet(
            f"color: {Colors.ACCENT}; font-size: 16px; font-weight: bold; "
            f"background: {glass_bg_heavy(210)};")
        lay.addWidget(logo)

        self._nav = QListWidget()
        self._nav.setObjectName("sidebar")
        self._nav.currentRowChanged.connect(self._navigate)

        for label, _ in NAV_ITEMS:
            item = QListWidgetItem(f"  {label}")
            self._nav.addItem(item)

        self._sidebar_account_labels: list[QListWidgetItem] = []
        self._refresh_sidebar_accounts()
        lay.addWidget(self._nav, 1)

        ver = QLabel(f"  v{config.APP_VERSION}")
        ver.setStyleSheet(f"color: {Colors.TEXT_MUTED}; font-size: 9px; "
                          f"background: {glass_bg_heavy(210)}; padding: 6px;")
        lay.addWidget(ver)

        self._nav.setCurrentRow(0)
        return side

    def _refresh_sidebar_accounts(self) -> None:
        for item in self._sidebar_account_labels:
            row = self._nav.row(item)
            if row >= 0:
                self._nav.takeItem(row)
        self._sidebar_account_labels = []

        accounts = self._db.get_accounts()
        for account in accounts[:3]:
            item = QListWidgetItem(f"   {account.display_name[:20]}")
            item.setFlags(Qt.NoItemFlags)
            item.setForeground(QColor(account.platform.color))
            self._nav.addItem(item)
            self._sidebar_account_labels.append(item)
        if not accounts:
            item = QListWidgetItem("   No accounts")
            item.setFlags(Qt.NoItemFlags)
            item.setForeground(QColor(Colors.TEXT_MUTED))
            self._nav.addItem(item)
            self._sidebar_account_labels.append(item)

    # ── Navigation ──

    def _navigate(self, row: int) -> None:
        if 0 <= row < len(self._panels):
            self._stack.setCurrentIndex(row)
            self._current_panel = row

    # ── Wiring ──

    def _setup_connections(self) -> None:
        self._search.set_search_callback(self._perform_search)
        self._search.set_play_callback(self._play_track_direct)
        self._dashboard.set_play_track_callback(self._play_track_direct)
        self._dashboard.set_play_artist_callback(self._play_artist_direct)
        self._dashboard.set_play_playlist_callback(self._play_playlist_context)
        self._playlists.set_play_callback(self._play_track_direct)
        self._playlists.set_play_playlist_callback(self._play_playlist_direct)

        self._player_bar.bind_play_pause(self._toggle_playback)
        self._player_bar.bind_next(lambda: self._audio.next_track())
        self._player_bar.bind_prev(lambda: self._audio.previous_track())
        self._player_bar.bind_seek(lambda pos: self._audio.seek(pos))
        self._player_bar.bind_volume(lambda vol: self._audio.set_volume(vol))

    def _perform_search(self, query: str) -> None:
        if not self._api_clients:
            self._search.display_error("No accounts connected. Go to Settings to add one.")
            return
        worker = SearchWorker(
            query,
            self._api_clients,
            on_done=self._search.display_results,
            on_error=self._search.display_error,
        )
        worker.start()

    # ── Playback ──

    def _play_track_direct(self, track: Track) -> None:
        client = self._api_clients.get(track.platform)
        account = client.account if client and hasattr(client, "account") else None
        self._audio.play_track(track, account)

    def _play_artist_direct(self, artist) -> None:
        client = self._api_clients.get(Platform.SPOTIFY)
        if client and hasattr(client, "start_artist_playback"):
            try:
                client.start_artist_playback(artist.id)
            except Exception as e:
                print(f"Error playing artist: {e}")

    def _play_playlist_context(self, playlist) -> None:
        client = self._api_clients.get(Platform.SPOTIFY)
        if client and hasattr(client, "start_playlist_playback"):
            try:
                playlist_id = playlist.get("id", "") if isinstance(playlist, dict) else playlist.id
                client.start_playlist_playback(playlist_id)
            except Exception as e:
                print(f"Error playing playlist: {e}")

    def _play_playlist_direct(self, tracks: list[Track]) -> None:
        if tracks:
            self._audio.play_playlist(tracks)

    def _toggle_playback(self) -> None:
        if self._audio.state == PlaybackState.PLAYING:
            self._audio.pause()
        elif self._audio.state == PlaybackState.PAUSED:
            self._audio.resume()

    # ── Engine callbacks (already on the GUI thread via the bridge) ──

    def _on_track_changed(self, track: Track | None) -> None:
        self._player_bar.update_track(track)
        if track:
            self.setWindowTitle(f"{track.artist} - {track.title} | {config.APP_NAME}")
        else:
            self.setWindowTitle(config.WINDOW_TITLE)

    def _on_state_changed(self, state: PlaybackState) -> None:
        self._player_bar.update_state(state == PlaybackState.PLAYING)

    def _on_position_changed(self, position_ms: int, duration_ms: int) -> None:
        self._player_bar.update_position(position_ms, duration_ms)

    # ── Dashboard refresh ──

    def _refresh_dashboard(self) -> None:
        if not self._api_clients:
            self._dashboard.update_status("No accounts connected")
            return

        accounts = self._db.get_accounts()
        platforms = ", ".join(set(a.platform.display_name for a in accounts))
        self._dashboard.update_status(f"Loading... ({platforms})")

        worker = DashboardWorker(
            self._api_clients,
            on_done=self._on_dashboard_loaded,
            on_error=self._on_dashboard_error,
        )
        worker.start()

    def _on_dashboard_loaded(self, data: dict) -> None:
        self._dashboard.update_dashboard(data)
        accounts = self._db.get_accounts()
        count = len(accounts)
        platforms = ", ".join(set(a.platform.display_name for a in accounts))
        self._dashboard.update_status(
            f"{count} account(s): {platforms}" if count else "No accounts connected"
        )

    def _on_dashboard_error(self, error: str) -> None:
        self._dashboard.update_status(f"Error: {error}")

    def closeEvent(self, event) -> None:
        self._refresh_timer.stop()
        self._audio.cleanup()
        self._sfx.cleanup()
        self._db.close()
        event.accept()
