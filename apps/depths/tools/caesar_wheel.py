"""Caesar Wheel - The Depths"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

from PySide6.QtWidgets import (
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

from apps.depths.tools._ui import BTN_STYLE, CYAN, GREEN, INPUT_STYLE, OUT_STYLE, YELLOW, hline, make_header
from core.theme import COLORS, FONTS


def caesar(s, shift):
    out = []
    for ch in s:
        if "a" <= ch <= "z":
            out.append(chr((ord(ch) - 97 + shift) % 26 + 97))
        elif "A" <= ch <= "Z":
            out.append(chr((ord(ch) - 65 + shift) % 26 + 65))
        else:
            out.append(ch)
    return "".join(out)


class CaesarWheelWindow(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Caesar Wheel - The Depths")
        self.resize(720, 560)
        self.setStyleSheet(f"QMainWindow {{ background: {COLORS['bg_light']}; }}")

        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(10)

        layout.addWidget(make_header(
            "\U0001F300 Caesar Wheel",
            "Spin the wheel of shifting tides - decode Caesar ciphers"
        ))
        layout.addWidget(hline())

        row = QHBoxLayout()
        lbl = QLabel("Text:")
        lbl.setStyleSheet(f"color: {COLORS['text']}; font-size: {FONTS['size_md']}px;")
        row.addWidget(lbl)
        self.text = QLineEdit("Wkh vkrs lv orzq ri hyloh ilvk")
        self.text.setStyleSheet(INPUT_STYLE)
        row.addWidget(self.text, 1)
        layout.addLayout(row)

        row2 = QHBoxLayout()
        lbl2 = QLabel("Shift:")
        lbl2.setStyleSheet(f"color: {COLORS['text']}; font-size: {FONTS['size_md']}px;")
        row2.addWidget(lbl2)
        self.shift = QSpinBox()
        self.shift.setRange(-25, 25)
        self.shift.setValue(3)
        self.shift.setStyleSheet(INPUT_STYLE + "QSpinBox{padding:4px;}")
        row2.addWidget(self.shift)

        self.shift.valueChanged.connect(self._update)

        self.encode_btn = QPushButton("Encode")
        self.encode_btn.setStyleSheet(BTN_STYLE.replace(COLORS["teal"], COLORS["bg_dark"]).replace("#fff", COLORS["text"]))
        self.encode_btn.clicked.connect(lambda: self._set_shift(-self.shift.value()))
        row2.addWidget(self.encode_btn)

        self.auto_btn = QPushButton("\U0001F50D Brute Force All")
        self.auto_btn.setStyleSheet(BTN_STYLE)
        self.auto_btn.clicked.connect(self._bruteforce)
        row2.addWidget(self.auto_btn)
        row2.addStretch()
        layout.addLayout(row2)

        self.output = QTextEdit()
        self.output.setReadOnly(True)
        self.output.setStyleSheet(OUT_STYLE)
        layout.addWidget(self.output, 1)

        self._update()

    def _log(self, msg):
        self.output.append(msg)

    def _update(self):
        self.output.clear()
        text = self.text.text()
        shift = self.shift.value()
        res = caesar(text, shift)
        self.output.setTextColor(GREEN)
        self._log(f"Decoded (shift {shift}):\n")
        self._log(f"    {res}")

        shifted = caesar(text, -shift)
        self.output.setTextColor(CYAN)
        self._log(f"\nEncoded (shift -{shift}, i.e. {(-shift)%26}):\n")
        self._log(f"    {shifted}")

    def _set_shift(self, val):
        self.shift.setValue(val)

    def _bruteforce(self):
        self.output.clear()
        text = self.text.text()
        self.output.setTextColor(YELLOW)
        self._log("[*] Trying all 25 shifts...\n")
        for i in range(1, 26):
            res = caesar(text, i)
            self.output.setTextColor(GREEN if i == self.shift.value() and (i % 26) == (self.shift.value() % 26) or i == (-self.shift.value() % 26) else CYAN)
            self._log(f"  shift {i:>2}: {res}")

    def closeEvent(self, event):
        super().closeEvent(event)


def run(parent=None):
    win = CaesarWheelWindow(parent)
    win.show()
    return win
