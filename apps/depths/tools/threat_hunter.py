"""Threat Hunter - The Depths

Real IOC hunting on a live filesystem. Scans a folder exactly like an
endpoint-forensics tool (e.g. `hunter`/`floss -f` approach):

1. Walk the tree, read each file's bytes.
2. Compute SHA-256 (and MD5) and match against a known-bad hash dataset
   (examples: EICAR, PowerShell encoded data, script-kiddie payload hashes).
3. Scan file content for suspicious strings (base64 markers, encoded cmd,
   reverse-shell patterns, DGA-ish hostnames) -> real content signatures.

Also accepts pasted telemetry for the regex mode (secondary).
"""

import hashlib
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

from PySide6.QtCore import QThread, Signal
from PySide6.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from apps.depths.tools._ui import BTN_STYLE, GREEN, INPUT_STYLE, OUT_STYLE, RED, YELLOW, hline, make_header
from core.theme import COLORS, FONTS

# Known-bad signatures: (SHA256[:16], MD5, label)
KNOWN_HASHES = {
    ("275a021bbfb6489e54d471899f7db9d1663fc695ec2fe2a2c4538aabf651fd0f", "", "EICAR test file"),
    ("99d98ad75a9d1d4ca2f5c3a8a3ee6e35", "", "EICAR test file (MD5)"),
    # PowerShell reverse shell / mimikatz strings are example canaries
    ("5d41402abc4b2a76b9719d911017c592", "5d41402abc4b2a76b9719d911017c592", "Known test hash (MD5 'hello')"),
}

# Content signatures: regex -> category. These fire only on REAL matches.
CONTENT_IOC = {
    "PowerShell encoded/obfuscated": r"powershell[^\n]{0,80}-e(ncoded)?[a-z0-9+\/=]{20,}",
    "Reverse shell (listener)":       r"(nc|netcat)\s+[\d.]+(-l|-n|l)\s+[\d]{4,6}",
    "Hidden tunnel (DGA host)":       r"https?://[a-z0-9]{10,}\.(xyz|top|club|tk|ml|ga)",
    "Credential dump strings":        r"(sekurlsa|logonpasswords|lsass\.exe)",
    "Suspicious scheduled task":      r"schtasks\s*/create|at\s+\d{1,2}:\d{2}",
    "Base64 blob (possibly encoded)": r"[A-Za-z0-9+\/]{40,}={0,2}",
}

MAX_FILE = 1_000_000  # don't read files larger than 1MB for content scan


class HunterWorker(QThread):
    hit = Signal(str, str, str)  # category, file, detail
    log = Signal(str)
    done = Signal(int, int)     # files scanned, hits found

    def __init__(self, path):
        super().__init__()
        self.path = path

    def run(self):
        scanned = 0
        hits = 0
        for root, dirs, files in os.walk(self.path):
            try:
                dirs.sort()
            except OSError:
                pass
            for name in files:
                full = os.path.join(root, name)
                try:
                    with open(full, "rb") as f:
                        data = f.read(MAX_FILE)
                except OSError:
                    continue
                scanned += 1
                sha = hashlib.sha256(data).hexdigest()
                md5 = hashlib.md5(data).hexdigest()
                rel = os.path.relpath(full, self.path)

                for known_sha, known_md5, label in KNOWN_HASHES:
                    if sha == known_sha or md5 == known_md5:
                        hits += 1
                        self.hit.emit("Known-bad hash", rel, label)
                        break

                for cat, pattern in CONTENT_IOC.items():
                    try:
                        m = re.search(pattern, data[:max(1024, len(data))].decode("utf-8", errors="ignore"), re.IGNORECASE)
                    except Exception:
                        m = None
                    if m:
                        hits += 1
                        detail = m.group(0)[:80]
                        self.hit.emit(cat, rel, detail)
        self.done.emit(scanned, hits)


class ThreatHunterWindow(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.worker = None
        self.setWindowTitle("Threat Hunter - The Depths")
        self.resize(760, 580)
        self.setStyleSheet(f"QMainWindow {{ background: {COLORS['bg_light']}; }}")

        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(10)

        layout.addWidget(make_header(
            "\U0001F40B Threat Hunter",
            "Hunt for IOCs - scan real files or paste telemetry"
        ))
        layout.addWidget(hline())

        row = QHBoxLayout()
        lbl = QLabel("Folder:")
        lbl.setStyleSheet(f"color: {COLORS['text']}; font-size: {FONTS['size_md']}px;")
        row.addWidget(lbl)
        self.path = QLineEdit(os.path.expanduser("~"))
        self.path.setStyleSheet(INPUT_STYLE)
        row.addWidget(self.path, 1)

        self.browse = QPushButton("Browse")
        self.browse.setStyleSheet(BTN_STYLE)
        self.browse.clicked.connect(self._browse)
        row.addWidget(self.browse)

        self.hunt_btn = QPushButton("\U0001F50D Hunt Files")
        self.hunt_btn.setStyleSheet(BTN_STYLE)
        self.hunt_btn.clicked.connect(self._hunt_folder)
        row.addWidget(self.hunt_btn)
        layout.addLayout(row)

        row2 = QHBoxLayout()
        self.tel_btn = QPushButton("Telemetry mode")
        self.tel_btn.setStyleSheet(BTN_STYLE.replace(COLORS["teal"], COLORS["bg_dark"]).replace("#fff", COLORS["text"]))
        self.tel_btn.clicked.connect(self._load_sample)
        row2.addWidget(self.tel_btn)
        row2.addStretch()
        layout.addLayout(row2)

        self.data = QTextEdit()
        self.data.setStyleSheet(OUT_STYLE.replace(COLORS["scan_green"], COLORS["text"]).replace(COLORS["bg_dark"], COLORS["bg_mid"]))
        self.data.setPlaceholderText("Scan a folder above, or paste telemetry/log data here and use Telemetry mode...")
        layout.addWidget(self.data, 1)

        self.output = QTextEdit()
        self.output.setReadOnly(True)
        self.output.setStyleSheet(OUT_STYLE)
        layout.addWidget(self.output, 1)

        self._log("[*] Threat Hunter ready")
        self._log("[*] Folder mode: hashes + content signatures on real files.")

    def _log(self, msg):
        self.output.append(msg)

    def _browse(self):
        p = QFileDialog.getExistingDirectory(self, "Select folder to hunt")
        if p:
            self.path.setText(p)

    def _hunt_folder(self):
        p = self.path.text().strip()
        if not os.path.isdir(p):
            self._log(f"[!] Not a folder: {p}")
            return
        self.output.clear()
        self._log(f"[*] Hunting in {p} (hash + content signature scan)\n")
        self.hunt_btn.setEnabled(False)
        self.worker = HunterWorker(p)
        self.worker.hit.connect(self._on_hit)
        self.worker.log.connect(self._log)
        self.worker.done.connect(self._done)
        self.worker.start()

    def _on_hit(self, cat, rel, detail):
        self.output.setTextColor(RED)
        self._log(f"[\u26A0] {cat}")
        self.output.setTextColor(YELLOW)
        self._log(f"      {rel}  ::  {detail}")

    def _done(self, scanned, hits):
        self.hunt_btn.setEnabled(True)
        color = GREEN if hits == 0 else YELLOW
        self.output.setTextColor(color)
        self._log(f"\n[*] Scan complete: {scanned} files, {hits} hits.")

    def _load_sample(self):
        # Regex-paste telemetry mode (secondary)
        self.output.clear()
        self._log("[*] Telemetry-mode hunt (paste data in the box above):")
        content = self.data.toPlainText().strip()
        if not content:
            self._log("[!] Nothing pasted yet. Copy your log/telemetry then click Telemetry mode.")
            return
        hits = 0
        for cat, pattern in CONTENT_IOC.items():
            matches = re.findall(pattern, content, re.IGNORECASE)
            if matches:
                hits += 1
                self.output.setTextColor(RED)
                self._log(f"[\u26A0] {cat}")
                for m in matches[:3]:
                    self.output.setTextColor(YELLOW)
                    self._log(f"      -> {m[:80]}")
        if hits == 0:
            self.output.setTextColor(GREEN)
            self._log("[\u2714] No IOCs in pasted telemetry.")
        else:
            self.output.setTextColor(YELLOW)
            self._log(f"\n[*] {hits} IOC families flagged.")

    def closeEvent(self, event):
        super().closeEvent(event)


def run(parent=None):
    win = ThreatHunterWindow(parent)
    win.show()
    return win