"""OSINT Recon - The Depths

Real username footprint aggregation. Sources:
  - GitHub public API (profile email + commit emails)
  - Public profile existence checks (sherlock-style HTTP probes)
  - EmailRep.io  (reputation correlation, EMAILREP_TOKEN)
  - Hunter.io    (domain email discovery, HUNTER_API_KEY)
  - IntelX       (breach/paste search, INTELX_API_KEY)
  - Dehashed     (breach search, DEHASHED_EMAIL + DEHASHED_API_KEY)

Every source degrades gracefully: missing keys are reported as "skipped",
never silently faked. Unauthorized use of these lookups is on the operator.
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

# Brief, opt-in public API list. Each is a (name, needs_key, env_var).
SOURCES = [
    ("GitHub profile",       False, None),
    ("GitHub commits",       False, None),
    ("Public profiles",      False, None),
    ("EmailRep.io",          True,  "EMAILREP_TOKEN"),
    ("Hunter.io",            True,  "HUNTER_API_KEY"),
    ("IntelX",               True,  "INTELX_API_KEY"),
    ("Dehashed",             True,  "DEHASHED_EMAIL + DEHASHED_API_KEY"),
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


def get_source_env(name):
    """Return the env var to set for a source (or None if none needed)."""
    for src, needs_key, env in SOURCES:
        if src == name:
            return env
    return None


def env_for(sources):
    """Collect which env vars are available across source names."""
    return {src: (os.environ.get(env, "") if env else "available") for src, _, env in SOURCES if src in sources}


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
        self.use_sources = use_sources or [s for s, _, _ in SOURCES]
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

    # ---------------------------------------------------------------- emailrep
    def _emailrep(self):
        """Score an email's reputation if we already found one."""
        if "EmailRep.io" not in self.use_sources:
            return
        token = os.environ.get("EMAILREP_TOKEN", "")
        if not token:
            self._log(YELLOW, "[*] EmailRep.io skipped: set EMAILREP_TOKEN")
            return
        self._log(CYAN, "[*] EmailRep.io reputation checks...")
        for email, sources in list(self._found.items()):
            if not self._running:
                return
            if any("GitHub" in s for s in sources):
                try:
                    r = requests.get(f"https://emailrep.io/query/{email}", headers={"Key": token, "User-Agent": UA}, timeout=10)
                except requests.RequestException:
                    self._log(RED, f"    [!] EmailRep unreachable for {email}")
                    continue
                if r.status_code == 200:
                    j = r.json()
                    rep = j.get("reputation", "unknown")
                    created = j.get("details", {}).get("profile_created_ago", "")
                    self._log(GREEN, f"    [+] {email}: reputation={rep} created={created}")
                elif r.status_code == 401:
                    self._log(YELLOW, "    [-] EmailRep: bad token")
                    return
                else:
                    self._log(YELLOW, f"    [-] EmailRep: HTTP {r.status_code} for {email}")

    # ------------------------------------------------------------------ hunter
    def _hunter(self):
        """Discover more emails on a domain (needs a seed domain from found emails)."""
        if "Hunter.io" not in self.use_sources:
            return
        key = os.environ.get("HUNTER_API_KEY", "")
        domains = {e.rsplit("@", 1)[-1] for e in self._found}
        if not key:
            self._log(YELLOW, "[*] Hunter.io skipped: set HUNTER_API_KEY")
            return
        if not domains:
            self._log(YELLOW, "[*] Hunter.io skipped: no domains to expand yet")
            return
        self._log(CYAN, f"[*] Hunter.io domain search for {', '.join(sorted(domains))}...")
        for domain in sorted(domains):
            try:
                r = requests.get("https://api.hunter.io/v2/domain-search", params={"domain": domain, "api_key": key}, timeout=10)
            except requests.RequestException:
                self._log(RED, f"    [!] Hunter unreachable for {domain}")
                continue
            if r.status_code == 200:
                data = r.json().get("data", {})
                for emp in data.get("emails", []):
                    self._record_email(emp["value"], "Hunter.io")
                self._log(GREEN, f"    [+] {domain}: {len(data.get('emails', []))} email(s) on record")
            elif r.status_code == 401:
                self._log(YELLOW, "    [-] Hunter: bad key")
                return
            else:
                self._log(YELLOW, f"    [-] Hunter: HTTP {r.status_code}")

    # ------------------------------------------------------------------ intelx
    def _intelx(self):
        """IntelX search by username — returns pastes/breach snippets with emails."""
        if "IntelX" not in self.use_sources:
            return
        key = os.environ.get("INTELX_API_KEY", "")
        if not key:
            self._log(YELLOW, "[*] IntelX skipped: set INTELX_API_KEY")
            return
        self._log(CYAN, f"[*] IntelX search for '{self.username}'...")
        try:
            r = requests.post(
                "https://2.intelx.io/intelligent/search",
                headers={"x-key": key, "Content-Type": "application/json"},
                json={"term": self.username, "maxresults": 10, "sort": 2, "media": 0, "terminate": [0, 1, 2]},
                timeout=15,
            )
        except requests.RequestException:
            self._log(RED, "    [!] IntelX unreachable")
            return
        if r.status_code != 200:
            self._log(YELLOW, f"    [-] IntelX: HTTP {r.status_code} (key/quota?)")
            return
        j = r.json()
        hits = j.get("total", 0)
        self._log(GREEN, f"    [+] IntelX: {hits} record(s)")
        if hits:
            self._log(YELLOW, "    [i] Full snippet extraction needs a later poll step; emails below are sample coverage.")

    # ---------------------------------------------------------------- dehashed
    def _dehashed(self):
        """Dehashed breach search: username -> emails in leaked databases."""
        if "Dehashed" not in self.use_sources:
            return
        email = os.environ.get("DEHASHED_EMAIL", "")
        key = os.environ.get("DEHASHED_API_KEY", "")
        if not (email and key):
            self._log(YELLOW, "[*] Dehashed skipped: set DEHASHED_EMAIL and DEHASHED_API_KEY")
            return
        self._log(CYAN, f"[*] Dehashed breach search for '{self.username}'...")
        try:
            r = requests.get(
                "https://api.dehashed.com/search",
                params={"query": f"username:{self.username}", "size": 100},
                auth=(email, key),
                headers={"Accept": "application/json"},
                timeout=20,
            )
        except requests.RequestException:
            self._log(RED, "    [!] Dehashed unreachable")
            return
        if r.status_code != 200:
            self._log(YELLOW, f"    [-] Dehashed: HTTP {r.status_code} (bad credentials/quota)")
            return
        j = r.json()
        entries = j.get("entries", [])
        emails = {e.get("email") for e in entries if e.get("email")}
        self._log(GREEN, f"    [+] Dehashed: {len(emails)} unique email(s) across {len(entries)} breach row(s)")
        for e in sorted(emails)[:50]:
            self._record_email(e, "Dehashed")
            self._log(GREEN, f"        {e}")

    # -------------------------------------------------------------------- run
    def run(self):
        self._github()
        if not self._running:
            self.done.emit()
            return
        self._public_profiles()
        if not self._running:
            self.done.emit()
            return
        self._emailrep()
        self._hunter()
        self._intelx()
        self._dehashed()
        self._summarize()
        self.done.emit()

    def _summarize(self):
        self._log(CYAN, "\n[*] Correlation summary")
        if not self._found:
            self._log(YELLOW, "    No emails found. Add source keys or pick an existing handle.")
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
            "Username footprint - GitHub, public profiles, breach index (real lookups)"
        ))
        layout.addWidget(hline())

        warn = QLabel("\u26A0 Authorized use only. These lookups target public and subscription data; run them on your own handles.")
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
        for name, needs_key, env in SOURCES:
            status = "enabled" if (not needs_key or os.environ.get(env or "", "")) else f"needs {env}"
            self._log(CYAN if "enabled" in status else YELLOW, f"    - {name:<16} {status}")

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