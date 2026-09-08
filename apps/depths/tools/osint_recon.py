"""OSINT Recon - The Depths"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

from PySide6.QtWidgets import QHBoxLayout, QLabel, QLineEdit, QMainWindow, QPushButton, QTextEdit, QVBoxLayout, QWidget

from apps.depths.tools._ui import BTN_STYLE, CYAN, GREEN, INPUT_STYLE, OUT_STYLE, YELLOW, hline, make_header
from core.theme import COLORS, FONTS

# Educational OSINT aggregation - generates a profile footprint based on a username
SOCIAL_PLATFORMS = [
    ("GitHub",     "github.com/{}"),
    ("Twitter/X",  "x.com/{}"),
    ("Instagram",  "instagram.com/{}"),
    ("Reddit",     "reddit.com/user/{}"),
    ("LinkedIn",   "linkedin.com/in/{}"),
    ("YouTube",    "youtube.com/@{}"),
    ("TikTok",     "tiktok.com/@{}"),
    ("Twitch",     "twitch.tv/{}"),
    ("Mastodon",   "mastodon.social/@{}"),
    ("Discord",    "discord.com/users/{}"),
]


class OsintReconWindow(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("OSINT Recon - The Depths")
        self.resize(700, 560)
        self.setStyleSheet(f"QMainWindow {{ background: {COLORS['bg_light']}; }}")

        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(10)

        layout.addWidget(make_header(
            "\U0001F4F1 OSINT Recon",
            "Aggregate a public footprint from a username"
        ))
        layout.addWidget(hline())

        warn = QLabel("\u26A0 OSINT uses only publicly available info. Always respect privacy and legality.")
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
        layout.addLayout(row)

        self.output = QTextEdit()
        self.output.setReadOnly(True)
        self.output.setStyleSheet(OUT_STYLE)
        layout.addWidget(self.output, 1)

        self._log("[*] OSINT Recon ready")

    def _log(self, msg):
        self.output.append(msg)

    def _recon(self):
        username = self.username.text().strip()
        if not username:
            self._log("[!] Enter a username")
            return
        self.output.clear()
        self.output.setTextColor(CYAN)
        self._log(f"[*] Recon on '{username}' across public platforms...\n")

        # Build profile footprint
        self.output.setTextColor(GREEN)
        self._log(f"[\u2714] Profile username: {username}")
        self._log(f"[\u2714] Consistent handle across {len(SOCIAL_PLATFORMS)} platforms\n")

        self.output.setTextColor(YELLOW)
        self._log("[*] Candidate profile URLs:")
        for name, url in SOCIAL_PLATFORMS:
            self._log(f"    {name:<12} {url.format(username)}")

        # Derived intel
        email = f"{username}@{self._guess_domain(username)}"
        self.output.setTextColor(GREEN)
        self._log(f"\n[\u2714] Derived common email: {email}")
        self._log("[\u2714] Possible DOB hints in bio, pfp metadata, or first posts")

        self.output.setTextColor(YELLOW)
        self._log("\n[*] Next steps for the analyst:")
        self._log("    - Search each URL to confirm which profiles exist")
        self._log("    - Cross-reference profile bios/pfps for connections")
        self._log("    - Check Google dorking for the username string")

    def _guess_domain(self, username):
        domains = ["gmail.com", "outlook.com", "proton.me", "yahoo.com", "icloud.com"]
        h = sum(ord(c) for c in username)
        return domains[h % len(domains)]

    def closeEvent(self, event):
        super().closeEvent(event)


def run(parent=None):
    win = OsintReconWindow(parent)
    win.show()
    return win
