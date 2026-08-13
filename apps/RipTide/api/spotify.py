"""Riptide Audio - Spotify Web API Client"""
from __future__ import annotations

import requests

from apps.RipTide.auth.spotify import SpotifyOAuth
from apps.RipTide.models import Account, Platform, Track


class Artist:
    __slots__ = ("genres", "id", "image_url", "name", "popularity")

    def __init__(self, id: str = "", name: str = "", genres: list = None,
                 image_url: str = "", popularity: int = 0):
        self.id = id
        self.name = name
        self.genres = genres or []
        self.image_url = image_url
        self.popularity = popularity


class PlaylistInfo:
    __slots__ = ("description", "id", "image_url", "name", "owner", "track_count")

    def __init__(self, id: str = "", name: str = "", description: str = "",
                 image_url: str = "", track_count: int = 0, owner: str = ""):
        self.id = id
        self.name = name
        self.description = description
        self.image_url = image_url
        self.track_count = track_count
        self.owner = owner


class SpotifyAPI:
    BASE_URL = "https://api.spotify.com/v1"

    def __init__(self, account: Account):
        self.account = account
        self._oauth = SpotifyOAuth()
        self._session = requests.Session()

    def _headers(self) -> dict:
        return {"Authorization": f"Bearer {self.account.access_token}"}

    def _ensure_valid_token(self) -> None:
        if self.account.is_token_expired:
            refreshed = self._oauth.refresh_access_token(self.account)
            if refreshed:
                self.account = refreshed
            else:
                self.account.access_token = ""

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
        if resp.status_code == 429:
            retry_after = int(resp.headers.get("Retry-After", 5))
            import time
            time.sleep(retry_after)
            resp = self._session.get(
                url, headers=self._headers(), params=params or {}, timeout=30
            )
        if resp.status_code != 200:
            return None
        return resp.json()

    def _post(
        self, endpoint: str, data: dict = None, json_data: dict = None
    ) -> dict | None:
        self._ensure_valid_token()
        url = f"{self.BASE_URL}{endpoint}"
        resp = self._session.post(
            url,
            headers=self._headers(),
            data=data,
            json=json_data,
            timeout=30,
        )
        if resp.status_code == 401:
            refreshed = self._oauth.refresh_access_token(self.account)
            if refreshed:
                self.account = refreshed
                resp = self._session.post(
                    url,
                    headers=self._headers(),
                    json=json_data,
                    timeout=30,
                )
        if resp.status_code in (200, 201):
            return resp.json() if resp.text else {}
        return None

    def search(
        self, query: str, limit: int = 20, search_type: str = "track"
    ) -> list[Track]:
        data = self._get(
            "/search",
            {"q": query, "type": search_type, "limit": limit},
        )
        if not data:
            return []
        items = data.get("tracks", {}).get("items", [])
        return [self._parse_track(item) for item in items]

    def get_playlists(self, limit: int = 50) -> list:
        data = self._get("/me/playlists", {"limit": limit})
        if not data:
            return []
        return data.get("items", [])

    def get_playlist_tracks(
        self, playlist_id: str, limit: int = 100
    ) -> list[Track]:
        data = self._get(
            f"/playlists/{playlist_id}/tracks", {"limit": limit}
        )
        if not data:
            return []
        return [
            self._parse_track(item["track"])
            for item in data.get("items", [])
            if item.get("track")
        ]

    def get_saved_tracks(self, limit: int = 50) -> list[Track]:
        data = self._get("/me/tracks", {"limit": limit})
        if not data:
            return []
        return [
            self._parse_track(item["track"])
            for item in data.get("items", [])
        ]

    def get_recently_played(self, limit: int = 50) -> list[Track]:
        data = self._get("/me/player/recently-played", {"limit": limit})
        if not data:
            return []
        return [
            self._parse_track(item["track"])
            for item in data.get("items", [])
        ]

    def get_top_tracks(
        self, limit: int = 50, time_range: str = "short_term"
    ) -> list[Track]:
        data = self._get(
            "/me/top/tracks",
            {"limit": limit, "time_range": time_range},
        )
        if not data:
            return []
        return [self._parse_track(item) for item in data.get("items", [])]

    def get_top_artists(
        self, limit: int = 10, time_range: str = "medium_term"
    ) -> list[Artist]:
        data = self._get(
            "/me/top/artists",
            {"limit": limit, "time_range": time_range},
        )
        if not data:
            return []
        results = []
        for item in data.get("items", []):
            images = item.get("images", [])
            results.append(Artist(
                id=item.get("id", ""),
                name=item.get("name", ""),
                genres=item.get("genres", []),
                image_url=images[0]["url"] if images else "",
                popularity=item.get("popularity", 0),
            ))
        return results

    def start_artist_playback(self, artist_id: str) -> bool:
        body = {"context_uri": f"spotify:artist:{artist_id}"}
        result = self._put("/me/player/play", json_data=body)
        return result is not None

    def start_playlist_playback(self, playlist_id: str) -> bool:
        body = {"context_uri": f"spotify:playlist:{playlist_id}"}
        result = self._put("/me/player/play", json_data=body)
        return result is not None

    def get_recommendations(
        self, seed_track_ids: list[str], limit: int = 20
    ) -> list[Track]:
        data = self._get(
            "/recommendations",
            {
                "seed_tracks": ",".join(seed_track_ids[:5]),
                "limit": limit,
            },
        )
        if not data:
            return []
        return [self._parse_track(t) for t in data.get("tracks", [])]

    def get_track(self, track_id: str) -> Track | None:
        data = self._get(f"/tracks/{track_id}")
        if not data:
            return None
        return self._parse_track(data)

    def start_playback(
        self,
        track_ids: list[str] = None,
        context_uri: str = None,
        position: int = 0,
    ) -> bool:
        body = {}
        if track_ids:
            body["uris"] = [f"spotify:track:{tid}" for tid in track_ids]
        elif context_uri:
            body["context_uri"] = context_uri
            body["offset"] = {"position": position}
        result = self._put("/me/player/play", json_data=body)
        return result is not None

    def pause_playback(self) -> bool:
        return self._put("/me/player/pause") is not None

    def resume_playback(self) -> bool:
        return self._put("/me/player/play") is not None

    def get_playback_state(self) -> dict | None:
        return self._get("/me/player")

    def _put(
        self, endpoint: str, json_data: dict = None
    ) -> dict | None:
        self._ensure_valid_token()
        url = f"{self.BASE_URL}{endpoint}"
        resp = self._session.put(
            url, headers=self._headers(), json=json_data, timeout=30
        )
        if resp.status_code in (200, 204):
            return resp.json() if resp.text else {}
        return None

    @staticmethod
    def _parse_track(item: dict) -> Track:
        album = item.get("album", {})
        images = album.get("images", [])
        return Track(
            platform=Platform.SPOTIFY,
            platform_id=item.get("id", ""),
            title=item.get("name", ""),
            artist=", ".join(
                a.get("name", "") for a in item.get("artists", [])
            ),
            album=album.get("name", ""),
            duration_ms=item.get("duration_ms", 0),
            thumbnail_url=images[0]["url"] if images else "",
            preview_url=item.get("preview_url"),
            explicit=item.get("explicit", False),
            popularity=item.get("popularity", 0),
        )
