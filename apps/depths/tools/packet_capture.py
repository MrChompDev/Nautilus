"""Packet Capture - The Depths

Real live packet capture of the machine's network interfaces when scapy is
available and the process has the required permissions; otherwise it degrades
to a simulated traffic feed so the analysis workflow still works (e.g. when
scapy is not installed or no root privileges are available).
"""

import os
import random
import sys
import threading

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

from PySide6.QtCore import QThread, Signal
from PySide6.QtWidgets import QHBoxLayout, QLabel, QMainWindow, QPushButton, QTextEdit, QVBoxLayout, QWidget

from apps.depths.tools._ui import BTN_STYLE, CYAN, GREEN, OUT_STYLE, YELLOW, hline, make_header
from core.theme import COLORS, FONTS

try:
    from scapy.all import ICMP, IP, TCP, UDP, sniff

    HAVE_SCAPY = True
except ImportError:
    HAVE_SCAPY = False
    ICMP = IP = TCP = UDP = None

SIM_INTERVAL = 0.7
SIM_PROTOS = ["TCP", "UDP", "ICMP", "DNS", "HTTP", "HTTPS", "SSH"]
SIM_PORTS = [21, 22, 53, 80, 443, 445, 8080, 3306, 8000, 9000]
SIM_FLAGS = ["SYN", "ACK", "PSH,ACK", "SYN,ACK", "FIN", "RST"]


def _sim_packet():
    """One synthetic packet line (fallback feed)."""
    src = f"192.168.1.{random.randint(1, 250)}"
    dst = f"192.168.1.{random.randint(1, 250)}"
    sport = random.choice(SIM_PORTS)
    dport = random.choice(SIM_PORTS)
    proto = random.choice(SIM_PROTOS)
    flags = random.choice(SIM_FLAGS) if proto == "TCP" else "-"
    size = random.randint(46, 1500)
    ttl = random.randint(32, 128)
    color = YELLOW if proto in ("HTTP", "HTTPS") else GREEN
    line = (f"    {src:<16} :{sport:<6} -> {dst:<16} :{dport:<6}"
            f"  {proto:<5} {flags:<8} size={size:<5} ttl={ttl}")
    return line, color


class CaptureWorker(QThread):
    """Pull packets off the wire (or a simulated feed) in the background."""

    packet_ready = Signal(str)
    log = Signal(str)
    finished = Signal()

    def __init__(self, real):
        super().__init__()
        self.real = real
        self._stop = threading.Event()
        self._count = 0

    def stop(self):
        self._stop.set()

    def run(self):
        if self.real and HAVE_SCAPY:
            try:
                self._sniff_real()
                self.log.emit("[*] Live capture ended")
                self.finished.emit()
                return
            except PermissionError:
                self.log.emit("[!] Live capture needs root privileges - falling back to simulated feed")
            except Exception as exc:
                self.log.emit(f"[!] Live capture failed ({exc}) - falling back to simulated feed")
        self._simulate()

    def _sniff_real(self):
        def _prn(pkt):
            self._handle_real(pkt)

        sniff(prn=_prn, store=False, stop_filter=lambda _p: self._stop.is_set())

    def _handle_real(self, pkt):
        try:
            if IP not in pkt:
                return
            src = pkt[IP].src
            dst = pkt[IP].dst
            ttl = pkt[IP].ttl
            size = len(pkt)
            proto = None
            sport, dport, flags = "-", "-", "-"
            if TCP in pkt:
                proto, sport, dport = "TCP", pkt[TCP].sport, pkt[TCP].dport
                flags = pkt[TCP].flags
            elif UDP in pkt:
                proto, sport, dport = "UDP", pkt[UDP].sport, pkt[UDP].dport
                if src.endswith(".53") or dst.endswith(".53"):
                    proto = "DNS"
            elif ICMP in pkt:
                proto = "ICMP"
            if proto is None:
                return
            color = YELLOW if proto in ("HTTP", "HTTPS", "DNS") else GREEN
            line = (f"    {src:<16} :{sport:<6} -> {dst:<16} :{dport:<6}"
                    f"  {proto:<5} {str(flags):<8} size={size:<5} ttl={ttl}")
            self._count += 1
            self.packet_ready.emit(f"{line}\x00{color}")
        except Exception:
            pass

    def _simulate(self):
        self.log.emit("[*] Simulated traffic feed")
        while not self._stop.is_set():
            line, color = _sim_packet()
            self._count += 1
            self.packet_ready.emit(f"{line}\x00{color}")
            self._stop.wait(SIM_INTERVAL)
        self.finished.emit()


class PacketCaptureWindow(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.worker = None
        self.captured = 0
        self.setWindowTitle("Packet Capture - The Depths")
        self.resize(720, 560)
        self.setStyleSheet(f"QMainWindow {{ background: {COLORS['bg_light']}; }}")

        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(10)

        layout.addWidget(make_header(
            "\U0001F4E6 Packet Capture",
            "See network traffic flowing by"
        ))
        layout.addWidget(hline())

        row = QHBoxLayout()
        self.toggle_btn = QPushButton("\u25B6 Capture")
        self.toggle_btn.setStyleSheet(BTN_STYLE)
        self.toggle_btn.clicked.connect(self.toggle)
        row.addWidget(self.toggle_btn)

        self.clear_btn = QPushButton("Clear")
        self.clear_btn.setStyleSheet(BTN_STYLE.replace(COLORS["teal"], COLORS["bg_dark"]).replace("#fff", COLORS["text"]))
        self.clear_btn.clicked.connect(self._clear)
        row.addWidget(self.clear_btn)

        self.mode_label = QLabel("")
        self.mode_label.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: {FONTS['size_sm']}px;")
        row.addWidget(self.mode_label)
        row.addStretch()

        lbl = QLabel("Packets:")
        lbl.setStyleSheet(f"color: {COLORS['text']}; font-size: {FONTS['size_md']}px;")
        row.addWidget(lbl)
        self.count_label = QLabel("0")
        self.count_label.setStyleSheet(f"color: {COLORS['teal_light']}; font-weight: bold; font-size: {FONTS['size_md']}px;")
        row.addWidget(self.count_label)
        layout.addLayout(row)

        self.output = QTextEdit()
        self.output.setReadOnly(True)
        self.output.setStyleSheet(OUT_STYLE)
        layout.addWidget(self.output, 1)

        mode = "scapy (real capture)" if HAVE_SCAPY else "simulated feed"
        self.mode_label.setText(f"backend: {mode}")
        self.mode = HAVE_SCAPY
        self._log("[*] Packet Capture ready")
        if HAVE_SCAPY:
            self._log("[*] Backend: scapy. Live capture needs root privileges; it will degrade gracefully otherwise.") 
        else:
            self._log("[*] Backend: scapy not available - using simulated traffic feed")
            self._log("[*] Install scapy and run with privileges for real capture")

    def _log(self, msg):
        self.output.append(msg)

    def toggle(self):
        if self.worker is None:
            self.start()
        else:
            self.stop()

    def start(self):
        self.captured = 0
        self.count_label.setText("0")
        self.toggle_btn.setText("\u23F9 Stop")
        self.mode_label.setText("capturing...")
        self._log("\n[*] Capturing...")
        self.worker = CaptureWorker(self.mode)
        self.worker.packet_ready.connect(self._on_packet)
        self.worker.log.connect(self._on_log)
        self.worker.finished.connect(self._on_done)
        self.worker.start()

    def stop(self):
        if self.worker is not None:
            self.worker.stop()

    def _on_packet(self, payload):
        line, color = payload.split("\x00")
        self.captured += 1
        self.output.setTextColor(color)
        self.output.append(line)
        self.count_label.setText(str(self.captured))

    def _on_log(self, msg):
        self.output.setTextColor(CYAN)
        self.output.append(msg)

    def _on_done(self):
        self.toggle_btn.setText("\u25B6 Capture")
        self.mode_label.setText(f"backend: {'scapy' if self.mode else 'simulated feed'}")
        self.count_label.setText(str(self.captured))
        self._log(f"[*] Capture stopped ({self.captured} packets)")
        self.worker = None

    def _clear(self):
        self.captured = 0
        self.count_label.setText("0")
        self.output.clear()

    def closeEvent(self, event):
        if self.worker is not None:
            self.worker.stop()
        super().closeEvent(event)


def run(parent=None):
    win = PacketCaptureWindow(parent)
    win.show()
    return win
