"""Timeline Builder - The Depths"""

import datetime
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

from PySide6.QtWidgets import QHBoxLayout, QMainWindow, QPushButton, QTextEdit, QVBoxLayout, QWidget

from apps.depths.tools._ui import BTN_STYLE, CYAN, GREEN, OUT_STYLE, RED, YELLOW, hline, make_header
from core.theme import COLORS

SAMPLE_EVENTS = [
    "2026-08-19 01:30:02 - Initial access: brute force on sshd (45.155.205.12)",
    "2026-08-19 01:32:11 - Successful login as admin (password reused)",
    "2026-08-19 01:35:00 - User added to sudoers group",
    "2026-08-19 01:40:22 - Persistence: scheduled task 'SystemCheck' created",
    "2026-08-19 01:45:09 - Defense evasion: antivirus service stopped",
    "2026-08-19 02:00:00 - Lateral movement: SMB connection to 10.0.0.20",
    "2026-08-19 02:15:44 - Credential access: lsass.exe memory dumped",
    "2026-08-19 03:10:01 - Exfiltration: 2.4 GB uploaded to evil.example",
    "2026-08-19 03:45:00 - Impact: files encrypted with .locked extension",
]

KILL_CHAIN = [
    "Initial Access", "Execution", "Persistence", "Privilege Escalation",
    "Defense Evasion", "Credential Access", "Discovery", "Lateral Movement",
    "Collection", "Exfiltration", "Impact",
]


class TimelineBuilderWindow(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Timeline Builder - The Depths")
        self.resize(760, 580)
        self.setStyleSheet(f"QMainWindow {{ background: {COLORS['bg_light']}; }}")

        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(10)

        layout.addWidget(make_header(
            "\U0001F4C5 Timeline Builder",
            "Map the attack - reconstruct the kill chain from events"
        ))
        layout.addWidget(hline())

        row = QHBoxLayout()
        self.load_btn = QPushButton("Load sample")
        self.load_btn.setStyleSheet(BTN_STYLE)
        self.load_btn.clicked.connect(self._load)
        row.addWidget(self.load_btn)

        self.build_btn = QPushButton("\U0001F4C5 Build Timeline")
        self.build_btn.setStyleSheet(BTN_STYLE.replace(COLORS["teal"], COLORS["coral"]).replace(COLORS["teal_light"], COLORS["coral_deep"]))
        self.build_btn.clicked.connect(self._build)
        row.addWidget(self.build_btn)
        row.addStretch()
        layout.addLayout(row)

        self.events = QTextEdit()
        self.events.setStyleSheet(OUT_STYLE.replace(COLORS["scan_green"], COLORS["text"]).replace(COLORS["bg_dark"], COLORS["bg_mid"]))
        self.events.setPlaceholderText("Paste timestamped events (one per line)...")
        layout.addWidget(self.events, 2)

        self.output = QTextEdit()
        self.output.setReadOnly(True)
        self.output.setStyleSheet(OUT_STYLE)
        layout.addWidget(self.output, 1)

        self._log("[*] Timeline Builder ready")

    def _log(self, msg):
        self.output.append(msg)

    def _load(self):
        self.events.setPlainText("\n".join(SAMPLE_EVENTS))
        self._log("[*] Sample events loaded")

    def _build(self):
        content = self.events.toPlainText()
        if not content.strip():
            self._log("[!] No events to build timeline")
            return
        self.output.clear()

        lines = [line.strip() for line in content.splitlines() if line.strip()]
        self._log(f"[*] Parsing {len(lines)} events...")

        def sort_key(line):
            m = re.match(r"(\d{4}-\d{2}-\d{2})[ T](\d{2}:\d{2}:\d{2})", line)
            if m:
                try:
                    return datetime.datetime.strptime(m.group(1) + " " + m.group(2), "%Y-%m-%d %H:%M:%S")
                except ValueError:
                    return datetime.datetime.min
            return datetime.datetime.min

        try:
            sorted_events = sorted(lines, key=sort_key)
        except Exception:
            sorted_events = lines

        self._log("\n[*] Chronological timeline:\n")
        self.output.setTextColor(CYAN)
        for i, ev in enumerate(sorted_events, 1):
            self.output.setTextColor(YELLOW)
            self._log(f"  {i:2}. {ev}")

        # Kill chain mapping
        self._log("\n[*] Kill chain phase mapping:\n")
        for ev in sorted_events:
            phase = "Discovery"
            for kw, p in [
                ("brute force", "Initial Access"),
                ("login", "Execution"),
                ("scheduled task", "Persistence"),
                ("sudoers", "Privilege Escalation"),
                ("antivirus stopped", "Defense Evasion"),
                ("lsass", "Credential Access"),
                ("SMB connection", "Lateral Movement"),
                ("uploaded", "Exfiltration"),
                ("encrypted", "Impact"),
            ]:
                if kw.lower() in ev.lower():
                    phase = p
                    break
            color = RED if phase in ("Exfiltration", "Impact") else YELLOW
            self.output.setTextColor(color)
            self._log(f"  [{phase:<20}] {ev[:60]}")

        self.output.setTextColor(GREEN)
        self._log("\n[*] Timeline complete. You can see the full attack sequence.")

    def closeEvent(self, event):
        super().closeEvent(event)


def run(parent=None):
    win = TimelineBuilderWindow(parent)
    win.show()
    return win
