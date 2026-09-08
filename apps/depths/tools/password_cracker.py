"""Password Cracker - The Depths"""

import hashlib
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

from PySide6.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from apps.depths.tools._ui import BTN_STYLE, GREEN, INPUT_STYLE, OUT_STYLE, RED, hline, make_header
from core.theme import COLORS, FONTS

WEAK_PASSWORDS = [
    "password", "123456", "12345678", "1234", "qwerty", "letmein",
    "admin", "welcome", "monkey", "dragon", "master", "football",
    "login", "princess", "abc123", "passw0rd", "shadow", "sunshine",
    "iloveyou", "trustno1", "admin123", "root", "toor", "changeme",
    "hunter2", "123123", "111111", "000000", "654321", "pass123",
    "letmein1", "password1", "qwerty123", "test123", "demo123",
]

HASHMAPS = {
    "MD5": lambda s: hashlib.md5(s.encode()).hexdigest(),
    "SHA-1": lambda s: hashlib.sha1(s.encode()).hexdigest(),
    "SHA-256": lambda s: hashlib.sha256(s.encode()).hexdigest(),
    "SHA-512": lambda s: hashlib.sha512(s.encode()).hexdigest(),
}


class PasswordCrackerWindow(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Password Cracker - The Depths")
        self.resize(680, 560)
        self.setStyleSheet(f"QMainWindow {{ background: {COLORS['bg_light']}; }}")

        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(10)

        layout.addWidget(make_header(
            "\U0001F511 Password Cracker",
            "Recover weak passwords from hashes (dictionary attack)"
        ))
        layout.addWidget(hline())

        row = QHBoxLayout()
        lbl = QLabel("Hash:")
        lbl.setStyleSheet(f"color: {COLORS['text']}; font-size: {FONTS['size_md']}px;")
        row.addWidget(lbl)
        self.hash_input = QLineEdit()
        self.hash_input.setPlaceholderText("Paste MD5/SHA hash to crack")
        self.hash_input.setStyleSheet(INPUT_STYLE)
        row.addWidget(self.hash_input, 1)
        layout.addLayout(row)

        row2 = QHBoxLayout()
        self.algo = QComboBox()
        self.algo.addItems(HASHMAPS.keys())
        self.algo.setStyleSheet(INPUT_STYLE + "QComboBox { padding: 4px 8px; }")
        row2.addWidget(self.algo)

        self.crack_btn = QPushButton("\U0001F50C Crack")
        self.crack_btn.setStyleSheet(BTN_STYLE)
        self.crack_btn.clicked.connect(self.start)
        row2.addWidget(self.crack_btn)

        self.gen_btn = QPushButton("Gen example hash")
        self.gen_btn.setStyleSheet(BTN_STYLE.replace(COLORS["teal"], COLORS["bg_dark"]).replace("#fff", COLORS["text"]))
        self.gen_btn.clicked.connect(self._gen)
        row2.addWidget(self.gen_btn)
        row2.addStretch()
        layout.addLayout(row2)

        self.output = QTextEdit()
        self.output.setReadOnly(True)
        self.output.setStyleSheet(OUT_STYLE)
        layout.addWidget(self.output, 1)

        self._log("[*] Password Cracker ready")
        self._log(f"[*] Dictionary: {len(WEAK_PASSWORDS)} common passwords loaded")

    def _log(self, msg):
        self.output.append(msg)

    def _gen(self):
        import secrets
        pw = secrets.choice(WEAK_PASSWORDS)
        algo = self.algo.currentText()
        hashed = HASHMAPS[algo](pw)
        self.hash_input.setText(hashed)
        self._log(f"[*] Generated example: '{pw}' hashed with {algo}")

    def start(self):
        target = self.hash_input.text().strip()
        if not target:
            self._log("[!] Enter a hash to crack")
            return
        algo = self.algo.currentText()
        self.output.clear()
        self._log(f"[*] Cracking hash with {algo}...")
        self._log(f"[*] Trying {len(WEAK_PASSWORDS)} dictionary words\n")
        self.crack_btn.setEnabled(False)

        found = None
        for i, pw in enumerate(WEAK_PASSWORDS):
            if HASHMAPS[algo](pw) == target.lower():
                found = pw
                break

        self.crack_btn.setEnabled(True)
        if found:
            self.output.setTextColor(GREEN)
            self._log(f"\n[\u2714] Password recovered: {found}")
            self._log(f"[*] '{found}' is a known weak password - change it!")
        else:
            self.output.setTextColor(RED)
            self._log("\n[\u2716] Password not in dictionary.")
            self._log("[*] Try a stronger algorithm or brute-force mode.")

    def closeEvent(self, event):
        super().closeEvent(event)


def run(parent=None):
    win = PasswordCrackerWindow(parent)
    win.show()
    return win
