"""OSINT Recon - The Depths

Real username footprint aggregation, using only free, key-less public sources:
  - GitHub public API (profile email + commit emails)
  - Public profile existence checks (sherlock-style HTTP probes)

Paid/key-gated services (EmailRep, Hunter.io, IntelX, Dehashed) are
deliberately not used, so this tool needs no account, subscription, or API key
and cannot leak one. Every source degrades gracefully: a failed lookup is
reported as such, never silently faked. Use it on handles you own or are
authorised to investigate.
"""

import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

import requests
from PySide6.QtCore import QThread, Signal
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from apps.depths.tools._ui import BTN_STYLE, CYAN, GREEN, INPUT_STYLE, OUT_STYLE, RED, YELLOW, hline, make_header
from core.theme import COLORS, FONTS

UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36"

# Free public sources, in run order. None require an account or an API key.
SOURCES = [
    "GitHub profile",
    "GitHub commits",
    "Public profiles",
]

# Public sites checked for profile existence. Format: name, url template.
# These only tell you the profile *exists*; they never leak emails.
PROFILE_SITES = [
    ("GitHub",  "https://github.com/{}"),
    ("X/Twitter", "https://x.com/{}"),
    ("Reddit",  "https://www.reddit.com/user/{}"),
    ("YouTube", "https://www.youtube.com/@{x}" if False else "https://www.youtube.com/@{}"),
    ("TikTok",  "https://www.tiktok.com/@{}"),
    ("Instagram", "https://www.instagram.com/{}"),
    ("Twitch",  "https://www.twitch.tv/{}"),
    ("Mastodon", "https://mastodon.social/@{}"),
    ("Pinterest", "https://www.pinterest.com/{}"),
]

EMAIL_RE = re.compile(r"[\w.+-]+@[\w-]+\.[\w.]+")


def parse_emails(text):
    if not text:
        return []
    return list(dict.fromkeys(EMAIL_RE.findall(text)))


class ReconWorker(QThread):
    """Runs OSINT lookups off the UI thread. Emits (color, text) log lines."""

    log = Signal(str, str)
    done = Signal()

    def __init__(self, username, use_sources=None):
        super().__init__()
        self.username = username.strip()
        self.use_sources = use_sources or list(SOURCES)
        self._running = True
        self._found = {}
        self._profiles = {}

    def stop(self):
        self._running = False

    def _log(self, color, msg):
        self.log.emit(color, msg)

    def _record_email(self, email, source):
        """Dedupe emails and record which source(s) found them."""
        self._found.setdefault(email, []).append(source)

    def _record_profile(self, platform, exists, status=0):
        self._profiles[platform] = (exists, status)

    # ------------------------------------------------------------------ github
    def _github(self):
        """Public email from profile, plus commit-author emails from events."""
        if "GitHub profile" not in self.use_sources and "GitHub commits" not in self.use_sources:
            return
        self._log(CYAN, f"[*] GitHub API for '{self.username}'...")
        try:
            r = requests.get(f"https://api.github.com/users/{self.username}", headers={"User-Agent": UA}, timeout=10)
        except requests.RequestException:
            self._log(RED, "    [!] GitHub API unreachable")
            return

        if r.status_code == 404:
            self._log(YELLOW, f"    [-] No GitHub user '{self.username}'")
            return
        if r.status_code != 200:
            self._log(YELLOW, f"    [-] GitHub API HTTP {r.status_code} (rate limit?)")
            return

        data = r.json()
        email = data.get("email")
        if email:
            self._record_email(email, "GitHub profile")
            self._log(GREEN, f"    [+] Profile email: {email}")
        else:
            self._log(YELLOW, "    [-] No public email on profile")

        if "GitHub commits" not in self.use_sources:
            return
        try:
            ev = requests.get(f"https://api.github.com/users/{self.username}/events/public", headers={"User-Agent": UA}, timeout=10)
        except requests.RequestException:
            self._log(RED, "    [!] GitHub events unreachable")
            return
        if ev.status_code != 200:
            self._log(YELLOW, f"    [-] No public events (HTTP {ev.status_code})")
            return
        emails = []
        for event in ev.json():
            for commit in event.get("payload", {}).get("commits", []):
                addr = commit.get("author", {}).get("email")
                if addr and addr not in emails:
                    emails.append(addr)
        for addr in emails[:20]:
            self._record_email(addr, "GitHub commits")
        self._log(GREEN if emails else YELLOW, f"    {'[+] ' + str(len(emails)) + ' commit email(s)' if emails else '[-] no commit emails'}")

    # --------------------------------------------------------------- profiles
    def _public_profiles(self):
        """Existence checks — no emails, but confirms where the handle lives."""
        if "Public profiles" not in self.use_sources:
            return
        self._log(CYAN, f"[*] Checking public profiles for '{self.username}'...")
        for name, tmpl in PROFILE_SITES:
            if not self._running:
                return
            url = tmpl.format(self.username)
            try:
                r = requests.get(url, headers={"User-Agent": UA}, timeout=8)
                status = r.status_code
            except requests.RequestException:
                status = 0
            exists = status == 200
            self._record_profile(name, exists, status)
            if exists:
                self._log(GREEN, f"    [+] {name:<12} exists")
            elif status:
                self._log(YELLOW, f"    [-] {name:<12} not found (HTTP {status})")
            else:
                self._log(YELLOW, f"    [~] {name:<12} unreachable")
        self._log(YELLOW, "    [i] Profile existence only. No email is ever exposed by these sites.")

    # -------------------------------------------------------------------- run
    def run(self):
        self._github()
        if not self._running:
            self.done.emit()
            return
        self._public_profiles()
        self._summarize()
        self.done.emit()

    def _summarize(self):
        self._log(CYAN, "\n[*] Correlation summary")
        if not self._found:
            self._log(YELLOW, "    No emails found. Try a handle that has a public GitHub profile.")
            return
        for email, sources in sorted(self._found.items()):
            tags = ", ".join(sorted(set(sources)))
            self._log(GREEN, f"    [+] {email}   <- {tags}")
        self._log(YELLOW, f"    {len(self._found)} unique email(s) across {len(self._profiles)} profile checks.")


class OsintReconWindow(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.worker = None
        self.setWindowTitle("OSINT Recon - Signal Depths")
        self.resize(760, 620)
        self.setStyleSheet(f"QMainWindow {{ background: {COLORS['bg_light']}; }}")

        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(10)

        layout.addWidget(make_header(
            "\U0001F4F1 OSINT Recon",
            "Username footprint - GitHub API + public profile checks (no API key needed)"
        ))
        layout.addWidget(hline())

        warn = QLabel("\u26A0 Authorized use only. These lookups read public pages and public APIs; run them on your own handles.")
        warn.setWordWrap(True)
        warn.setStyleSheet(f"color: {COLORS['warning']}; font-size: {FONTS['size_sm']}px;")
        layout.addWidget(warn)

        row = QHBoxLayout()
        lbl = QLabel("Username:")
        lbl.setStyleSheet(f"color: {COLORS['text']}; font-size: {FONTS['size_md']}px;")
        row.addWidget(lbl)
        self.username = QLineEdit("mrchompdev")
        self.username.setStyleSheet(INPUT_STYLE)
        row.addWidget(self.username, 1)

        self.recon_btn = QPushButton("\U0001F50D Recon")
        self.recon_btn.setStyleSheet(BTN_STYLE)
        self.recon_btn.clicked.connect(self._recon)
        row.addWidget(self.recon_btn)

        self.stop_btn = QPushButton("Stop")
        self.stop_btn.setStyleSheet(BTN_STYLE.replace(COLORS["teal"], COLORS["alert_red"]).replace(COLORS["teal_light"], COLORS["coral_deep"]))
        self.stop_btn.clicked.connect(self.stop)
        self.stop_btn.setEnabled(False)
        row.addWidget(self.stop_btn)
        layout.addLayout(row)

        self.output = QTextEdit()
        self.output.setReadOnly(True)
        self.output.setStyleSheet(OUT_STYLE)
        layout.addWidget(self.output, 1)

        self._log(YELLOW, "[*] OSINT Recon ready. Sources:")
        for name in SOURCES:
            self._log(CYAN, f"    - {name:<16} enabled (free, no key)")

    def _log(self, color, msg):
        self.output.setTextColor(color if isinstance(color, str) and color.startswith("#") else color)
        self.output.append(msg)

    def _recon(self):
        user = self.username.text().strip()
        if not user:
            self._log(YELLOW, "[!] Enter a username")
            return
        if self.worker and self.worker.isRunning():
            self._log(YELLOW, "[*] A recon is already running")
            return
        self.output.clear()
        self._log(CYAN, f"[*] Recon starting for '{user}'...\n")
        self.recon_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)

        self.worker = ReconWorker(user)
        self.worker.log.connect(self._log)
        self.worker.done.connect(self._done)
        self.worker.start()

    def _done(self):
        self.recon_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)

    def stop(self):
        if self.worker and self.worker.isRunning():
            self.worker.stop()
            self._log(YELLOW, "\n[*] Recon stopped by user")

    def closeEvent(self, event):
        self.stop()
        super().closeEvent(event)


def run(parent=None):
    win = OsintReconWindow(parent)
    win.show()
    return win


def main():
    from PySide6.QtWidgets import QApplication
    app = QApplication(sys.argv)
    win = OsintReconWindow()
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()