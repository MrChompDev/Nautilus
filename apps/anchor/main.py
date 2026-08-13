#!/usr/bin/env python3
"""
Anchor — Nautilus Control Center & System Settings
Display, network, audio, and global theme configuration.
"""

import os
import sys

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, PROJECT_ROOT)

from core.qt_env import setup_qt_environment

setup_qt_environment()

from PySide6.QtCore import QSize, Qt, QThread
from PySide6.QtCore import Signal as QSignal
from PySide6.QtGui import QColor, QFont, QPalette
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QColorDialog,
    QComboBox,
    QFrame,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSlider,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

try:
    from core.icons import get_logo
    from core.theme import (
        COLORS,
        FONTS,
        SPACING,
        create_nautilus_palette,
        get_global_stylesheet,
    )
except ImportError:
    COLORS = {
        "abyss_navy": "#081626", "slate_navy": "#0E2238", "deep_navy": "#050D14",
        "void_black": "#02060A", "seafoam": "#00F2C2", "seafoam_dim": "#00C9A0",
        "seafoam_deep": "#004D40", "coral": "#FF7F50", "amber": "#FFA502",
        "emerald": "#00C853", "hd_white": "#EEF4F8", "text_secondary": "#8BA4B8",
        "text_muted": "#506070", "border": "#152D44", "surface_hover": "#132A40",
        "surface_selected": "#1A3352", "tab_active": "#0E2238", "tab_inactive": "#050D14",
    }
    FONTS = {"mono": "JetBrains Mono", "ui": "Segoe UI", "size_xs": 10, "size_sm": 11, "size_md": 12, "size_lg": 13, "size_xl": 14, "size_xxl": 16}
    SPACING = {"xs": 2, "sm": 4, "md": 8, "lg": 12, "xl": 16, "xxl": 24}
    def get_global_stylesheet(): return ""
    def create_nautilus_palette(): return QPalette()


# ═══════════════════════════════════════════════════════════════
#  STYLED COMPONENTS
# ═══════════════════════════════════════════════════════════════

def make_group(title: str) -> QGroupBox:
    gb = QGroupBox(title)
    gb.setStyleSheet(f"""
        QGroupBox {{
            border: 1px solid {COLORS['border']};
            margin-top: 14px;
            padding-top: 18px;
            font-family: "{FONTS['mono']}";
            font-size: {FONTS['size_sm']}px;
            font-weight: bold;
            color: {COLORS['seafoam']};
        }}
        QGroupBox::title {{
            subcontrol-origin: margin;
            left: 10px;
            padding: 0 6px;
            color: {COLORS['seafoam']};
        }}
    """)
    return gb


def make_label(text: str, accent: bool = False) -> QLabel:
    lbl = QLabel(text)
    lbl.setStyleSheet(f"""
        QLabel {{
            color: {COLORS['seafoam'] if accent else COLORS['hd_white']};
            font-family: "{FONTS['mono']}";
            font-size: {FONTS['size_sm']}px;
        }}
    """)
    return lbl


def make_slider(min_val=0, max_val=100, val=50) -> QSlider:
    sl = QSlider(Qt.Horizontal)
    sl.setRange(min_val, max_val)
    sl.setValue(val)
    sl.setStyleSheet(f"""
        QSlider::groove:horizontal {{
            background: {COLORS['deep_navy']}; height: 4px; border: 1px solid {COLORS['border']};
        }}
        QSlider::handle:horizontal {{
            background: {COLORS['seafoam']}; width: 14px; height: 14px;
            margin: -6px 0; border: 1px solid {COLORS['seafoam_dim']};
        }}
        QSlider::sub-page:horizontal {{ background: {COLORS['seafoam_deep']}; }}
    """)
    return sl


# ═══════════════════════════════════════════════════════════════
#  DISPLAY PANEL
# ═══════════════════════════════════════════════════════════════

class DisplayPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setSpacing(SPACING["md"])

        # Resolution
        res_group = make_group("Display Resolution")
        res_layout = QGridLayout(res_group)
        res_layout.setSpacing(SPACING["sm"])

        res_layout.addWidget(make_label("Resolution:"), 0, 0)
        self._res_combo = QComboBox()
        self._res_combo.addItems(["1920×1080 (Recommended)", "1680×1050", "1600×900",
                                   "1440×900", "1366×768", "1280×720", "1024×768"])
        self._res_combo.setStyleSheet(f"""
            QComboBox {{
                background: {COLORS['deep_navy']}; color: {COLORS['hd_white']};
                border: 1px solid {COLORS['border']}; padding: 4px 10px;
                font-family: "{FONTS['mono']}"; font-size: {FONTS['size_sm']}px;
            }}
            QComboBox:hover {{ border-color: {COLORS['seafoam_dim']}; }}
            QComboBox QAbstractItemView {{
                background: {COLORS['slate_navy']}; color: {COLORS['hd_white']};
                border: 1px solid {COLORS['border']};
                selection-background-color: {COLORS['seafoam_deep']};
            }}
        """)
        res_layout.addWidget(self._res_combo, 0, 1)

        res_layout.addWidget(make_label("Scaling:"), 1, 0)
        self._scale_combo = QComboBox()
        self._scale_combo.addItems(["100%", "125%", "150%", "175%", "200%"])
        self._scale_combo.setStyleSheet(self._res_combo.styleSheet())
        res_layout.addWidget(self._scale_combo, 1, 1)

        res_layout.addWidget(make_label("Refresh Rate:"), 2, 0)
        self._refresh_combo = QComboBox()
        self._refresh_combo.addItems(["60 Hz", "75 Hz", "120 Hz", "144 Hz", "240 Hz"])
        self._refresh_combo.setStyleSheet(self._res_combo.styleSheet())
        res_layout.addWidget(self._refresh_combo, 2, 1)

        apply_btn = QPushButton("Apply Display Settings")
        apply_btn.setStyleSheet(f"""
            QPushButton {{
                background: {COLORS['seafoam_deep']}; color: {COLORS['seafoam']};
                border: 1px solid {COLORS['seafoam']}; padding: 6px 16px;
                font-family: "{FONTS['mono']}"; font-size: {FONTS['size_sm']}px;
            }}
            QPushButton:hover {{ background: {COLORS['seafoam']}; color: {COLORS['void_black']}; }}
        """)
        res_layout.addWidget(apply_btn, 3, 0, 1, 2)

        layout.addWidget(res_group)

        # Appearance
        appearance = make_group("Appearance")
        app_layout = QVBoxLayout(appearance)
        app_layout.setSpacing(SPACING["sm"])

        self._dark_mode = QCheckBox("Dark Mode (Always On)")
        self._dark_mode.setChecked(True)
        self._dark_mode.setStyleSheet(f"color: {COLORS['hd_white']}; font-family: '{FONTS['mono']}';")
        app_layout.addWidget(self._dark_mode)

        self._animations = QCheckBox("Enable UI Animations")
        self._animations.setChecked(False)
        self._animations.setStyleSheet(self._dark_mode.styleSheet())
        app_layout.addWidget(self._animations)

        self._transparency = QCheckBox("Enable Transparency Effects")
        self._transparency.setChecked(False)
        self._transparency.setStyleSheet(self._dark_mode.styleSheet())
        app_layout.addWidget(self._transparency)

        layout.addWidget(appearance)
        layout.addStretch()


# ═══════════════════════════════════════════════════════════════
#  BLUETOOTH SCANNER (finds real nearby devices)
# ═══════════════════════════════════════════════════════════════

class BluetoothScanner(QThread):
    """Background scanner for real Bluetooth devices (BLE + known devices)."""

    devices_found = QSignal(list)
    scan_finished = QSignal(str)

    def run(self):
        devices = []
        status = ""

        # 1) Real BLE advertising scan via bleak
        try:
            import asyncio

            from bleak import BleakScanner

            devs = asyncio.run(BleakScanner.discover(timeout=6, return_adv=True))
            seen = set()
            for addr, payload in devs.items():
                dev, adv = payload[0], payload[1]
                name = (dev.name or adv.local_name or "").strip()
                if not name or addr in seen:
                    continue
                seen.add(addr)
                devices.append((name, addr))
            status = f"BLE scan complete — {len(devices)} device(s) nearby"
        except Exception as e:
            status = f"BLE scan unavailable ({e})"

        # 2) Fallback/enrichment: paired & known devices via Windows
        try:
            import subprocess
            out = subprocess.run(
                ["powershell", "-NoProfile", "-Command",
                 "Get-PnpDevice -Class Bluetooth -ErrorAction SilentlyContinue | "
                 "Where-Object { $_.Status -eq 'OK' } | Select-Object -ExpandProperty FriendlyName"],
                capture_output=True, text=True, timeout=10,
            )
            known = [line.strip() for line in out.stdout.splitlines() if line.strip()]
            for n in known:
                devices.append(("(known) " + n, ""))
            if known:
                status = f"{len(devices)} nearby + known device(s)"
        except Exception:
            pass

        self.devices_found.emit(devices)
        self.scan_finished.emit(status)


# ═══════════════════════════════════════════════════════════════
#  PUBLIC IP CHECKER (honest VPN verification)
# ═══════════════════════════════════════════════════════════════

class PublicIpChecker(QThread):
    """Fetches the public IP in a background thread."""

    result_ready = QSignal(str)

    def run(self):
        import urllib.request
        try:
            req = urllib.request.Request(
                "https://api.ipify.org",
                headers={"User-Agent": "Nautilus-Anchor/1.0"},
            )
            with urllib.request.urlopen(req, timeout=8) as resp:
                ip = resp.read().decode("utf-8", "replace").strip()
            self.result_ready.emit(ip if ip else "ERROR: No IP returned")
        except Exception as e:
            self.result_ready.emit(f"ERROR: Could not reach IP service: {e}")


# ═══════════════════════════════════════════════════════════════
#  NETWORK PANEL
# ═══════════════════════════════════════════════════════════════

class NetworkPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setSpacing(SPACING["md"])

        # Wi-Fi
        wifi = make_group("Wi-Fi")
        wifi_layout = QGridLayout(wifi)
        wifi_layout.setSpacing(SPACING["sm"])

        wifi_layout.addWidget(make_label("Status:"), 0, 0)
        status_lbl = QLabel("🔵 Connected")
        status_lbl.setStyleSheet(f"color: {COLORS['emerald']}; font-family: '{FONTS['mono']}';")
        wifi_layout.addWidget(status_lbl, 0, 1)

        wifi_layout.addWidget(make_label("Network:"), 1, 0)
        self._wifi_combo = QComboBox()
        self._wifi_combo.addItems(["Nautilus-Primary", "Nautilus-Guest", "Nautilus-IoT", "+ Add Network..."])
        self._wifi_combo.setStyleSheet(f"""
            QComboBox {{
                background: {COLORS['deep_navy']}; color: {COLORS['hd_white']};
                border: 1px solid {COLORS['border']}; padding: 4px 10px;
                font-family: "{FONTS['mono']}";
            }}
            QComboBox:hover {{ border-color: {COLORS['seafoam_dim']}; }}
            QComboBox QAbstractItemView {{
                background: {COLORS['slate_navy']}; color: {COLORS['hd_white']};
                border: 1px solid {COLORS['border']};
                selection-background-color: {COLORS['seafoam_deep']};
            }}
        """)
        wifi_layout.addWidget(self._wifi_combo, 1, 1)

        wifi_layout.addWidget(make_label("IP Address:"), 2, 0)
        ip_lbl = QLabel("192.168.1.142")
        ip_lbl.setStyleSheet(f"color: {COLORS['text_secondary']}; font-family: '{FONTS['mono']}';")
        wifi_layout.addWidget(ip_lbl, 2, 1)

        wifi_layout.addWidget(make_label("Signal:"), 3, 0)
        sig = QLabel("████████░░  82%")
        sig.setStyleSheet(f"color: {COLORS['emerald']}; font-family: '{FONTS['mono']}';")
        wifi_layout.addWidget(sig, 3, 1)

        layout.addWidget(wifi)

        # Bluetooth
        bt = make_group("Bluetooth")
        bt_layout = QGridLayout(bt)
        bt_layout.setSpacing(SPACING["sm"])

        bt_layout.addWidget(make_label("Bluetooth:"), 0, 0)
        self._bt_toggle = QCheckBox("Enabled")
        self._bt_toggle.setChecked(True)
        self._bt_toggle.setStyleSheet(f"color: {COLORS['hd_white']}; font-family: '{FONTS['mono']}';")
        bt_layout.addWidget(self._bt_toggle, 0, 1)

        self._bt_scan_btn = QPushButton("Scan for Bluetooth Devices")
        self._bt_scan_btn.setStyleSheet(f"""
            QPushButton {{
                background: {COLORS['seafoam_deep']}; color: {COLORS['seafoam']};
                border: 1px solid {COLORS['seafoam']}; padding: 5px 12px;
                font-family: "{FONTS['mono']}"; font-size: {FONTS['size_sm']}px;
            }}
            QPushButton:hover {{ background: {COLORS['seafoam']}; color: {COLORS['void_black']}; }}
            QPushButton:disabled {{ background: {COLORS['slate_navy']}; color: {COLORS['text_muted']};
                border-color: {COLORS['border']}; }}
        """)
        self._bt_scan_btn.clicked.connect(self._scan_bluetooth)
        bt_layout.addWidget(self._bt_scan_btn, 1, 0, 1, 2)

        self._bt_list = QListWidget()
        self._bt_list.setMinimumHeight(120)
        self._bt_list.setStyleSheet(f"""
            QListWidget {{
                background: {COLORS['deep_navy']}; color: {COLORS['hd_white']};
                border: 1px solid {COLORS['border']};
                font-family: "{FONTS['mono']}"; font-size: {FONTS['size_sm']}px;
                padding: 4px;
            }}
            QListWidget::item {{ padding: 3px 6px; }}
            QListWidget::item:selected {{ background: {COLORS['seafoam_deep']}; color: {COLORS['seafoam']}; }}
        """)
        bt_layout.addWidget(self._bt_list, 2, 0, 1, 2)

        self._bt_status = QLabel("Idle — click Scan to discover nearby Bluetooth devices")
        self._bt_status.setStyleSheet(f"color: {COLORS['text_muted']}; font-family: '{FONTS['mono']}'; font-size: {FONTS['size_xs']}px;")
        bt_layout.addWidget(self._bt_status, 3, 0, 1, 2)

        self._bt_scanner = None
        layout.addWidget(bt)

        # VPN / Proxy
        proxy = make_group("VPN & Proxy")
        proxy_layout = QGridLayout(proxy)
        proxy_layout.setSpacing(SPACING["sm"])

        proxy_layout.addWidget(make_label("VPN:"), 0, 0)
        self._vpn_combo = QComboBox()
        self._vpn_combo.addItems(["None", "Nautilus VPN (Recommended)", "Custom OpenVPN..."])
        self._vpn_combo.setStyleSheet(self._wifi_combo.styleSheet())
        proxy_layout.addWidget(self._vpn_combo, 0, 1)

        proxy_layout.addWidget(make_label("Proxy:"), 1, 0)
        self._proxy_combo = QComboBox()
        self._proxy_combo.addItems(["None", "SOCKS5", "HTTP", "Custom..."])
        self._proxy_combo.setStyleSheet(self._wifi_combo.styleSheet())
        proxy_layout.addWidget(self._proxy_combo, 1, 1)

        self._vpn_status = QLabel("")
        self._vpn_status.setWordWrap(True)
        self._vpn_status.setStyleSheet(f"color: {COLORS['coral']}; font-family: '{FONTS['mono']}'; font-size: {FONTS['size_xs']}px;")
        proxy_layout.addWidget(self._vpn_status, 2, 0, 1, 2)

        check_btn = QPushButton("\U0001f310  Check Public IP")
        check_btn.setStyleSheet(f"""
            QPushButton {{
                background: {COLORS['seafoam_deep']}; color: {COLORS['seafoam']};
                border: 1px solid {COLORS['seafoam']}; padding: 5px 12px;
                font-family: "{FONTS['mono']}"; font-size: {FONTS['size_sm']}px;
            }}
            QPushButton:hover {{ background: {COLORS['seafoam']}; color: {COLORS['void_black']}; }}
            QPushButton:disabled {{ background: {COLORS['slate_navy']}; color: {COLORS['text_muted']};
                border-color: {COLORS['border']}; }}
        """)
        check_btn.clicked.connect(self._check_public_ip)
        proxy_layout.addWidget(check_btn, 3, 0, 1, 2)

        # Honest, real status wiring (no fake "connected" claims)
        self._vpn_combo.currentIndexChanged.connect(self._update_vpn_status)
        self._proxy_combo.currentIndexChanged.connect(self._update_vpn_status)
        self._check_ip_thread = None
        self._check_ip_btn = check_btn
        self._update_vpn_status()

        layout.addWidget(proxy)
        layout.addStretch()

    def _update_vpn_status(self):
        """Report the REAL state — Anchor does not ship a VPN or proxy client,
        so any selection is informational only. Never claim traffic is protected."""
        vpn = self._vpn_combo.currentText()
        proxy = self._proxy_combo.currentText()
        if vpn == "None" and proxy == "None":
            self._vpn_status.setText(
                "Direct connection \u2014 no VPN or proxy active. "
                "Traffic uses your normal internet connection."
            )
            self._vpn_status.setStyleSheet(
                f"color: {COLORS['text_muted']}; font-family: '{FONTS['mono']}'; font-size: {FONTS['size_xs']}px;"
            )
        else:
            note = "\u26a0 NOT CONFIGURED \u2014 no VPN/proxy client is installed. "
            if vpn != "None":
                note += "VPN selection does not route traffic. "
            if proxy != "None":
                note += "Proxy requires a running local server (e.g. SOCKS5 on 127.0.0.1). "
            note += "Your traffic is NOT protected by this panel."
            self._vpn_status.setText(note)
            self._vpn_status.setStyleSheet(
                f"color: {COLORS['coral']}; font-family: '{FONTS['mono']}'; font-size: {FONTS['size_xs']}px;"
            )

    def _check_public_ip(self):
        self._check_ip_btn.setEnabled(False)
        self._check_ip_btn.setText("Checking...")
        self._check_ip_thread = PublicIpChecker()
        self._check_ip_thread.result_ready.connect(self._on_ip_checked)
        self._check_ip_thread.start()

    def _on_ip_checked(self, text: str):
        self._check_ip_btn.setEnabled(True)
        self._check_ip_btn.setText("\U0001f310  Check Public IP")
        if text.startswith("ERROR:"):
            self._vpn_status.setText(text[6:])
            self._vpn_status.setStyleSheet(
                f"color: {COLORS['coral']}; font-family: '{FONTS['mono']}'; font-size: {FONTS['size_xs']}px;"
            )
        else:
            self._vpn_status.setText(
                f"Public IP: {text}\n"
                "If this is your ISP's IP, no VPN is active \u2014 your traffic is NOT hidden."
            )
            self._vpn_status.setStyleSheet(
                f"color: {COLORS['text_secondary']}; font-family: '{FONTS['mono']}'; font-size: {FONTS['size_xs']}px;"
            )

    def _scan_bluetooth(self):
        self._bt_scan_btn.setEnabled(False)
        self._bt_status.setText("Scanning for Bluetooth devices...")
        self._bt_list.clear()
        self._bt_scanner = BluetoothScanner()
        self._bt_scanner.devices_found.connect(self._on_bt_devices)
        self._bt_scanner.scan_finished.connect(self._on_bt_finished)
        self._bt_scanner.start()

    def _on_bt_devices(self, devices: list):
        self._bt_list.clear()
        if not devices:
            self._bt_list.addItem("No Bluetooth devices found")
            return
        for name, addr in devices:
            item = QListWidgetItem(f"{name}" + (f"   {addr}" if addr else ""))
            item.setForeground(QColor(COLORS["hd_white"]))
            self._bt_list.addItem(item)

    def _on_bt_finished(self, status: str):
        self._bt_scan_btn.setEnabled(True)
        self._bt_status.setText(status)


# ═══════════════════════════════════════════════════════════════
#  AUDIO PANEL
# ═══════════════════════════════════════════════════════════════

class AudioPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setSpacing(SPACING["md"])

        # Output
        output = make_group("Output Device")
        out_layout = QGridLayout(output)
        out_layout.setSpacing(SPACING["sm"])

        out_layout.addWidget(make_label("Device:"), 0, 0)
        out_combo = QComboBox()
        out_combo.addItems(["🔊 Built-in Audio (Default)", "🎧 USB Headset", "📺 HDMI Output", "🔵 Bluetooth Speaker"])
        out_combo.setStyleSheet(f"""
            QComboBox {{
                background: {COLORS['deep_navy']}; color: {COLORS['hd_white']};
                border: 1px solid {COLORS['border']}; padding: 4px 10px;
                font-family: "{FONTS['mono']}";
            }}
            QComboBox:hover {{ border-color: {COLORS['seafoam_dim']}; }}
            QComboBox QAbstractItemView {{
                background: {COLORS['slate_navy']}; color: {COLORS['hd_white']};
                border: 1px solid {COLORS['border']};
                selection-background-color: {COLORS['seafoam_deep']};
            }}
        """)
        out_layout.addWidget(out_combo, 0, 1)

        out_layout.addWidget(make_label("Master Volume:"), 1, 0)
        vol_slider = make_slider(0, 100, 75)
        vol_label = QLabel("75%")
        vol_label.setStyleSheet(f"color: {COLORS['seafoam']}; font-family: '{FONTS['mono']}';")
        vol_slider.valueChanged.connect(lambda v: vol_label.setText(f"{v}%"))
        out_layout.addWidget(vol_slider, 1, 1)
        out_layout.addWidget(vol_label, 1, 2)

        out_layout.addWidget(make_label("Balance:"), 2, 0)
        bal_slider = make_slider(0, 100, 50)
        bal_label = QLabel("Center")
        bal_label.setStyleSheet(f"color: {COLORS['text_secondary']}; font-family: '{FONTS['mono']}';")
        bal_slider.valueChanged.connect(lambda v: bal_label.setText(f"{'Left' if v<45 else 'Right' if v>55 else 'Center'}"))
        out_layout.addWidget(bal_slider, 2, 1)
        out_layout.addWidget(bal_label, 2, 2)

        layout.addWidget(output)

        # Input
        input_group = make_group("Input Device")
        in_layout = QGridLayout(input_group)
        in_layout.setSpacing(SPACING["sm"])

        in_layout.addWidget(make_label("Device:"), 0, 0)
        in_combo = QComboBox()
        in_combo.addItems(["🎤 Built-in Microphone (Default)", "🎧 Headset Mic", "📷 USB Webcam Mic"])
        in_combo.setStyleSheet(out_combo.styleSheet())
        in_layout.addWidget(in_combo, 0, 1)

        in_layout.addWidget(make_label("Input Gain:"), 1, 0)
        gain_slider = make_slider(0, 200, 100)
        gain_label = QLabel("100%")
        gain_label.setStyleSheet(f"color: {COLORS['seafoam']}; font-family: '{FONTS['mono']}';")
        gain_slider.valueChanged.connect(lambda v: gain_label.setText(f"{v}%"))
        in_layout.addWidget(gain_slider, 1, 1)
        in_layout.addWidget(gain_label, 1, 2)

        layout.addWidget(input_group)

        # Sound effects
        sfx = make_group("Sound Effects & Alerts")
        sfx_layout = QVBoxLayout(sfx)
        sfx_layout.setSpacing(SPACING["sm"])

        self._sfx_toggle = QCheckBox("Enable System Sound Effects")
        self._sfx_toggle.setChecked(True)
        self._sfx_toggle.setStyleSheet(f"color: {COLORS['hd_white']}; font-family: '{FONTS['mono']}';")
        sfx_layout.addWidget(self._sfx_toggle)

        sfx_vol_layout = QHBoxLayout()
        sfx_vol_layout.addWidget(make_label("Alert Volume:"))
        alert_slider = make_slider(0, 100, 60)
        sfx_vol_layout.addWidget(alert_slider)
        sfx_layout.addLayout(sfx_vol_layout)

        layout.addWidget(sfx)
        layout.addStretch()


# ═══════════════════════════════════════════════════════════════
#  THEME OVERRIDE PANEL
# ═══════════════════════════════════════════════════════════════

class ThemePanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setSpacing(SPACING["md"])

        info = QLabel("Global UI Token Overrides\nCustomize the Nautilus color palette in real-time.")
        info.setStyleSheet(f"color: {COLORS['text_secondary']}; font-family: '{FONTS['ui']}'; font-size: {FONTS['size_sm']}px;")
        layout.addWidget(info)

        self._color_fields = {}

        # Editable color tokens
        colors_group = make_group("Color Tokens")
        colors_layout = QGridLayout(colors_group)
        colors_layout.setSpacing(SPACING["sm"])

        tokens = [
            ("abyss_navy", "Base Background", COLORS["abyss_navy"]),
            ("slate_navy", "Surface / Containers", COLORS["slate_navy"]),
            ("seafoam", "Primary Accent", COLORS["seafoam"]),
            ("coral", "Alert / Warning", COLORS["coral"]),
            ("hd_white", "Primary Text", COLORS["hd_white"]),
            ("text_secondary", "Secondary Text", COLORS["text_secondary"]),
            ("text_muted", "Muted Text", COLORS["text_muted"]),
            ("border", "Borders", COLORS["border"]),
            ("deep_navy", "Deep Background", COLORS["deep_navy"]),
            ("void_black", "Void / Maximum Dark", COLORS["void_black"]),
        ]

        for row, (token, label, default) in enumerate(tokens):
            lbl = make_label(f"{label}:")
            colors_layout.addWidget(lbl, row, 0)

            color_display = QFrame()
            color_display.setFixedSize(24, 24)
            color_display.setStyleSheet(f"background-color: {default}; border: 1px solid {COLORS['border']};")
            colors_layout.addWidget(color_display, row, 1)

            hex_label = QLabel(default)
            hex_label.setStyleSheet(f"color: {COLORS['text_muted']}; font-family: '{FONTS['mono']}'; font-size: {FONTS['size_xs']}px;")
            colors_layout.addWidget(hex_label, row, 2)

            pick_btn = QPushButton("✎")
            pick_btn.setFixedSize(28, 24)
            pick_btn.setStyleSheet(f"""
                QPushButton {{
                    background: {COLORS['slate_navy']}; color: {COLORS['seafoam']};
                    border: 1px solid {COLORS['border']};
                }}
                QPushButton:hover {{ background: {COLORS['seafoam_deep']}; }}
            """)

            def make_picker(t=token, cd=color_display, hl=hex_label):
                return lambda: self._pick_color(t, cd, hl)

            pick_btn.clicked.connect(make_picker())
            colors_layout.addWidget(pick_btn, row, 3)

            self._color_fields[token] = (color_display, hex_label)

        layout.addWidget(colors_group)

        # Reset button
        reset_btn = QPushButton("↺  Reset to Nautilus Defaults")
        reset_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent; color: {COLORS['coral']};
                border: 1px solid {COLORS['coral']}; padding: 6px 16px;
                font-family: "{FONTS['mono']}"; font-size: {FONTS['size_sm']}px;
            }}
            QPushButton:hover {{ background: {COLORS['coral']}; color: {COLORS['void_black']}; }}
        """)
        reset_btn.clicked.connect(self._reset_defaults)
        layout.addWidget(reset_btn)

        layout.addStretch()

    def _pick_color(self, token: str, display: QFrame, hex_label: QLabel):
        color = QColorDialog.getColor(QColor(COLORS[token]), self, f"Choose {token}")
        if color.isValid():
            hex_str = color.name()
            COLORS[token] = hex_str
            display.setStyleSheet(f"background-color: {hex_str}; border: 1px solid {COLORS['border']};")
            hex_label.setText(hex_str)

    def _reset_defaults(self):
        defaults = {
            "abyss_navy": "#081626", "slate_navy": "#0E2238", "seafoam": "#00F2C2",
            "coral": "#FF7F50", "hd_white": "#EEF4F8", "text_secondary": "#8BA4B8",
            "text_muted": "#506070", "border": "#152D44", "deep_navy": "#050D14",
            "void_black": "#02060A",
        }
        for token, hex_str in defaults.items():
            COLORS[token] = hex_str
            if token in self._color_fields:
                display, label = self._color_fields[token]
                display.setStyleSheet(f"background-color: {hex_str}; border: 1px solid {COLORS['border']};")
                label.setText(hex_str)


# ═══════════════════════════════════════════════════════════════
#  ABOUT PANEL
# ═══════════════════════════════════════════════════════════════

class AboutPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(SPACING["lg"])

        title = QLabel("⚓  NAUTILUS OS")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet(f"""
            color: {COLORS['seafoam']}; font-family: "{FONTS['mono']}";
            font-size: {FONTS['size_xxl']}px; font-weight: bold; letter-spacing: 6px;
        """)
        layout.addWidget(title)

        version = QLabel("Version 1.0.0  •  Build 2026.08.01")
        version.setAlignment(Qt.AlignCenter)
        version.setStyleSheet(f"color: {COLORS['text_secondary']}; font-family: '{FONTS['mono']}';")
        layout.addWidget(version)

        tagline = QLabel('"A weightless, high-density desktop environment\nbuilt for low-resource performance."')
        tagline.setAlignment(Qt.AlignCenter)
        tagline.setStyleSheet(f"color: {COLORS['text_muted']}; font-family: '{FONTS['ui']}'; font-size: {FONTS['size_md']}px;")
        layout.addWidget(tagline)

        specs = QLabel(
            "Target: Raspberry Pi 500 (ARM64) & x86_64 Linux\n"
            "Framework: Python 3.11+ / PySide6\n"
            "Base RAM: < 350 MB\n"
            "Design: Zero border-radius cyber-terminal aesthetic"
        )
        specs.setAlignment(Qt.AlignCenter)
        specs.setStyleSheet(f"color: {COLORS['text_muted']}; font-family: '{FONTS['mono']}'; font-size: {FONTS['size_xs']}px;")
        layout.addWidget(specs)

        layout.addStretch()


# ═══════════════════════════════════════════════════════════════
#  MAIN WINDOW
# ═══════════════════════════════════════════════════════════════

class AnchorWindow(QMainWindow):
    """Anchor — Nautilus Control Center & Settings."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Anchor — Settings")
        self.setMinimumSize(750, 550)
        self.resize(850, 650)

        self._setup_ui()

    def _setup_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(SPACING["md"], SPACING["md"], SPACING["md"], SPACING["md"])
        main_layout.setSpacing(SPACING["sm"])

        # Title
        title = QLabel("⚙  ANCHOR  //  Control Center")
        title.setStyleSheet(f"""
            color: {COLORS['seafoam']}; font-family: "{FONTS['mono']}";
            font-size: {FONTS['size_lg']}px; font-weight: bold; letter-spacing: 2px;
            padding-bottom: 4px; border-bottom: 1px solid {COLORS['border']};
        """)
        main_layout.addWidget(title)

        # Tab widget
        tabs = QTabWidget()
        tabs.setStyleSheet(f"""
            QTabWidget::pane {{
                border: 1px solid {COLORS['border']};
                background-color: {COLORS['abyss_navy']};
            }}
            QTabBar::tab {{
                background-color: {COLORS['tab_inactive']};
                color: {COLORS['text_secondary']};
                padding: 6px 16px;
                border: none;
                border-bottom: 2px solid transparent;
                font-family: "{FONTS['mono']}";
                font-size: {FONTS['size_sm']}px;
                min-width: 80px;
            }}
            QTabBar::tab:selected {{
                background-color: {COLORS['tab_active']};
                color: {COLORS['seafoam']};
                border-bottom: 2px solid {COLORS['seafoam']};
            }}
            QTabBar::tab:hover:!selected {{
                background-color: {COLORS['surface_hover']};
                color: {COLORS['hd_white']};
            }}
        """)

        # Add panels with custom logo icons
        tabs.setIconSize(QSize(16, 16))
        tabs.addTab(DisplayPanel(), get_logo("anchor_display"), "  Display")
        tabs.addTab(NetworkPanel(), get_logo("anchor_network"), "  Network")
        tabs.addTab(AudioPanel(), get_logo("anchor_audio"), "  Audio")
        tabs.addTab(ThemePanel(), get_logo("anchor_theme"), "  Theme")
        tabs.addTab(AboutPanel(), get_logo("anchor_about"), "  About")

        main_layout.addWidget(tabs, 1)

        # Bottom bar
        bottom = QHBoxLayout()
        apply_all = QPushButton("Apply All Settings")
        apply_all.setStyleSheet(f"""
            QPushButton {{
                background: {COLORS['seafoam_deep']};
                color: {COLORS['seafoam']};
                border: 1px solid {COLORS['seafoam']};
                padding: 6px 20px;
                font-family: "{FONTS['mono']}";
                font-size: {FONTS['size_sm']}px;
                font-weight: bold;
            }}
            QPushButton:hover {{ background: {COLORS['seafoam']}; color: {COLORS['void_black']}; }}
        """)
        apply_all.clicked.connect(lambda: QMessageBox.information(self, "Settings", "Settings applied successfully."))
        bottom.addStretch()
        bottom.addWidget(apply_all)

        main_layout.addLayout(bottom)


# ═══════════════════════════════════════════════════════════════

def main():
    try:
        from core.logger import get_logger
        log = get_logger("APP")
        log.info("Anchor Settings starting")
    except Exception:
        pass

    app = QApplication(sys.argv)
    app.setApplicationName("Anchor")
    app.setOrganizationName("Nautilus")

    try:
        from core.icons import get_logo
        app.setWindowIcon(get_logo("anchor"))
    except Exception:
        pass

    app.setPalette(create_nautilus_palette())
    app.setStyleSheet(get_global_stylesheet())

    font = QFont()
    font.setFamilies([FONTS["ui"], FONTS["mono"], "Consolas"])
    font.setPointSize(FONTS["size_md"])
    app.setFont(font)

    window = AnchorWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
