"""Steganography Lab - The Depths"""

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

from apps.depths.tools._ui import BTN_STYLE, GREEN, INPUT_STYLE, OUT_STYLE, YELLOW, hline, make_header
from core.theme import COLORS, FONTS


class SteganographyWindow(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Steganography Lab - The Depths")
        self.resize(720, 560)
        self.setStyleSheet(f"QMainWindow {{ background: {COLORS['bg_light']}; }}")

        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(10)

        layout.addWidget(make_header(
            "\U0001F3E0 Steganography Lab",
            "Hide and extract messages in images (LSB technique)"
        ))
        layout.addWidget(hline())

        row = QHBoxLayout()
        lbl = QLabel("Mode:")
        lbl.setStyleSheet(f"color: {COLORS['text']}; font-size: {FONTS['size_md']}px;")
        row.addWidget(lbl)
        self.mode = QComboBox()
        self.mode.addItems(["Encode (hide message)", "Decode (extract message)"])
        self.mode.setStyleSheet(INPUT_STYLE + "QComboBox { padding: 4px 8px; }")
        row.addWidget(self.mode, 1)
        layout.addLayout(row)

        self.msg_label = QLabel("Secret message:")
        self.msg_label.setStyleSheet(f"color: {COLORS['text']}; font-size: {FONTS['size_md']}px;")
        layout.addWidget(self.msg_label)
        self.message = QLineEdit()
        self.message.setPlaceholderText("Your hidden message...")
        self.message.setStyleSheet(INPUT_STYLE)
        layout.addWidget(self.message)

        self.mode.currentIndexChanged.connect(self._mode_changed)

        row2 = QHBoxLayout()
        self.do_btn = QPushButton("\U0001F9EA Run")
        self.do_btn.setStyleSheet(BTN_STYLE)
        self.do_btn.clicked.connect(self._run)
        row2.addWidget(self.do_btn)
        row2.addStretch()
        layout.addLayout(row2)

        self.output = QTextEdit()
        self.output.setReadOnly(True)
        self.output.setStyleSheet(OUT_STYLE)
        layout.addWidget(self.output, 1)

        self._log("[*] Steganography Lab ready")
        self._log("[*] Demonstrates LSB embedding into a base-color image.")

    def _log(self, msg):
        self.output.append(msg)

    def _mode_changed(self, idx):
        if idx == 0:
            self.msg_label.setText("Secret message:")
            self.message.setPlaceholderText("Your hidden message...")
        else:
            self.msg_label.setText("Secret message (extract):")
            self.message.setPlaceholderText("(leave empty to extract)")

    def _run(self):
        if self.mode.currentIndex() == 0:
            msg = self.message.text()
            if not msg.strip():
                self._log("[!] Enter a message to hide")
                return
            self._encode(msg)
        else:
            self._decode()

    def _encode(self, msg):
        self.output.clear()
        data = msg.encode()
        self._log(f"[*] Embedding message ({len(data)} bytes) using LSB steganography...")
        self._log("[*] Technique: modify least significant bit of each RGB channel")
        self._log("\n[*] Concept:")
        self._log("    Original pixel:  ( 34,  77, 200)  = 00100010 01001101 11001000")
        self._log("    Secret bit 0:    \u0394 last bit of red channel")
        self._log("    Modified pixel:  ( 34,  77, 201)")
        self._log("\n[*] Visually identical, but the message rides in the noise.\n")
        self._log("[*] Example binary stream:")
        bits = " ".join(f"{b:08b}" for b in data[:4])
        self._log(f"    {bits}  ...")
        self._log("\n[\u2714] Message encoded. In a real lab, saved to a PNG.")
        self._log("[*] Detection: statistical analysis reveals anomalous LSB patterns.")

    def _decode(self):
        self.output.clear()
        self._log("[*] Extracting message from LSB planes...")
        self._log("[*] Reading least significant bit of each color channel")
        self._log("[*] Reassembling bytes until null terminator...\n")
        self.output.setTextColor(GREEN)
        self._log("[\u2714] DECODED MESSAGE:")
        self._log("")
        self._log("    Welcome to the Deep. FLAG{DEEP_DIVE_SUCCESS}")
        self._log("")
        self.output.setTextColor(YELLOW)
        self._log("[*] Try hiding a message and see how it looks to an analyst.")

    def closeEvent(self, event):
        super().closeEvent(event)


def run(parent=None):
    win = SteganographyWindow(parent)
    win.show()
    return win
