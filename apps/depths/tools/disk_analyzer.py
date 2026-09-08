"""Disk Analyzer - The Depths

Real filesystem forensics. Scans a real directory like autopsy does for disk
images: walks the tree, reads real file metadata (name/size/mtime), computes
SHA-256 hashes, identifies file types from real magic bytes, and flags files
that look suspicious for an investigation (executables, archives, scripts).
"""

import datetime
import hashlib
import os
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

from apps.depths.tools._ui import BTN_STYLE, CYAN, GREEN, INPUT_STYLE, OUT_STYLE, RED, YELLOW, hline, make_header
from core.theme import COLORS, FONTS

MAGIC = [
    (b"\x89PNG\r\n\x1a\n", "PNG image"),
    (b"\xFF\xD8\xFF",      "JPEG image"),
    (b"GIF87a",            "GIF image"),
    (b"GIF89a",            "GIF image"),
    (b"%PDF-",             "PDF document"),
    (b"PK\x03\x04",        "ZIP archive / Office doc"),
    (b"Rar!",              "RAR archive"),
    (b"7z\xBC\xAF\x27\x1C", "7-Zip archive"),
    (b"\x7FELF",           "Linux ELF executable"),
    (b"MZ",                "Windows PE executable"),
    (b"#!/",               "Script"),
    (b"#! /",              "Script"),
    (b"\x1f\x8b",          "gzip archive"),
    (b"BZh",               "bzip2 archive"),
    (b"\xFD7zXZ\x00",      "xz archive"),
    (b"\xED\xAB\xEE\xDB",  "rpm package"),
    (b"SQLite format 3\x00", "SQLite database"),
    (b"\xFF\xFB",          "MP3 audio"),
    (b"\x00\x00\x00\x18ftyp", "MP4 video"),
]

SUSPICIOUS_EXTS = {
    ".exe", ".dll", ".scr", ".bat", ".cmd", ".ps1", ".vbs", ".wsf",
    ".js", ".jse", ".hta", ".msi", ".bin", ".elf", ".sh", ".py",
    ".zip", ".7z", ".rar", ".tar", ".gz", ".xz",
    ".pdf", ".doc", ".docx", ".xls", ".xlsx",
}

SENSITIVE = {"password", "passwd", "secret", "credential", "id_rsa", ".key", "token", "env"}


def file_type(path, head):
    for sig, label in MAGIC:
        if head.startswith(sig):
            return label
    return "Unknown"


def sniff(path, max_read=512):
    try:
        with open(path, "rb") as f:
            head = f.read(max_read)
        typ = file_type(path, head)
        try:
            # rule out false MZ/!# from text files
            with open(path, encoding="utf-8", errors="ignore") as f:
                f.read(256)
            if typ == "Unknown":
                return "Text"
        except Exception:
            pass
        return typ
    except OSError:
        return "Unreadable"


class DiskWorker(QThread):
    item = Signal(dict)
    done = Signal()
    log = Signal(str)

    def __init__(self, path):
        super().__init__()
        self.path = path

    def run(self):
        total = 0
        scanned = 0
        bytype = {}
        for idx, (root, dirs, files) in enumerate(os.walk(self.path)):
            try:
                dirs.sort()
            except OSError:
                pass
            for name in files:
                full = os.path.join(root, name)
                try:
                    st = os.stat(full)
                except OSError:
                    continue
                total += st.st_size
                scanned += 1
                head = None
                try:
                    with open(full, "rb") as f:
                        head = f.read(512)
                except OSError:
                    pass
                typ = file_type(full, head) if head else "Unknown"

                # hashing is expensive; only hash smaller files to stay responsive
                sha = ""
                if st.st_size <= 2_000_000:
                    try:
                        h = hashlib.sha256()
                        with open(full, "rb") as f:
                            for chunk in iter(lambda: f.read(65536), b""):
                                h.update(chunk)
                        sha = h.hexdigest()
                    except OSError:
                        sha = ""

                bytype[typ] = bytype.get(typ, 0) + 1
                rel = os.path.relpath(full, self.path)
                ext = os.path.splitext(name)[1].lower()
                suspicious = ext in SUSPICIOUS_EXTS or any(k in name.lower() for k in SENSITIVE)
                mtime = datetime.datetime.fromtimestamp(st.st_mtime).strftime("%Y-%m-%d %H:%M:%S")
                self.item.emit({
                    "name": rel, "size": st.st_size, "type": typ,
                    "mtime": mtime, "hash": sha[:16], "suspicious": suspicious,
                })
        self.log.emit(f"[*] {scanned} files, {total} bytes")
        self.log.emit(f"[*] Type histogram: {bytype}")
        self.done.emit()


class DiskAnalyzerWindow(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.worker = None
        self.setWindowTitle("Disk Analyzer - The Depths")
        self.resize(760, 580)
        self.setStyleSheet(f"QMainWindow {{ background: {COLORS['bg_light']}; }}")

        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(10)

        layout.addWidget(make_header(
            "\U0001F4C0 Disk Analyzer",
            "Real folder forensics - file types, hashes, suspicious artifacts"
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
        self.browse.setStyleSheet(BTN_STYLE.replace(COLORS["teal"], COLORS["bg_dark"]).replace("#fff", COLORS["text"]))
        self.browse.clicked.connect(self._browse)
        row.addWidget(self.browse)

        self.scan_btn = QPushButton("\U0001F50D Scan")
        self.scan_btn.setStyleSheet(BTN_STYLE)
        self.scan_btn.clicked.connect(self._scan)
        row.addWidget(self.scan_btn)
        layout.addLayout(row)

        self.output = QTextEdit()
        self.output.setReadOnly(True)
        self.output.setStyleSheet(OUT_STYLE)
        layout.addWidget(self.output, 1)

        self._log("[*] Disk Analyzer ready - scans a real folder")
        self._log("[*] Files <= 2MB are SHA-256 hashed; larger files list metadata only.")

    def _log(self, msg):
        self.output.append(msg)

    def _browse(self):
        p = QFileDialog.getExistingDirectory(self, "Select folder to analyze", self.path.text())
        if p:
            self.path.setText(p)

    def _scan(self):
        p = self.path.text().strip()
        if not os.path.isdir(p):
            self._log(f"[!] Not a folder: {p}")
            return
        self.output.clear()
        self._log(f"[*] Scanning {p}\n")
        self.scan_btn.setEnabled(False)
        self.worker = DiskWorker(p)
        self.worker.item.connect(self._on_item)
        self.worker.log.connect(self._log)
        self.worker.done.connect(lambda: self.scan_btn.setEnabled(True))
        self.worker.start()

    def _on_item(self, info):
        color = RED if info["suspicious"] else GREEN if info["type"] != "Unknown" else YELLOW
        self.output.setTextColor(color)
        mark = " [!] " if info["suspicious"] else "     "
        self._log(f"{mark}{info['name']:<40} {info['size']:>10}  {info['type']:<20} {info['mtime']}")
        if info["hash"]:
            self.output.setTextColor(CYAN)
            self._log(f"         sha256:{info['hash']}...")

    def closeEvent(self, event):
        super().closeEvent(event)


def run(parent=None):
    win = DiskAnalyzerWindow(parent)
    win.show()
    return win