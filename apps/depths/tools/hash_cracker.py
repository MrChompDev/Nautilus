"""Hash Cracker - The Depths"""

import hashlib
import itertools
import os
import string
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

from PySide6.QtCore import QThread, Signal
from PySide6.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QPushButton,
    QSpinBox,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from apps.depths.tools._ui import BTN_STYLE, GREEN, INPUT_STYLE, OUT_STYLE, YELLOW, hline, make_header
from core.theme import COLORS, FONTS

ALGOS = ["MD5", "SHA-1", "SHA-256"]

DICT = ["123456", "password", "admin", "qwerty", "abc123", "letmein", "welcome",
        "monkey", "test", "pass", "secret", "root", "user", "guest", "demo",
        "pass123", "qwerty123", "iloveyou", "sunshine", "dragon", "shadow"]


class CrackerWorker(QThread):
    found = Signal(str)
    progress = Signal(int)
    done = Signal(bool)

    def __init__(self, target, algo, length):
        super().__init__()
        self.target = target
        self.algo = algo
        self.length = length
        hasher = {
            "MD5": hashlib.md5, "SHA-1": hashlib.sha1, "SHA-256": hashlib.sha256
        }[algo]
        self.hash = lambda s: hasher(s.encode()).hexdigest()
        self.charset = string.ascii_lowercase + string.digits

    def run(self):
        for pw in DICT:
            if self.hash(pw) == self.target:
                self.found.emit(pw + " (dictionary)")
                self.done.emit(True)
                return
        total = len(self.charset) ** self.length
        for i, combo in enumerate(itertools.product(self.charset, repeat=self.length)):
            pw = "".join(combo)
            if self.hash(pw) == self.target:
                self.found.emit(pw + f" (brute force length {self.length})")
                self.done.emit(True)
                return
            if i % 2000 == 0:
                self.progress.emit(int(i / total * 100))
        self.done.emit(False)


class HashCrackerWindow(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.worker = None
        self.setWindowTitle("Hash Cracker - The Depths")
        self.resize(680, 560)
        self.setStyleSheet(f"QMainWindow {{ background: {COLORS['bg_light']}; }}")

        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(10)

        layout.addWidget(make_header(
            "\U0001F5DD Hash Cracker",
            "Brute-force short passwords against a hash"
        ))
        layout.addWidget(hline())

        row = QHBoxLayout()
        lbl = QLabel("Alg:")
        lbl.setStyleSheet(f"color: {COLORS['text']}; font-size: {FONTS['size_md']}px;")
        row.addWidget(lbl)
        self.algo = QComboBox()
        self.algo.addItems(ALGOS)
        self.algo.setStyleSheet(INPUT_STYLE + "QComboBox{padding:4px 8px;}")
        row.addWidget(self.algo)

        row.addWidget(QLabel("Hash:"))
        self.hash_in = QLineEdit()
        self.hash_in.setStyleSheet(INPUT_STYLE)
        row.addWidget(self.hash_in, 1)
        layout.addLayout(row)

        row2 = QHBoxLayout()
        row2.addWidget(QLabel("Max len:"))
        self.length = QSpinBox()
        self.length.setRange(1, 4)
        self.length.setValue(3)
        self.length.setStyleSheet(INPUT_STYLE + "QSpinBox{padding:4px;}")
        row2.addWidget(self.length)

        self.crack_btn = QPushButton("\U0001F50C Crack")
        self.crack_btn.setStyleSheet(BTN_STYLE)
        self.crack_btn.clicked.connect(self._crack)
        row2.addWidget(self.crack_btn)
        row2.addStretch()
        layout.addLayout(row2)

        self.output = QTextEdit()
        self.output.setReadOnly(True)
        self.output.setStyleSheet(OUT_STYLE)
        layout.addWidget(self.output, 1)

        self._log("[*] Hash Cracker ready")

    def _log(self, msg):
        self.output.append(msg)

    def _crack(self):
        target = self.hash_in.text().strip()
        if not target:
            self._log("[!] Enter a hash")
            return
        self.output.clear()
        algo = self.algo.currentText()
        self._log(f"[*] Attacking {algo} hash: {target}")
        self._log(f"[*] Phase 1: dictionary ({len(DICT)} words)...")
        self.crack_btn.setEnabled(False)
        self.worker = CrackerWorker(target, algo, self.length.value())
        self.worker.found.connect(self._found)
        self.worker.done.connect(self._done)
        self.worker.start()

    def _found(self, msg):
        self.output.setTextColor(GREEN)
        self._log(f"[\u2714] CRACKED: {msg}")

    def _done(self, success):
        self.crack_btn.setEnabled(True)
        if not success:
            self.output.setTextColor(YELLOW)
            self._log("[*] Brute force complete - password not found at this length.")

    def closeEvent(self, event):
        if self.worker:
            self.worker.quit()
        super().closeEvent(event)


def run(parent=None):
    win = HashCrackerWindow(parent)
    win.show()
    return win
