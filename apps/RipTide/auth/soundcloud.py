"""Riptide Audio - SoundCloud OAuth Provider"""
from __future__ import annotations

import time
from urllib.parse import urlencode

import requests

from apps.RipTide import config
from apps.RipTide.auth.base import OAuthProvider
from apps.RipTide.models import Platform


class SoundCloudOAuth(OAuthProvider):
    platform = Platform.SOUNDCLOUD
    AUTH_URL = "https://soundcloud.com/connect"
    TOKEN_URL = "https://api.soundcloud.com/oauth2/token"
    USER_URL = "https://api.soundcloud.com/me"

    def get_auth_url(self, state: str) -> str:
        params = {
            "client_id": config.SOUNDCLOUD_CLIENT_ID,
            "redirect_uri": config.SOUNDCLOUD_REDIRECT_URI,
            "response_type": "code",
            "scope": "non-expiring",
            "state": state,
        }
        return f"{self.AUTH_URL}?{urlencode(params)}"

    def exchange_code(self, code: str) -> dict:
        data = {
            "grant_type": "authorization_code",
            "client_id": config.SOUNDCLOUD_CLIENT_ID,
            "client_secret": config.SOUNDCLOUD_CLIENT_SECRET,
            "redirect_uri": config.SOUNDCLOUD_REDIRECT_URI,
            "code": code,
        }
        resp = requests.post(self.TOKEN_URL, data=data, timeout=30)
        if resp.status_code != 200:
            print(f"SoundCloud token exchange failed: {resp.text}")
            return {}
        token_data = resp.json()
        token_data["expires_at"] = time.time() + token_data.get(
            "expires_in", 3600
        )
        return token_data

    def refresh_token(self, refresh_token: str) -> dict:
        data = {
            "grant_type": "refresh_token",
            "client_id": config.SOUNDCLOUD_CLIENT_ID,
            "client_secret": config.SOUNDCLOUD_CLIENT_SECRET,
            "refresh_token": refresh_token,
        }
        resp = requests.post(self.TOKEN_URL, data=data, timeout=30)
        if resp.status_code != 200:
            print(f"SoundCloud token refresh failed: {resp.text}")
            return {}
        return resp.json()

    def get_user_info(self, access_token: str) -> dict:
        headers = {"Authorization": f"OAuth {access_token}"}
        resp = requests.get(self.USER_URL, headers=headers, timeout=30)
        if resp.status_code != 200:
            return {"display_name": "SoundCloud User", "username": ""}
        data = resp.json()
        avatar = data.get("avatar_url", "")
        return {
            "display_name": data.get("username", "SoundCloud User"),
            "username": str(data.get("id", "")),
            "avatar_url": avatar,
        }
