"""Riptide Audio - Data Models"""
from __future__ import annotations

import enum
import time
from dataclasses import dataclass, field


class Platform(enum.Enum):
    SPOTIFY = "spotify"
    YOUTUBE = "youtube"
    SOUNDCLOUD = "soundcloud"

    @property
    def display_name(self) -> str:
        return _PLATFORM_NAMES[self]

    @property
    def color(self) -> str:
        return _PLATFORM_COLORS[self]


_PLATFORM_NAMES = {
    Platform.SPOTIFY: "Spotify",
    Platform.YOUTUBE: "YouTube Music",
    Platform.SOUNDCLOUD: "SoundCloud",
}

_PLATFORM_COLORS = {
    Platform.SPOTIFY: "#1db954",
    Platform.YOUTUBE: "#ff0000",
    Platform.SOUNDCLOUD: "#ff5500",
}


class PlaybackState(enum.Enum):
    STOPPED = "stopped"
    PLAYING = "playing"
    PAUSED = "paused"
    BUFFERING = "buffering"


@dataclass
class Account:
    id: int | None = None
    platform: Platform = Platform.SPOTIFY
    display_name: str = ""
    username: str = ""
    access_token: str = ""
    refresh_token: str = ""
    token_expires: float = 0.0
    is_active: bool = True
    avatar_url: str = ""
    created_at: float = field(default_factory=time.time)

    @property
    def is_token_expired(self) -> bool:
        return time.time() >= self.token_expires - 60

    @property
    def label(self) -> str:
        return f"{self.display_name} ({self.platform.display_name})"


@dataclass
class Track:
    id: int | None = None
    platform: Platform = Platform.SPOTIFY
    platform_id: str = ""
    title: str = ""
    artist: str = ""
    album: str = ""
    duration_ms: int = 0
    thumbnail_url: str = ""
    preview_url: str | None = None
    stream_url: str | None = None
    explicit: bool = False
    popularity: int = 0
    account_id: int | None = None

    @property
    def duration_str(self) -> str:
        total_sec = self.duration_ms // 1000
        minutes = total_sec // 60
        seconds = total_sec % 60
        return f"{minutes}:{seconds:02d}"

    @property
    def display_label(self) -> str:
        return f"{self.artist} - {self.title}"


@dataclass
class PlaylistTrack:
    id: int | None = None
    playlist_id: int = 0
    track_id: int = 0
    position: int = 0
    added_at: float = field(default_factory=time.time)


@dataclass
class Playlist:
    id: int | None = None
    name: str = ""
    description: str = ""
    is_mega: bool = True
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)
    track_count: int = 0
    total_duration_ms: int = 0

    @property
    def duration_str(self) -> str:
        total_sec = self.total_duration_ms // 1000
        hours = total_sec // 3600
        minutes = (total_sec % 3600) // 60
        if hours > 0:
            return f"{hours}h {minutes}m"
        return f"{minutes}m"


@dataclass
class SFXClip:
    id: int | None = None
    name: str = ""
    file_path: str = ""
    hotkey: str = ""
    category: str = "general"
    volume: float = 1.0
    duration_ms: int = 0
    is_builtin: bool = False

    @property
    def display_label(self) -> str:
        label = self.name
        if self.hotkey:
            label += f" [{self.hotkey}]"
        return label
