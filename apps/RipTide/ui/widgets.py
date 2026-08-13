"""Riptide Audio - PySide6 reusable widgets: track rows, cards, now-playing bar."""

from __future__ import annotations

from PySide6.QtCore import QObject, Qt, QUrl, Signal
from PySide6.QtGui import QPixmap
from PySide6.QtNetwork import QNetworkAccessManager, QNetworkRequest
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSlider,
    QVBoxLayout,
)

from apps.RipTide.models import Track
from apps.RipTide.ui.styles import Colors

C = Colors


class ThumbLoader(QObject):
    """Fetches remote thumbnails off-thread and hands QPixmaps to the GUI thread."""

    loaded = Signal(str, QPixmap)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._nam = QNetworkAccessManager(self)
        self._nam.finished.connect(self._on_finished)
        self._cache: dict[str, QPixmap] = {}

    def get(self, key: str, url: str, size: int = 36):
        if key in self._cache:
            self.loaded.emit(key, self._cache[key])
            return
        req = QNetworkRequest(QUrl(url))
        req.setRawHeader(b"User-Agent", b"RiptideAudio/3.0")
        req.setAttribute(QNetworkRequest.User, (key, size))
        self._nam.get(req)

    def _on_finished(self, reply):
        key, size = reply.request().attribute(QNetworkRequest.User)
        data = bytes(reply.readAll())
        reply.deleteLater()
        if not data:
            return
        pix = QPixmap()
        if not pix.loadFromData(data):
            return
        pix = pix.scaled(size, size, Qt.KeepAspectRatioByExpanding,
                         Qt.SmoothTransformation)
        self._cache[key] = pix
        self.loaded.emit(key, pix)


THUMB_LOADER = None


def thumb_loader():
    global THUMB_LOADER
    if THUMB_LOADER is None:
        THUMB_LOADER = ThumbLoader()
    return THUMB_LOADER


def _platform_badge(platform) -> QLabel:
    badge = QLabel(platform.display_name[0])
    badge.setFixedSize(18, 18)
    badge.setAlignment(Qt.AlignCenter)
    color = platform.color
    badge.setStyleSheet(
        f"background-color: {color}; color: #ffffff; font-size: 9px; font-weight: bold; "
        f"border-radius: 9px;")
    return badge


def _thumb_label(key: str, url: str, size: int = 36) -> QLabel:
    lbl = QLabel()
    lbl.setFixedSize(size, size)
    lbl.setAlignment(Qt.AlignCenter)
    lbl.setStyleSheet(
        f"background-color: {C.BG_TERTIARY}; color: {C.TEXT_MUTED}; "
        f"border-radius: {size // 2}px; font-size: {size // 2}px;")
    lbl.setText("\U0001F3B5")
    if url:
        thumb_loader().get(key, url, size)
        thumb_loader().loaded.connect(lambda k, pix, target=lbl, s=size, kk=key:
                                      target.setPixmap(pix) if k == kk else None)
    return lbl


class TrackRow(QFrame):
    """A playable row for a track: index, platform badge, art, title/artist, duration."""

    play_clicked = Signal(object)
    activated = Signal(object, int)

    def __init__(self, track: Track, index: int = 0, parent=None):
        super().__init__(parent)
        self.track = track
        self.index = index
        self.setObjectName("trackrow")
        self.setFixedHeight(52)
        self.setCursor(Qt.PointingHandCursor)

        lay = QHBoxLayout(self)
        lay.setContentsMargins(10, 6, 10, 6)
        lay.setSpacing(10)

        idx = QLabel(f"{index + 1}")
        idx.setFixedWidth(20)
        idx.setStyleSheet(f"color: {C.TEXT_MUTED}; background: transparent;")
        lay.addWidget(idx)

        lay.addWidget(_platform_badge(track.platform))

        art = _thumb_label(f"thumb_{track.platform_id}", track.thumbnail_url, 36)
        lay.addWidget(art)

        text = QVBoxLayout()
        text.setSpacing(0)
        title = QLabel(track.title[:55])
        title.setStyleSheet(f"color: {C.TEXT_PRIMARY}; font-weight: bold; background: transparent;")
        text.addWidget(title)
        artist = QLabel(track.artist[:45])
        artist.setStyleSheet(f"color: {C.TEXT_SECONDARY}; font-size: 10px; background: transparent;")
        text.addWidget(artist)
        lay.addLayout(text, 1)

        album = QLabel(track.album[:28])
        album.setFixedWidth(200)
        album.setStyleSheet(f"color: {C.TEXT_MUTED}; background: transparent;")
        lay.addWidget(album)

        dur = QLabel(track.duration_str)
        dur.setFixedWidth(48)
        dur.setStyleSheet(f"color: {C.TEXT_MUTED}; background: transparent;")
        lay.addWidget(dur)

        play = QPushButton("\u25B6")
        play.setObjectName("ghost_btn")
        play.setFixedSize(28, 28)
        play.setToolTip("Play")
        play.clicked.connect(lambda: self.play_clicked.emit(self.track))
        lay.addWidget(play)

    def mouseDoubleClickEvent(self, event):
        self.activated.emit(self.track, self.index)


class ArtistCard(QFrame):
    clicked = Signal(object)

    def __init__(self, artist, parent=None):
        super().__init__(parent)
        self.artist = artist
        self.setObjectName("card")
        self.setFixedSize(130, 170)
        self.setCursor(Qt.PointingHandCursor)

        lay = QVBoxLayout(self)
        lay.setContentsMargins(8, 8, 8, 6)
        lay.setSpacing(4)

        art = _thumb_label(f"artist_{getattr(artist, 'id', '')}", getattr(artist, "image_url", ""), 100)
        art.setFixedSize(100, 100)
        lay.addWidget(art, 0, Qt.AlignHCenter)

        name = getattr(artist, "name", "Unknown")
        name_lbl = QLabel(name[:16] + ("..." if len(name) > 16 else ""))
        name_lbl.setAlignment(Qt.AlignCenter)
        name_lbl.setStyleSheet(f"color: {C.TEXT_PRIMARY}; font-weight: bold; background: transparent;")
        lay.addWidget(name_lbl)

        genre = (artist.genres[0].title() if getattr(artist, "genres", None) else "Artist")
        genre_lbl = QLabel(genre)
        genre_lbl.setAlignment(Qt.AlignCenter)
        genre_lbl.setStyleSheet(f"color: {C.TEXT_MUTED}; font-size: 10px; background: transparent;")
        lay.addWidget(genre_lbl)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit(self.artist)


class PlaylistCard(QFrame):
    clicked = Signal(object)

    def __init__(self, playlist, parent=None):
        super().__init__(parent)
        self.playlist = playlist
        self.setObjectName("card")
        self.setFixedSize(160, 200)
        self.setCursor(Qt.PointingHandCursor)

        images = playlist.get("images", []) if isinstance(playlist, dict) else []
        img_url = images[0]["url"] if images else ""
        pid = playlist.get("id", "") if isinstance(playlist, dict) else ""

        lay = QVBoxLayout(self)
        lay.setContentsMargins(8, 8, 8, 6)
        lay.setSpacing(4)

        art = _thumb_label(f"pl_{pid}", img_url, 144)
        art.setFixedSize(144, 144)
        lay.addWidget(art)

        name = playlist.get("name", "")[:22]
        name_lbl = QLabel(name)
        name_lbl.setStyleSheet(f"color: {C.TEXT_PRIMARY}; font-weight: bold; background: transparent;")
        lay.addWidget(name_lbl)

        tc = (playlist.get("tracks") or {}).get("total", 0)
        owner = (playlist.get("owner") or {}).get("display_name", "")
        detail = f"{tc} tracks" + (f" \u00b7 {owner}" if owner else "")
        det = QLabel(detail)
        det.setStyleSheet(f"color: {C.TEXT_MUTED}; font-size: 10px; background: transparent;")
        lay.addWidget(det)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit(self.playlist)


class NowPlayingBar(QFrame):
    """Bottom transport bar: track info, prev/play/next, seek, volume."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("nowplaying")
        self.setFixedHeight(80)
        self._playing = False
        self._track: Track | None = None
        self._position_ms = 0
        self._duration_ms = 0
        self._volume = 80
        self._callbacks = {"play_pause": [], "next": [], "prev": [], "seek": [], "volume": []}

        lay = QHBoxLayout(self)
        lay.setContentsMargins(16, 10, 16, 10)
        lay.setSpacing(12)

        self._title = QLabel("No track selected")
        self._title.setFixedWidth(260)
        self._title.setStyleSheet(f"color: {C.TEXT_MUTED}; font-size: 12px; background: transparent;")
        lay.addWidget(self._title)

        self._artist = QLabel("")
        self._artist.setFixedWidth(200)
        self._artist.setStyleSheet(f"color: {C.TEXT_SECONDARY}; font-size: 10px; background: transparent;")
        lay.addWidget(self._artist)

        prev = self._transport_btn("\u23EE", "Previous")
        prev.clicked.connect(lambda: self._emit("prev"))
        lay.addWidget(prev)

        self._play_btn = QPushButton("\u25B6")
        self._play_btn.setObjectName("accent_btn")
        self._play_btn.setFixedSize(40, 40)
        self._play_btn.setToolTip("Play / Pause")
        self._play_btn.clicked.connect(lambda: self._emit("play_pause"))
        lay.addWidget(self._play_btn)

        nxt = self._transport_btn("\u23ED", "Next")
        nxt.clicked.connect(lambda: self._emit("next"))
        lay.addWidget(nxt)

        self._pos_label = QLabel("0:00")
        self._pos_label.setFixedWidth(36)
        self._pos_label.setStyleSheet(f"color: {C.TEXT_MUTED}; background: transparent;")
        lay.addWidget(self._pos_label)

        self._seek = QSlider(Qt.Horizontal)
        self._seek.setRange(0, 0)
        self._seek.sliderReleased.connect(self._on_seek_released)
        lay.addWidget(self._seek, 1)

        self._dur_label = QLabel("0:00")
        self._dur_label.setFixedWidth(36)
        self._dur_label.setStyleSheet(f"color: {C.TEXT_MUTED}; background: transparent;")
        lay.addWidget(self._dur_label)

        vol = QLabel("Vol")
        vol.setStyleSheet(f"color: {C.TEXT_MUTED}; background: transparent;")
        lay.addWidget(vol)

        self._volume_slider = QSlider(Qt.Horizontal)
        self._volume_slider.setRange(0, 100)
        self._volume_slider.setValue(self._volume)
        self._volume_slider.setFixedWidth(90)
        self._volume_slider.valueChanged.connect(self._on_volume_changed)
        lay.addWidget(self._volume_slider)

        self._vol_label = QLabel(f"{self._volume}%")
        self._vol_label.setFixedWidth(36)
        self._vol_label.setStyleSheet(f"color: {C.TEXT_MUTED}; background: transparent;")
        lay.addWidget(self._vol_label)

    @staticmethod
    def _transport_btn(text: str, tip: str) -> QPushButton:
        btn = QPushButton(text)
        btn.setObjectName("ghost_btn")
        btn.setFixedSize(36, 36)
        btn.setToolTip(tip)
        btn.setCursor(Qt.PointingHandCursor)
        return btn

    def _emit(self, key: str):
        for cb in self._callbacks[key]:
            cb()

    def bind_play_pause(self, cb):
        self._callbacks["play_pause"].append(cb)

    def bind_next(self, cb):
        self._callbacks["next"].append(cb)

    def bind_prev(self, cb):
        self._callbacks["prev"].append(cb)

    def bind_seek(self, cb):
        self._callbacks["seek"].append(cb)

    def bind_volume(self, cb):
        self._callbacks["volume"].append(cb)

    def update_track(self, track: Track | None) -> None:
        self._track = track
        if track:
            self._title.setText(track.title[:48])
            self._title.setStyleSheet(f"color: {C.TEXT_PRIMARY}; font-weight: bold; background: transparent;")
            self._artist.setText(track.artist[:36])
        else:
            self._title.setText("No track selected")
            self._title.setStyleSheet(f"color: {C.TEXT_MUTED}; background: transparent;")
            self._artist.setText("")
        self._seek.setRange(0, max(0, self._duration_ms))
        self._seek.blockSignals(True)
        self._seek.setValue(min(self._position_ms, self._duration_ms))
        self._seek.blockSignals(False)

    def update_state(self, playing: bool) -> None:
        self._playing = playing
        self._play_btn.setText("\u23F8" if playing else "\u25B6")

    def update_position(self, position_ms: int, duration_ms: int) -> None:
        self._position_ms = position_ms
        self._duration_ms = duration_ms
        self._seek.blockSignals(True)
        self._seek.setRange(0, max(0, duration_ms))
        self._seek.setValue(min(position_ms, duration_ms))
        self._seek.blockSignals(False)
        self._pos_label.setText(self._format_ms(position_ms))
        self._dur_label.setText(self._format_ms(duration_ms))

    def _on_seek_released(self):
        if self._duration_ms <= 0:
            return
        for cb in self._callbacks["seek"]:
            cb(self._seek.value())

    def _on_volume_changed(self, value: int):
        self._volume = value
        self._vol_label.setText(f"{value}%")
        for cb in self._callbacks["volume"]:
            cb(value)

    @staticmethod
    def _format_ms(ms: int) -> str:
        total_sec = max(0, ms) // 1000
        m = total_sec // 60
        s = total_sec % 60
        return f"{m}:{s:02d}"
