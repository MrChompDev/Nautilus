"""Riptide Audio - Self-Contained Audio Engine (pygame.mixer)

No external players required. Handles:
  - Music playback from local files and HTTP URLs
  - Seeking, volume, shuffle, repeat
  - Track-end detection via background polling
  - Separate SFX channel bus (managed by SFXEngine)
"""
from __future__ import annotations

import os
import tempfile
import threading
import urllib.request
from collections.abc import Callable

from apps.RipTide import config
from apps.RipTide.models import Platform, PlaybackState, Track

try:
    os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")
    import pygame
    import pygame.mixer
    _PYGAME_AVAILABLE = True
except (ImportError, OSError):
    _PYGAME_AVAILABLE = False


def _init_mixer() -> bool:
    if not _PYGAME_AVAILABLE:
        return False
    try:
        if pygame.mixer.get_init():
            return True
        pygame.mixer.pre_init(
            frequency=44100,
            size=-16,
            channels=2,
            buffer=config.AUDIO_BUFFER_MS,
        )
        pygame.mixer.init()
        return True
    except Exception as e:
        print(f"[Riptide] Mixer init failed: {e}")
        return False


class AudioEngine:
    """Plays one music stream at a time via pygame.mixer.music.

    The SFXEngine (separate module) owns extra mixer Channels so SFX
    can play over the music bus without interruption.
    """

    def __init__(self):
        self._mixer_ok = _init_mixer()

        self._state = PlaybackState.STOPPED
        self._current_track: Track | None = None
        self._current_account = None
        self._playlist: list[Track] = []
        self._playlist_index: int = -1
        self._volume: int = config.MUSIC_VOLUME_DEFAULT
        self._shuffle: bool = False
        self._repeat: bool = False

        self._position_ms: int = 0
        self._duration_ms: int = 0
        self._track_start_tick: int = 0
        self._pause_offset_ms: int = 0
        self._last_poll_tick: int = 0

        self._lock = threading.Lock()
        self._tmp_files: list[str] = []
        self._api_clients: dict = {}
        self._progress_thread: threading.Thread | None = None
        self._progress_stop = threading.Event()

        self.on_track_changed: Callable[[Track | None], None] | None = None
        self.on_state_changed: Callable[[PlaybackState], None] | None = None
        self.on_position_changed: Callable[[int, int], None] | None = None
        self.on_playlist_end: Callable[[], None] | None = None

    # -- Registration --

    def register_api_client(self, platform: Platform, client) -> None:
        self._api_clients[platform] = client

    # -- Properties --

    @property
    def state(self) -> PlaybackState:
        return self._state

    @property
    def current_track(self) -> Track | None:
        return self._current_track

    @property
    def volume(self) -> int:
        return self._volume

    @property
    def position_ms(self) -> int:
        if self._state == PlaybackState.PLAYING:
            elapsed = pygame.time.get_ticks() - self._track_start_tick
            self._position_ms = self._pause_offset_ms + elapsed
        return self._position_ms

    @property
    def duration_ms(self) -> int:
        return self._duration_ms

    @property
    def shuffle(self) -> bool:
        return self._shuffle

    @property
    def repeat(self) -> bool:
        return self._repeat

    # -- Controls --

    def set_volume(self, volume: int) -> None:
        self._volume = max(0, min(100, volume))
        if self._mixer_ok and self._state != PlaybackState.STOPPED:
            try:
                pygame.mixer.music.set_volume(self._volume / 100.0)
            except Exception:
                pass

    def set_shuffle(self, enabled: bool) -> None:
        self._shuffle = enabled

    def set_repeat(self, enabled: bool) -> None:
        self._repeat = enabled

    def play_track(self, track: Track, account=None) -> None:
        if not self._mixer_ok:
            return
        with self._lock:
            self._stop_internal()
            self._current_track = track
            self._current_account = account
            self._pause_offset_ms = 0
            self._notify_track_changed()

            resolved = self._resolve_source(track)
            if resolved:
                self._load_and_play(resolved)
            else:
                self._fetch_stream_async(track)

    def play_playlist(self, tracks: list[Track], start_index: int = 0) -> None:
        with self._lock:
            self._playlist = tracks
            self._playlist_index = start_index
            if 0 <= start_index < len(tracks):
                self.play_track(tracks[start_index])

    def pause(self) -> None:
        with self._lock:
            if self._state == PlaybackState.PLAYING:
                try:
                    self._pause_offset_ms = self.position_ms
                    pygame.mixer.music.pause()
                    self._set_state(PlaybackState.PAUSED)
                except Exception:
                    pass

    def resume(self) -> None:
        with self._lock:
            if self._state == PlaybackState.PAUSED:
                try:
                    pygame.mixer.music.unpause()
                    self._track_start_tick = pygame.time.get_ticks()
                    self._set_state(PlaybackState.PLAYING)
                except Exception:
                    pass

    def stop(self) -> None:
        with self._lock:
            self._stop_internal()
            self._current_track = None
            self._position_ms = 0
            self._duration_ms = 0
            self._set_state(PlaybackState.STOPPED)
            self._notify_track_changed()

    def seek(self, position_ms: int) -> None:
        with self._lock:
            if not self._mixer_ok or self._state == PlaybackState.STOPPED:
                return
            try:
                pos_sec = max(0, position_ms) / 1000.0
                pygame.mixer.music.set_pos(pos_sec)
                self._pause_offset_ms = position_ms
                self._track_start_tick = pygame.time.get_ticks()
                self._position_ms = position_ms
            except Exception:
                pass

    def next_track(self) -> None:
        with self._lock:
            if not self._playlist:
                return
            if self._shuffle:
                import random
                self._playlist_index = random.randint(0, len(self._playlist) - 1)
            else:
                self._playlist_index += 1
            if self._playlist_index >= len(self._playlist):
                if self._repeat:
                    self._playlist_index = 0
                else:
                    self._stop_internal()
                    self._set_state(PlaybackState.STOPPED)
                    if self.on_playlist_end:
                        self.on_playlist_end()
                    return
            self.play_track(self._playlist[self._playlist_index])

    def previous_track(self) -> None:
        with self._lock:
            if self.position_ms > 3000:
                self.seek(0)
                return
            if not self._playlist:
                return
            self._playlist_index -= 1
            if self._playlist_index < 0:
                self._playlist_index = 0
            self.play_track(self._playlist[self._playlist_index])

    def get_playlist(self) -> list[Track]:
        return list(self._playlist)

    def get_playlist_index(self) -> int:
        return self._playlist_index

    # -- Internal --

    def _resolve_source(self, track: Track) -> str | None:
        if track.stream_url and track.stream_url.startswith(("http://", "https://")):
            return track.stream_url
        if track.preview_url and track.preview_url.startswith(("http://", "https://")):
            return track.preview_url
        return None

    def _load_and_play(self, source: str) -> None:
        try:
            if source.startswith(("http://", "https://")):
                tmp = self._download_to_tmp(source)
                if not tmp:
                    self._set_state(PlaybackState.STOPPED)
                    return
                source = tmp

            pygame.mixer.music.load(source)
            pygame.mixer.music.set_volume(self._volume / 100.0)
            pygame.mixer.music.play()
            self._track_start_tick = pygame.time.get_ticks()
            self._pause_offset_ms = 0
            self._duration_ms = self._probe_duration(source)
            self._set_state(PlaybackState.PLAYING)
        except Exception as e:
            print(f"[Riptide] Playback error: {e}")
            self._set_state(PlaybackState.STOPPED)

    def _fetch_stream_async(self, track: Track) -> None:
        def _worker():
            client = self._api_clients.get(track.platform)
            if not client:
                return
            stream_url = None
            try:
                if track.platform == Platform.SOUNDCLOUD:
                    stream_url = client.get_stream_url(track.platform_id)
                elif track.platform == Platform.SPOTIFY:
                    stream_url = track.preview_url
                elif track.platform == Platform.YOUTUBE:
                    stream_url = track.stream_url
            except Exception as e:
                print(f"[Riptide] Stream fetch error: {e}")
                return

            if stream_url:
                with self._lock:
                    if self._current_track and self._current_track.id == track.id:
                        self._load_and_play(stream_url)

        threading.Thread(target=_worker, daemon=True).start()

    def _download_to_tmp(self, url: str, max_bytes: int = 50 * 1024 * 1024) -> str | None:
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "RiptideAudio/3.0"})
            with urllib.request.urlopen(req, timeout=30) as resp:
                ext = ".mp3"
                ct = resp.headers.get("Content-Type", "")
                if "ogg" in ct or url.endswith(".ogg"):
                    ext = ".ogg"
                elif "wav" in ct or url.endswith(".wav"):
                    ext = ".wav"
                elif "flac" in ct or url.endswith(".flac"):
                    ext = ".flac"

                tmp = tempfile.NamedTemporaryFile(
                    delete=False, suffix=ext, prefix="riptide_"
                )
                total = 0
                while True:
                    chunk = resp.read(65536)
                    if not chunk:
                        break
                    total += len(chunk)
                    if total > max_bytes:
                        break
                    tmp.write(chunk)
                tmp.close()
                self._tmp_files.append(tmp.name)
                return tmp.name
        except Exception as e:
            print(f"[Riptide] Download error: {e}")
            return None

    @staticmethod
    def _probe_duration(filepath: str) -> int:
        try:
            info = pygame.mixer.Sound(filepath)
            samples = info.get_length()
            return int(samples * 1000)
        except Exception:
            return 0

    def _stop_internal(self) -> None:
        try:
            if self._mixer_ok and pygame.mixer.get_init():
                pygame.mixer.music.stop()
                pygame.mixer.music.unload()
        except Exception:
            pass
        self._stop_progress()
        self._cleanup_tmp_files()

    def _cleanup_tmp_files(self) -> None:
        for path in self._tmp_files:
            try:
                os.unlink(path)
            except Exception:
                pass
        self._tmp_files.clear()

    def _set_state(self, state: PlaybackState) -> None:
        if self._state != state:
            self._state = state
            if self.on_state_changed:
                self.on_state_changed(state)
            if state == PlaybackState.PLAYING:
                self._start_progress()
            elif state in (PlaybackState.STOPPED, PlaybackState.PAUSED):
                if state == PlaybackState.STOPPED:
                    self._stop_progress()

    def _start_progress(self) -> None:
        self._stop_progress()
        self._progress_stop.clear()
        self._progress_thread = threading.Thread(
            target=self._progress_loop, daemon=True
        )
        self._progress_thread.start()

    def _stop_progress(self) -> None:
        self._progress_stop.set()

    def _progress_loop(self) -> None:
        while not self._progress_stop.is_set():
            if self._state == PlaybackState.PLAYING:
                pos = self.position_ms
                dur = self.duration_ms
                if self.on_position_changed and dur > 0:
                    self.on_position_changed(pos, dur)
                if not pygame.mixer.music.get_busy() and self._current_track:
                    _after(self.next_track)
            self._progress_stop.wait(0.5)

    def _notify_track_changed(self) -> None:
        if self.on_track_changed:
            self.on_track_changed(self._current_track)

    def cleanup(self) -> None:
        self._stop_progress()
        self._stop_internal()
        if self._mixer_ok:
            try:
                pygame.mixer.quit()
            except Exception:
                pass


def _after(func):
    """Run func on the GUI thread via the Qt dispatcher (wx fallback)."""
    try:
        from apps.RipTide.workers.api_workers import post
        post(func)
    except Exception:
        try:
            import wx
            wx.CallAfter(func)
        except ImportError:
            func()
