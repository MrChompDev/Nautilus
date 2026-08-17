#!/usr/bin/env python3
"""
Current — Nautilus System Telemetry & Process Monitor
Real-time CPU, RAM, thermal, and process tree monitoring with interactive kill.
"""

import os
import signal
import sys
import time
from collections import namedtuple

# Ensure project root is on path for theme access
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, PROJECT_ROOT)

from core.qt_env import setup_qt_environment

setup_qt_environment()

from PySide6.QtCore import QThread
from PySide6.QtCore import Signal as QSignal
from PySide6.QtGui import QColor, QFont, QPalette
from PySide6.QtWidgets import (
    QAbstractItemView,
    QApplication,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

try:
    from core.logger import get_logger  # noqa: F401
    from core.theme import (
        COLORS,
        FONTS,
        SPACING,
        create_nautilus_palette,
        get_global_stylesheet,
        glass_bg,
        glass_bg_dark,
        glass_edge,
        glass_sheen,
    )
except ImportError:
    # Fallback for standalone execution
    COLORS = {
        "abyss_navy": "#081626", "slate_navy": "#0E2238", "deep_navy": "#050D14",
        "void_black": "#02060A", "seafoam": "#00F2C2", "seafoam_dim": "#00C9A0",
        "seafoam_deep": "#004D40", "coral": "#FF7F50", "amber": "#FFA502",
        "emerald": "#00C853", "hd_white": "#EEF4F8", "text_secondary": "#8BA4B8",
        "text_muted": "#506070", "border": "#152D44", "surface_hover": "#132A40",
        "surface_selected": "#1A3352", "scrollbar_bg": "#050D14", "scrollbar_handle": "#1A3352",
    }
    FONTS = {"mono": "JetBrains Mono", "ui": "Segoe UI", "size_xs": 10, "size_sm": 11, "size_md": 12, "size_lg": 13, "size_xl": 14}
    SPACING = {"xs": 2, "sm": 4, "md": 8, "lg": 12, "xl": 16, "xxl": 24}

    def get_global_stylesheet(): return ""
    def create_nautilus_palette(): return QPalette()
    def hex_to_rgba(h, a=255):
        v = h.lstrip("#")
        return f"rgba({int(v[0:2],16)},{int(v[2:4],16)},{int(v[4:6],16)},{a})"
    def glass_bg(a=180): return hex_to_rgba(COLORS["slate_navy"], a)
    def glass_bg_dark(a=140): return hex_to_rgba(COLORS["deep_navy"], a)
    def glass_edge(a=48): return hex_to_rgba(COLORS["seafoam"], a)
    def glass_sheen(): return "rgba(238, 244, 248, 26)"


# ═══════════════════════════════════════════════════════════════
#  SYSTEM METRICS COLLECTOR (runs in background thread)
# ═══════════════════════════════════════════════════════════════

ProcInfo = namedtuple("ProcInfo", ["pid", "name", "cpu_percent", "memory_mb", "status"])

class SystemCollector(QThread):
    """Background thread for collecting system metrics without blocking UI."""
    metrics_ready = QSignal(dict)
    processes_ready = QSignal(object)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._running = True
        self._interval = 1.0
        self._psutil_available = False

        try:
            import psutil
            self._psutil = psutil
            self._psutil_available = True
        except ImportError:
            self._psutil_available = False

    def run(self):
        while self._running:
            if self._psutil_available:
                self._collect_real()
            else:
                self._collect_fallback()
            time.sleep(self._interval)

    def _collect_real(self):
        psutil = self._psutil
        try:
            # CPU
            per_cpu = psutil.cpu_percent(interval=0.1, percpu=True)
            cpu_percent = sum(per_cpu) / len(per_cpu) if per_cpu else 0.0
            cpu_freq = psutil.cpu_freq()
            cpu_count = psutil.cpu_count()

            # Memory
            mem = psutil.virtual_memory()

            # Swap
            swap = psutil.swap_memory()

            # Disk
            disk = psutil.disk_usage("/")

            # Thermal sensors
            temps = {}
            try:
                sensors = psutil.sensors_temperatures()
                for name, entries in sensors.items():
                    if entries:
                        temps[name] = entries[0].current
            except Exception:
                temps["CPU"] = 0.0

            # Battery
            battery = None
            try:
                bat = psutil.sensors_battery()
                if bat:
                    battery = {"percent": bat.percent, "charging": bat.power_plugged}
            except Exception:
                pass

            # Network
            net = psutil.net_io_counters()
            net_sent = net.bytes_sent
            net_recv = net.bytes_recv

            # Uptime
            boot_time = psutil.boot_time()
            uptime = time.time() - boot_time

            metrics = {
                "cpu_percent": cpu_percent,
                "cpu_freq_current": cpu_freq.current if cpu_freq else 0,
                "cpu_freq_max": cpu_freq.max if cpu_freq else 0,
                "cpu_count": cpu_count,
                "per_cpu": per_cpu,
                "mem_total": mem.total,
                "mem_available": mem.available,
                "mem_used": mem.used,
                "mem_percent": mem.percent,
                "swap_total": swap.total,
                "swap_used": swap.used,
                "swap_percent": swap.percent,
                "disk_total": disk.total,
                "disk_used": disk.used,
                "disk_free": disk.free,
                "disk_percent": disk.percent,
                "temperatures": temps,
                "battery": battery,
                "net_sent": net_sent,
                "net_recv": net_recv,
                "uptime": uptime,
                "boot_time": boot_time,
            }
            self.metrics_ready.emit(metrics)

            # Processes
            procs = []
            for proc in psutil.process_iter(["pid", "name", "cpu_percent", "memory_info", "status"]):
                try:
                    info = proc.info
                    mem_mb = info["memory_info"].rss / (1024 * 1024)
                    procs.append(ProcInfo(
                        pid=info["pid"],
                        name=info["name"] or "",
                        cpu_percent=info["cpu_percent"] or 0.0,
                        memory_mb=round(mem_mb, 1),
                        status=info["status"],
                    ))
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass

            procs.sort(key=lambda p: p.memory_mb, reverse=True)
            self.processes_ready.emit(procs[:100])

        except Exception as e:
            self.metrics_ready.emit({"error": str(e)})

    def _collect_fallback(self):
        """Fallback metrics when psutil is not available."""
        try:
            metrics = {
                "cpu_percent": 0,
                "cpu_count": os.cpu_count() or 1,
                "mem_total": 0,
                "mem_used": 0,
                "mem_percent": 0,
                "disk_total": 0,
                "disk_used": 0,
                "disk_percent": 0,
                "temperatures": {"CPU": 0.0},
                "uptime": 0,
                "per_cpu": [],
                "cpu_freq_current": 0,
                "cpu_freq_max": 0,
                "swap_total": 0, "swap_used": 0, "swap_percent": 0,
                "net_sent": 0, "net_recv": 0,
            }
            self.metrics_ready.emit(metrics)
            self.processes_ready.emit([])
        except Exception:
            pass

    def stop(self):
        self._running = False


# ═══════════════════════════════════════════════════════════════
#  METRIC CARD WIDGET
# ═══════════════════════════════════════════════════════════════

class MetricCard(QFrame):
    """A single metric display card with label, value, and progress bar."""

    def __init__(self, title: str, unit: str = "", parent=None):
        super().__init__(parent)
        self.setStyleSheet(f"""
            MetricCard {{
                background: {glass_bg(170)};
                border: 1px solid {glass_edge()};
                border-top: 1px solid {glass_sheen()};
                border-radius: 18px;
            }}
        """)
        self.setMinimumHeight(90)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(SPACING["md"], SPACING["sm"], SPACING["md"], SPACING["sm"])
        layout.setSpacing(2)

        self._title_label = QLabel(title.upper())
        self._title_label.setStyleSheet(f"""
            color: {COLORS['text_muted']};
            font-family: "{FONTS['mono']}";
            font-size: {FONTS['size_xs']}px;
            letter-spacing: 1px;
            background: transparent;
        """)
        layout.addWidget(self._title_label)

        self._value_label = QLabel("—")
        self._value_label.setStyleSheet(f"""
            color: {COLORS['seafoam']};
            font-family: "{FONTS['mono']}";
            font-size: {FONTS['size_xl']}px;
            font-weight: bold;
            background: transparent;
        """)
        layout.addWidget(self._value_label)

        self._unit = unit
        self._unit_label = QLabel(unit)
        self._unit_label.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: {FONTS['size_xs']}px; background: transparent;")
        layout.addWidget(self._unit_label)

        self._progress = QProgressBar()
        self._progress.setFixedHeight(4)
        self._progress.setTextVisible(False)
        self._progress.setStyleSheet(f"""
            QProgressBar {{ background: {glass_bg_dark(100)}; border: 1px solid {glass_edge(50)}; border-radius: 2px; }}
            QProgressBar::chunk {{ background: qlineargradient(x1:0,y1:0,x2:1,y2:0, stop:0 {COLORS['seafoam_deep']}, stop:1 {COLORS['seafoam']}); border-radius: 2px; }}
        """)
        layout.addWidget(self._progress)

    def update_value(self, value_str: str, percent: float = 0):
        self._value_label.setText(value_str)
        self._progress.setValue(int(min(percent, 100)))


# ═══════════════════════════════════════════════════════════════
#  PROCESS TREE WIDGET
# ═══════════════════════════════════════════════════════════════

class ProcessTree(QWidget):
    """Interactive tree view of running processes with kill capability."""

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(SPACING["sm"])

        # Toolbar
        toolbar = QHBoxLayout()

        self._search_label = QLabel("PROCESSES")
        self._search_label.setStyleSheet(f"""
            color: {COLORS['seafoam']}; font-family: "{FONTS['mono']}";
            font-size: {FONTS['size_sm']}px; font-weight: bold; letter-spacing: 1px;
        """)
        toolbar.addWidget(self._search_label)
        toolbar.addStretch()

        self._kill_btn = QPushButton("⏻  KILL")
        self._kill_btn.setStyleSheet(f"""
            QPushButton {{
                background: rgba(255, 127, 80, 140); color: {COLORS['coral']};
                border: 1px solid rgba(255, 127, 80, 100);
                border-radius: 8px;
                font-family: "{FONTS['mono']}"; font-size: {FONTS['size_xs']}px;
                padding: 4px 12px; font-weight: bold;
            }}
            QPushButton:hover {{ background: rgba(255, 127, 80, 200); }}
            QPushButton:disabled {{ background: rgba(255, 127, 80, 60); color: {COLORS['text_muted']}; border-color: {COLORS['border_dim']}; }}
        """)
        self._kill_btn.clicked.connect(self._kill_selected)
        self._kill_btn.setEnabled(False)
        toolbar.addWidget(self._kill_btn)

        self._refresh_btn = QPushButton("↻")
        self._refresh_btn.setStyleSheet(f"""
            QPushButton {{
                background: {glass_bg(120)}; color: {COLORS['text_secondary']};
                border: 1px solid {glass_edge(50)};
                border-radius: 8px;
                font-family: "{FONTS['mono']}"; font-size: {FONTS['size_sm']}px;
                padding: 4px 10px;
            }}
            QPushButton:hover {{ color: {COLORS['seafoam']}; background: {glass_bg(180)}; border-color: {glass_edge(80)}; }}
        """)
        toolbar.addWidget(self._refresh_btn)

        layout.addLayout(toolbar)

        # Tree
        self._tree = QTreeWidget()
        self._tree.setHeaderLabels(["PID", "Name", "CPU %", "Memory", "Status"])
        self._tree.setColumnWidth(0, 70)
        self._tree.setColumnWidth(1, 200)
        self._tree.setColumnWidth(2, 70)
        self._tree.setColumnWidth(3, 90)
        self._tree.setColumnWidth(4, 80)
        self._tree.setAlternatingRowColors(False)
        self._tree.setRootIsDecorated(False)
        self._tree.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self._tree.setStyleSheet(f"""
            QTreeWidget {{
                background: {glass_bg(100)};
                color: {COLORS['hd_white']};
                border: 1px solid {glass_edge()};
                border-radius: 12px;
                font-family: "{FONTS['mono']}";
                font-size: {FONTS['size_sm']}px;
            }}
            QTreeWidget::item {{ padding: 3px 6px; border: none; border-radius: 0px; }}
            QTreeWidget::item:selected {{ background: rgba(30, 58, 95, 180); color: {COLORS['seafoam']}; }}
            QHeaderView::section {{
                background: {glass_bg_dark(180)};
                color: {COLORS['seafoam']};
                font-family: "{FONTS['mono']}";
                font-size: {FONTS['size_xs']}px;
                padding: 4px 8px;
                border: none;
                border-right: 1px solid {COLORS['border_dim']};
                border-bottom: 2px solid {glass_edge()};
            }}
        """)
        self._tree.itemSelectionChanged.connect(self._on_selection_changed)
        layout.addWidget(self._tree)

        self._processes = []

    def update_processes(self, processes: list):
        self._processes = processes
        self._tree.clear()
        for proc in processes:
            item = QTreeWidgetItem([
                str(proc.pid),
                proc.name,
                f"{proc.cpu_percent:.1f}",
                f"{proc.memory_mb:.1f} MB",
                proc.status,
            ])

            # Color memory-heavy processes
            if proc.memory_mb > 500:
                for col in range(5):
                    item.setForeground(col, QColor(COLORS["coral"]))
            elif proc.memory_mb > 200:
                for col in range(5):
                    item.setForeground(col, QColor(COLORS["amber"]))

            self._tree.addTopLevelItem(item)

    def _on_selection_changed(self):
        self._kill_btn.setEnabled(len(self._tree.selectedItems()) > 0)

    def _kill_selected(self):
        items = self._tree.selectedItems()
        if not items:
            return
        item = items[0]
        pid = int(item.text(0))
        name = item.text(1)

        reply = QMessageBox.question(
            self, "Kill Process",
            f"Send SIGKILL to:\n\n{name} (PID {pid})?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if reply == QMessageBox.Yes:
            try:
                if sys.platform == "win32":
                    import subprocess as sp
                    sp.run(["taskkill", "/F", "/PID", str(pid)], capture_output=True)
                else:
                    os.kill(pid, signal.SIGKILL)
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to kill process:\n{e}")

    def set_refresh_callback(self, callback):
        self._refresh_btn.clicked.connect(callback)


# ═══════════════════════════════════════════════════════════════
#  MAIN WINDOW
# ═══════════════════════════════════════════════════════════════

class CurrentWindow(QMainWindow):
    """Current — Nautilus System Telemetry Monitor."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Current — System Telemetry")
        self.setMinimumSize(900, 600)
        self.resize(1100, 700)

        self._prev_net = {"sent": 0, "recv": 0, "time": time.time()}

        self._setup_ui()
        self._setup_collector()

    def _setup_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        central.setStyleSheet(f"QWidget {{ background: {glass_bg(180)}; }}")
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(SPACING["md"], SPACING["md"], SPACING["md"], SPACING["md"])
        main_layout.setSpacing(SPACING["md"])

        # Title
        title = QLabel("📊  CURRENT  //  System Telemetry")
        title.setStyleSheet(f"""
            color: {COLORS['seafoam']}; font-family: "{FONTS['mono']}";
            font-size: {FONTS['size_lg']}px; font-weight: bold; letter-spacing: 2px;
            padding-bottom: 4px; border-bottom: 1px solid {glass_edge()};
            background: transparent;
        """)
        main_layout.addWidget(title)

        # Metric cards grid
        cards_layout = QGridLayout()
        cards_layout.setSpacing(SPACING["sm"])

        self._cpu_card = MetricCard("CPU Usage", "%")
        self._ram_card = MetricCard("RAM", "%")
        self._temp_card = MetricCard("Temperature", "°C")
        self._disk_card = MetricCard("Disk", "%")
        self._swap_card = MetricCard("Swap", "%")
        self._uptime_card = MetricCard("Uptime", "")

        cards_layout.addWidget(self._cpu_card, 0, 0)
        cards_layout.addWidget(self._ram_card, 0, 1)
        cards_layout.addWidget(self._temp_card, 0, 2)
        cards_layout.addWidget(self._disk_card, 0, 3)
        cards_layout.addWidget(self._swap_card, 1, 0)
        cards_layout.addWidget(self._uptime_card, 1, 1)

        # CPU frequency card
        self._freq_card = MetricCard("CPU Freq", "MHz")
        cards_layout.addWidget(self._freq_card, 1, 2)

        # Network card
        self._net_card = MetricCard("Network", "")
        cards_layout.addWidget(self._net_card, 1, 3)

        main_layout.addLayout(cards_layout)

        # Process tree
        self._process_tree = ProcessTree()
        main_layout.addWidget(self._process_tree, 1)

        # Status bar
        status = QLabel("Ready — Refresh interval: 1s")
        status.setStyleSheet(f"""
            color: {COLORS['text_muted']}; font-family: "{FONTS['mono']}";
            font-size: {FONTS['size_xs']}px; padding-top: 4px;
            border-top: 1px solid {COLORS['border']};
        """)
        main_layout.addWidget(status)

    def _setup_collector(self):
        self._collector = SystemCollector()
        self._collector.metrics_ready.connect(self._on_metrics)
        self._collector.processes_ready.connect(self._process_tree.update_processes)
        self._collector.start()

        self._process_tree.set_refresh_callback(lambda: None)  # Auto-refreshes

    def _on_metrics(self, metrics: dict):
        if "error" in metrics:
            return

        # CPU
        cpu = metrics.get("cpu_percent", 0)
        freq = metrics.get("cpu_freq_current", 0)
        self._cpu_card.update_value(f"{cpu:.1f} %", cpu)
        self._freq_card.update_value(f"{freq:.0f} MHz", min(freq / 4000 * 100, 100) if metrics.get("cpu_freq_max", 0) > 0 else 0)

        # RAM
        mem_pct = metrics.get("mem_percent", 0)
        mem_used_gb = metrics.get("mem_used", 0) / (1024**3)
        mem_total_gb = metrics.get("mem_total", 0) / (1024**3)
        self._ram_card.update_value(f"{mem_used_gb:.1f} / {mem_total_gb:.1f} GB", mem_pct)

        # Temp
        temps = metrics.get("temperatures", {})
        max_temp = max(temps.values()) if temps else 0
        self._temp_card.update_value(f"{max_temp:.0f} °C", min(max_temp / 100 * 100, 100))

        # Disk
        disk_pct = metrics.get("disk_percent", 0)
        self._disk_card.update_value(f"{disk_pct:.1f} %", disk_pct)

        # Swap
        swap_pct = metrics.get("swap_percent", 0)
        self._swap_card.update_value(f"{swap_pct:.1f} %", swap_pct)

        # Uptime
        uptime_s = metrics.get("uptime", 0)
        h, m = divmod(int(uptime_s), 3600)
        m, s = divmod(m, 60)
        d, h = divmod(h, 24)
        if d > 0:
            uptime_str = f"{d}d {h}h {m}m"
        else:
            uptime_str = f"{h}h {m}m {s}s"
        self._uptime_card.update_value(uptime_str, 0)

        # Network card
        sent = metrics.get("net_sent", 0)
        recv = metrics.get("net_recv", 0)
        now = time.time()
        elapsed = now - self._prev_net["time"]
        if elapsed > 0:
            sent_rate = (sent - self._prev_net["sent"]) / elapsed
            recv_rate = (recv - self._prev_net["recv"]) / elapsed
            self._net_card.update_value(f"↓ {self._fmt_bytes(recv_rate)}/s  ↑ {self._fmt_bytes(sent_rate)}/s", 0)
        self._prev_net = {"sent": sent, "recv": recv, "time": now}

    @staticmethod
    def _fmt_bytes(b: float) -> str:
        for unit in ["B", "KB", "MB", "GB"]:
            if abs(b) < 1024.0:
                return f"{b:.1f} {unit}"
            b /= 1024.0
        return f"{b:.1f} TB"

    def closeEvent(self, event):
        self._collector.stop()
        self._collector.wait(2000)
        event.accept()


# ═══════════════════════════════════════════════════════════════

def main():
    log = None
    try:
        from core.logger import get_logger
        log = get_logger("APP")
        log.info("Current Telemetry starting")
    except Exception:
        pass

    app = QApplication(sys.argv)
    app.setApplicationName("Current")
    app.setOrganizationName("Nautilus")

    try:
        from core.icons import get_logo
        app.setWindowIcon(get_logo("current"))
    except Exception:
        pass

    app.setPalette(create_nautilus_palette())
    app.setStyleSheet(get_global_stylesheet())

    font = QFont()
    font.setFamilies([FONTS["ui"], FONTS["mono"], "Consolas"])
    font.setPointSize(FONTS["size_md"])
    app.setFont(font)

    window = CurrentWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
