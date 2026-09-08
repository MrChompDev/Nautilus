"""Hash Analyzer - The Depths"""

import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

from PySide6.QtWidgets import QHBoxLayout, QLabel, QLineEdit, QMainWindow, QPushButton, QTextEdit, QVBoxLayout, QWidget

from apps.depths.tools._ui import BTN_STYLE, GREEN, INPUT_STYLE, OUT_STYLE, YELLOW, hline, make_header
from core.theme import COLORS, FONTS


def identify_hash(value: str):
    v = value.strip()
    info = []
    kind = "Unknown"

    if "$2" in v and v.startswith("$2"):
        kind = "bcrypt"
        info = ["Blowfish-based, salted, slow by design", "Common for password storage"]
    elif "$1$" in v:
        kind = "MD5-crypt"
        info = ["Unix MD5 password hash (salted)"]
    elif "$6$" in v:
        kind = "SHA-512-crypt"
        info = ["Unix SHA-512 password hash (salted)"]
    elif re.fullmatch(r"[0-9a-fA-F]{32}", v):
        kind = "MD5"
        info = ["32 hex chars", "Fast to crack (dictionary/rainbow)"]
    elif re.fullmatch(r"[0-9a-fA-F]{40}", v):
        kind = "SHA-1"
        info = ["40 hex chars", "Deprecated for security, still common"]
    elif re.fullmatch(r"[0-9a-fA-F]{56}", v):
        kind = "SHA-224"
        info = ["56 hex chars"]
    elif re.fullmatch(r"[0-9a-fA-F]{64}", v):
        kind = "SHA-256"
        info = ["64 hex chars", "Strong, current standard"]
    elif re.fullmatch(r"[0-9a-fA-F]{128}", v):
        kind = "SHA-512"
        info = ["128 hex chars", "Strong"]
    elif re.fullmatch(r"[A-Za-z0-9+/=]{16}", v):
        kind = "the base64" if False else "NT LAN Manager"
        info = ["Windows NTLM hash (16 bytes)"]
    elif re.fullmatch(r"[A-Za-z0-9+/=]+", v) and len(v) % 4 == 0:
        kind = "Base64 (maybe encrypted)"
        info = ["Encoded text - decode to see content"]

    return kind, info


class HashAnalyzerWindow(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Hash Analyzer - The Depths")
        self.resize(620, 420)
        self.setStyleSheet(f"QMainWindow {{ background: {COLORS['bg_light']}; }}")

        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(10)

        layout.addWidget(make_header(
            "\U0001F9EE Hash Analyzer",
            "Fingerprint a hash to identify its algorithm"
        ))
        layout.addWidget(hline())

        row = QHBoxLayout()
        lbl = QLabel("Hash:")
        lbl.setStyleSheet(f"color: {COLORS['text']}; font-size: {FONTS['size_md']}px;")
        row.addWidget(lbl)
        self.hash_input = QLineEdit()
        self.hash_input.setPlaceholderText("e.g. 5f4dcc3b5aa765d61d8327deb882cf99")
        self.hash_input.setStyleSheet(INPUT_STYLE)
        row.addWidget(self.hash_input, 1)

        self.analyze_btn = QPushButton("\U0001F50D Analyze")
        self.analyze_btn.setStyleSheet(BTN_STYLE)
        self.analyze_btn.clicked.connect(self.analyze)
        row.addWidget(self.analyze_btn)
        layout.addLayout(row)

        self.output = QTextEdit()
        self.output.setReadOnly(True)
        self.output.setStyleSheet(OUT_STYLE)
        layout.addWidget(self.output, 1)

        self._log("[*] Hash Analyzer ready")
        self._log("[*] Paste a hash to identify its type")

    def _log(self, msg):
        self.output.append(msg)

    def analyze(self):
        value = self.hash_input.text()
        if not value.strip():
            self._log("[!] Enter a hash")
            return
        self.output.clear()
        kind, info = identify_hash(value)
        self._log(f"[*] Hash length: {len(value.strip())} characters")
        self.output.setTextColor(GREEN if kind != "Unknown" else YELLOW)
        self._log(f"[*] Detected type: {kind}")
        self.output.setTextColor(YELLOW)
        for line in info:
            self._log(f"    - {line}")
        if kind == "Unknown":
            self._log("    - Could not identify. If it's hashed text, length hints help.")

    def closeEvent(self, event):
        super().closeEvent(event)


def run(parent=None):
    win = HashAnalyzerWindow(parent)
    win.show()
    return win
