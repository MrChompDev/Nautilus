"""Riptide Audio - Application Configuration"""
import os
from pathlib import Path

APP_NAME = "Riptide Audio"
APP_VERSION = "3.0.0"
APP_AUTHOR = "Chomp OS"

BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

DB_PATH = DATA_DIR / "riptide.db"
TOKEN_DIR = DATA_DIR / "tokens"
TOKEN_DIR.mkdir(exist_ok=True)

WINDOW_TITLE = f"{APP_NAME} v{APP_VERSION}"
WINDOW_MIN_WIDTH = 1280
WINDOW_MIN_HEIGHT = 800

SPOTIFY_CLIENT_ID = os.getenv("RIPTIDE_SPOTIFY_CLIENT_ID", "")
SPOTIFY_CLIENT_SECRET = os.getenv("RIPTIDE_SPOTIFY_CLIENT_SECRET", "")
SPOTIFY_REDIRECT_URI = "http://127.0.0.1:8765/callback"
SPOTIFY_SCOPES = [
    "user-read-playback-state",
    "user-modify-playback-state",
    "user-read-currently-playing",
    "playlist-read-private",
    "playlist-read-collaborative",
    "playlist-modify-public",
    "playlist-modify-private",
    "user-library-read",
    "user-top-read",
    "user-read-recently-played",
    "streaming",
]

YOUTUBE_CLIENT_ID = os.getenv("RIPTIDE_YOUTUBE_CLIENT_ID", "")
YOUTUBE_CLIENT_SECRET = os.getenv("RIPTIDE_YOUTUBE_CLIENT_SECRET", "")
YOUTUBE_REDIRECT_URI = "http://127.0.0.1:8765/callback"
YOUTUBE_SCOPES = [
    "https://www.googleapis.com/auth/youtube.readonly",
    "https://www.googleapis.com/auth/youtube",
    "https://www.googleapis.com/auth/youtube.force-ssl",
]

SOUNDCLOUD_CLIENT_ID = os.getenv("RIPTIDE_SOUNDCLOUD_CLIENT_ID", "")
SOUNDCLOUD_CLIENT_SECRET = os.getenv("RIPTIDE_SOUNDCLOUD_CLIENT_SECRET", "")
SOUNDCLOUD_REDIRECT_URI = "http://127.0.0.1:8765/callback"

OAUTH_PORT = 8765
OAUTH_HOST = "127.0.0.1"

AUDIO_BUFFER_MS = 300
SFX_FADE_MS = 50
MAX_SFX_CHANNELS = 16
MUSIC_VOLUME_DEFAULT = 80
SFX_VOLUME_DEFAULT = 70

THEME_DARK = {
    "bg_primary": "#060b14",
    "bg_secondary": "#0c1424",
    "bg_tertiary": "#111d33",
    "bg_card": "#0e1829",
    "bg_hover": "#142240",
    "bg_active": "#1a2d50",
    "accent": "#00b4ff",
    "accent_hover": "#33c4ff",
    "accent_dim": "#0a2a4a",
    "text_primary": "#e0eaff",
    "text_secondary": "#7b9cc2",
    "text_muted": "#4a6a8a",
    "border": "#1a2d50",
    "border_light": "#243b5e",
    "danger": "#ff4466",
    "success": "#44ddaa",
    "warning": "#ffcc33",
    "spotify": "#1db954",
    "youtube": "#ff0000",
    "soundcloud": "#ff5500",
}
