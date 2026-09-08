"""Incident Responder - The Depths

Guided interaction with the NIST 800-61 IR lifecycle PLUS a real live-triage
evidence collector: gathers actual system facts (host, kernel, uptime, top
processes by CPU, listening sockets, recent logins) and writes them to a
forensics-style report file the analyst can attach to a ticket - mirroring
what a triage tool like FastIR/`auditd` collects.
"""

import datetime
import os
import subprocess
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QProgressBar,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from apps.depths.tools._ui import BTN_STYLE, CYAN, GREEN, OUT_STYLE, RED, YELLOW, hline, make_header
from core.theme import COLORS, FONTS

PHASES = [
    ("1. Preparation", "Establish a response team, define roles, and prepare tools and playbooks."),
    ("2. Detection & Analysis", "Detect the incident, triage, and perform analysis to confirm and scope it."),
    ("3. Containment", "Stop the spread. Isolate affected systems, preserve evidence, block IOCs."),
    ("4. Eradication", "Remove the root cause. Patch vulnerabilities, delete malware, clean systems."),
    ("5. Recovery", "Restore systems to normal operation, strengthen defenses, validate integrity."),
    ("6. Lessons Learned", "Document what happened, improve processes, update playbooks."),
]


def run_cmd(cmd, timeout=4):
    """Run a command, return stdout text or ''."""
    try:
        out = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout).stdout
        return out.strip()
    except Exception:
        return ""


def collect_evidence():
    """Collect a dict of REAL system facts for the triage report."""
    dt = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S %Z")
    data = {"timestamp": dt}
    data["hostname"] = (run_cmd(["hostname"]) or os.uname().nodename)
    data["kernel"] = os.uname().release
    data["machine"] = os.uname().machine
    # uptime
    try:
        with open("/proc/uptime") as f:
            secs = float(f.read().split()[0])
        mins, _s = divmod(int(secs), 60)
        hrs, mins = divmod(mins, 60)
        data["uptime"] = f"{hrs}h {mins}m"
    except Exception:
        data["uptime"] = "unknown"
    # load + memory from /proc
    data["loadavg"] = " ".join(x.strip() for x in _proc("/proc/loadavg")[:3])
    mem_total, mem_avail = 0, 0
    for line in _proc("/proc/meminfo").splitlines():
        if line.startswith("MemTotal:"):
            mem_total = int(line.split()[1]) // 1024
        elif line.startswith("MemAvailable:"):
            mem_avail = int(line.split()[1]) // 1024
    data["mem_mb"] = f"{mem_total} total / {mem_avail} avail"
    # top processes by CPU (ps if present, else /proc fallback)
    data["top_cpu"] = _top_processes(5)
    data["listeners"] = _listeners(10)
    data["recent_logins"] = run_cmd(["last", "-n", "8", "-w"]).splitlines()[:8]
    data["users_now"] = run_cmd(["who"]).splitlines()[:10]
    return data


def _proc(path):
    try:
        with open(path) as f:
            return f.read()
    except Exception:
        return ""


def _top_processes(n=5):
    if os.name == "nt":
        return []
    try:
        with open("/proc/uptime") as f:
            uptime = float(f.read().split()[0])
        procs = []
        for pid in _proc("/proc").split():
            if not pid.isdigit():
                continue
            try:
                with open(f"/proc/{pid}/stat") as f:
                    fields = f.read().split()
                comm = fields[1].strip("()") if len(fields) > 1 else "?"
                ticks = int(fields[13]) + int(fields[14]) if len(fields) > 14 else 0
                procs.append((ticks, comm))
            except Exception:
                continue
        # crude busyness: total clock ticks since boot
        hz = 100.0
        procs.sort(reverse=True)
        return [f"{comm} ({ticks / hz / uptime * 100:4.1f}%)" for ticks, comm in procs[:n]]
    except Exception:
        return []


def _listeners(n=10):
    """Parse /proc/net/tcp + tcp6 for LISTEN sockets."""
    out = []
    for fname in ("/proc/net/tcp", "/proc/net/tcp6"):
        lines = _proc(fname).splitlines()[1:]
        for line in lines:
            parts = line.split()
            if len(parts) < 4:
                continue
            st = int(parts[3], 16)
            if st != 0x0A:  # LISTEN
                continue
            laddr = parts[1]
            src_ip, port = laddr.split(":")
            port = int(port, 16)
            if port >= 1:
                out.append(f"0.0.0.0:{port}" if src_ip not in ("00000000", "00000000000000000000000000000000") else f"*:{port}")
    return list(dict.fromkeys(out))[:n]


class IncidentResponderWindow(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.phase = 0
        self.setWindowTitle("Incident Responder - The Depths")
        self.resize(720, 600)
        self.setStyleSheet(f"QMainWindow {{ background: {COLORS['bg_light']}; }}")

        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(10)

        layout.addWidget(make_header(
            "\U0001F916 Incident Responder",
            "NIST 800-61 lifecycle + live evidence triage"
        ))
        layout.addWidget(hline())

        self.phase_label = QLabel("")
        self.phase_label.setStyleSheet(f"color: {COLORS['teal_light']}; font-family: \"{FONTS['mono']}\"; font-size: {FONTS['size_lg']}px; font-weight: bold;")
        layout.addWidget(self.phase_label)

        self.progress = QProgressBar()
        self.progress.setRange(0, len(PHASES))
        self.progress.setValue(0)
        self.progress.setStyleSheet(f"""
            QProgressBar {{ background: {COLORS['bg_mid']}; border: 1px solid {COLORS['border']};
                border-radius: 4px; height: 10px; }}
            QProgressBar::chunk {{ background: {COLORS['teal']}; border-radius: 4px; }}
        """)
        layout.addWidget(self.progress)

        self.output = QTextEdit()
        self.output.setReadOnly(True)
        self.output.setStyleSheet(OUT_STYLE.replace(COLORS["scan_green"], COLORS["text"]))
        layout.addWidget(self.output, 1)

        row = QHBoxLayout()
        self.evidence_btn = QPushButton("\U0001F4BE Collect Evidence")
        self.evidence_btn.setStyleSheet(BTN_STYLE.replace(COLORS["teal"], COLORS["coral"]).replace(COLORS["teal_light"], COLORS["coral_deep"]))
        self.evidence_btn.clicked.connect(self._collect_evidence)
        row.addWidget(self.evidence_btn)

        self.prev_btn = QPushButton("\u2190 Prev")
        self.prev_btn.setStyleSheet(BTN_STYLE.replace(COLORS["teal"], COLORS["bg_dark"]).replace("#fff", COLORS["text"]))
        self.prev_btn.clicked.connect(self._prev)
        self.prev_btn.setEnabled(False)
        row.addWidget(self.prev_btn)

        row.addStretch()

        self.next_btn = QPushButton("Next Phase \u2192")
        self.next_btn.setStyleSheet(BTN_STYLE)
        self.next_btn.clicked.connect(self._next)
        row.addWidget(self.next_btn)
        layout.addLayout(row)

        self._render()

    def _render(self):
        name, desc = PHASES[self.phase]
        self.phase_label.setText(name)
        self.progress.setValue(self.phase + 1)
        self.output.clear()
        self.output.setTextColor(COLORS["text_dark"])
        self.output.append(f"\n  {name}\n")
        self.output.setTextColor(COLORS["text"])
        self.output.append(f"  {desc}\n")

        actions = {
            0: "  \u2022 Assemble the IR team\n  \u2022 Define severity levels\n  \u2022 Prepare the toolchain",
            1: "  \u2022 Identify suspicious activity\n  \u2022 Preserve volatile evidence (memory)\n  \u2022 Determine scope & impact",
            2: "  \u2022 Quarantine affected hosts\n  \u2022 Block malicious IPs/hashes\n  \u2022 Preserve forensic images",
            3: "  \u2022 Remove malware\n  \u2022 Patch exploited vulnerabilities\n  \u2022 Rotate compromised credentials",
            4: "  \u2022 Restore from clean backups\n  \u2022 Validate system integrity\n  \u2022 Reconnect monitoring",
            5: "  \u2022 Document findings\n  \u2022 Update detection rules\n  \u2022 Share lessons with the team",
        }
        self.output.setTextColor(YELLOW)
        self.output.append(f"\n  Recommended actions:\n{actions[self.phase]}")
        self.prev_btn.setEnabled(self.phase > 0)
        self.next_btn.setText("Complete IR" if self.phase == len(PHASES) - 1 else "Next Phase \u2192")

    def _collect_evidence(self):
        self.output.clear()
        self._log("[\u26A0] Collecting LIVE evidence...", color=CYAN)
        data = collect_evidence()
        lines = [
            "=== INCIDENT TRIAGE REPORT ===",
            f"Collected:      {data['timestamp']}",
            f"Hostname:       {data['hostname']}",
            f"Kernel:         {data['kernel']} ({data['machine']})",
            f"Uptime:         {data['uptime']}",
            f"Loadavg:        {data['loadavg']}",
            f"Memory:         {data['mem_mb']}",
            "",
            "[*] Top CPU processes:\n" + "\n".join(f"      {p}" for p in data["top_cpu"] or ["(none)"]),
            "[*] Listening TCP sockets:\n" + "\n".join(f"      {p}" for p in data["listeners"] or ["(none readable)"]),
            "[*] Users logged in now:\n" + "\n".join(f"      {p}" for p in data["users_now"] or ["(none)"]),
            "[*] Recent logins (last -w):\n" + "\n".join(f"      {p}" for p in data["recent_logins"] or ["(log unavailable)"]),
        ]
        text = "\n".join(lines)
        for line in lines:
            self._log(line, color=CYAN if line.startswith("[*]") or line.startswith("=== ") else YELLOW)

        # write a real report file
        try:
            out_dir = os.path.expanduser("~/DepthsReports")
            os.makedirs(out_dir, exist_ok=True)
            fname = os.path.join(out_dir, f"ir_report_{os.uname().nodename}_{time.strftime('%Y%m%d_%H%M%S')}.txt")
            with open(fname, "w") as f:
                f.write(text + "\n")
            self._log(f"\n[\u2714] Report written: {fname}", color=GREEN)
            self._log("[*] Ask your incident ticket system to attach this file.", color=YELLOW)
        except Exception as e:
            self._log(f"[!] Could not write report: {e}", color=RED)

    def _log(self, msg, color=YELLOW):
        self.output.setTextColor(color)
        self.output.append(msg)

    def _next(self):
        if self.phase < len(PHASES) - 1:
            self.phase += 1
            self._render()
        else:
            from core.profile import Profile
            p = Profile()
            p.record_challenge("incident_responder", 100, 3)
            self.output.clear()
            self.output.setTextColor(GREEN)
            self.output.append("\n  \u2705 INCIDENT RESPONSE COMPLETE")
            self.output.setTextColor(YELLOW)
            self.output.append("\n  +200 XP  +100 coins  \u2b50\u2b50\u2b50 (challenge unlocked)")

    def _prev(self):
        if self.phase > 0:
            self.phase -= 1
            self._render()

    def closeEvent(self, event):
        super().closeEvent(event)


def run(parent=None):
    win = IncidentResponderWindow(parent)
    win.show()
    return win