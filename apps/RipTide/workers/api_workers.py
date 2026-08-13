"""Riptide Audio - PySide6 Background Workers

Workers run API calls on daemon threads and hand results back to the GUI
thread through a shared ``_MainThreadDispatcher`` (queued Qt signal).
"""
from __future__ import annotations

import threading

from PySide6.QtCore import QObject, Signal

from apps.RipTide.models import Platform, Track


class _MainThreadDispatcher(QObject):
    """Marshals arbitrary callables from worker threads onto the GUI thread."""

    _dispatch = Signal(object, object)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._dispatch.connect(self._invoke)

    def _invoke(self, func, args) -> None:
        func(*args)


_DISPATCHER = None


def _dispatcher() -> _MainThreadDispatcher:
    global _DISPATCHER
    if _DISPATCHER is None:
        _DISPATCHER = _MainThreadDispatcher()
    return _DISPATCHER


def post(func, *args) -> None:
    """Queue ``func(*args)`` to run on the main/GUI thread."""
    _dispatcher()._dispatch.emit(func, args)


class DashboardWorker:
    def __init__(self, clients: dict[Platform, object], on_done, on_error):
        self.clients = clients
        self.on_done = on_done
        self.on_error = on_error
        self._thread = threading.Thread(target=self._run, daemon=True)

    def start(self) -> None:
        self._thread.start()

    def _run(self) -> None:
        result = {
            "top_artists": [],
            "playlists": [],
            "recently_played": [],
            "top_tracks": [],
        }
        try:
            from apps.RipTide.api.spotify import SpotifyAPI
            client = self.clients.get(Platform.SPOTIFY)
            if client and isinstance(client, SpotifyAPI):
                try:
                    result["top_artists"] = client.get_top_artists(limit=10)
                except Exception as e:
                    print(f"Dashboard top_artists error: {e}")
                try:
                    result["playlists"] = client.get_playlists(limit=12)
                except Exception as e:
                    print(f"Dashboard playlists error: {e}")
                try:
                    result["recently_played"] = client.get_recently_played(limit=10)
                except Exception as e:
                    print(f"Dashboard recently_played error: {e}")
                try:
                    result["top_tracks"] = client.get_top_tracks(limit=10)
                except Exception as e:
                    print(f"Dashboard top_tracks error: {e}")
            post(self.on_done, result)
        except Exception as e:
            post(self.on_error, str(e))


class SearchWorker:
    def __init__(self, query: str, clients: dict[Platform, object], on_done, on_error):
        self.query = query
        self.clients = clients
        self.on_done = on_done
        self.on_error = on_error
        self._thread = threading.Thread(target=self._run, daemon=True)

    def start(self) -> None:
        self._thread.start()

    def _run(self) -> None:
        all_results: list[Track] = []
        try:
            for platform, client in self.clients.items():
                try:
                    results = client.search(self.query, limit=20)
                    all_results.extend(results)
                except Exception as e:
                    print(f"Search error ({platform.value}): {e}")
            all_results.sort(key=lambda t: t.popularity, reverse=True)
            post(self.on_done, all_results)
        except Exception as e:
            post(self.on_error, str(e))


class LibraryLoaderWorker:
    def __init__(self, platform: Platform, client, library_type: str, on_done, on_error):
        self.platform = platform
        self.client = client
        self.library_type = library_type
        self.on_done = on_done
        self.on_error = on_error
        self._thread = threading.Thread(target=self._run, daemon=True)

    def start(self) -> None:
        self._thread.start()

    def _run(self) -> None:
        try:
            if self.platform == Platform.SPOTIFY:
                if self.library_type == "liked":
                    tracks = self.client.get_saved_tracks()
                elif self.library_type == "recent":
                    tracks = self.client.get_recently_played()
                elif self.library_type == "top":
                    tracks = self.client.get_top_tracks()
                else:
                    tracks = []
            elif self.platform == Platform.YOUTUBE:
                if self.library_type == "liked":
                    tracks = self.client.get_liked_videos()
                else:
                    tracks = []
            elif self.platform == Platform.SOUNDCLOUD:
                if self.library_type == "liked":
                    tracks = self.client.get_liked_tracks()
                elif self.library_type == "recent":
                    tracks = self.client.get_recently_played()
                else:
                    tracks = []
            else:
                tracks = []
            post(self.on_done, self.platform, self.library_type, tracks)
        except Exception as e:
            post(self.on_error, f"{self.platform.value}: {e}")
