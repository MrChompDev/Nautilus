"""Riptide Audio - Database Layer"""
from __future__ import annotations

import sqlite3
import time
from pathlib import Path

from apps.RipTide import config
from apps.RipTide.models import Account, Platform, Playlist, SFXClip, Track


class Database:
    def __init__(self, db_path: Path = config.DB_PATH):
        self.db_path = db_path
        self._conn: sqlite3.Connection | None = None
        self._init_db()

    def _get_conn(self) -> sqlite3.Connection:
        if self._conn is None:
            self._conn = sqlite3.connect(str(self.db_path))
            self._conn.row_factory = sqlite3.Row
            self._conn.execute("PRAGMA journal_mode=WAL")
            self._conn.execute("PRAGMA foreign_keys=ON")
        return self._conn

    def _init_db(self) -> None:
        conn = self._get_conn()
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS accounts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                platform TEXT NOT NULL,
                display_name TEXT NOT NULL DEFAULT '',
                username TEXT NOT NULL DEFAULT '',
                access_token TEXT NOT NULL DEFAULT '',
                refresh_token TEXT NOT NULL DEFAULT '',
                token_expires REAL NOT NULL DEFAULT 0,
                is_active INTEGER NOT NULL DEFAULT 1,
                avatar_url TEXT NOT NULL DEFAULT '',
                created_at REAL NOT NULL DEFAULT 0
            );

            CREATE TABLE IF NOT EXISTS tracks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                platform TEXT NOT NULL,
                platform_id TEXT NOT NULL,
                title TEXT NOT NULL DEFAULT '',
                artist TEXT NOT NULL DEFAULT '',
                album TEXT NOT NULL DEFAULT '',
                duration_ms INTEGER NOT NULL DEFAULT 0,
                thumbnail_url TEXT NOT NULL DEFAULT '',
                preview_url TEXT DEFAULT NULL,
                stream_url TEXT DEFAULT NULL,
                explicit INTEGER NOT NULL DEFAULT 0,
                popularity INTEGER NOT NULL DEFAULT 0,
                account_id INTEGER DEFAULT NULL,
                FOREIGN KEY (account_id) REFERENCES accounts(id) ON DELETE SET NULL
            );

            CREATE TABLE IF NOT EXISTS playlists (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL DEFAULT '',
                description TEXT NOT NULL DEFAULT '',
                is_mega INTEGER NOT NULL DEFAULT 1,
                created_at REAL NOT NULL DEFAULT 0,
                updated_at REAL NOT NULL DEFAULT 0
            );

            CREATE TABLE IF NOT EXISTS playlist_tracks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                playlist_id INTEGER NOT NULL,
                track_id INTEGER NOT NULL,
                position INTEGER NOT NULL DEFAULT 0,
                added_at REAL NOT NULL DEFAULT 0,
                FOREIGN KEY (playlist_id) REFERENCES playlists(id) ON DELETE CASCADE,
                FOREIGN KEY (track_id) REFERENCES tracks(id) ON DELETE CASCADE,
                UNIQUE(playlist_id, track_id)
            );

            CREATE TABLE IF NOT EXISTS sfx_clips (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL DEFAULT '',
                file_path TEXT NOT NULL DEFAULT '',
                hotkey TEXT NOT NULL DEFAULT '',
                category TEXT NOT NULL DEFAULT 'general',
                volume REAL NOT NULL DEFAULT 1.0,
                duration_ms INTEGER NOT NULL DEFAULT 0,
                is_builtin INTEGER NOT NULL DEFAULT 0
            );

            CREATE INDEX IF NOT EXISTS idx_tracks_platform
                ON tracks(platform, platform_id);
            CREATE INDEX IF NOT EXISTS idx_tracks_account
                ON tracks(account_id);
            CREATE INDEX IF NOT EXISTS idx_playlist_tracks_playlist
                ON playlist_tracks(playlist_id);
            CREATE INDEX IF NOT EXISTS idx_accounts_platform
                ON accounts(platform);
        """)
        conn.commit()

    def close(self) -> None:
        if self._conn:
            self._conn.close()
            self._conn = None

    # -- Accounts --

    def upsert_account(self, account: Account) -> int:
        conn = self._get_conn()
        existing = self.get_account_by_platform(
            account.platform, account.username
        )
        if existing and existing.id:
            conn.execute(
                """UPDATE accounts SET
                    display_name=?, access_token=?, refresh_token=?,
                    token_expires=?, avatar_url=?, is_active=1
                WHERE id=?""",
                (
                    account.display_name,
                    account.access_token,
                    account.refresh_token,
                    account.token_expires,
                    account.avatar_url,
                    existing.id,
                ),
            )
            conn.commit()
            return existing.id
        cursor = conn.execute(
            """INSERT INTO accounts
                (platform, display_name, username, access_token,
                 refresh_token, token_expires, is_active, avatar_url, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                account.platform.value,
                account.display_name,
                account.username,
                account.access_token,
                account.refresh_token,
                account.token_expires,
                int(account.is_active),
                account.avatar_url,
                account.created_at,
            ),
        )
        conn.commit()
        return cursor.lastrowid

    def get_account(self, account_id: int) -> Account | None:
        conn = self._get_conn()
        row = conn.execute(
            "SELECT * FROM accounts WHERE id=?", (account_id,)
        ).fetchone()
        return self._row_to_account(row) if row else None

    def get_account_by_platform(
        self, platform: Platform, username: str
    ) -> Account | None:
        conn = self._get_conn()
        row = conn.execute(
            "SELECT * FROM accounts WHERE platform=? AND username=?",
            (platform.value, username),
        ).fetchone()
        return self._row_to_account(row) if row else None

    def get_accounts(
        self, platform: Platform | None = None, active_only: bool = True
    ) -> list[Account]:
        conn = self._get_conn()
        if platform:
            query = "SELECT * FROM accounts WHERE platform=?"
            params: tuple = (platform.value,)
        else:
            query = "SELECT * FROM accounts WHERE 1=1"
            params = ()
        if active_only:
            query += " AND is_active=1"
        rows = conn.execute(query, params).fetchall()
        return [self._row_to_account(r) for r in rows]

    def delete_account(self, account_id: int) -> None:
        conn = self._get_conn()
        conn.execute("DELETE FROM accounts WHERE id=?", (account_id,))
        conn.commit()

    @staticmethod
    def _row_to_account(row: sqlite3.Row) -> Account:
        return Account(
            id=row["id"],
            platform=Platform(row["platform"]),
            display_name=row["display_name"],
            username=row["username"],
            access_token=row["access_token"],
            refresh_token=row["refresh_token"],
            token_expires=row["token_expires"],
            is_active=bool(row["is_active"]),
            avatar_url=row["avatar_url"],
            created_at=row["created_at"],
        )

    # -- Tracks --

    def insert_track(self, track: Track) -> int:
        conn = self._get_conn()
        cursor = conn.execute(
            """INSERT OR IGNORE INTO tracks
                (platform, platform_id, title, artist, album, duration_ms,
                 thumbnail_url, preview_url, stream_url, explicit, popularity,
                 account_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                track.platform.value,
                track.platform_id,
                track.title,
                track.artist,
                track.album,
                track.duration_ms,
                track.thumbnail_url,
                track.preview_url,
                track.stream_url,
                int(track.explicit),
                track.popularity,
                track.account_id,
            ),
        )
        conn.commit()
        if cursor.lastrowid:
            return cursor.lastrowid
        row = conn.execute(
            "SELECT id FROM tracks WHERE platform=? AND platform_id=?",
            (track.platform.value, track.platform_id),
        ).fetchone()
        return row["id"] if row else 0

    def get_track(self, track_id: int) -> Track | None:
        conn = self._get_conn()
        row = conn.execute(
            "SELECT * FROM tracks WHERE id=?", (track_id,)
        ).fetchone()
        return self._row_to_track(row) if row else None

    def search_tracks(
        self, query: str, limit: int = 50
    ) -> list[Track]:
        conn = self._get_conn()
        like = f"%{query}%"
        rows = conn.execute(
            """SELECT * FROM tracks
            WHERE title LIKE ? OR artist LIKE ? OR album LIKE ?
            ORDER BY popularity DESC LIMIT ?""",
            (like, like, like, limit),
        ).fetchall()
        return [self._row_to_track(r) for r in rows]

    def get_recent_tracks(self, limit: int = 50) -> list[Track]:
        conn = self._get_conn()
        rows = conn.execute(
            """SELECT t.* FROM tracks t
            INNER JOIN playlist_tracks pt ON t.id = pt.track_id
            ORDER BY pt.added_at DESC LIMIT ?""",
            (limit,),
        ).fetchall()
        return [self._row_to_track(r) for r in rows]

    @staticmethod
    def _row_to_track(row: sqlite3.Row) -> Track:
        return Track(
            id=row["id"],
            platform=Platform(row["platform"]),
            platform_id=row["platform_id"],
            title=row["title"],
            artist=row["artist"],
            album=row["album"],
            duration_ms=row["duration_ms"],
            thumbnail_url=row["thumbnail_url"],
            preview_url=row["preview_url"],
            stream_url=row["stream_url"],
            explicit=bool(row["explicit"]),
            popularity=row["popularity"],
            account_id=row["account_id"],
        )

    # -- Playlists --

    def create_playlist(self, playlist: Playlist) -> int:
        conn = self._get_conn()
        cursor = conn.execute(
            """INSERT INTO playlists (name, description, is_mega, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?)""",
            (
                playlist.name,
                playlist.description,
                int(playlist.is_mega),
                playlist.created_at,
                playlist.updated_at,
            ),
        )
        conn.commit()
        return cursor.lastrowid

    def get_playlist(self, playlist_id: int) -> Playlist | None:
        conn = self._get_conn()
        row = conn.execute(
            "SELECT * FROM playlists WHERE id=?", (playlist_id,)
        ).fetchone()
        if not row:
            return None
        pl = self._row_to_playlist(row)
        count_row = conn.execute(
            "SELECT COUNT(*) as cnt FROM playlist_tracks WHERE playlist_id=?",
            (playlist_id,),
        ).fetchone()
        pl.track_count = count_row["cnt"]
        return pl

    def get_playlists(self) -> list[Playlist]:
        conn = self._get_conn()
        rows = conn.execute(
            "SELECT * FROM playlists ORDER BY updated_at DESC"
        ).fetchall()
        result = []
        for row in rows:
            pl = self._row_to_playlist(row)
            cnt = conn.execute(
                "SELECT COUNT(*) as cnt FROM playlist_tracks WHERE playlist_id=?",
                (row["id"],),
            ).fetchone()
            pl.track_count = cnt["cnt"]
            result.append(pl)
        return result

    def delete_playlist(self, playlist_id: int) -> None:
        conn = self._get_conn()
        conn.execute("DELETE FROM playlists WHERE id=?", (playlist_id,))
        conn.commit()

    def add_track_to_playlist(
        self, playlist_id: int, track_id: int, position: int = -1
    ) -> int:
        conn = self._get_conn()
        if position < 0:
            max_pos = conn.execute(
                "SELECT COALESCE(MAX(position), -1) as mp FROM playlist_tracks WHERE playlist_id=?",
                (playlist_id,),
            ).fetchone()
            position = max_pos["mp"] + 1
        cursor = conn.execute(
            """INSERT OR IGNORE INTO playlist_tracks
                (playlist_id, track_id, position, added_at)
            VALUES (?, ?, ?, ?)""",
            (playlist_id, track_id, position, time.time()),
        )
        conn.execute(
            "UPDATE playlists SET updated_at=? WHERE id=?",
            (time.time(), playlist_id),
        )
        conn.commit()
        return cursor.lastrowid

    def remove_track_from_playlist(
        self, playlist_id: int, track_id: int
    ) -> None:
        conn = self._get_conn()
        conn.execute(
            """DELETE FROM playlist_tracks
            WHERE playlist_id=? AND track_id=?""",
            (playlist_id, track_id),
        )
        conn.commit()

    def get_playlist_tracks(self, playlist_id: int) -> list[Track]:
        conn = self._get_conn()
        rows = conn.execute(
            """SELECT t.* FROM tracks t
            INNER JOIN playlist_tracks pt ON t.id = pt.track_id
            WHERE pt.playlist_id = ?
            ORDER BY pt.position ASC""",
            (playlist_id,),
        ).fetchall()
        return [self._row_to_track(r) for r in rows]

    def reorder_playlist_track(
        self, playlist_id: int, track_id: int, new_position: int
    ) -> None:
        conn = self._get_conn()
        conn.execute(
            """UPDATE playlist_tracks SET position=?
            WHERE playlist_id=? AND track_id=?""",
            (new_position, playlist_id, track_id),
        )
        conn.commit()

    @staticmethod
    def _row_to_playlist(row: sqlite3.Row) -> Playlist:
        return Playlist(
            id=row["id"],
            name=row["name"],
            description=row["description"],
            is_mega=bool(row["is_mega"]),
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )

    # -- SFX --

    def add_sfx_clip(self, clip: SFXClip) -> int:
        conn = self._get_conn()
        cursor = conn.execute(
            """INSERT INTO sfx_clips
                (name, file_path, hotkey, category, volume, duration_ms, is_builtin)
            VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (
                clip.name,
                clip.file_path,
                clip.hotkey,
                clip.category,
                clip.volume,
                clip.duration_ms,
                int(clip.is_builtin),
            ),
        )
        conn.commit()
        return cursor.lastrowid

    def get_sfx_clips(
        self, category: str | None = None
    ) -> list[SFXClip]:
        conn = self._get_conn()
        if category:
            rows = conn.execute(
                "SELECT * FROM sfx_clips WHERE category=? ORDER BY name",
                (category,),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM sfx_clips ORDER BY category, name"
            ).fetchall()
        return [self._row_to_sfx(r) for r in rows]

    def delete_sfx_clip(self, clip_id: int) -> None:
        conn = self._get_conn()
        conn.execute("DELETE FROM sfx_clips WHERE id=?", (clip_id,))
        conn.commit()

    def update_sfx_clip(self, clip: SFXClip) -> None:
        if not clip.id:
            return
        conn = self._get_conn()
        conn.execute(
            """UPDATE sfx_clips SET
                name=?, hotkey=?, category=?, volume=?
            WHERE id=?""",
            (clip.name, clip.hotkey, clip.category, clip.volume, clip.id),
        )
        conn.commit()

    @staticmethod
    def _row_to_sfx(row: sqlite3.Row) -> SFXClip:
        return SFXClip(
            id=row["id"],
            name=row["name"],
            file_path=row["file_path"],
            hotkey=row["hotkey"],
            category=row["category"],
            volume=row["volume"],
            duration_ms=row["duration_ms"],
            is_builtin=bool(row["is_builtin"]),
        )
