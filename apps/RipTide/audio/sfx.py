"""Riptide Audio - SFX Soundboard Engine (pygame.mixer)

Self-contained SFX playback using pygame.mixer channels.
Multiple sounds can play simultaneously on separate channels.
SFX plays OVER the music bus without interrupting it.
"""
from __future__ import annotations

import os
import threading
from collections.abc import Callable

from apps.RipTide import config
from apps.RipTide.models import SFXClip

try:
    os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")
    import pygame
    import pygame.mixer
    _PYGAME_AVAILABLE = True
except (ImportError, OSError):
    _PYGAME_AVAILABLE = False


def _ensure_mixer() -> bool:
    if not _PYGAME_AVAILABLE:
        return False
    try:
        if not pygame.mixer.get_init():
            pygame.mixer.pre_init(frequency=44100, size=-16, channels=2, buffer=512)
            pygame.mixer.init()
        return True
    except Exception:
        return False


class SFXChannel:
    __slots__ = ("_channel", "_playing", "_sound", "clip")

    def __init__(self, clip: SFXClip):
        self.clip = clip
        self._sound: pygame.mixer.Sound | None = None
        self._channel: pygame.mixer.Channel | None = None
        self._playing = False

    def load(self) -> bool:
        if not os.path.isfile(self.clip.file_path):
            print(f"[Riptide SFX] File not found: {self.clip.file_path}")
            return False
        try:
            self._sound = pygame.mixer.Sound(self.clip.file_path)
            return True
        except Exception as e:
            print(f"[Riptide SFX] Load error: {e}")
            return False

    def play(self, master_volume: int) -> None:
        if not self._sound:
            if not self.load():
                return
        ch = pygame.mixer.find_channel(True)
        if not ch:
            print("[Riptide SFX] No free mixer channel")
            return
        self._channel = ch
        effective_vol = (master_volume / 100.0) * self.clip.volume
        self._sound.set_volume(max(0.0, min(1.0, effective_vol)))
        ch.play(self._sound)
        self._playing = True

    def stop(self) -> None:
        if self._channel:
            self._channel.stop()
        self._playing = False

    @property
    def is_playing(self) -> bool:
        if self._channel and self._playing:
            return self._channel.get_busy()
        return False


class SFXEngine:
    def __init__(self):
        self._mixer_ok = _ensure_mixer()
        self._volume: int = config.SFX_VOLUME_DEFAULT
        self._clips: list[SFXClip] = []
        self._hotkey_map: dict[str, SFXClip] = {}
        self._active: list[SFXChannel] = []
        self._lock = threading.Lock()
        self.on_clip_triggered: Callable[[SFXClip], None] | None = None

    def set_volume(self, volume: int) -> None:
        self._volume = max(0, min(100, volume))

    @property
    def volume(self) -> int:
        return self._volume

    def load_clips(self, clips: list[SFXClip]) -> None:
        with self._lock:
            self._clips = clips
            self._hotkey_map.clear()
            for clip in clips:
                if clip.hotkey:
                    self._hotkey_map[clip.hotkey.lower()] = clip

    def trigger_clip(self, clip: SFXClip) -> None:
        if not self._mixer_ok:
            return
        with self._lock:
            self._cleanup()
            channel = SFXChannel(clip)
            channel.play(self._volume)
            self._active.append(channel)
            if self.on_clip_triggered:
                self.on_clip_triggered(clip)

    def trigger_by_hotkey(self, hotkey: str) -> bool:
        clip = self._hotkey_map.get(hotkey.lower())
        if clip:
            self.trigger_clip(clip)
            return True
        return False

    def stop_all(self) -> None:
        with self._lock:
            for ch in self._active:
                ch.stop()
            self._active.clear()

    def stop_clip(self, clip: SFXClip) -> None:
        with self._lock:
            remaining = []
            for ch in self._active:
                if ch.clip.id == clip.id:
                    ch.stop()
                else:
                    remaining.append(ch)
            self._active = remaining

    def _cleanup(self) -> None:
        self._active = [ch for ch in self._active if ch.is_playing]

    def get_playing_clips(self) -> list[SFXClip]:
        with self._lock:
            self._cleanup()
            return [ch.clip for ch in self._active]

    def cleanup(self) -> None:
        self.stop_all()
