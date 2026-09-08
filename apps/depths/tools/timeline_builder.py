"""Timeline Builder - The Depths

Real timeline reconstruction from actual file metadata. Scans a real folder
and builds a chronological timeline from file ctime/mtime/atime - the same
"file activity timeline" a forensic tool like Plaso or `fls -m` produces from
a filesystem. Kill-chain phase mapping is applied to the real metadata when
suspicious artifacts (scripts, executables, archives) are present.

Also accepts pasted timestamped events as a secondary mode (sample provided).
"""

import datetime
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

from PySide6.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from apps.depths.tools._ui import BTN_STYLE, CYAN, GREEN, OUT_STYLE, RED, YELLOW, hline, make_header
from core.theme import COLORS, FONTS

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

MAPPINGS = [
    ("brute force", "Initial Access"),
    ("ssh", "Initial Access"),
    ("login", "Execution"),
    ("scheduled task", "Persistence"),
    ("cron", "Persistence"),
    ("sudoers", "Privilege Escalation"),
    ("sudo", "Privilege Escalation"),
    ("antivirus stopped", "Defense Evasion"),
    ("lsass", "Credential Access"),
    ("SMB connection", "Lateral Movement"),
    ("wget", "Exfiltration"),
    ("uploaded", "Exfiltration"),
    ("encrypted", "Impact"),
    (".locked", "Impact"),
]

SUSPICIOUS_EXT = {".sh", ".py", ".bat", ".cmd", ".ps1", ".exe", ".bin", ".elf", ".zip", ".7z", ".gz", ".rar", ".tar"}


def ts(st):
    return datetime.datetime.fromtimestamp(st).strftime("%Y-%m-%d %H:%M:%S")


def kill_chain(line):
    for kw, phase in MAPPINGS:
        if kw.lower() in line.lower():
            return phase
    return "Discovery"


class TimelineBuilderWindow(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Timeline Builder - The Depths")
        self.resize(800, 640)
        self.setStyleSheet(f"QMainWindow {{ background: {COLORS['bg_light']}; }}")

        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(10)

        layout.addWidget(make_header(
            "\U0001F4C5 Timeline Builder",
            "Build a forensics timeline - from disk metadata or pasted events"
        ))
        layout.addWidget(hline())

        row = QHBoxLayout()
        self.load_btn = QPushButton("\U0001F4C1 Scan folder")
        self.load_btn.setStyleSheet(BTN_STYLE)
        self.load_btn.clicked.connect(self._scan_folder)
        row.addWidget(self.load_btn)

        self.sample_btn = QPushButton("Load sample events")
        self.sample_btn.setStyleSheet(BTN_STYLE.replace(COLORS["teal"], COLORS["bg_dark"]).replace("#fff", COLORS["text"]))
        self.sample_btn.clicked.connect(self._load_sample)
        row.addWidget(self.sample_btn)

        self.build_btn = QPushButton("\u2705 Build Timeline")
        self.build_btn.setStyleSheet(BTN_STYLE.replace(COLORS["teal"], COLORS["coral"]).replace(COLORS["teal_light"], COLORS["coral_deep"]))
        self.build_btn.clicked.connect(self._build)
        row.addWidget(self.build_btn)
        row.addStretch()
        layout.addLayout(row)

        self.mode_label = QLabel()
        self.mode_label.setStyleSheet(f"color: {COLORS['scan_green']}; font-size: {FONTS['size_sm']}px;")
        layout.addWidget(self.mode_label)

        self.events = QTextEdit()
        self.events.setStyleSheet(OUT_STYLE.replace(COLORS["scan_green"], COLORS["text"]).replace(COLORS["bg_dark"], COLORS["bg_mid"]))
        self.events.setPlaceholderText("Paste timestamped events (one per line), or scan a folder to build a real file-metadata timeline...")
        layout.addWidget(self.events, 2)

        self.output = QTextEdit()
        self.output.setReadOnly(True)
        self.output.setStyleSheet(OUT_STYLE)
        layout.addWidget(self.output, 1)

        self._log("[*] Timeline Builder ready")
        self._log("[*] Scan a folder to build a REAL timeline from file ctime/mtime/atime.")

    def _log(self, msg):
        self.output.append(msg)

    def _scan_folder(self):
        p = QFileDialog.getExistingDirectory(self, "Select folder to build timeline")
        if not p:
            return
        artifacts = []
        max_files = 3000
        count = 0
        for root, dirs, files in os.walk(p):
            try:
                dirs.sort()
            except OSError:
                pass
            for name in files:
                if count >= max_files:
                    break
                full = os.path.join(root, name)
                try:
                    st = os.lstat(full)
                except OSError:
                    continue
                rel = os.path.relpath(full, p)
                ext = os.path.splitext(name)[1].lower()
                susp = " [SUSPICIOUS]" if ext in SUSPICIOUS_EXT else ""
                artifacts.append(f"{ts(st.st_ctime)} [C] {rel} {st.st_size}B{susp}")
                artifacts.append(f"{ts(st.st_mtime)} [M] {rel} {st.st_size}B{susp}")
                artifacts.append(f"{ts(st.st_atime)} [A] {rel} {st.st_size}B{susp}")
                count += 1
        self.events.setPlainText("\n".join(artifacts))
        self.mode_label.setText(f"\U0001F4C1 Real metadata timeline for {count} files (created/modified/accessed)")
        self._log("[*] Folder scanned - file metadata timeline built into the events box.")

    def _load_sample(self):
        self.events.setPlainText("\n".join(SAMPLE_EVENTS))
        self.mode_label.setText("Sample incident events")
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

        sorted_events = sorted(lines, key=sort_key)

        self._log("\n[*] Chronological timeline:\n")
        self.output.setTextColor(CYAN)
        for i, ev in enumerate(sorted_events, 1):
            self.output.setTextColor(YELLOW)
            self._log(f"  {i:2}. {ev}")

        self._log("\n[*] Kill chain phase mapping:\n")
        for ev in sorted_events:
            phase = kill_chain(ev)
            color = RED if phase in ("Exfiltration", "Impact") else YELLOW
            self.output.setTextColor(color)
            self._log(f"  [{phase:<20}] {ev[:75]}")

        self.output.setTextColor(GREEN)
        self._log("\n[*] Timeline complete. You can see the full attack sequence.")

    def closeEvent(self, event):
        super().closeEvent(event)


def run(parent=None):
    win = TimelineBuilderWindow(parent)
    win.show()
    return win