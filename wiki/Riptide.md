# Riptide Audio

**The Nautilus audio hub** — multi-provider music streaming plus an SFX
soundboard, all in one window.

- **Launch:** `python3 apps/RipTide/main.py` or `Ctrl+Alt+R`
- **Memory target:** ~60 MB
- **UI:** PySide6 (+ `requests` + `pygame`)

## Overview

Riptide is a full music client with a sidebar for Dashboard, Search,
Playlists, the SFX Board, and Settings, plus a persistent Now Playing bar for
transport controls.

## Features

- **Multi-provider streaming** — Spotify, YouTube, and SoundCloud via
  provider-specific API clients (`api/`):
  - Spotify: search, playlists, saved/recent/top tracks, recommendations,
    playback control, with 401-refresh and 429-retry handling.
  - YouTube: Data v3 search with ISO-8601 duration parsing.
  - SoundCloud: API client.
- **OAuth** — PKCE/S256 flow for Spotify, OAuth for YouTube and SoundCloud via
  a local callback server on `127.0.0.1:8765` (`auth/`).
- **Audio engine** — `pygame.mixer.music` playback at 44.1 kHz / 16-bit /
  2-channel with a 300 ms buffer; streams from local files and HTTP URLs
  (`audio/engine.py`).
- **SFX soundboard** — multi-channel SFX engine for rapid sound clips
  (`audio/sfx.py`).
- **Library** — SQLite (WAL mode) backing accounts, tracks, playlists, and SFX
  clips (`database/db.py`).
- **Non-blocking UI** — background daemon worker threads for dashboard,
  search, and library loading, marshalled back to the GUI through a queued
  signal dispatcher (`workers/api_workers.py`).

## How It Plays

1. Connect an account through Settings (OAuth in a browser dialog).
2. Search across providers (400 ms debounced input + platform filter).
3. Stream tracks through the Now Playing bar, or trigger SFX clips from the
   soundboard.

## Dependencies

| Package | Purpose |
| :--- | :--- |
| `requests` | Spotify / SoundCloud / YouTube API calls |
| `pygame` | Audio engine + SFX soundboard |
