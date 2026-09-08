"""Packet Capture - The Depths"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QHBoxLayout, QLabel, QMainWindow, QPushButton, QTextEdit, QVBoxLayout, QWidget

from apps.depths.tools._ui import BTN_STYLE, GREEN, OUT_STYLE, YELLOW, hline, make_header
from core.theme import COLORS, FONTS


class PacketCaptureWindow(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.captured = 0
        self.running = False
        self.timer = QTimer()
        self.timer.timeout.connect(self._capture)
        self.setWindowTitle("Packet Capture - The Depths")
        self.resize(680, 560)
        self.setStyleSheet(f"QMainWindow {{ background: {COLORS['bg_light']}; }}")

        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(10)

        layout.addWidget(make_header(
            "\U0001F4E6 Packet Capture",
            "See network traffic flowing by (simulated analyzer)"
        ))
        layout.addWidget(hline())

        row = QHBoxLayout()
        self.start_btn = QPushButton("\u25B6 Capture")
        self.start_btn.setStyleSheet(BTN_STYLE)
        self.start_btn.clicked.connect(self.toggle)
        row.addWidget(self.start_btn)

        self.clear_btn = QPushButton("Clear")
        self.clear_btn.setStyleSheet(BTN_STYLE.replace(COLORS["teal"], COLORS["bg_dark"]).replace("#fff", COLORS["text"]))
        self.clear_btn.clicked.connect(self._clear)
        row.addWidget(self.clear_btn)

        lbl = QLabel("Packets:")
        lbl.setStyleSheet(f"color: {COLORS['text']}; font-size: {FONTS['size_md']}px;")
        row.addWidget(lbl)
        self.count_label = QLabel("0")
        self.count_label.setStyleSheet(f"color: {COLORS['teal_light']}; font-weight: bold; font-size: {FONTS['size_md']}px;")
        row.addWidget(self.count_label)
        row.addStretch()
        layout.addLayout(row)

        self.output = QTextEdit()
        self.output.setReadOnly(True)
        self.output.setStyleSheet(OUT_STYLE)
        layout.addWidget(self.output, 1)

        self._log("[*] Packet Capture ready")
        self._log("[*] Note: This demonstrates packet analysis. Root privileges " \
                  "are required for real capture; this simulates the workflow.")

    def _log(self, msg):
        self.output.append(msg)

    def toggle(self):
        self.running = not self.running
        if self.running:
            self.start_btn.setText("\u23F9 Stop")
            self._log("\n[*] Capturing...")
            self.timer.start(700)
        else:
            self.start_btn.setText("\u25B6 Capture")
            self.timer.stop()
            self._log(f"[*] Capture stopped ({self.captured} packets)")

    def _capture(self):
        import random
        self.captured += 1
        src = f"192.168.1.{random.randint(1, 250)}"
        dst = f"192.168.1.{random.randint(1, 250)}"
        proto = random.choice(["TCP", "UDP", "ICMP", "DNS", "HTTP", "HTTPS", "SSH"])
        port = random.choice([21, 22, 53, 80, 443, 8080, 445, 3306, 8000, 9000])
        size = random.randint(46, 1500)
        flags = random.choice(["SYN", "ACK", "PSH,ACK", "SYN,ACK", "FIN", "RST"])
        ttl = random.randint(32, 128)
        color = YELLOW if proto in ("HTTP", "HTTPS") else GREEN
        line = f"    {src:<16} :{port:<6} -> {dst:<16}  {proto:<5} {flags:<8} size={size:<5} ttl={ttl}"
        self.output.setTextColor(color)
        self.output.append(line)
        self.count_label.setText(str(self.captured))

    def _clear(self):
        self.captured = 0
        self.count_label.setText("0")
        self.output.clear()

    def closeEvent(self, event):
        self.timer.stop()
        super().closeEvent(event)


def run(parent=None):
    win = PacketCaptureWindow(parent)
    win.show()
    return win
