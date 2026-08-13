"""Riptide Audio - OAuth Provider Base"""
from __future__ import annotations

import abc
import base64
import hashlib
import secrets
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs, urlparse

from apps.RipTide import config
from apps.RipTide.models import Account, Platform


class OAuthCallbackHandler(BaseHTTPRequestHandler):
    auth_code: str | None = None
    auth_state: str | None = None

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path == "/favicon.ico":
            self.send_response(204)
            self.end_headers()
            return
        params = parse_qs(parsed.query)
        if "code" in params:
            OAuthCallbackHandler.auth_code = params["code"][0]
            OAuthCallbackHandler.auth_state = params.get(
                "state", [None]
            )[0]
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.end_headers()
            self.wfile.write(
                b"<html><body><h2 style='color:#00b4ff;background:#060b14;padding:20px;font-family:sans-serif'>"
                b"Authentication successful!</h2>"
                b"<p style='color:#e0eaff;background:#060b14;padding:0 20px 20px;font-family:sans-serif'>"
                b"You can close this window and return to Riptide Audio.</p>"
                b"</body></html>"
            )
        elif "error" in params:
            self.send_response(400)
            self.send_header("Content-Type", "text/html")
            self.end_headers()
            error = params.get("error", ["unknown"])[0]
            self.wfile.write(
                f"<html><body><h2 style='color:#ff4466;background:#060b14;padding:20px;font-family:sans-serif'>"
                f"Authentication failed: {error}</h2>"
                f"</body></html>".encode()
            )
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format: str, *args) -> None:
        pass


class OAuthProvider(abc.ABC):
    platform: Platform
    _verifier: str | None = None

    @abc.abstractmethod
    def get_auth_url(self, state: str) -> str:
        ...

    @abc.abstractmethod
    def exchange_code(self, code: str) -> dict:
        ...

    @abc.abstractmethod
    def refresh_token(self, refresh_token: str) -> dict:
        ...

    @abc.abstractmethod
    def get_user_info(self, access_token: str) -> dict:
        ...

    def _generate_pkce_pair(self) -> tuple[str, str]:
        verifier = base64.urlsafe_b64encode(
            secrets.token_bytes(32)
        ).rstrip(b"=").decode("ascii")
        digest = hashlib.sha256(verifier.encode("ascii")).digest()
        challenge = base64.urlsafe_b64encode(digest).rstrip(b"=").decode(
            "ascii"
        )
        return verifier, challenge

    def authenticate(self) -> Account | None:
        state = secrets.token_urlsafe(16)
        auth_url = self.get_auth_url(state)

        OAuthCallbackHandler.auth_code = None
        OAuthCallbackHandler.auth_state = None

        server = HTTPServer(
            (config.OAUTH_HOST, config.OAUTH_PORT), OAuthCallbackHandler
        )
        server.timeout = 120

        webbrowser.open(auth_url)
        print(f"Opening browser for {self.platform.display_name} login...")

        while OAuthCallbackHandler.auth_code is None:
            server.handle_request()

        server.server_close()

        if (
            OAuthCallbackHandler.auth_state is not None
            and OAuthCallbackHandler.auth_state != state
        ):
            print("OAuth state mismatch - possible CSRF attack")
            return None

        code = OAuthCallbackHandler.auth_code
        if not code:
            return None

        token_data = self.exchange_code(code)
        if not token_data:
            return None

        access_token = token_data.get("access_token", "")
        refresh_token = token_data.get("refresh_token", "")
        expires_in = token_data.get("expires_in", 3600)

        user_info = self.get_user_info(access_token)

        return Account(
            platform=self.platform,
            display_name=user_info.get("display_name", "Unknown"),
            username=user_info.get("username", ""),
            access_token=access_token,
            refresh_token=refresh_token,
            token_expires=expires_in,
            avatar_url=user_info.get("avatar_url", ""),
        )

    def refresh_access_token(self, account: Account) -> Account | None:
        token_data = self.refresh_token(account.refresh_token)
        if not token_data:
            return None
        account.access_token = token_data.get("access_token", account.access_token)
        if "refresh_token" in token_data:
            account.refresh_token = token_data["refresh_token"]
        expires_in = token_data.get("expires_in", 3600)
        import time
        account.token_expires = time.time() + expires_in
        return account
