"""Riptide Audio - SoundCloud API Client"""
from __future__ import annotations

import requests

from apps.RipTide import config
from apps.RipTide.auth.soundcloud import SoundCloudOAuth
from apps.RipTide.models import Account, Platform, Track


class SoundCloudAPI:
    BASE_URL = "https://api.soundcloud.com"

    def __init__(self, account: Account):
        self.account = account
        self._oauth = SoundCloudOAuth()
        self._session = requests.Session()

    def _headers(self) -> dict:
        return {"Authorization": f"OAuth {self.account.access_token}"}

    def _ensure_valid_token(self) -> None:
        if self.account.is_token_expired:
            refreshed = self._oauth.refresh_access_token(self.account)
            if refreshed:
                self.account = refreshed

    def _get(self, endpoint: str, params: dict = None) -> dict | None:
        self._ensure_valid_token()
        url = f"{self.BASE_URL}{endpoint}"
        resp = self._session.get(
            url, headers=self._headers(), params=params or {}, timeout=30
        )
        if resp.status_code == 401:
            refreshed = self._oauth.refresh_access_token(self.account)
            if refreshed:
                self.account = refreshed
                resp = self._session.get(
                    url,
                    headers=self._headers(),
                    params=params or {},
                    timeout=30,
                )
        if resp.status_code != 200:
            return None
        return resp.json()

    def search(self, query: str, limit: int = 20) -> list[Track]:
        data = self._get(
            "/tracks",
            {"q": query, "limit": limit, "filter.created_at": "last-week"},
        )
        if not data:
            return []
        return [self._parse_track(item) for item in data]

    def get_liked_tracks(self, limit: int = 50) -> list[Track]:
        user_id = self.account.username
        if not user_id:
            me = self._get("/me")
            if me:
                user_id = str(me.get("id", ""))
        if not user_id:
            return []
        data = self._get(
            f"/users/{user_id}/likes/tracks", {"limit": limit}
        )
        if not data:
            return []
        return [self._parse_track(item) for item in data.get("collection", [])]

    def get_user_playlists(self, limit: int = 50) -> list:
        user_id = self.account.username
        if not user_id:
            me = self._get("/me")
            if me:
                user_id = str(me.get("id", ""))
        if not user_id:
            return []
        data = self._get(
            f"/users/{user_id}/playlists", {"limit": limit}
        )
        if not data:
            return []
        return data

    def get_playlist_tracks(
        self, playlist_id: str, limit: int = 50
    ) -> list[Track]:
        data = self._get(f"/playlists/{playlist_id}")
        if not data:
            return []
        tracks = data.get("tracks", [])
        return [self._parse_track(item) for item in tracks[:limit]]

    def get_stream_url(self, track_id: str) -> str | None:
        data = self._get(f"/tracks/{track_id}/stream")
        if data and "url" in data:
            return data["url"]
        return f"https://api.soundcloud.com/tracks/{track_id}/stream?client_id={config.SOUNDCLOUD_CLIENT_ID}"

    def get_track(self, track_id: str) -> Track | None:
        data = self._get(f"/tracks/{track_id}")
        if not data:
            return None
        return self._parse_track(data)

    def get_recently_played(self, limit: int = 50) -> list[Track]:
        data = self._get("/me/activities/tracks/played", {"limit": limit})
        if not data:
            return []
        collection = data.get("collection", [])
        return [
            self._parse_track(item["track"])
            for item in collection
            if "track" in item
        ]

    @staticmethod
    def _parse_track(item: dict) -> Track:
        user = item.get("user", {})
        artwork = item.get("artwork_url", "")
        if not artwork:
            artwork = user.get("avatar_url", "")
        if artwork:
            artwork = artwork.replace("-large", "-t300x300")
        duration_ms = item.get("duration", 0)
        return Track(
            platform=Platform.SOUNDCLOUD,
            platform_id=str(item.get("id", "")),
            title=item.get("title", ""),
            artist=user.get("username", "Unknown"),
            album="SoundCloud",
            duration_ms=duration_ms,
            thumbnail_url=artwork,
            preview_url=None,
            stream_url=item.get("stream_url"),
            explicit=False,
            popularity=item.get("playback_count", 0),
        )
