"""Threat Hunter - The Depths"""

import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

from PySide6.QtWidgets import QHBoxLayout, QMainWindow, QPushButton, QTextEdit, QVBoxLayout, QWidget

from apps.depths.tools._ui import BTN_STYLE, GREEN, OUT_STYLE, RED, YELLOW, hline, make_header
from core.theme import COLORS

IOC_PATTERNS = {
    "Malicious IP (known C2)": r"(45\.155\.205\.\d{1,3}|185\.220\.\d{1,3}\.\d{1,3})",
    "Suspicious domain (DGA)": r"([a-z]{8,}\.xyz|[a-z]{10,}\.top|[a-z]{12,}\.club)",
    "Hash (SHA256 malware)":   r"[a-f0-9]{64}",
    "PowerShell encoded cmd":  r"(powershell|pwsh).*-e[nc]*ode?|encode",
    "Rare high port outbound": r"to\s+[\d.]+:(4444|5555|6666|7777|8888|31337)",
    "Suspicious scheduled task": r"schtasks.*creat|at\s+\d",
    "Exfil pattern (large up)": r"up=-1|upload|POST /upload",
    "Credential dump attempt":   r"(sekurlsa|mimikatz|lsass\.exe dump)",
}

SAMPLE_DATA = """
[12:01:22] 10.0.0.5 connects to 45.155.205.12:4444 (outbound)
[12:01:30] 10.0.0.5 connects to 185.220.101.44:8080
[12:02:01] user runs: powershell -enc SQBFAFgAKAAmACgAWwBSAGUAcwBvAGwAdgBlAGUAcgBdACIA
[12:03:11] file detected: q1w2e3r4t5y6u7i8o9p0a1s2d3f4g5h6j7k8l9z0x9c8v7b6n
[12:04:44] network: 192.168.1.10 -> 66.66.66.66:31337 (data transfer 485 MB)
[12:05:02] process: lsass.exe dump initiated by attacker
[12:06:00] scheduled task created: "WindowsUptimeService"
[12:07:12] 192.168.1.10 uploads 2.4 GB to storage-windows.xyz
[12:08:00] normal: user opens Word document
[12:09:00] normal: printer job submitted
"""


class ThreatHunterWindow(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Threat Hunter - The Depths")
        self.resize(720, 560)
        self.setStyleSheet(f"QMainWindow {{ background: {COLORS['bg_light']}; }}")

        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(10)

        layout.addWidget(make_header(
            "\U0001F40B Threat Hunter",
            "Hunt for indicators of compromise in telemetry"
        ))
        layout.addWidget(hline())

        row = QHBoxLayout()
        self.load_btn = QPushButton("Load sample")
        self.load_btn.setStyleSheet(BTN_STYLE)
        self.load_btn.clicked.connect(self._load_sample)
        row.addWidget(self.load_btn)

        self.hunt_btn = QPushButton("\U0001F50D Hunt")
        self.hunt_btn.setStyleSheet(BTN_STYLE.replace(COLORS["teal"], COLORS["coral"]).replace(COLORS["teal_light"], COLORS["coral_deep"]))
        self.hunt_btn.clicked.connect(self._hunt)
        row.addWidget(self.hunt_btn)
        row.addStretch()
        layout.addLayout(row)

        self.data = QTextEdit()
        self.data.setStyleSheet(OUT_STYLE.replace(COLORS["scan_green"], COLORS["text"]).replace(COLORS["bg_dark"], COLORS["bg_mid"]))
        self.data.setPlaceholderText("Paste telemetry/log data, or load the sample...")
        layout.addWidget(self.data, 2)

        self.output = QTextEdit()
        self.output.setReadOnly(True)
        self.output.setStyleSheet(OUT_STYLE)
        layout.addWidget(self.output, 1)

        self._log("[*] Threat Hunter ready")

    def _log(self, msg):
        self.output.append(msg)

    def _load_sample(self):
        self.data.setPlainText(SAMPLE_DATA.strip())
        self._log("[*] Sample telemetry loaded")

    def _hunt(self):
        content = self.data.toPlainText()
        if not content.strip():
            self._log("[!] No data to hunt through")
            return
        self.output.clear()
        self._log(f"[*] Hunting through {len(content.splitlines())} lines for IOCs...\n")
        hits = 0
        for name, pattern in IOC_PATTERNS.items():
            matches = re.findall(pattern, content, re.IGNORECASE)
            if matches:
                hits += 1
                self.output.setTextColor(RED)
                self._log(f"[\u26A0] {name}")
                for m in matches[:3]:
                    self._log(f"      -> {m}")

        if hits == 0:
            self.output.setTextColor(GREEN)
            self._log("[\u2714] No IOCs detected in this data.")
        else:
            self.output.setTextColor(YELLOW)
            self._log(f"\n[*] Hunt complete: {hits} IOC families flagged.")

    def closeEvent(self, event):
        super().closeEvent(event)


def run(parent=None):
    win = ThreatHunterWindow(parent)
    win.show()
    return win
