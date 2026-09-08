"""WiFi Analyzer - The Depths

Real wireless scan. Uses `nmcli device wifi list` (NetworkManager, default on
most distros incl. Raspberry Pi OS desktop) or falls back to `iw dev <iface>
scan`. Each result line carries real SSID, BSSID, signal (dBm), channel,
security mode, and frequency.

If neither tool exists (no WiFi hardware / minimal install) it shows a clearly
labeled demo set instead of pretending to scan.
"""

import os
import re
import shutil
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

from PySide6.QtCore import QThread, Signal
from PySide6.QtWidgets import QHBoxLayout, QLabel, QMainWindow, QPushButton, QTextEdit, QVBoxLayout, QWidget

from apps.depths.tools._ui import BTN_STYLE, CYAN, GREEN, OUT_STYLE, RED, YELLOW, hline, make_header
from core.theme import COLORS, FONTS


def wifi_hardware():
    """Return True if a compatible command+driver exists, False otherwise."""
    if shutil.which("nmcli"):
        return True
    if shutil.which("iw"):
        return any(iface for iface in os.listdir("/sys/class/net") if iface != "lo")
    return False


def run_cmd(cmd, timeout=8):
    try:
        out = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return out.stdout.strip()
    except Exception:
        return ""


def parse_nmcli(text):
    """Parse `nmcli -f SSID,BSSID,SIGNAL,CHAN,SECURITY dev wifi list` output."""
    nets = []
    line_re = re.compile(
        r"^(?P<ssid>[^\s].*?)\s+"
        r"(?P<bssid>[0-9A-Fa-f:]{17})\s+"
        r"(?P<sig>\d+)\s+"
        r"(?P<chan>[\d.]+)\s+"
        r"(?P<sec>(WPA2|WPA3|WPA|Open|IEEE 802\.1X|Enterprise).*)$"
    )
    for line in text.splitlines()[1:]:
        m = line_re.match(line)
        if m:
            nets.append({
                "ssid": m.group("ssid"),
                "bssid": m.group("bssid"),
                "signal": int(m.group("sig")),
                "chan": m.group("chan"),
                "sec": m.group("sec") or "Open",
            })
    return nets


def real_scan():
    """Perform a real scan; return (nets, source_label, error_msg)."""
    if shutil.which("nmcli"):
        text = run_cmd(["nmcli", "-f", "SSID,BSSID,SIGNAL,CHAN,SECURITY", "dev", "wifi", "list"])
        if text and len(text.splitlines()) > 1:
            nets = parse_nmcli(text)
            return nets, "nmcli", ""
        # nmcli present but list empty -> not connected / no scanning
    if shutil.which("iw"):
        # try each wifi interface
        for iface in os.listdir("/sys/class/net"):
            if iface == "lo":
                continue
            try:
                with open(f"/sys/class/net/{iface}/type") as f:
                    if int(f.read().strip()) != 1:  # only Ethernet/wireless-ish
                        continue
            except OSError:
                continue
            text = run_cmd(["iw", "dev", iface, "scan"])
            if text:
                return parse_iw(text), f"iw ({iface})", ""
    return [], "", "No WiFi scan possible (no nmcli/iw or no wireless adapter)."


def parse_iw(text):
    """Parse `iw dev <if> scan` block output into dicts."""
    nets = []
    cur = {}
    for line in text.splitlines():
        line = line.strip()
        if line.startswith("BSS "):
            if cur:
                nets.append(cur)
            cur = {"bssid": line.split()[1], "signal": None, "chan": "", "sec": "Open"}
        elif line.startswith("signal:"):
            m = re.search(r"signal:\s*(-?[\d.]+) dBm", line)
            if m:
                cur["signal"] = float(m.group(1))
        elif line.startswith("freq:"):
            pass
        elif line.startswith("SSID:"):
            cur["ssid"] = line.split(":", 1)[1].strip() or "(hidden)"
        elif "RSN:" in line or "WPA:" in line:
            if "RSN" in line:
                cur["sec"] = "WPA2/3/IEEE8021X if WPA3 capable" if "WPA3" in line else "WPA2/3"
            elif "WPA:" in line:
                cur["sec"] = "WPA"
        elif "capability:" in line and "Privacy" in line and cur.get("sec") == "Open":
            cur["sec"] = "WPA (privacy flag)"
    if cur:
        nets.append(cur)
    return nets


SAMPLE_NETWORKS = [
    {"ssid": "HomeNet", "signal": -50,  "sec": "WPA2", "chan": "6",  "bssid": "aa:bb:cc:00:11:22"},
    {"ssid": "Starbucks_WiFi", "signal": -65, "sec": "Open", "chan": "11", "bssid": "00:11:22:33:44:55"},
    {"ssid": "ATT3482", "signal": -72, "sec": "WPA2", "chan": "1", "bssid": "11:22:33:44:55:66"},
    {"ssid": "Neighbor5G", "signal": -78, "sec": "WPA3", "chan": "149", "bssid": "22:33:44:55:66:77"},
    {"ssid": "FBI_Surveillance_Van", "signal": -90, "sec": "Open", "chan": "6", "bssid": "33:44:55:66:77:88"},
]


class WifiScanWorker(QThread):
    result = Signal(list, str)   # networks, source label
    error = Signal(str)
    done = Signal()

    def __init__(self):
        super().__init__()

    def run(self):
        nets, source, err = real_scan()
        if err:
            self.error.emit(err)
        else:
            self.result.emit(nets, source)
        self.done.emit()


class WifiAnalyzerWindow(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.worker = None
        self.setWindowTitle("WiFi Analyzer - Signal Depths")
        self.resize(760, 600)
        self.setStyleSheet(f"QMainWindow {{ background: {COLORS['bg_light']}; }}")

        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(10)

        layout.addWidget(make_header(
            "\U0001F4F6 WiFi Analyzer",
            "Scan real wireless networks (nmcli / iw)"
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
        if wifi_hardware():
            self._log("[*] Wi-Fi hardware detected - scanning on demand.")
        else:
            self._log("[!] No nmcli/iw or wireless adapter found - will show labeled demo data.")

    def _log(self, msg, color=None):
        if color is not None:
            self.output.setTextColor(color)
        self.output.append(msg)

    def _scan(self):
        self.output.clear()
        self.scan_btn.setEnabled(False)
        if not wifi_hardware():
            self.count_label.setText(str(len(SAMPLE_NETWORKS)))
            self._log("[!] DEMO DATA (no wireless hardware available):\n")
            self._render(SAMPLE_NETWORKS, "demo")
            self.scan_btn.setEnabled(True)
            return
        self._log("[*] Scanning (this can take several seconds)...")
        self.worker = WifiScanWorker()
        self.worker.result.connect(lambda nets, src: (self.count_label.setText(str(len(nets))), self._render(nets, src)))
        self.worker.error.connect(lambda e: self._log(f"[!] {e}"))
        self.worker.done.connect(lambda: self.scan_btn.setEnabled(True))
        self.worker.start()

    def _render(self, nets, source):
        if not nets:
            self._log("[*] No networks visible - check adapter state (rfkill/internet).")
            return
        self._log(f"[*] Source: {source}  -  {len(nets)} networks")
        self._log(f"{'SSID':<30}{'BSSID':<20}{'SIGNAL':<8}{'CH':<6}{'SEC'}")
        self._log("-" * 80)
        for n in nets:
            sig = n.get("signal")
            color = GREEN if sig is not None and sig >= -50 else YELLOW if sig is not None and sig >= -70 else RED
            self.output.setTextColor(color)
            sec = n.get("sec", "Open")
            sec_color = RED if "Open" in str(sec) else YELLOW if "WPA" in str(sec) else CYAN
            line = f"{n.get('ssid', '?')[:28]:<30}{n.get('bssid', '?'):<20}{str(sig):<8}{str(n.get('chan', '')):<6}"
            self._log(line, color=color)
            self._log(str(sec), color=sec_color)

        opens = [n for n in nets if "Open" in str(n.get("sec", ""))]
        if opens:
            self.output.setTextColor(RED)
            self._log(f"\n[\u26A0] {len(opens)} OPEN (unencrypted) network(s) detected - avoid sensitive traffic on these.")
        self.output.setTextColor(YELLOW)
        self._log("[*] Honeypot/rogue APs often mimic trusted names and use Open security to intercept traffic.")

    def closeEvent(self, event):
        super().closeEvent(event)


def run(parent=None):
    win = WifiAnalyzerWindow(parent)
    win.show()
    return win