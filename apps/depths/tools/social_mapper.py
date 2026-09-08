"""Social Mapper - The Depths

Real username-existence mapping across a set of internet platforms, modeled
directly on the sherlock methodology:

- Each site entry defines a URL template, a detection METHOD, and (for the
  "message" method) an error_string or error_type that marks "not found".
- sherlock detection methods: STATUS_CODE (HTTP != 200 => not found),
  MESSAGE (200 + body contains an error marker => not found),
  RESPONSE_URL (HTTP 3xx/bodies redirect to a "does not exist" URL).
- A browser User-Agent is sent so sites don't serve bot-block pages.
- We stop politely on 429 (rate limit) and skip color/JS-only checks.

Pure education: we only read public profile URLs, never log in, never collect
private data. The result is a "does this handle exist" footprint summary.
"""

import os
import re
import sys
import urllib.error
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

from PySide6.QtWidgets import QHBoxLayout, QLabel, QLineEdit, QMainWindow, QPushButton, QTextEdit, QVBoxLayout, QWidget

from apps.depths.tools._ui import BTN_STYLE, CYAN, GREEN, INPUT_STYLE, OUT_STYLE, YELLOW, hline, make_header
from core.theme import COLORS, FONTS

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")

# (name, url_with_{}, method, error_string_or_None, response_url_or_None)
SITES = [
    ("GitHub",        "https://github.com/{username}",              "STATUS_CODE", None, None),
    ("Reddit",        "https://www.reddit.com/user/{username}/",    "STATUS_CODE", None, None),
    ("Mastodon",      "https://mastodon.social/@{username}",        "STATUS_CODE", None, None),
    ("Pinterest",     "https://www.pinterest.com/{username}/",      "MESSAGE", "Sorry, we couldn't find that page.", None),
    ("TikTok",        "https://www.tiktok.com/@{username}",         "MESSAGE", "user_not_found", None),
    ("Instagram",     "https://www.instagram.com/{username}/",      "MESSAGE", "Page Not Found", None),
    ("YouTube",       "https://www.youtube.com/@{username}",        "MESSAGE", "Not Found", None),
    ("X",             "https://x.com/{username}",                   "MESSAGE", "This account doesn't exist", None),
    ("Twitch",        "https://www.twitch.tv/{username}",           "MESSAGE", "Sorry. Unless you've got a time machine, that content is unavailable.", None),
    ("Flickr",        "https://www.flickr.com/people/{username}",   "STATUS_CODE", None, None),
    ("Dribbble",      "https://dribbble.com/{username}",            "MESSAGE", "That page is gone, so let's get you back to work.", None),
    ("HackerNews",    "https://news.ycombinator.com/user?id={username}", "STATUS_CODE", None, None),
]


def check_site(name, url, method, err_str, resp_url, username):
    """Return ("FOUND"/"NOT FOUND"/"SKIPPED", detail-or-None)."""
    full = url.format(username=username)
    req = urllib.request.Request(full, headers={"User-Agent": UA, "Accept": "text/html"})
    try:
        with urllib.request.urlopen(req, timeout=8) as resp:
            code = resp.getcode()
            final = resp.geturl()
            body = ""
            if method in ("MESSAGE",):
                body = resp.read(200_000).decode("utf-8", errors="ignore")
            if method == "STATUS_CODE":
                return ("FOUND", f"HTTP {code}") if code == 200 else ("NOT FOUND", f"HTTP {code}")
            if method == "RESPONSE_URL":
                return ("NOT FOUND", f"redirected to {final[:60]}") if resp_url and resp_url in final else ("FOUND", f"HTTP {code}")
            if method == "MESSAGE":
                if err_str and err_str.lower() in body.lower():
                    return ("NOT FOUND", "error marker in page")
                return ("FOUND", f"HTTP {code}")
    except urllib.error.HTTPError as e:
        if e.code == 429:
            return ("SKIPPED", "rate limited (429)")
        if e.code == 403:
            return ("SKIPPED", "forbidden (403)")
        if e.code == 404:
            return ("NOT FOUND", "HTTP 404")
        if e.code == 410:
            return ("NOT FOUND", "HTTP 410 (gone)")
        return ("SKIPPED", f"HTTP {e.code}")
    except (urllib.error.URLError, TimeoutError, OSError) as e:
        return ("SKIPPED", f"network error: {type(e).__name__}")
    return ("SKIPPED", "unhandled")


class SocialMapperWindow(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Social Mapper - The Depths")
        self.resize(760, 620)
        self.setStyleSheet(f"QMainWindow {{ background: {COLORS['bg_light']}; }}")

        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(10)

        layout.addWidget(make_header(
            "\U0001F465 Social Mapper",
            "Map one username across public platforms (sherlock-style)"
        ))
        layout.addWidget(hline())

        warn = QLabel("\u26A0 Privacy-first awareness tool. Reads only public profile pages - never logs in, never collects private data.")
        warn.setWordWrap(True)
        warn.setStyleSheet(f"color: {COLORS['warning']}; font-size: {FONTS['size_sm']}px;")
        layout.addWidget(warn)

        row = QHBoxLayout()
        lbl = QLabel("Username:")
        lbl.setStyleSheet(f"color: {COLORS['text']}; font-size: {FONTS['size_md']}px;")
        row.addWidget(lbl)
        self.identity = QLineEdit("mrchomp")
        self.identity.setStyleSheet(INPUT_STYLE)
        row.addWidget(self.identity, 1)

        self.map_btn = QPushButton("\U0001F50D Map")
        self.map_btn.setStyleSheet(BTN_STYLE)
        self.map_btn.clicked.connect(self._map)
        row.addWidget(self.map_btn)
        layout.addLayout(row)

        self.output = QTextEdit()
        self.output.setReadOnly(True)
        self.output.setStyleSheet(OUT_STYLE)
        layout.addWidget(self.output, 1)

        self._log("[*] Social Mapper ready")
        self._log(f"[*] {len(SITES)} platforms checked (real GET requests).")

    def _log(self, msg, color=None):
        if color is not None:
            self.output.setTextColor(color)
        self.output.append(msg)

    def _map(self):
        base = self.identity.text().strip()
        if not base:
            self._log("[!] Enter a username")
            return
        if not re.fullmatch(r"[A-Za-z0-9_.-]{1,40}", base):
            self._log("[!] Invalid username (letters, numbers, . _ - only)")
            return
        self.output.clear()
        self._log(f"[*] Checking existence of '{base}' on {len(SITES)} platforms (this may take ~30s)...\n")
        self.map_btn.setEnabled(False)

        found, missing, skipped = [], [], []
        for name, url, method, err_str, resp_url in SITES:
            status, detail = check_site(name, url, method, err_str, resp_url, base)
            if status == "FOUND":
                found.append(name)
                self._log(f"    [\u2714] {name:<14} FOUND", color=GREEN)
            elif status == "NOT FOUND":
                missing.append(name)
                self._log(f"    [\u2718] {name:<14} not found   ({detail})", color=YELLOW)
            else:
                skipped.append(name)
                self._log(f"    [\u2014] {name:<14} skipped     ({detail})", color=CYAN)

        self.map_btn.setEnabled(True)
        self._log("\n" + "=" * 60)
        if found:
            self._log(f"[\u2714] Known footprint ({len(found)}): " + ", ".join(found), color=GREEN)
        if missing:
            self._log(f"[\u2718] No account ({len(missing)}): " + ", ".join(missing), color=YELLOW)
        if skipped:
            self._log(f"[\u2014] Could not verify ({len(skipped)}): " + ", ".join(skipped), color=CYAN)
        self._log("\n    Tip: check the FOUND platforms manually for linked emails/avatars.", color=YELLOW)

    def closeEvent(self, event):
        super().closeEvent(event)


def run(parent=None):
    win = SocialMapperWindow(parent)
    win.show()
    return win