"""Disk Analyzer - The Depths"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

from PySide6.QtWidgets import QComboBox, QHBoxLayout, QLabel, QMainWindow, QPushButton, QTextEdit, QVBoxLayout, QWidget

from apps.depths.tools._ui import BTN_STYLE, CYAN, GREEN, INPUT_STYLE, OUT_STYLE, RED, YELLOW, hline, make_header
from core.theme import COLORS, FONTS

# Simulated FAT/NTFS image file listing
SAMPLE_FILES = [
    {"name": "autorun.inf",  "size": 128,   "deleted": True,  "suspicious": True,  "date": "2026-08-19 03:12"},
    {"name": "report.pdf",   "size": 4200,  "deleted": False, "suspicious": False, "date": "2026-08-18 14:02"},
    {"name": "payload.bin",  "size": 64000, "deleted": True,  "suspicious": True,  "date": "2026-08-19 03:30"},
    {"name": "notes.txt",    "size": 240,   "deleted": False, "suspicious": False, "date": "2026-08-10 09:00"},
    {"name": "script.ps1",   "size": 1800,  "deleted": False, "suspicious": True,  "date": "2026-08-19 02:55"},
    {"name": "config.ini",   "size": 512,   "deleted": True,  "suspicious": False, "date": "2026-08-01 12:00"},
    {"name": "secret.jpg",   "size": 88000, "deleted": True,  "suspicious": True,  "date": "2026-08-19 03:45"},
]


class DiskAnalyzerWindow(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Disk Analyzer - The Depths")
        self.resize(720, 560)
        self.setStyleSheet(f"QMainWindow {{ background: {COLORS['bg_light']}; }}")

        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(10)

        layout.addWidget(make_header(
            "\U0001F4C0 Disk Analyzer",
            "Scan the seafloor - analyze disk images and recover artifacts"
        ))
        layout.addWidget(hline())

        row = QHBoxLayout()
        lbl = QLabel("Subsystem:")
        lbl.setStyleSheet(f"color: {COLORS['text']}; font-size: {FONTS['size_md']}px;")
        row.addWidget(lbl)
        self.type = QComboBox()
        self.type.addItems(["FAT32", "NTFS", "EXT4", "APFS"])
        self.type.setStyleSheet(INPUT_STYLE + "QComboBox { padding: 4px 8px; }")
        row.addWidget(self.type, 1)
        layout.addLayout(row)

        row2 = QHBoxLayout()
        self.load_btn = QPushButton("Load sample image")
        self.load_btn.setStyleSheet(BTN_STYLE)
        self.load_btn.clicked.connect(self._load)
        row2.addWidget(self.load_btn)

        self.recover_btn = QPushButton("\U0001F50D Recover Deleted")
        self.recover_btn.setStyleSheet(BTN_STYLE.replace(COLORS["teal"], COLORS["coral"]).replace(COLORS["teal_light"], COLORS["coral_deep"]))
        self.recover_btn.clicked.connect(self._recover)
        row2.addWidget(self.recover_btn)
        row2.addStretch()
        layout.addLayout(row2)

        self.output = QTextEdit()
        self.output.setReadOnly(True)
        self.output.setStyleSheet(OUT_STYLE)
        layout.addWidget(self.output, 1)

        self._files = []
        self._log("[*] Disk Analyzer ready")

    def _log(self, msg):
        self.output.append(msg)

    def _load(self):
        self._files = [dict(f) for f in SAMPLE_FILES]
        self.output.clear()
        fs = self.type.currentText()
        self._log(f"[*] Mounted {fs} image, scanning directory entries...\n")
        self.output.setTextColor(CYAN)
        self._log(f"{'FILE':<20}{'SIZE':<12}{'STATUS':<12}{'DATE'}")
        self._log("-" * 60)
        for f in self._files:
            status = "DELETED" if f["deleted"] else "active"
            color = RED if f["suspicious"] else GREEN if f["deleted"] else CYAN
            self.output.setTextColor(color)
            self._log(f"{f['name']:<20}{f['size']:<12}{status:<12}{f['date']}")
        self.output.setTextColor(YELLOW)
        self._log(f"\n[*] {sum(1 for f in self._files if f['deleted'])} deleted file(s) detected - candidates for recovery.")

    def _recover(self):
        if not self._files:
            self._log("[!] Load a disk image first")
            return
        self._log("\n[*] Attempting recovery of deleted files...\n")
        recovered = []
        for f in self._files:
            if f["deleted"]:
                recovered.append(f)
                color = GREEN if not f["suspicious"] else RED
                self.output.setTextColor(color)
                self._log(f"[\u2714] Recovered: {f['name']} ({f['size']} bytes)")
                if f["suspicious"]:
                    self.output.setTextColor(RED)
                    self._log("      \u26A0 Suspicious content detected in recovered file")
        if not recovered:
            self.output.setTextColor(YELLOW)
            self._log("[*] No deleted files to recover.")

    def closeEvent(self, event):
        super().closeEvent(event)


def run(parent=None):
    win = DiskAnalyzerWindow(parent)
    win.show()
    return win
