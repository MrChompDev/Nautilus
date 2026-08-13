"""Riptide Audio - Spotify OAuth Provider (PKCE)"""
from __future__ import annotations

import time
from urllib.parse import urlencode

import requests

from apps.RipTide import config
from apps.RipTide.auth.base import OAuthProvider
from apps.RipTide.models import Platform


class SpotifyOAuth(OAuthProvider):
    platform = Platform.SPOTIFY
    AUTH_URL = "https://accounts.spotify.com/authorize"
    TOKEN_URL = "https://accounts.spotify.com/api/token"
    USER_URL = "https://api.spotify.com/v1/me"

    def get_auth_url(self, state: str) -> str:
        self._verifier, challenge = self._generate_pkce_pair()
        params = {
            "client_id": config.SPOTIFY_CLIENT_ID,
            "response_type": "code",
            "redirect_uri": config.SPOTIFY_REDIRECT_URI,
            "scope": " ".join(config.SPOTIFY_SCOPES),
            "state": state,
            "code_challenge_method": "S256",
            "code_challenge": challenge,
            "show_dialog": "true",
        }
        return f"{self.AUTH_URL}?{urlencode(params)}"

    def exchange_code(self, code: str) -> dict:
        data = {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": config.SPOTIFY_REDIRECT_URI,
            "client_id": config.SPOTIFY_CLIENT_ID,
            "code_verifier": self._verifier,
        }
        resp = requests.post(self.TOKEN_URL, data=data, timeout=30)
        if resp.status_code != 200:
            print(f"Spotify token exchange failed: {resp.text}")
            return {}
        token_data = resp.json()
        token_data["expires_at"] = time.time() + token_data.get("expires_in", 3600)
        return token_data

    def refresh_token(self, refresh_token: str) -> dict:
        data = {
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
            "client_id": config.SPOTIFY_CLIENT_ID,
        }
        resp = requests.post(self.TOKEN_URL, data=data, timeout=30)
        if resp.status_code != 200:
            print(f"Spotify token refresh failed: {resp.text}")
            return {}
        return resp.json()

    def get_user_info(self, access_token: str) -> dict:
        headers = {"Authorization": f"Bearer {access_token}"}
        resp = requests.get(self.USER_URL, headers=headers, timeout=30)
        if resp.status_code != 200:
            return {"display_name": "Spotify User", "username": ""}
        data = resp.json()
        return {
            "display_name": data.get("display_name", "Spotify User"),
            "username": data.get("id", ""),
            "avatar_url": (
                data.get("images", [{}])[0].get("url", "")
                if data.get("images")
                else ""
            ),
        }
