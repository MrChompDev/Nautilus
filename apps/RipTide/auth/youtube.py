"""Riptide Audio - YouTube Music OAuth Provider"""
from __future__ import annotations

import time
from urllib.parse import urlencode

import requests

from apps.RipTide import config
from apps.RipTide.auth.base import OAuthProvider
from apps.RipTide.models import Platform


class YouTubeOAuth(OAuthProvider):
    platform = Platform.YOUTUBE
    AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
    TOKEN_URL = "https://oauth2.googleapis.com/token"
    USER_URL = "https://www.googleapis.com/oauth2/v2/userinfo"

    def get_auth_url(self, state: str) -> str:
        params = {
            "client_id": config.YOUTUBE_CLIENT_ID,
            "redirect_uri": config.YOUTUBE_REDIRECT_URI,
            "response_type": "code",
            "scope": " ".join(config.YOUTUBE_SCOPES),
            "state": state,
            "access_type": "offline",
            "prompt": "consent",
        }
        return f"{self.AUTH_URL}?{urlencode(params)}"

    def exchange_code(self, code: str) -> dict:
        data = {
            "code": code,
            "client_id": config.YOUTUBE_CLIENT_ID,
            "client_secret": config.YOUTUBE_CLIENT_SECRET,
            "redirect_uri": config.YOUTUBE_REDIRECT_URI,
            "grant_type": "authorization_code",
        }
        resp = requests.post(self.TOKEN_URL, data=data, timeout=30)
        if resp.status_code != 200:
            print(f"YouTube token exchange failed: {resp.text}")
            return {}
        token_data = resp.json()
        token_data["expires_at"] = time.time() + token_data.get(
            "expires_in", 3600
        )
        return token_data

    def refresh_token(self, refresh_token: str) -> dict:
        data = {
            "client_id": config.YOUTUBE_CLIENT_ID,
            "client_secret": config.YOUTUBE_CLIENT_SECRET,
            "refresh_token": refresh_token,
            "grant_type": "refresh_token",
        }
        resp = requests.post(self.TOKEN_URL, data=data, timeout=30)
        if resp.status_code != 200:
            print(f"YouTube token refresh failed: {resp.text}")
            return {}
        return resp.json()

    def get_user_info(self, access_token: str) -> dict:
        headers = {"Authorization": f"Bearer {access_token}"}
        resp = requests.get(self.USER_URL, headers=headers, timeout=30)
        if resp.status_code != 200:
            return {"display_name": "YouTube User", "username": ""}
        data = resp.json()
        return {
            "display_name": data.get("name", "YouTube User"),
            "username": data.get("id", ""),
            "avatar_url": data.get("picture", ""),
        }
