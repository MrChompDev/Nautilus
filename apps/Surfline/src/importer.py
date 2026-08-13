"""
Surfline Browser Importer
Import bookmarks, history, and passwords from Chrome, Firefox, Edge, Brave, Opera, and CSV files.
"""
import csv
import json
import os
import re
import shutil
import sqlite3
import sys
import time
from typing import Any


class BrowserInfo:
    """Metadata about a detectable browser."""
    def __init__(self, name: str, browser_type: str, profile_path: str):
        self.name = name
        self.browser_type = browser_type
        self.profile_path = profile_path
        self.bookmarks_found = 0
        self.history_found = 0
        self.passwords_found = 0
        self.settings_found = 0
        self.available = os.path.exists(profile_path)


class ImportResult:
    """Result of an import operation."""
    def __init__(self):
        self.bookmarks_imported: int = 0
        self.history_imported: int = 0
        self.passwords_imported: int = 0
        self.errors: list[str] = []

    def summary(self) -> str:
        parts = []
        if self.bookmarks_imported:
            parts.append(f"{self.bookmarks_imported} bookmarks")
        if self.history_imported:
            parts.append(f"{self.history_imported} history entries")
        if self.passwords_imported:
            parts.append(f"{self.passwords_imported} passwords")
        if self.errors:
            parts.append(f"{len(self.errors)} errors")
        return ", ".join(parts) if parts else "Nothing imported"


class BrowserImporter:
    """Import data from various web browsers into Surfline."""

    def __init__(self):
        self.browsers: list[BrowserInfo] = []
        self._detect_browsers()

    def _get_user_data_dir(self) -> str:
        if sys.platform == "win32":
            return os.path.join(os.environ.get("LOCALAPPDATA", ""), "")
        elif sys.platform == "darwin":
            return os.path.expanduser("~/Library/Application Support")
        else:
            return os.path.expanduser("~/.config")

    def _detect_browsers(self):
        self.browsers = []

        if sys.platform == "win32":
            local = os.environ.get("LOCALAPPDATA", "")
            roam = os.environ.get("APPDATA", "")
            chrome_path = os.path.join(local, "Google", "Chrome", "User Data")
            edge_path = os.path.join(local, "Microsoft", "Edge", "User Data")
            brave_path = os.path.join(local, "BraveSoftware", "Brave-Browser", "User Data")
            opera_path = os.path.join(roam, "Opera Software", "Opera Stable")
            firefox_path = os.path.join(roam, "Mozilla", "Firefox", "Profiles")
        elif sys.platform == "darwin":
            chrome_path = os.path.expanduser("~/Library/Application Support/Google/Chrome")
            edge_path = os.path.expanduser("~/Library/Application Support/Microsoft Edge")
            brave_path = os.path.expanduser("~/Library/Application Support/BraveSoftware/Brave-Browser")
            opera_path = os.path.expanduser("~/Library/Application Support/com.operasoftware.Opera")
            firefox_path = os.path.expanduser("~/Library/Application Support/Firefox/Profiles")
        else:
            chrome_path = os.path.expanduser("~/.config/google-chrome")
            edge_path = os.path.expanduser("~/.config/microsoft-edge")
            brave_path = os.path.expanduser("~/.config/BraveSoftware/Brave-Browser")
            opera_path = os.path.expanduser("~/.config/opera")
            firefox_path = os.path.expanduser("~/.mozilla/firefox")

        self.browsers = [
            BrowserInfo("Google Chrome", "chromium", chrome_path),
            BrowserInfo("Microsoft Edge", "chromium", edge_path),
            BrowserInfo("Brave Browser", "chromium", brave_path),
            BrowserInfo("Opera", "chromium", opera_path),
            BrowserInfo("Vivaldi", "chromium", self._get_vivaldi_path()),
            BrowserInfo("Arc Browser", "chromium", self._get_arc_path()),
            BrowserInfo("Mozilla Firefox", "firefox", firefox_path),
        ]
        # Scan for any additional Chromium-based browsers
        self._detect_extra_chromium_browsers()

    def get_available_browsers(self) -> list[BrowserInfo]:
        for b in self.browsers:
            b.available = os.path.exists(b.profile_path)
        return [b for b in self.browsers if b.available]

    def _get_chromium_profiles(self, base_path: str) -> list[str]:
        profiles = []
        default = os.path.join(base_path, "Default")
        if os.path.exists(default):
            profiles.append(default)
        for entry in os.listdir(base_path):
            if entry.startswith("Profile ") and os.path.isdir(os.path.join(base_path, entry)):
                profiles.append(os.path.join(base_path, entry))
        return profiles

    def _get_firefox_profiles(self, base_path: str) -> list[str]:
        profiles = []
        if not os.path.exists(base_path):
            return profiles
        for entry in os.listdir(base_path):
            prof_dir = os.path.join(base_path, entry)
            if os.path.isdir(prof_dir):
                profiles.append(prof_dir)
        return profiles

    def import_bookmarks_chromium(self, profile_dir: str) -> list[dict]:
        bookmarks_file = os.path.join(profile_dir, "Bookmarks")
        if not os.path.exists(bookmarks_file):
            return []
        try:
            with open(bookmarks_file, encoding="utf-8") as f:
                data = json.load(f)
        except (OSError, json.JSONDecodeError):
            return []

        bookmarks = []
        roots = data.get("roots", {})
        for root_data in roots.values():
            if isinstance(root_data, dict):
                self._walk_bookmark_nodes(root_data, bookmarks)
        return bookmarks

    def _walk_bookmark_nodes(self, node: dict, bookmarks: list):
        if node.get("type") == "url":
            date_added = node.get("date_added", "0")
            try:
                ts = int(date_added) / 1000000 - 11644473600
            except (ValueError, TypeError):
                ts = time.time()
            bookmarks.append({
                "url": node.get("url", ""),
                "title": node.get("name", ""),
                "added_at": ts,
            })
        for child in node.get("children", []):
            self._walk_bookmark_nodes(child, bookmarks)

    def import_history_chromium(self, profile_dir: str, max_entries: int = 10000) -> list[dict]:
        history_db = os.path.join(profile_dir, "History")
        if not os.path.exists(history_db):
            return []

        tmp_copy = history_db + ".surfline_tmp"
        try:
            shutil.copy2(history_db, tmp_copy)
            conn = sqlite3.connect(tmp_copy)
            cursor = conn.cursor()
            cursor.execute(
                "SELECT url, title, last_visit_time FROM urls "
                "ORDER BY last_visit_time DESC LIMIT ?",
                (max_entries,)
            )
            entries = []
            chrome_epoch = 11644473600
            for url, title, visit_time in cursor.fetchall():
                ts = (visit_time / 1000000) - chrome_epoch if visit_time else time.time()
                entries.append({
                    "url": url or "",
                    "title": title or url or "",
                    "visited_at": ts,
                })
            conn.close()
            return entries
        except Exception:
            return []
        finally:
            if os.path.exists(tmp_copy):
                try:
                    os.remove(tmp_copy)
                except OSError:
                    pass

    def import_settings_chromium(self, profile_dir: str) -> dict[str, Any]:
        """Import browser settings from a Chromium profile's Preferences JSON."""
        prefs_file = os.path.join(profile_dir, "Preferences")
        if not os.path.exists(prefs_file):
            return {}
        try:
            with open(prefs_file, encoding="utf-8") as f:
                data = json.load(f)
        except (OSError, json.JSONDecodeError):
            return {}
        return self._extract_chromium_settings(data)

    def _extract_chromium_settings(self, data: dict) -> dict[str, Any]:
        """Extract relevant settings from Chromium Preferences JSON."""
        settings = {}
        # Homepage
        session = data.get("session", {})
        if session.get("restore_on_startup") == 4:
            startup_urls = session.get("startup_urls", [])
            if startup_urls:
                settings["homepage"] = startup_urls[0]
                settings["startup_page"] = "homepage"
            else:
                settings["startup_page"] = "new_tab"
        elif session.get("restore_on_startup") == 1:
            settings["startup_page"] = "last_session"

        # Search engine
        dse = data.get("default_search_provider_data", {})
        template = dse.get("template_url_data", {})
        if template.get("url"):
            search_url = template.get("url", "")
            engine_name = template.get("short_name", template.get("keyword", ""))
            if engine_name:
                settings["search_engine"] = engine_name
            if search_url:
                settings["search_url"] = search_url.replace("{searchTerms}", "{}")

        # Web prefs
        webkit = data.get("webkit", {}).get("webprefs", {})
        if webkit.get("default_font_size"):
            settings["font_size"] = webkit["default_font_size"]
        if webkit.get("default_fixed_font_size"):
            settings["mono_font_size"] = webkit["default_fixed_font_size"]
        if "javascript_enabled" in webkit:
            settings["javascript_enabled"] = webkit["javascript_enabled"]
        if "images_enabled" in webkit:
            settings["images_enabled"] = webkit["images_enabled"]

        return settings

    def import_settings_firefox(self, profile_dir: str) -> dict[str, Any]:
        """Import browser settings from a Firefox profile's prefs.js."""
        prefs_file = os.path.join(profile_dir, "prefs.js")
        if not os.path.exists(prefs_file):
            return {}
        try:
            with open(prefs_file, encoding="utf-8") as f:
                lines = f.readlines()
        except OSError:
            return {}
        return self._extract_firefox_settings(lines)

    def _extract_firefox_settings(self, lines: list[str]) -> dict[str, Any]:
        """Extract relevant settings from Firefox prefs.js lines."""
        settings = {}
        prefs = {}
        for line in lines:
            match = re.match(r'user_pref\("([^"]+)",\s*(.+)\);', line.strip())
            if match:
                key = match.group(1)
                value_str = match.group(2).strip()
                try:
                    value = json.loads(value_str)
                except (json.JSONDecodeError, ValueError):
                    value = value_str.strip('"').strip("'")
                prefs[key] = value

        # Homepage
        homepage = prefs.get("browser.startup.homepage", "")
        if homepage and homepage != "about:blank":
            settings["homepage"] = str(homepage)
            settings["startup_page"] = "homepage"

        startup = prefs.get("browser.startup.page")
        if startup == 0:
            settings["startup_page"] = "homepage"
        elif startup == 3:
            settings["startup_page"] = "last_session"
        elif startup == 1:
            settings["startup_page"] = "new_tab"

        # Search engine
        search_default = prefs.get("browser.search.defaultenginename", "")
        if search_default:
            settings["search_engine"] = search_default

        # Font size
        font_size = prefs.get("font.size.variable.x-western")
        if font_size:
            try:
                settings["font_size"] = int(font_size)
            except (ValueError, TypeError):
                pass

        # JavaScript
        js_enabled = prefs.get("javascript.enabled")
        if js_enabled is not None:
            settings["javascript_enabled"] = bool(js_enabled)

        # Smooth scrolling
        smooth = prefs.get("general.smoothScroll")
        if smooth is not None:
            settings["smooth_scrolling"] = bool(smooth)

        # Notifications
        notif = prefs.get("dom.webnotifications.enabled")
        if notif is not None:
            settings["enable_notifications"] = bool(notif)

        # Geolocation
        geo = prefs.get("geo.enabled")
        if geo is not None:
            settings["enable_geolocation"] = bool(geo)

        # Auto-play
        autoplay = prefs.get("media.autoplay.default")
        if autoplay is not None:
            settings["auto_play_media"] = (autoplay == 0)

        # DNT
        dnt = prefs.get("privacy.donottrackheader.enabled")
        if dnt is not None:
            settings["enable_do_not_track"] = bool(dnt)

        return settings

    def _get_vivaldi_path(self) -> str:
        if sys.platform == "win32":
            local = os.environ.get("LOCALAPPDATA", "")
            return os.path.join(local, "Vivaldi", "User Data")
        elif sys.platform == "darwin":
            return os.path.expanduser("~/Library/Application Support/Vivaldi")
        else:
            return os.path.expanduser("~/.config/vivaldi")

    def _get_arc_path(self) -> str:
        if sys.platform == "win32":
            local = os.environ.get("LOCALAPPDATA", "")
            return os.path.join(local, "Arc", "User Data")
        elif sys.platform == "darwin":
            return os.path.expanduser("~/Library/Application Support/Arc")
        else:
            return os.path.expanduser("~/.config/arc")

    def _detect_extra_chromium_browsers(self):
        """Scan for additional Chromium-based browsers from common paths."""
        existing_paths = {b.profile_path for b in self.browsers}
        extra_discoveries = [
            ("chromium", "Chromium"),
            ("Chromium", "Chromium"),
            ("YandexBrowser", "Yandex Browser"),
            ("Slimjet", "Slimjet"),
            ("Iridium", "Iridium Browser"),
            ("Torch", "Torch Browser"),
        ]
        if sys.platform == "win32":
            local = os.environ.get("LOCALAPPDATA", "")
            roam = os.environ.get("APPDATA", "")
            base_dirs = [local, roam]
        else:
            base_dirs = [self._get_user_data_dir()]

        for base_dir in base_dirs:
            if not os.path.exists(base_dir):
                continue
            for dirname, display_name in extra_discoveries:
                # Check for "User Data" subdirectory (modern Chromium layout)
                path = os.path.join(base_dir, dirname, "User Data")
                if os.path.exists(path) and path not in existing_paths:
                    # Verify it's a real Chromium profile by checking for Preferences
                    if os.path.exists(os.path.join(path, "Default", "Preferences")):
                        self.browsers.append(
                            BrowserInfo(display_name, "chromium", path)
                        )
                        existing_paths.add(path)
                else:
                    # Fallback: app dir itself is the user data dir
                    path = os.path.join(base_dir, dirname)
                    if (path not in existing_paths
                            and os.path.exists(path)
                            and os.path.exists(os.path.join(path, "Default", "Preferences"))):
                        self.browsers.append(
                            BrowserInfo(display_name, "chromium", path)
                        )
                        existing_paths.add(path)

    def import_passwords_chromium(self, profile_dir: str) -> list[dict]:
        login_data = os.path.join(profile_dir, "Login Data")
        if not os.path.exists(login_data):
            return []

        tmp_copy = login_data + ".surfline_tmp"
        try:
            shutil.copy2(login_data, tmp_copy)
            conn = sqlite3.connect(tmp_copy)
            cursor = conn.cursor()
            cursor.execute(
                "SELECT origin_url, username_value, password_value, date_created "
                "FROM logins"
            )
            entries = []
            for origin, username, encrypted_pw, created in cursor.fetchall():
                if not username:
                    continue
                decrypted = self._decrypt_chromium_password(encrypted_pw)
                chrome_epoch = 11644473600
                ts = (created / 1000000) - chrome_epoch if created else time.time()
                entries.append({
                    "url": origin or "",
                    "username": username or "",
                    "password": decrypted or "",
                    "created_at": ts,
                    "browser": "chromium",
                })
            conn.close()
            return entries
        except Exception:
            return []
        finally:
            if os.path.exists(tmp_copy):
                try:
                    os.remove(tmp_copy)
                except OSError:
                    pass

    def _decrypt_chromium_password(self, encrypted_password: bytes) -> str:
        if not encrypted_password:
            return ""
        if sys.platform == "win32":
            return self._decrypt_win32(encrypted_password)
        elif sys.platform == "darwin":
            return self._decrypt_macos(encrypted_password)
        else:
            return self._decrypt_linux(encrypted_password)

    def _decrypt_win32(self, encrypted_password: bytes) -> str:
        try:
            import win32crypt
            if encrypted_password[:3] == b"v10":
                encrypted_password = encrypted_password[3:]
            decrypted = win32crypt.CryptUnprotectData(encrypted_password, None, None, None, 0)[1]
            return decrypted.decode("utf-8", errors="replace")
        except Exception:
            return "[encrypted - install pywin32]"

    def _decrypt_macos(self, encrypted_password: bytes) -> str:
        try:
            if encrypted_password[:3] == b"v10":
                encrypted_password = encrypted_password[3:]
            safe_key = self._get_macos_key()
            if not safe_key:
                return "[encrypted - keychain access denied]"
            import hashlib
            key = hashlib.pbkdf2_hmac("sha1", safe_key.encode(), b"saltysalt", 1003)
            from cryptography.hazmat.backends import default_backend
            from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
            iv = b" " * 16
            cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
            decryptor = cipher.decryptor()
            decrypted = decryptor.update(encrypted_password) + decryptor.finalize()
            padding = decrypted[-1]
            if isinstance(padding, int) and 0 < padding <= 16:
                decrypted = decrypted[:-padding]
            return decrypted.decode("utf-8", errors="replace")
        except Exception:
            return "[encrypted - install cryptography]"

    def _get_macos_key(self) -> str:
        try:
            import subprocess
            result = subprocess.run(
                ["security", "find-generic-password", "-s", "Chrome Safe Storage", "-w"],
                capture_output=True, text=True, timeout=5
            )
            return result.stdout.strip()
        except Exception:
            return "peanuts"

    def _decrypt_linux(self, encrypted_password: bytes) -> str:
        try:
            import secretstorage
            bus = secretstorage.dbus_init()
            collection = secretstorage.get_default_collection(bus)
            for item in collection.get_all_items():
                if item.get_label() == "Chrome Safe Storage":
                    key = item.get_secret()
                    break
            else:
                key = b"peanuts"

            if encrypted_password[:3] == b"v10":
                encrypted_password = encrypted_password[3:]

            import hashlib
            derived_key = hashlib.pbkdf2_hmac("sha1", key, b"saltysalt", 1)

            from cryptography.hazmat.backends import default_backend
            from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
            iv = b" " * 16
            cipher = Cipher(algorithms.AES(derived_key), modes.CBC(iv), backend=default_backend())
            decryptor = cipher.decryptor()
            decrypted = decryptor.update(encrypted_password) + decryptor.finalize()
            padding = decrypted[-1]
            if isinstance(padding, int) and 0 < padding <= 16:
                decrypted = decrypted[:-padding]
            return decrypted.decode("utf-8", errors="replace")
        except Exception:
            return "[encrypted - install secretstorage + cryptography]"

    def import_bookmarks_firefox(self, profile_dir: str) -> list[dict]:
        places_db = os.path.join(profile_dir, "places.sqlite")
        if not os.path.exists(places_db):
            return []

        tmp_copy = places_db + ".surfline_tmp"
        try:
            shutil.copy2(places_db, tmp_copy)
            conn = sqlite3.connect(tmp_copy)
            cursor = conn.cursor()
            cursor.execute(
                "SELECT p.url, p.title, p.dateAdded "
                "FROM moz_bookmarks b "
                "JOIN moz_places p ON b.fk = p.id "
                "WHERE b.type = 1 AND p.url NOT LIKE 'place:%' "
                "ORDER BY b.dateAdded DESC"
            )
            bookmarks = []
            firefox_epoch = 1000000
            for url, title, date_added in cursor.fetchall():
                ts = (date_added / firefox_epoch) if date_added else time.time()
                bookmarks.append({
                    "url": url or "",
                    "title": title or url or "",
                    "added_at": ts,
                })
            conn.close()
            return bookmarks
        except Exception:
            return []
        finally:
            if os.path.exists(tmp_copy):
                try:
                    os.remove(tmp_copy)
                except OSError:
                    pass

    def import_history_firefox(self, profile_dir: str, max_entries: int = 10000) -> list[dict]:
        places_db = os.path.join(profile_dir, "places.sqlite")
        if not os.path.exists(places_db):
            return []

        tmp_copy = places_db + ".surfline_tmp"
        try:
            shutil.copy2(places_db, tmp_copy)
            conn = sqlite3.connect(tmp_copy)
            cursor = conn.cursor()
            cursor.execute(
                "SELECT p.url, p.title, h.visit_date "
                "FROM moz_historyvisits h "
                "JOIN moz_places p ON h.place_id = p.id "
                "ORDER BY h.visit_date DESC LIMIT ?",
                (max_entries,)
            )
            entries = []
            firefox_epoch = 1000000
            for url, title, visit_date in cursor.fetchall():
                ts = (visit_date / firefox_epoch) if visit_date else time.time()
                entries.append({
                    "url": url or "",
                    "title": title or url or "",
                    "visited_at": ts,
                })
            conn.close()
            return entries
        except Exception:
            return []
        finally:
            if os.path.exists(tmp_copy):
                try:
                    os.remove(tmp_copy)
                except OSError:
                    pass

    def import_passwords_firefox(self, profile_dir: str) -> list[dict]:
        logins_json = os.path.join(profile_dir, "logins.json")
        if not os.path.exists(logins_json):
            return []

        try:
            with open(logins_json, encoding="utf-8") as f:
                data = json.load(f)
            logins = data.get("logins", [])
            entries = []
            for login in logins:
                entries.append({
                    "url": login.get("hostname", ""),
                    "username": login.get("encryptedUsername", ""),
                    "password": login.get("encryptedPassword", ""),
                    "created_at": login.get("timeCreated", 0) / 1000,
                    "browser": "firefox_encrypted",
                })
            return entries
        except Exception:
            return []

    def import_from_file(self, file_path: str, data_type: str = "auto") -> tuple[list[dict], str]:
        ext = os.path.splitext(file_path)[1].lower()

        if ext == ".csv":
            return self._import_csv(file_path), "csv"
        elif ext == ".json":
            return self._import_json(file_path), "json"
        elif ext == ".html":
            return self._import_html_bookmarks(file_path), "html"
        else:
            return [], "unknown"

    def _import_csv(self, file_path: str) -> list[dict]:
        entries = []
        try:
            with open(file_path, encoding="utf-8-sig") as f:
                reader = csv.DictReader(f)
                headers = [h.lower().strip() for h in (reader.fieldnames or [])]

                if "name" in headers and "url" in headers:
                    for row in reader:
                        entries.append({
                            "url": row.get("url", ""),
                            "title": row.get("name", row.get("title", "")),
                            "added_at": time.time(),
                        })
                elif "hostname" in headers or "url" in headers:
                    for row in reader:
                        entries.append({
                            "url": row.get("url", row.get("hostname", "")),
                            "username": row.get("username", row.get("login", "")),
                            "password": row.get("password", ""),
                            "created_at": time.time(),
                        })
                else:
                    for row in reader:
                        vals = list(row.values())
                        if len(vals) >= 2:
                            entries.append({
                                "url": vals[1] if len(vals) > 1 else vals[0],
                                "title": vals[0],
                                "added_at": time.time(),
                            })
        except Exception:
            pass
        return entries

    def _import_json(self, file_path: str) -> list[dict]:
        entries = []
        try:
            with open(file_path, encoding="utf-8") as f:
                data = json.load(f)

            if isinstance(data, list):
                for item in data:
                    if isinstance(item, dict):
                        entries.append({
                            "url": item.get("url", item.get("href", "")),
                            "title": item.get("title", item.get("name", "")),
                            "username": item.get("username", item.get("login", "")),
                            "password": item.get("password", ""),
                            "added_at": item.get("added_at", time.time()),
                        })
            elif isinstance(data, dict):
                if "roots" in data:
                    self._walk_bookmark_nodes(data, entries)
                elif "bookmarks" in data:
                    entries = data["bookmarks"]
                elif "passwords" in data:
                    entries = data["passwords"]
        except Exception:
            pass
        return entries

    def _import_html_bookmarks(self, file_path: str) -> list[dict]:
        entries = []
        try:
            with open(file_path, encoding="utf-8") as f:
                content = f.read()

            for match in re.finditer(
                r'<A\s+HREF="([^"]*)"[^>]*>(.*?)</A>',
                content, re.IGNORECASE | re.DOTALL
            ):
                url = match.group(1)
                title = re.sub(r'<[^>]+>', '', match.group(2)).strip()
                entries.append({
                    "url": url,
                    "title": title or url,
                    "added_at": time.time(),
                })
        except Exception:
            pass
        return entries

    def scan_browser(self, browser: BrowserInfo) -> BrowserInfo:
        if browser.browser_type == "chromium":
            profiles = self._get_chromium_profiles(browser.profile_path)
            for prof_dir in profiles:
                bm = self.import_bookmarks_chromium(prof_dir)
                browser.bookmarks_found += len(bm)
                hist = self.import_history_chromium(prof_dir)
                browser.history_found += len(hist)
                pw = self.import_passwords_chromium(prof_dir)
                browser.passwords_found += len(pw)
                settings = self.import_settings_chromium(prof_dir)
                if settings:
                    browser.settings_found += 1
        elif browser.browser_type == "firefox":
            profiles = self._get_firefox_profiles(browser.profile_path)
            for prof_dir in profiles:
                bm = self.import_bookmarks_firefox(prof_dir)
                browser.bookmarks_found += len(bm)
                hist = self.import_history_firefox(prof_dir)
                browser.history_found += len(hist)
                pw = self.import_passwords_firefox(prof_dir)
                browser.passwords_found += len(pw)
                settings = self.import_settings_firefox(prof_dir)
                if settings:
                    browser.settings_found += 1
        return browser
