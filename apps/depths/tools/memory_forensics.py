"""Memory Forensics - The Depths"""

import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

from PySide6.QtWidgets import QHBoxLayout, QMainWindow, QPushButton, QTextEdit, QVBoxLayout, QWidget

from apps.depths.tools._ui import BTN_STYLE, CYAN, GREEN, OUT_STYLE, RED, YELLOW, hline, make_header
from core.theme import COLORS

# Simulated memory dump content for the lab
SAMPLE_MEMORY = """
[PROCESS] PID 1    SYSTEM  (kernel)
[PROCESS] PID 120  svchost.exe  C:\\Windows\\System32
[PROCESS] PID 350  explorer.exe  USER SESSION
[PROCESS] PID 512  chrome.exe   (net: established 45.155.205.12:4444)
[PROCESS] PID 620  lsass.exe   SECURITY
[PROCESS] PID 700  calc.exe    (suspicious - not in normal runlist)
[THREAD]  PID 512  thread 4: CreateRemoteThread in svchost
[STRING]  "powershell -enc SQBFAFgAKAAkA..."
[STRING]  "C:\\Users\\admin\\AppData\\Roaming\\payload.bin"
[ARTIFACT] Scheduled task: "SystemCheck" -> cmd.exe /c rundll32
[NET]  Established: 10.0.0.5 -> 185.220.101.44:8080
[NET]  Established: 10.0.0.5 -> 45.155.205.12:4444
[HASH]  Running process hash: a1b2c3d4...
[VOLATILE] New process injected into PID 512
"""


class MemoryForensicsWindow(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Memory Forensics - The Depths")
        self.resize(720, 560)
        self.setStyleSheet(f"QMainWindow {{ background: {COLORS['bg_light']}; }}")

        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(10)

        layout.addWidget(make_header(
            "\U0001F4BE Memory Forensics",
            "Dredge artifacts from a volatile memory dump"
        ))
        layout.addWidget(hline())

        row = QHBoxLayout()
        self.load_btn = QPushButton("Load sample dump")
        self.load_btn.setStyleSheet(BTN_STYLE)
        self.load_btn.clicked.connect(self._load)
        row.addWidget(self.load_btn)

        self.analyze_btn = QPushButton("\U0001F50D Analyze")
        self.analyze_btn.setStyleSheet(BTN_STYLE.replace(COLORS["teal"], COLORS["coral"]).replace(COLORS["teal_light"], COLORS["coral_deep"]))
        self.analyze_btn.clicked.connect(self._analyze)
        row.addWidget(self.analyze_btn)
        row.addStretch()
        layout.addLayout(row)

        self.dump = QTextEdit()
        self.dump.setStyleSheet(OUT_STYLE.replace(COLORS["scan_green"], COLORS["text"]).replace(COLORS["bg_dark"], COLORS["bg_mid"]))
        self.dump.setPlaceholderText("Paste raw memory strings/artifacts...")
        layout.addWidget(self.dump, 2)

        self.output = QTextEdit()
        self.output.setReadOnly(True)
        self.output.setStyleSheet(OUT_STYLE)
        layout.addWidget(self.output, 1)

        self._log("[*] Memory Forensics ready")

    def _log(self, msg):
        self.output.append(msg)

    def _load(self):
        self.dump.setPlainText(SAMPLE_MEMORY.strip())
        self._log("[*] Sample memory dump loaded")

    def _analyze(self):
        content = self.dump.toPlainText()
        if not content.strip():
            self._log("[!] No memory data")
            return
        self.output.clear()
        self._log("[*] Running volatility-style analysis...\n")

        procs = re.findall(r"\[PROCESS\]\s+(.+)", content)
        self.output.setTextColor(CYAN)
        self._log(f"[*] {len(procs)} processes enumerated")

        suspicious = []
        for p in procs:
            if "suspicious" in p.lower() or "calc" in p.lower() or "mimi" in p.lower():
                suspicious.append(p)
        if suspicious:
            self.output.setTextColor(RED)
            self._log("[\u26A0] Suspicious processes:")
            for s in suspicious:
                self._log(f"      -> {s}")

        net = re.findall(r"\[NET\][^\n]*", content)
        self.output.setTextColor(YELLOW)
        self._log(f"\n[*] {len(net)} network connections")
        for n in net:
            if "4444" in n or "8080" in n:
                self.output.setTextColor(RED)
                self._log(f"[\u26A0] {n.strip()}  <-- suspicious C2")
            else:
                self.output.setTextColor(YELLOW)
                self._log(f"      {n.strip()}")

        strings = re.findall(r'\[STRING\]\s+"([^"]+)"', content)
        self.output.setTextColor(CYAN)
        self._log(f"\n[*] {len(strings)} interesting strings extracted")
        for s in strings:
            self.output.setTextColor(YELLOW)
            self._log(f"      -> {s}")

        artifacts = re.findall(r"\[ARTIFACT\][^\n]*", content)
        self.output.setTextColor(CYAN)
        self._log(f"\n[*] {len(artifacts)} artifacts found")
        for a in artifacts:
            self.output.setTextColor(RED)
            self._log(f"[\u26A0] {a.strip()}")

        self.output.setTextColor(GREEN)
        self._log("\n[*] Analysis complete. Prioritize C2 connections and injected processes.")

    def closeEvent(self, event):
        super().closeEvent(event)


def run(parent=None):
    win = MemoryForensicsWindow(parent)
    win.show()
    return win
