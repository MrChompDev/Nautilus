"""WiFi Analyzer - The Depths"""

import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QHBoxLayout, QLabel, QMainWindow, QPushButton, QTextEdit, QVBoxLayout, QWidget

from apps.depths.tools._ui import BTN_STYLE, GREEN, OUT_STYLE, RED, YELLOW, hline, make_header
from core.theme import COLORS, FONTS

SAMPLE_NETWORKS = [
    ("HomeNet",        "-50",  "WPA2",  False, 0x8888),
    ("Starbucks_WiFi", "-65",  "Open",  False, 0xCCCC),
    ("ATT3482",        "-72",  "WPA2",  False, 0x1111),
    ("Neighbor5G",     "-78",  "WPA3",  False, 0x2222),
    ("FBI_Surveillance_Van", "-90", "Open", False, 0xAAAA),
    ("Free_Public_WiFi", "-58", "Open",  False, 0x9999),
]


class WifiAnalyzerWindow(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.networks = [list(n) for n in SAMPLE_NETWORKS]
        self.timer = QTimer()
        self.timer.timeout.connect(self._jitter)
        self.timer.start(2000)
        self.setWindowTitle("WiFi Analyzer - Signal Depths")
        self.resize(700, 560)
        self.setStyleSheet(f"QMainWindow {{ background: {COLORS['bg_light']}; }}")

        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(10)

        layout.addWidget(make_header(
            "\U0001F4F6 WiFi Analyzer",
            "Read the waves - scan nearby wireless networks"
        ))
        layout.addWidget(hline())

        row = QHBoxLayout()
        self.scan_btn = QPushButton("\U0001F50D Scan")
        self.scan_btn.setStyleSheet(BTN_STYLE)
        self.scan_btn.clicked.connect(self._scan)
        row.addWidget(self.scan_btn)

        lbl = QLabel("Networks found:")
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

        self._log("[*] WiFi Analyzer ready")
        self._log("[*] Requires monitor-mode adapter for real capture; demo mode shown here.")

    def _log(self, msg):
        self.output.append(msg)

    def _jitter(self):
        for net in self.networks:
            val = int(net[1])
            net[1] = str(val + random.randint(-2, 2))

    def _scan(self):
        self.output.clear()
        self.count_label.setText(str(len(self.networks)))
        self._log("[*] Scanning 2.4GHz and 5GHz channels...\n")
        self._log(f"{'SSID':<28}{'RSSI':<8}{'SEC':<8}{'CH'}")
        self._log("-" * 60)

        for ssid, rssi, sec, rogue, ch in self.networks:
            color = RED if sec == "Open" else GREEN
            self.output.setTextColor(color)
            rogue_mark = " [ROGUE?]" if ssid == "FBI_Surveillance_Van" else ""
            self._log(f"{ssid:<28}{rssi:<8}{sec:<8}6{rogue_mark}")

        self.output.setTextColor(YELLOW)
        self._log("\n[*] 2 open networks detected - unsafe for sensitive data.")
        self._log("[*] 'FBI_Surveillance_Van' has no corporate SSID match - investigate as potential rogue AP.")
        self._log("[*] Rogue APs mimic legitimate names (e.g., 'Free_Public_WiFi') to capture credentials.")

    def closeEvent(self, event):
        self.timer.stop()
        super().closeEvent(event)


def run(parent=None):
    win = WifiAnalyzerWindow(parent)
    win.show()
    return win
