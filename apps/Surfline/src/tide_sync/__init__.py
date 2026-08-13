"""
TideSync - Profile & Credential Manager
Isolated sandboxing with local-first JSON storage.

Passwords can be protected by an optional master-password vault:
  * Key derivation  -> PBKDF2-HMAC-SHA256 (200,000 iterations, stdlib)
  * Encryption      -> AES-256-GCM via the `cryptography` package
  * At-rest format  -> "ENC:<urlsafe base64(iv || ciphertext || tag)>"

If `cryptography` is not installed the vault feature is disabled at runtime
(no plaintext is written while a vault exists), and enabling it raises a
clear error telling the user to install the dependency.
"""
import base64
import hashlib
import hmac
import json
import os
import secrets
import shutil
import time

try:
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    _CRYPTO_AVAILABLE = True
except ImportError:  # pragma: no cover - dependency not installed
    AESGCM = None
    _CRYPTO_AVAILABLE = False

VAULT_PREFIX = "ENC:"
VAULT_ITERATIONS = 200_000
VAULT_KEY_LEN = 32  # AES-256

DEFAULT_SETTINGS = {
    "homepage": "about:blank",
    "javascript_enabled": True,
    "images_enabled": True,
    "search_engine": "Google",
    "search_url": "https://www.google.com/search?q={}",
    "default_zoom": 100,
    "font_size": 12,
    "download_path": "",
    "ask_download_location": True,
    "show_statusbar": True,
    "show_bookmarks_bar": False,
    "enable_do_not_track": True,
    "accept_cookies": True,
    "clear_on_exit": False,
    "clear_cookies": False,
    "clear_cache": False,
    "clear_history": False,
    "startup_page": "new_tab",
    "enable_webgl": True,
    "enable_webaudio": True,
    "enable_notifications": True,
    "enable_geolocation": False,
    "auto_play_media": True,
    "smooth_scrolling": True,
    "tab_close_activates_nearest": True,
    "warn_on_close": False,
    "accent_color": "#00F2C2",
    # Vault settings (internal)
    "vault_enabled": False,
    "vault_salt": "",
    "vault_master_hash": "",
}


class Profile:
    def __init__(self, name: str, directory: str):
        self.name = name
        self.directory = directory
        self.bookmarks = []
        self.history = []
        self.passwords = []
        self.settings = {}
        self.created_at = time.time()

    def to_dict(self):
        return {
            "name": self.name,
            "bookmarks": self.bookmarks,
            "settings": self.settings,
            "passwords": self.passwords,
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, data: dict, directory: str):
        p = cls(data.get("name", "default"), directory)
        p.bookmarks = data.get("bookmarks", [])
        p.settings = data.get("settings", {})
        p.passwords = data.get("passwords", [])
        p.created_at = data.get("created_at", time.time())
        return p


def crypto_available() -> bool:
    """True when AES-GCM encryption can be used."""
    return _CRYPTO_AVAILABLE


def _derive_vault_key(master_password: str, salt_hex: str, iterations: int = VAULT_ITERATIONS) -> bytes:
    """PBKDF2-HMAC-SHA256 key derivation (pure stdlib)."""
    salt = bytes.fromhex(salt_hex)
    return hashlib.pbkdf2_hmac("sha256", master_password.encode("utf-8"), salt, iterations)


class TideSyncManager:
    def __init__(self, base_dir: str = None):
        env_dir = os.environ.get("NAUTILUS_PROFILES_DIR")
        if base_dir:
            self.base_dir = base_dir
        elif env_dir:
            self.base_dir = env_dir
        else:
            self.base_dir = os.path.join(
                os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
                "assets", "profiles"
            )
        os.makedirs(self.base_dir, exist_ok=True)
        self.profiles = {}
        self.active_profile_name = None
        self.global_settings = dict(DEFAULT_SETTINGS)
        self._settings_file = os.path.join(self.base_dir, "settings.json")
        self._vault_key: bytes | None = None
        self._load_all_profiles()
        self._load_global_settings()

    # ── Vault (master-password encryption) ──────────────────────

    @property
    def vault_enabled(self) -> bool:
        return bool(self.global_settings.get("vault_enabled"))

    def is_vault_unlocked(self) -> bool:
        return self.vault_enabled and self._vault_key is not None

    def set_master_password(self, master_password: str) -> bool:
        """Enable the vault: derive+store a verifier, encrypt existing plaintext
        passwords. Returns True on success."""
        if not master_password:
            return False
        if not crypto_available():
            raise RuntimeError(
                "Password vault requires the 'cryptography' package. "
                "Install it with:  py -3.13 -m pip install cryptography"
            )
        salt_hex = secrets.token_hex(16)
        key = _derive_vault_key(master_password, salt_hex)
        verifier = hashlib.pbkdf2_hmac(
            "sha256", master_password.encode("utf-8"),
            bytes.fromhex(salt_hex), VAULT_ITERATIONS
        ).hex()
        self.global_settings["vault_enabled"] = True
        self.global_settings["vault_salt"] = salt_hex
        self.global_settings["vault_master_hash"] = verifier
        self._save_global_settings()
        self._vault_key = key
        # Encrypt any plaintext passwords already stored
        for name in list(self.profiles.keys()):
            prof = self.profiles[name]
            changed = False
            for pw in prof.passwords:
                blob = pw.get("password", "")
                if not blob.startswith(VAULT_PREFIX):
                    pw["password"] = self._encrypt_secret(blob)
                    changed = True
            if changed:
                self._save_profile(name)
        return True

    def unlock_vault(self, master_password: str) -> bool:
        """Derive the vault key and verify the master password. Returns True on success."""
        if not self.vault_enabled:
            return False
        salt_hex = self.global_settings.get("vault_salt", "")
        expected = self.global_settings.get("vault_master_hash", "")
        if not salt_hex or not expected:
            return False
        candidate = hashlib.pbkdf2_hmac(
            "sha256", master_password.encode("utf-8"),
            bytes.fromhex(salt_hex), VAULT_ITERATIONS
        ).hex()
        if not hmac.compare_digest(candidate, expected):
            return False
        self._vault_key = _derive_vault_key(master_password, salt_hex)
        return True

    def lock_vault(self):
        self._vault_key = None

    def change_master_password(self, old_password: str, new_password: str) -> bool:
        """Verify the current master password, then re-key the entire vault."""
        if not self.unlock_vault(old_password):
            return False
        old_key = self._vault_key
        payloads = []  # (profile_name, entry, plaintext)
        for name in self.profiles:
            for entry in self.profiles[name].passwords:
                blob = entry.get("password", "")
                if blob.startswith(VAULT_PREFIX):
                    plain = self._decrypt_secret(blob, key=old_key)
                    payloads.append((name, entry, plain or ""))
        if not self.set_master_password(new_password):
            return False
        for name, entry, plain in payloads:
            entry["password"] = self._encrypt_secret(plain)
        for name in {p[0] for p in payloads}:
            self._save_profile(name)
        return True

    def _encrypt_secret(self, plaintext: str, key: bytes | None = None) -> str:
        key = key or self._vault_key
        if key is None:
            return plaintext  # legacy plaintext mode (no vault configured)
        iv = secrets.token_bytes(12)
        ct = AESGCM(key).encrypt(iv, plaintext.encode("utf-8"), None)
        return VAULT_PREFIX + base64.urlsafe_b64encode(iv + ct).decode("ascii")

    def _decrypt_secret(self, blob: str, key: bytes | None = None) -> str | None:
        key = key or self._vault_key
        if key is None:
            return None
        if not blob.startswith(VAULT_PREFIX):
            return blob
        try:
            raw = base64.urlsafe_b64decode(blob[len(VAULT_PREFIX):].encode("ascii"))
            iv, ct = raw[:12], raw[12:]
            return AESGCM(key).decrypt(iv, ct, None).decode("utf-8")
        except Exception:
            return None

    # ── Persistence ─────────────────────────────────────────────

    def _load_all_profiles(self):
        profiles_index = os.path.join(self.base_dir, "profiles.json")
        if os.path.exists(profiles_index):
            try:
                with open(profiles_index) as f:
                    data = json.load(f)
                for name in data.get("profiles", []):
                    prof_dir = os.path.join(self.base_dir, name)
                    profile_file = os.path.join(prof_dir, "profile.json")
                    if os.path.exists(profile_file):
                        with open(profile_file) as f:
                            pdata = json.load(f)
                        self.profiles[name] = Profile.from_dict(pdata, prof_dir)
            except (OSError, json.JSONDecodeError):
                pass

        if not self.profiles:
            self.create_profile("Dev")
            self.create_profile("Prod")
            self.create_profile("Personal")
            self.set_active("Dev")

    def _save_index(self):
        profiles_index = os.path.join(self.base_dir, "profiles.json")
        data = {
            "profiles": list(self.profiles.keys()),
            "active": self.active_profile_name,
        }
        with open(profiles_index, "w") as f:
            json.dump(data, f, indent=2)

    def _save_profile(self, name: str):
        if name in self.profiles:
            prof = self.profiles[name]
            prof_dir = prof.directory
            os.makedirs(prof_dir, exist_ok=True)
            profile_file = os.path.join(prof_dir, "profile.json")
            with open(profile_file, "w") as f:
                json.dump(prof.to_dict(), f, indent=2)

    def _load_global_settings(self):
        if os.path.exists(self._settings_file):
            try:
                with open(self._settings_file) as f:
                    saved = json.load(f)
                self.global_settings.update(saved)
            except (OSError, json.JSONDecodeError):
                pass

    def _save_global_settings(self):
        with open(self._settings_file, "w") as f:
            json.dump(self.global_settings, f, indent=2)

    def get_setting(self, key: str, default=None):
        return self.global_settings.get(key, default)

    def set_setting(self, key: str, value):
        self.global_settings[key] = value
        self._save_global_settings()

    def update_settings(self, settings: dict):
        self.global_settings.update(settings)
        self._save_global_settings()

    def get_all_settings(self) -> dict:
        return dict(self.global_settings)

    def create_profile(self, name: str) -> Profile:
        prof_dir = os.path.join(self.base_dir, name)
        for sub in ["cookies", "local_storage", "cache", "bookmarks", "passwords"]:
            os.makedirs(os.path.join(prof_dir, sub), exist_ok=True)
        profile = Profile(name, prof_dir)
        self.profiles[name] = profile
        self._save_profile(name)
        self._save_index()
        return profile

    def delete_profile(self, name: str) -> bool:
        if name not in self.profiles:
            return False
        prof = self.profiles[name]
        if os.path.exists(prof.directory):
            shutil.rmtree(prof.directory, ignore_errors=True)
        del self.profiles[name]
        if self.active_profile_name == name:
            self.active_profile_name = None
        self._save_index()
        return True

    def set_active(self, name: str) -> bool:
        if name not in self.profiles:
            return False
        self.active_profile_name = name
        self._save_index()
        return True

    def get_active(self) -> Profile | None:
        if self.active_profile_name and self.active_profile_name in self.profiles:
            return self.profiles[self.active_profile_name]
        return None

    def get_profile_names(self):
        return list(self.profiles.keys())

    def add_bookmark(self, profile_name: str, url: str, title: str = ""):
        if profile_name in self.profiles:
            prof = self.profiles[profile_name]
            prof.bookmarks.append({
                "url": url,
                "title": title or url,
                "added_at": time.time(),
            })
            self._save_profile(profile_name)

    def get_bookmarks(self, profile_name: str):
        if profile_name in self.profiles:
            return self.profiles[profile_name].bookmarks
        return []

    def import_bookmarks(self, profile_name: str, bookmarks: list):
        if profile_name not in self.profiles:
            return 0
        prof = self.profiles[profile_name]
        existing_urls = {b.get("url") for b in prof.bookmarks}
        imported = 0
        for bm in bookmarks:
            url = bm.get("url", "")
            if url and url not in existing_urls:
                prof.bookmarks.append({
                    "url": url,
                    "title": bm.get("title", url),
                    "added_at": bm.get("added_at", time.time()),
                })
                existing_urls.add(url)
                imported += 1
        self._save_profile(profile_name)
        return imported

    def add_history(self, profile_name: str, url: str, title: str = ""):
        if profile_name in self.profiles:
            prof = self.profiles[profile_name]
            prof.history.append({
                "url": url,
                "title": title or url,
                "visited_at": time.time(),
            })
            if len(prof.history) > 5000:
                prof.history = prof.history[-5000:]
            self._save_profile(profile_name)

    def import_history(self, profile_name: str, history: list):
        if profile_name not in self.profiles:
            return 0
        prof = self.profiles[profile_name]
        existing = {(h.get("url"), h.get("visited_at", 0)) for h in prof.history}
        imported = 0
        for entry in history:
            key = (entry.get("url", ""), entry.get("visited_at", 0))
            if key not in existing:
                prof.history.append({
                    "url": entry.get("url", ""),
                    "title": entry.get("title", entry.get("url", "")),
                    "visited_at": entry.get("visited_at", time.time()),
                })
                imported += 1
        if len(prof.history) > 10000:
            prof.history = prof.history[-10000:]
        self._save_profile(profile_name)
        return imported

    # ── Passwords (vault-aware) ─────────────────────────────────

    def add_password(self, profile_name: str, url: str, username: str, password: str):
        if profile_name not in self.profiles:
            return
        if self.vault_enabled and self._vault_key is None:
            raise ValueError("Password vault is locked — unlock it before saving passwords.")
        prof = self.profiles[profile_name]
        stored = self._encrypt_secret(password)
        for pw in prof.passwords:
            if pw.get("url") == url and pw.get("username") == username:
                pw["password"] = stored
                pw["updated_at"] = time.time()
                self._save_profile(profile_name)
                return
        prof.passwords.append({
            "url": url,
            "username": username,
            "password": stored,
            "created_at": time.time(),
        })
        self._save_profile(profile_name)

    def get_passwords(self, profile_name: str) -> list:
        """Return passwords, decrypted when the vault is unlocked.

        Locked entries come back with ``password == ""`` and ``locked: True``
        so callers can prompt for the master password instead of showing junk."""
        if profile_name not in self.profiles:
            return []
        result = []
        for p in self.profiles[profile_name].passwords:
            entry = dict(p)
            blob = entry.get("password", "")
            if blob.startswith(VAULT_PREFIX):
                if self._vault_key is None:
                    entry["password"] = ""
                    entry["locked"] = True
                else:
                    entry["password"] = self._decrypt_secret(blob) or ""
            result.append(entry)
        return result

    def import_passwords(self, profile_name: str, passwords: list):
        if profile_name not in self.profiles:
            return 0
        if self.vault_enabled and self._vault_key is None:
            # Never persist plaintext into a locked vault.
            return 0
        prof = self.profiles[profile_name]
        existing = {(p.get("url"), p.get("username")) for p in prof.passwords}
        imported = 0
        for pw in passwords:
            if not pw.get("password") or pw["password"].startswith("[encrypted"):
                continue
            key = (pw.get("url", ""), pw.get("username", ""))
            if key not in existing:
                prof.passwords.append({
                    "url": pw.get("url", ""),
                    "username": pw.get("username", ""),
                    "password": self._encrypt_secret(pw.get("password", "")),
                    "created_at": pw.get("created_at", time.time()),
                    "imported_from": pw.get("browser", "csv"),
                })
                imported += 1
        self._save_profile(profile_name)
        return imported

    def delete_password(self, profile_name: str, url: str, username: str) -> bool:
        if profile_name not in self.profiles:
            return False
        prof = self.profiles[profile_name]
        before = len(prof.passwords)
        prof.passwords = [
            p for p in prof.passwords
            if not (p.get("url") == url and p.get("username") == username)
        ]
        if len(prof.passwords) < before:
            self._save_profile(profile_name)
            return True
        return False

    def export_bookmarks(self, profile_name: str, file_path: str) -> bool:
        bookmarks = self.get_bookmarks(profile_name)
        if not bookmarks:
            return False
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump({"bookmarks": bookmarks}, f, indent=2)
            return True
        except Exception:
            return False

    def export_passwords(self, profile_name: str, file_path: str) -> bool:
        if self.vault_enabled and self._vault_key is None:
            return False  # refuse to export ciphertext/empty as "passwords"
        passwords = self.get_passwords(profile_name)
        if not passwords:
            return False
        try:
            export_data = [
                {
                    "url": p.get("url", ""),
                    "username": p.get("username", ""),
                    "password": p.get("password", ""),
                }
                for p in passwords
            ]
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(export_data, f, indent=2)
            return True
        except Exception:
            return False

    def export_passwords_csv(self, profile_name: str, file_path: str) -> bool:
        if self.vault_enabled and self._vault_key is None:
            return False
        passwords = self.get_passwords(profile_name)
        if not passwords:
            return False
        try:
            import csv
            with open(file_path, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(["url", "username", "password"])
                for p in passwords:
                    writer.writerow([
                        p.get("url", ""),
                        p.get("username", ""),
                        p.get("password", ""),
                    ])
            return True
        except Exception:
            return False

    def import_settings(self, settings: dict) -> int:
        """Import browser settings into the global settings.
        Returns the number of settings that were actually changed."""
        if not settings:
            return 0
        changed = 0
        # Only import recognized setting keys
        valid_keys = set(DEFAULT_SETTINGS.keys())
        for key, value in settings.items():
            if key in valid_keys and key in self.global_settings:
                if self.global_settings[key] != value:
                    self.global_settings[key] = value
                    changed += 1
        if changed > 0:
            self._save_global_settings()
        return changed

    def clear_browsing_data(self, profile_name: str, clear_cookies=False,
                            clear_cache=False, clear_history=False) -> dict:
        result = {"cookies": False, "cache": False, "history": 0}
        if profile_name not in self.profiles:
            return result
        prof = self.profiles[profile_name]
        if clear_cookies:
            cookie_dir = os.path.join(prof.directory, "cookies")
            if os.path.exists(cookie_dir):
                for f in os.listdir(cookie_dir):
                    try:
                        os.remove(os.path.join(cookie_dir, f))
                    except OSError:
                        pass
            result["cookies"] = True
        if clear_cache:
            cache_dir = os.path.join(prof.directory, "cache")
            if os.path.exists(cache_dir):
                shutil.rmtree(cache_dir, ignore_errors=True)
                os.makedirs(cache_dir, exist_ok=True)
            result["cache"] = True
        if clear_history:
            count = len(prof.history)
            prof.history = []
            self._save_profile(profile_name)
            result["history"] = count
        return result
