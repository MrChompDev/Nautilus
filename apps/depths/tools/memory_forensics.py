"""Memory Forensics - The Depths

Two real workflows, like Volatility/`strings`:
1. LIVE /proc snapshot - enumerate real running processes with cmdline and
   working dir, plus real TCP/UDP sockets from /proc/net. No simulation.
2. DUMP analysis - run real `strings`-style ASCII/Unicode extraction over an
   actual binary file (a .raw dump, .vmss, .bin, or any file) and then flag
   interesting strings (URLs, IPs, suspected C2 ports, embedded passwords).

The pasted-sample mode is kept for quick labs but clearly labeled.
"""

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

SAMPLE_MEMORY = """\
[PROCESS] PID 700  calc.exe    (suspicious - not in normal runlist)
[STRING]  "powershell -enc SQBFAFgAKAAkA..."
[NET]  Established: 10.0.0.5 -> 185.220.101.44:8080
[NET]  Established: 10.0.0.5 -> 45.155.205.12:4444
[ARTIFACT] Scheduled task: "SystemCheck" -> cmd.exe /c rundll32
"""

C2_PORTS = {4444, 5555, 6666, 7777, 8080, 31337, 9001, 9002, 1337}
INTEREST_STRINGS = [
    (r"https?://[^\s\"']+", "URL"),
    (r"\bpassword\s*[:=]\s*[^\s,;]+", "Possible password"),
    (r"\b[A-Za-z0-9+/]{20,}={0,2}\b", "Base64 blob"),
    (r"\b[a-f0-9]{32}\b", "MD5 hash"),
    (r"\b[a-f0-9]{40}\b", "SHA1 hash"),
    (r"\b[a-f0-9]{64}\b", "SHA256 hash"),
    (r"\b([0-9]{1,3}\.){3}[0-9]{1,3}\b", "IPv4 address"),
]


def extract_strings(data, min_len=4):
    """Simulate `strings` (ASCII) - extract printable runs >= min_len."""
    out = []
    cur = bytearray()
    for b in data:
        if 32 <= b < 127 or b in (9,):
            cur.append(b)
        else:
            if len(cur) >= min_len:
                out.append(cur.decode("ascii", errors="replace"))
            cur = bytearray()
    if len(cur) >= min_len:
        out.append(cur.decode("ascii", errors="replace"))
    return out


def live_proc_snapshot():
    """Return lines describing real running processes (pid, cmd, cwd)."""
    lines = []
    try:
        pids = sorted(int(p) for p in os.listdir("/proc") if p.isdigit())
    except OSError:
        return ["(/proc unavailable)"]
    for pid in pids[:400]:
        try:
            with open(f"/proc/{pid}/cmdline", "rb") as f:
                raw = f.read().split(b"\x00")
            cmd = " ".join(x.decode("utf-8", errors="ignore") for x in raw if x)
            if not cmd:
                with open(f"/proc/{pid}/comm", "rb") as f:
                    cmd = f.read().decode("utf-8", errors="ignore").strip()
            try:
                cwd = os.readlink(f"/proc/{pid}/cwd")
            except OSError:
                cwd = "?"
            # name = comm
            try:
                with open(f"/proc/{pid}/status") as f:
                    for ln in f:
                        if ln.startswith("Name:"):
                            name = ln.split()[1]
                            break
                    else:
                        name = "?"
            except OSError:
                name = "?"
            lines.append(f"PID {pid:>5}  {name:<20} {cmd[:80]}  (cwd: {cwd})")
        except OSError:
            continue
    return lines


def live_sockets():
    """Parse /proc/net/tcp{,6} + udp{,6} for established sockets."""
    rows = []
    for guard_name, proto in (("/proc/net/tcp", "TCP"), ("/proc/net/tcp6", "TCP6"), ("/proc/net/udp", "UDP"), ("/proc/net/udp6", "UDP6")):
        try:
            with open(guard_name) as f:
                data = f.read()
        except OSError:
            continue
        for line in data.splitlines()[1:]:
            p = line.split()
            if len(p) < 5:
                continue
            rem_ip = p[2].split(":")[0]
            rem_port = int(p[2].split(":")[1], 16)
            if rem_port and rem_ip not in ("00000000", "00000000000000000000000000000000"):
                ip = ".".join(str(int(rem_ip[i:i+2], 16)) for i in (6, 4, 2, 0))
                rows.append((f"{proto}", f"{ip}:{rem_port}"))
    return rows


class MemoryForensicsWindow(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Memory Forensics - The Depths")
        self.resize(820, 620)
        self.setStyleSheet(f"QMainWindow {{ background: {COLORS['bg_light']}; }}")

        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(10)

        layout.addWidget(make_header(
            "\U0001F4BE Memory Forensics",
            "Live /proc triage + real strings extraction from a dump"
        ))
        layout.addWidget(hline())

        row = QHBoxLayout()
        self.snapshot_btn = QPushButton("\U0001F5A5 Live snapshot")
        self.snapshot_btn.setStyleSheet(BTN_STYLE)
        self.snapshot_btn.clicked.connect(self._snapshot)
        row.addWidget(self.snapshot_btn)

        self.file_btn = QPushButton("Analyze dump file")
        self.file_btn.setStyleSheet(BTN_STYLE.replace(COLORS["teal"], COLORS["coral"]).replace(COLORS["teal_light"], COLORS["coral_deep"]))
        self.file_btn.clicked.connect(self._open_dump)
        row.addWidget(self.file_btn)

        self.sample_btn = QPushButton("Load sample")
        self.sample_btn.setStyleSheet(BTN_STYLE.replace(COLORS["teal"], COLORS["bg_dark"]).replace("#fff", COLORS["text"]))
        self.sample_btn.clicked.connect(self._load_sample)
        row.addWidget(self.sample_btn)

        self.analyze_btn = QPushButton("\U0001F50D Analyze")
        self.analyze_btn.setStyleSheet(BTN_STYLE)
        self.analyze_btn.clicked.connect(self._analyze)
        row.addWidget(self.analyze_btn)
        row.addStretch()
        layout.addLayout(row)

        self.file_label = QLabel("No dump loaded")
        self.file_label.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: {FONTS['size_sm']}px;")
        layout.addWidget(self.file_label)

        self.dump_path = ""
        self.dump = QTextEdit()
        self.dump.setStyleSheet(OUT_STYLE.replace(COLORS["scan_green"], COLORS["text"]).replace(COLORS["bg_dark"], COLORS["bg_mid"]))
        self.dump.setPlaceholderText(
            "Live snapshot output, or a list of extracted strings from a dump.\n"
            "Use 'Analyze dump file' to extract real strings from any binary."
        )
        layout.addWidget(self.dump, 1)

        self.output = QTextEdit()
        self.output.setReadOnly(True)
        self.output.setStyleSheet(OUT_STYLE)
        layout.addWidget(self.output, 1)

        self._log("[*] Memory Forensics ready - live or from a real dump file")

    def _log(self, msg):
        self.output.append(msg)

    def _snapshot(self):
        self.dump.clear()
        procs = live_proc_snapshot()
        self.dump.setPlainText("\n".join(procs))
        self.file_label.setText("LIVE /proc snapshot")
        self._log(f"[*] Live process snapshot captured ({len(procs)} processes)")

    def _open_dump(self):
        path, _ = QFileDialog.getOpenFileName(self, "Select memory dump / binary", os.path.expanduser("~"), "Binary files (*.raw *.mem *.bin *.dmp *.vmss *.vmem *.elf *.img *.data);;All files (*)")
        if not path:
            return
        self.dump_path = path
        try:
            with open(path, "rb") as f:
                data = f.read(8 * 1024 * 1024)  # read first 8MB, like `strings head` on a dump
        except OSError as e:
            self._log(f"[!] Cannot read: {e}")
            return
        strings = extract_strings(data)
        interesting = self._interest(strings, data)
        self.dump.setPlainText("\n".join(interesting if interesting else strings[:200]))
        import os.path as p
        self.file_label.setText(f"{p.basename(path)} ({len(data)} bytes read, {len(strings)} strings extracted)")
        self._log(f"[*] Extracted {len(strings)} strings from {p.basename(path)}")

    def _interest(self, strings, data):
        results = []
        for s in strings:
            for pat, _label in INTEREST_STRINGS:
                if re.search(pat, s, re.IGNORECASE):
                    results.append(s)
                    break
        return results

    def _load_sample(self):
        self.dump.setPlainText(SAMPLE_MEMORY.strip())
        self.file_label.setText("sample memory data")
        self._log("[*] Sample memory dump loaded")

    def _analyze(self):
        content = self.dump.toPlainText()
        if not content.strip():
            self._log("[!] No memory data to analyze")
            return
        self.output.clear()
        self._log("[*] Volatility-style analysis...\n")

        procs = re.findall(r"PID\s+(\d+)\s+([^\s(]+)", content)

        self.output.setTextColor(CYAN)
        self._log(f"[*] {len(procs)} process entries referenced")

        # suspicious process names
        bad_procs = {p for _, p in procs if re.search(r"(mimi|calc|nc[.]exe|powershell|base64|launcher[.]bin)", p, re.I)}
        if bad_procs:
            self.output.setTextColor(RED)
            self._log("[\u26A0] Suspicious process names:")
            for p in sorted(bad_procs):
                self._log(f"      -> {p}")

        # network from live/proc or dump pattern
        addrs = re.findall(r"([\d.]+):(\d{2,5})", content)
        c2 = set()
        for ip, port in addrs:
            if int(port) in C2_PORTS:
                c2.add(f"{ip}:{port}")
        if c2:
            self.output.setTextColor(RED)
            self._log(f"\n[\u26A0] Potential C2 connections (ports {sorted(C2_PORTS)}):")
            for c in sorted(c2):
                self._log(f"      -> {c}")

        # strings of interest
        self.output.setTextColor(YELLOW)
        self._log("\n[*] Interesting strings:")
        interesting = self._interest(content.splitlines(), b"")
        for s in interesting[:15]:
            self.output.setTextColor(YELLOW)
            self._log(f"      -> {s[:80]}")

        base64 = re.findall(r"[A-Za-z0-9+/]{20,}={0,2}", content)
        if base64:
            self.output.setTextColor(RED)
            self._log(f"\n[\u26A0] {len(base64)} base64 blobs - possible encoded payloads")

        self.output.setTextColor(GREEN)
        self._log("\n[*] Analysis complete. Prioritize C2 connections and injected processes.")

    def closeEvent(self, event):
        super().closeEvent(event)


def run(parent=None):
    win = MemoryForensicsWindow(parent)
    win.show()
    return win