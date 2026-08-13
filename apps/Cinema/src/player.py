"""Cinema — video player widget.

Fullscreen-capable playback for local media files
via QMediaPlayer / QVideoWidget. All state reset on load so a movie can be
swapped in without leaks.
"""

from __future__ import annotations

import os

from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QKeyEvent
from PySide6.QtMultimedia import QAudioOutput, QMediaPlayer
from PySide6.QtMultimediaWidgets import QVideoWidget
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QSlider,
    QVBoxLayout,
    QWidget,
)

try:
    from core.theme import COLORS, FONTS, SPACING
except ImportError:
    COLORS = {"void_black": "#02060A", "abyss_navy": "#081626", "deep_navy": "#050D14",
              "seafoam": "#00F2C2", "seafoam_dim": "#00C9A0", "seafoam_deep": "#004D40",
              "coral": "#FF7F50", "hd_white": "#EEF4F8", "text_secondary": "#8BA4B8",
              "text_muted": "#506070", "border": "#152D44", "surface_hover": "#132A40"}
    FONTS = {"mono": "JetBrains Mono", "size_xs": 10, "size_sm": 11, "size_md": 12}
    SPACING = {"xs": 2, "sm": 4, "md": 8, "lg": 12}


class PlayerWindow(QWidget):
    """Standalone video player window with transport controls."""

    def __init__(self, source: str = "", title: str = "", headers: dict | None = None):
        super().__init__()
        self._headers = headers or {}
        self._title = title or "Cinema Player"
        self._dragging = False

        self.setWindowTitle(f"Now Playing — {self._title}")
        self.setMinimumSize(640, 400)
        self.resize(960, 560)
        self.setStyleSheet(f"background-color: {COLORS['void_black']};")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # ── Video surface ──
        self._video = QVideoWidget()
        layout.addWidget(self._video, 1)

        # ── Controls ──
        controls = QWidget()
        controls.setStyleSheet(f"background-color: {COLORS['abyss_navy']};")
        cl = QVBoxLayout(controls)
        cl.setContentsMargins(SPACING["md"], SPACING["sm"], SPACING["md"], SPACING["md"])
        cl.setSpacing(SPACING["sm"])

        self._title_lbl = QLabel(self._title)
        self._title_lbl.setStyleSheet(f"""
            color: {COLORS['seafoam']}; font-family: "{FONTS['mono']}";
            font-size: {FONTS['size_sm']}px; font-weight: bold;
        """)
        cl.addWidget(self._title_lbl)

        # Seek bar
        seek_row = QHBoxLayout()
        self._pos_lbl = QLabel("0:00:00")
        self._pos_lbl.setStyleSheet(f"color: {COLORS['text_muted']}; font-family: '{FONTS['mono']}'; font-size: {FONTS['size_xs']}px;")
        seek_row.addWidget(self._pos_lbl)

        self._seek = QSlider(Qt.Horizontal)
        self._seek.setRange(0, 1000)
        self._seek.setStyleSheet(f"""
            QSlider::groove:horizontal {{ background: {COLORS['deep_navy']}; height: 4px; border: 1px solid {COLORS['border']}; }}
            QSlider::handle:horizontal {{ background: {COLORS['seafoam']}; width: 12px; height: 12px; margin: -5px 0; }}
            QSlider::sub-page:horizontal {{ background: {COLORS['seafoam_deep']}; }}
        """)
        seek_row.addWidget(self._seek, 1)

        self._dur_lbl = QLabel("0:00:00")
        self._dur_lbl.setStyleSheet(f"color: {COLORS['text_muted']}; font-family: '{FONTS['mono']}'; font-size: {FONTS['size_xs']}px;")
        seek_row.addWidget(self._dur_lbl)
        cl.addLayout(seek_row)

        # Transport buttons
        btn_row = QHBoxLayout()
        btn_row.setSpacing(SPACING["sm"])

        def _mk(text: str, tip: str, color: str = COLORS["seafoam"]) -> QPushButton:
            b = QPushButton(text)
            b.setFixedSize(40, 34)
            b.setToolTip(tip)
            b.setStyleSheet(f"""
                QPushButton {{
                    background: transparent; color: {color};
                    border: 1px solid {COLORS['border']}; font-size: 15px;
                }}
                QPushButton:hover {{ background: {COLORS['surface_hover']}; border-color: {COLORS['seafoam']}; }}
                QPushButton:pressed {{ background: {COLORS['seafoam_deep']}; }}
            """)
            return b

        self._play_btn = _mk("\u25B6", "Play/Pause (Space)")
        self._stop_btn = _mk("\u25A0", "Stop")
        self._vol_btn = _mk("\U0001F50A", "Mute")
        self._fs_btn = _mk("\u26F6", "Fullscreen (F)")

        btn_row.addWidget(self._play_btn)
        btn_row.addWidget(self._stop_btn)
        btn_row.addWidget(self._vol_btn)
        btn_row.addStretch()

        self._vol = QSlider(Qt.Horizontal)
        self._vol.setRange(0, 100)
        self._vol.setValue(80)
        self._vol.setFixedWidth(140)
        self._vol.setToolTip("Volume")
        self._vol.setStyleSheet(self._seek.styleSheet())
        btn_row.addWidget(self._vol)

        btn_row.addWidget(self._fs_btn)
        cl.addLayout(btn_row)
        layout.addWidget(controls)

        # ── Media engine ──
        self._audio = QAudioOutput(self)
        self._audio.setVolume(0.8)
        self._player = QMediaPlayer(self)
        self._player.setAudioOutput(self._audio)
        self._player.setVideoOutput(self._video)

        self._player.errorOccurred.connect(self._on_error)
        self._player.playbackStateChanged.connect(self._on_state)
        self._player.positionChanged.connect(self._on_position)
        self._player.durationChanged.connect(self._on_duration)

        self._seek.sliderPressed.connect(lambda: setattr(self, "_dragging", True))
        self._seek.sliderReleased.connect(self._seek_to_slider)
        self._play_btn.clicked.connect(self.toggle_play)
        self._stop_btn.clicked.connect(self._player.stop)
        self._vol_btn.clicked.connect(self._toggle_mute)
        self._vol.valueChanged.connect(self._audio.setVolume)
        self._fs_btn.clicked.connect(self._toggle_fullscreen)

        if source:
            self.load(source, self._title)

    # ── Public API ──

    def load(self, source: str, title: str = ""):
        if title:
            self._title = title
            self.setWindowTitle(f"Now Playing — {title}")
            self._title_lbl.setText(title)
        url = QUrl(source)
        if os.path.exists(source):
            url = QUrl.fromLocalFile(source)
        if self._headers:
            req_headers = dict(self._headers)
            self._player.setProperty("_nautilus_headers", req_headers)
        self._player.setSource(url)
        self._player.play()

    def play(self):
        self._player.play()

    def pause(self):
        self._player.pause()

    def toggle_play(self):
        if self._player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            self._player.pause()
        else:
            self._player.play()

    def stop(self):
        self._player.stop()

    # ── Handlers ──

    def _on_state(self, state):
        self._play_btn.setText(
            "\u25B6" if state != QMediaPlayer.PlaybackState.PlayingState else "\u23F8"
        )

    def _on_position(self, ms: int):
        if not self._dragging:
            self._seek.setValue(self._pct(ms, self._player.duration()))
        self._pos_lbl.setText(_fmt_ms(ms))

    def _on_duration(self, ms: int):
        self._dur_lbl.setText(_fmt_ms(ms))

    def _pct(self, val: int, total: int) -> int:
        if total <= 0:
            return 0
        return int(val * 1000 / total)

    def _seek_to_slider(self):
        self._dragging = False
        total = self._player.duration()
        if total > 0:
            self._player.setPosition(int(self._seek.value() * total / 1000))

    def _toggle_mute(self):
        self._audio.setMuted(not self._audio.isMuted())
        self._vol_btn.setText("\U0001F507" if self._audio.isMuted() else "\U0001F50A")

    def _toggle_fullscreen(self):
        if self.isFullScreen():
            self.showNormal()
        else:
            self.showFullScreen()

    def _on_error(self, error, msg):
        self._play_btn.setText("\u25B6")
        self._title_lbl.setText("Playback error")
        QMessageBox.warning(self, "Playback Error",
                            f"Could not play:\n{self._title}\n\n{msg or error.name}")

    def keyPressEvent(self, event: QKeyEvent):
        if event.key() in (Qt.Key_Space, Qt.Key_MediaTogglePlayPause):
            self.toggle_play()
            event.accept()
        elif event.key() == Qt.Key_Escape:
            if self.isFullScreen():
                self.showNormal()
            event.accept()
        elif event.key() in (Qt.Key_F, Qt.Key_F11):
            self._toggle_fullscreen()
            event.accept()
        elif event.key() == Qt.Key_Left:
            self._player.setPosition(max(0, self._player.position() - 10000))
            event.accept()
        elif event.key() == Qt.Key_Right:
            self._player.setPosition(self._player.position() + 10000)
            event.accept()
        else:
            super().keyPressEvent(event)

    def closeEvent(self, event):
        self._player.stop()
        event.accept()


def _fmt_ms(ms: int) -> str:
    ms = max(0, int(ms))
    total = ms // 1000
    h, rem = divmod(total, 3600)
    m, s = divmod(rem, 60)
    if h:
        return f"{h}:{m:02d}:{s:02d}"
    return f"{m}:{s:02d}"
