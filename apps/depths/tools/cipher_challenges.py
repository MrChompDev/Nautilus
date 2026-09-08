"""Cipher Challenges - The Depths"""

import base64
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


def rot13(s):
    out = []
    for ch in s:
        if "a" <= ch <= "z":
            out.append(chr((ord(ch) - 97 + 13) % 26 + 97))
        elif "A" <= ch <= "Z":
            out.append(chr((ord(ch) - 65 + 13) % 26 + 65))
        else:
            out.append(ch)
    return "".join(out)


def atbash(s):
    out = []
    for ch in s:
        if "a" <= ch <= "z":
            out.append(chr(219 - ord(ch)))
        elif "A" <= ch <= "Z":
            out.append(chr(155 - ord(ch)))
        else:
            out.append(ch)
    return "".join(out)


def b64_decode(s):
    try:
        return base64.b64decode(s).decode()
    except Exception:
        return None


def hex_decode(s):
    try:
        return bytes.fromhex(s).decode()
    except Exception:
        return None


def xor_decode(s, key):
    if not s:
        return None
    try:
        raw = s.encode()
        keyb = key.encode()
        return bytes(b ^ keyb[i % len(keyb)] for i, b in enumerate(raw)).decode()
    except Exception:
        return None


class CipherChallengesWindow(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Cipher Challenges - The Depths")
        self.resize(720, 560)
        self.setStyleSheet(f"QMainWindow {{ background: {COLORS['bg_light']}; }}")

        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(10)

        layout.addWidget(make_header(
            "\U0001F4D1 Cipher Challenges",
            "The Codebook - decode classic ciphers"
        ))
        layout.addWidget(hline())

        row = QHBoxLayout()
        lbl = QLabel("Cipher:")
        lbl.setStyleSheet(f"color: {COLORS['text']}; font-size: {FONTS['size_md']}px;")
        row.addWidget(lbl)
        self.cipher = QComboBox()
        self.cipher.addItems(["ROT13", "Atbash", "Base64", "Hex", "XOR"])
        self.cipher.setStyleSheet(INPUT_STYLE + "QComboBox { padding: 4px 8px; }")
        row.addWidget(self.cipher, 1)
        layout.addLayout(row)

        self.key_label = QLabel("XOR key:")
        self.key_label.setStyleSheet(f"color: {COLORS['text']}; font-size: {FONTS['size_md']}px;")
        self.key_label.hide()
        layout.addWidget(self.key_label)

        self.key_input = QLineEdit("secret")
        self.key_input.setStyleSheet(INPUT_STYLE)
        self.key_input.hide()
        layout.addWidget(self.key_input)

        self.cipher.currentIndexChanged.connect(self._cipher_changed)

        row2 = QHBoxLayout()
        lbl2 = QLabel("Input:")
        lbl2.setStyleSheet(f"color: {COLORS['text']}; font-size: {FONTS['size_md']}px;")
        row2.addWidget(lbl2)
        self.input = QLineEdit()
        self.input.setPlaceholderText("Encoded text to decode...")
        self.input.setStyleSheet(INPUT_STYLE)
        row2.addWidget(self.input, 1)
        layout.addLayout(row2)

        self.decode_btn = QPushButton("\U0001F50D Decode")
        self.decode_btn.setStyleSheet(BTN_STYLE)
        self.decode_btn.clicked.connect(self._decode)
        layout.addWidget(self.decode_btn)

        self.output = QTextEdit()
        self.output.setReadOnly(True)
        self.output.setStyleSheet(OUT_STYLE)
        layout.addWidget(self.output, 1)

        self._log("[*] Cipher Challenges ready")
        self._log("[*] Pick a cipher and decode the message!")

    def _log(self, msg):
        self.output.append(msg)

    def _cipher_changed(self, idx):
        show = self.cipher.currentText() == "XOR"
        self.key_label.setVisible(show)
        self.key_input.setVisible(show)

    def _decode(self):
        txt = self.input.text()
        if not txt.strip():
            self._log("[!] Enter encoded text")
            return
        self.output.clear()
        cipher = self.cipher.currentText()
        self._log(f"[*] Decoding with {cipher}...\n")

        result = None
        if cipher == "ROT13":
            result = rot13(txt)
        elif cipher == "Atbash":
            result = atbash(txt)
        elif cipher == "Base64":
            result = b64_decode(txt)
        elif cipher == "Hex":
            result = hex_decode(txt)
        elif cipher == "XOR":
            key = self.key_input.text() or "secret"
            result = xor_decode(txt, key)

        if result:
            self.output.setTextColor(GREEN)
            self._log("[\u2714] Decoded message:")
            self._log("")
            self._log(f"    {result}")
        else:
            self.output.setTextColor(RED)
            self._log(f"[\u2716] Could not decode. Check the input format for {cipher}.")

    def closeEvent(self, event):
        super().closeEvent(event)


def run(parent=None):
    win = CipherChallengesWindow(parent)
    win.show()
    return win
