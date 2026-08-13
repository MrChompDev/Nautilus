from .base import OAuthProvider
from .soundcloud import SoundCloudOAuth
from .spotify import SpotifyOAuth
from .youtube import YouTubeOAuth

__all__ = ["OAuthProvider", "SoundCloudOAuth", "SpotifyOAuth", "YouTubeOAuth"]
