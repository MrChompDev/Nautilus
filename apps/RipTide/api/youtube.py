"""Riptide Audio - YouTube Music API Client"""
from __future__ import annotations

import requests

from apps.RipTide.auth.youtube import YouTubeOAuth
from apps.RipTide.models import Account, Platform, Track


class YouTubeAPI:
    BASE_URL = "https://www.googleapis.com/youtube/v3"

    def __init__(self, account: Account):
        self.account = account
        self._oauth = YouTubeOAuth()
        self._session = requests.Session()

    def _headers(self) -> dict:
        return {"Authorization": f"Bearer {self.account.access_token}"}

    def _ensure_valid_token(self) -> None:
        if self.account.is_token_expired:
            refreshed = self._oauth.refresh_access_token(self.account)
            if refreshed:
                self.account = refreshed

    def _get(self, endpoint: str, params: dict = None) -> dict | None:
        self._ensure_valid_token()
        url = f"{self.BASE_URL}{endpoint}"
        params = params or {}
        params.setdefault("part", "snippet,contentDetails")
        resp = self._session.get(
            url, headers=self._headers(), params=params, timeout=30
        )
        if resp.status_code == 401:
            refreshed = self._oauth.refresh_access_token(self.account)
            if refreshed:
                self.account = refreshed
                resp = self._session.get(
                    url, headers=self._headers(), params=params, timeout=30
                )
        if resp.status_code != 200:
            return None
        return resp.json()

    def search(self, query: str, limit: int = 20) -> list[Track]:
        data = self._get(
            "/search",
            {
                "part": "snippet",
                "q": query,
                "type": "video",
                "videoCategoryId": "10",
                "maxResults": limit,
            },
        )
        if not data:
            return []
        items = data.get("items", [])
        video_ids = [
            item["id"]["videoId"]
            for item in items
            if item.get("id", {}).get("videoId")
        ]
        if not video_ids:
            return []
        return self._get_video_details(video_ids)

    def get_video_details(self, video_ids: list[str]) -> list[Track]:
        data = self._get(
            "/videos",
            {
                "part": "snippet,contentDetails,statistics",
                "id": ",".join(video_ids),
            },
        )
        if not data:
            return []
        return [
            self._parse_video(item) for item in data.get("items", [])
        ]

    def get_liked_videos(self, limit: int = 50) -> list[Track]:
        data = self._get(
            "/videos",
            {
                "part": "snippet,contentDetails,statistics",
                "myRating": "like",
                "maxResults": limit,
            },
        )
        if not data:
            return []
        return [self._parse_video(item) for item in data.get("items", [])]

    def get_library_playlists(self, limit: int = 50) -> list:
        data = self._get(
            "/playlists",
            {
                "part": "snippet,contentDetails",
                "mine": "true",
                "maxResults": limit,
            },
        )
        if not data:
            return []
        return data.get("items", [])

    def get_playlist_videos(
        self, playlist_id: str, limit: int = 50
    ) -> list[Track]:
        playlist_data = self._get(
            "/playlistItems",
            {
                "part": "snippet,contentDetails",
                "playlistId": playlist_id,
                "maxResults": limit,
            },
        )
        if not playlist_data:
            return []
        video_ids = [
            item["contentDetails"]["videoId"]
            for item in playlist_data.get("items", [])
            if "contentDetails" in item
        ]
        if not video_ids:
            return []
        return self._get_video_details(video_ids)

    def get_recommendations(self, video_id: str, limit: int = 20) -> list[Track]:
        data = self._get(
            "/search",
            {
                "part": "snippet",
                "relatedToVideoId": video_id,
                "type": "video",
                "videoCategoryId": "10",
                "maxResults": limit,
            },
        )
        if not data:
            return []
        video_ids = [
            item["id"]["videoId"]
            for item in data.get("items", [])
            if item.get("id", {}).get("videoId")
        ]
        if not video_ids:
            return []
        return self._get_video_details(video_ids)

    def get_stream_url(self, video_id: str) -> str | None:
        data = self._get(
            "/videos",
            {
                "part": "contentDetails",
                "id": video_id,
            },
        )
        if not data:
            return None
        items = data.get("items", [])
        if not items:
            return None
        return f"https://www.youtube.com/watch?v={video_id}"

    @staticmethod
    def _parse_video(item: dict) -> Track:
        snippet = item.get("snippet", {})
        content = item.get("contentDetails", {})
        duration_str = content.get("duration", "PT0S")
        duration_ms = YouTubeAPI._parse_duration(duration_str)
        thumbnails = snippet.get("thumbnails", {})
        thumb_url = ""
        for key in ("maxres", "high", "medium", "default"):
            if key in thumbnails:
                thumb_url = thumbnails[key]["url"]
                break
        return Track(
            platform=Platform.YOUTUBE,
            platform_id=item.get("id", ""),
            title=snippet.get("title", ""),
            artist=snippet.get("channelTitle", ""),
            album="YouTube Music",
            duration_ms=duration_ms,
            thumbnail_url=thumb_url,
            stream_url=f"https://www.youtube.com/watch?v={item.get('id', '')}",
            explicit=False,
            popularity=0,
        )

    @staticmethod
    def _parse_duration(duration: str) -> int:
        import re
        match = re.match(r"PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?", duration)
        if not match:
            return 0
        hours = int(match.group(1) or 0)
        minutes = int(match.group(2) or 0)
        seconds = int(match.group(3) or 0)
        return (hours * 3600 + minutes * 60 + seconds) * 1000
