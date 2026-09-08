"""Social Mapper - The Depths"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

from PySide6.QtWidgets import QHBoxLayout, QLabel, QLineEdit, QMainWindow, QPushButton, QTextEdit, QVBoxLayout, QWidget

from apps.depths.tools._ui import BTN_STYLE, CYAN, GREEN, INPUT_STYLE, OUT_STYLE, YELLOW, hline, make_header
from core.theme import COLORS, FONTS


class SocialMapperWindow(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Social Mapper - The Depths")
        self.resize(700, 560)
        self.setStyleSheet(f"QMainWindow {{ background: {COLORS['bg_light']}; }}")

        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(10)

        layout.addWidget(make_header(
            "\U0001F465 Social Mapper",
            "Connect the dots - map one identity across networks"
        ))
        layout.addWidget(hline())

        warn = QLabel("\u26A0 Privacy-first awareness tool. For educational footprint analysis only.")
        warn.setWordWrap(True)
        warn.setStyleSheet(f"color: {COLORS['warning']}; font-size: {FONTS['size_sm']}px;")
        layout.addWidget(warn)

        row = QHBoxLayout()
        lbl = QLabel("Identity:")
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

    def _log(self, msg):
        self.output.append(msg)

    def _map(self):
        base = self.identity.text().strip()
        if not base:
            self._log("[!] Enter an identity")
            return
        self.output.clear()

        variants = [
            base,
            f"{base}1",
            f"the{base}",
            f"{base}dev",
            f"real{base}",
            f"{base}_official",
            f"{base}123",
            f"its{base}",
        ]

        self.output.setTextColor(CYAN)
        self._log(f"[*] Identity '{base}' -> common handle variants:\n")
        for v in variants:
            self._log(f"    \u2022 {v}")

        self.output.setTextColor(GREEN)
        self._log("\n[\u2714] Linked identities to search:")
        self._log(f"    Email: {base}@mail.com, {base}.dev@gmail.com")
        self._log(f"    GitHub: github.com/{base}")
        self._log(f"    Discord: {base}#(4-digit tag unknown)")

        self.output.setTextColor(YELLOW)
        self._log("\n[*] Correlation tips:")
        self._log("    - Same avatar across platforms = strong link")
        self._log("    - Same bio text = link")
        self._log("    - Mutual follows = link")
        self._log("    - Timezone of posts = location hint")

    def closeEvent(self, event):
        super().closeEvent(event)


def run(parent=None):
    win = SocialMapperWindow(parent)
    win.show()
    return win
