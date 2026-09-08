"""Nautilus OS - The Depths (Cybersecurity Hub)"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QProgressBar,
    QPushButton,
    QScrollArea,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from core.profile import Profile
from core.theme import COLORS, FONTS, RADIUS_MD, RADIUS_SM
from core.tutorials import TutorialEngine

CATEGORIES = [
    ("Recon",       "\U0001F50D", "Ocean Recon",       "#3DC98A"),
    ("RedTeam",     "\U0001F4A2", "Predator Ops",      "#FF5252"),
    ("BlueTeam",    "\U0001F6E1\ufe0f", "Defender Ops", "#4FC3F7"),
    ("Forensics",   "\U0001F50D", "Deep Sea Forensics", "#7C4DFF"),
    ("Crypto",      "\U0001F511", "The Vault",          "#FFD700"),
    ("OSINT",       "\U0001F30D", "Open Waters",        "#FF9100"),
    ("Wireless",    "\U0001F4E1", "Signal Depths",      "#00E5FF"),
]

TOOLS = [
    # (id, name, category, difficulty, coins, icon, desc, module)
    ("port_scanner",  "Port Scanner",    "Recon",    1,  120,  "\U0001F9ED",
     "Discover open ports on a target", "port_scanner"),
    ("network_map",   "Network Map",     "Recon",    1,  85,   "\U0001F5FA",
     "Discover hosts on your subnet",   "network_map"),
    ("whois_lookup",  "WHOIS Lookup",    "Recon",    0,  70,   "\U0001F3D8",
     "Query domain registration info",  "whois_lookup"),
    ("dns_enum",      "DNS Enumerator",  "Recon",    1,  90,   "\U0001F310",
     "Enumerate DNS records",           "dns_enum"),
    ("subdomain_find","Subdomain Finder","Recon",    2,  150,  "\U0001F3DC",
     "Brute-force subdomains",          "subdomain_finder"),
    ("packet_capture","Packet Capture",  "Recon",    2,  200,  "\U0001F4E6",
     "Capture network packets",         "packet_capture"),
    ("vuln_scanner",  "Vuln Scanner",    "RedTeam",  2,  160,  "\U0001F9F1",
     "Check target for vulnerabilities","vuln_scanner"),
    ("password_cracker","Password Cracker","RedTeam",1,130,   "\U0001F511",
     "Test password strength",          "password_cracker"),
    ("sql_injector",  "SQL Injector",    "RedTeam",  3,  200,  "\U0001F4A5",
     "Test for SQL injection",          "sql_injector"),
    ("exploit_builder","Exploit Builder","RedTeam",  3,  220,  "\U0001F4A3",
     "Construct exploit payloads",      "exploit_builder"),
    ("hash_analyzer", "Hash Analyzer",   "RedTeam",  1,  90,   "\U0001F9EE",
     "Identify hash types",             "hash_analyzer"),
    ("payload_craft", "Payload Crafter","RedTeam",  2,  180,  "\U0001F4C2",
     "Generate payloads",               "payload_craft"),
    ("log_analyzer",  "Log Analyzer",    "BlueTeam", 1,  110,  "\U0001F4CB",
     "Analyze system logs",             "log_analyzer"),
    ("firewall_manager","Firewall Manager","BlueTeam",1,120,  "\U0001F6E1\ufe0f",
     "Manage firewall rules",           "firewall_manager"),
    ("incident_responder","Incident Responder","BlueTeam",2,180,"\U0001F916",
     "Respond to security incidents",   "incident_responder"),
    ("threat_hunter", "Threat Hunter",   "BlueTeam", 3,  220,  "\U0001F40B",
     "Hunt for indicators of compromise","threat_hunter"),
    ("malware_sandbox","Malware Sandbox","BlueTeam",3, 240,   "\U0001F9EA",
     "Analyze suspicious files",        "malware_sandbox"),
    ("memory_forensics","Memory Forensics","Forensics",3,240, "\U0001F4BE",
     "Analyze memory dumps",            "memory_forensics"),
    ("disk_analyzer", "Disk Analyzer",   "Forensics",2, 200,   "\U0001F4C0",
     "Examine disk images",             "disk_analyzer"),
    ("steganography", "Steganography",   "Forensics",3, 220,   "\U0001F3E0",
     "Hide/extract messages in images", "steganography"),
    ("timeline_builder","Timeline Builder","Forensics",2,180,  "\U0001F4C5",
     "Build event timelines",           "timeline_builder"),
    ("cipher_challenges","Cipher Challenges","Crypto",0,80,    "\U0001F4D1",
     "Solve classic ciphers",           "cipher_challenges"),
    ("hash_cracker",  "Hash Cracker",    "Crypto",   1,  130,  "\U0001F5DD",
     "Brute-force hashes",              "hash_cracker"),
    ("caesar_wheel",  "Caesar Wheel",    "Crypto",   0,  60,   "\U0001F300",
     "Caesar cipher decoder",           "caesar_wheel"),
    ("rsa_playground","RSA Playground",  "Crypto",   2,  160,  "\U0001F510",
     "Explore RSA cryptography",        "rsa_playground"),
    ("osint_recon",   "OSINT Recon",     "OSINT",    1,  100,  "\U0001F4F1",
     "Aggregate public intel",          "osint_recon"),
    ("social_mapper", "Social Mapper",   "OSINT",    2,  150,  "\U0001F465",
     "Map social media profiles",       "social_mapper"),
    ("wifi_analyzer", "WiFi Analyzer",   "Wireless", 1,  120,  "\U0001F4F6",
     "Scan nearby networks",            "wifi_analyzer"),
    ("packet_injector","Packet Injector","Wireless", 3,  240,  "\U0001F4E8",
     "Craft packets",                   "packet_injector"),
]

DIFF_STARS = {
    0: "Beginner",
    1: "Novice",
    2: "Intermediate",
    3: "Advanced",
}


def get_tool_info(tool_id):
    for t in TOOLS:
        if t[0] == tool_id:
            return {
                "id": t[0], "name": t[1], "category": t[2],
                "difficulty": t[3], "coins": t[4], "icon": t[5],
                "desc": t[6], "module": t[7],
            }
    return None


class CoinBadge(QLabel):
    def __init__(self, profile: Profile):
        super().__init__()
        self.profile = profile
        self.setStyleSheet(f"""
            color: {COLORS['gold']};
            font-family: "{FONTS['mono']}";
            font-size: {FONTS['size_sm']}px;
            font-weight: bold;
            background: {COLORS['bg_mid']};
            border: 1px solid {COLORS['border']};
            border-radius: {RADIUS_SM};
            padding: 4px 10px;
        """)
        self.update_display()

    def update_display(self):
        self.setText(f"\U0001FA99 {self.profile.coins}  \u2693 Lv.{self.profile.level}")


class ToolCard(QFrame):
    def __init__(self, tool, profile: Profile, on_launch, on_tutorial):
        super().__init__()
        self.tool = tool
        self._on_launch = on_launch
        self._on_tutorial = on_tutorial
        self.setFixedSize(205, 140)
        self.setStyleSheet(f"""
            QFrame {{
                background: {COLORS['bg_mid']};
                border: 1px solid {COLORS['border']};
                border-radius: {RADIUS_MD};
            }}
            QFrame:hover {{
                background: {COLORS['hover']};
                border: 1px solid {COLORS['teal']};
            }}
        """)
        self.setCursor(Qt.PointingHandCursor)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(4)

        name_row = QHBoxLayout()
        icon = QLabel(self.tool["icon"])
        icon.setStyleSheet("background: transparent; border: none; font-size: 20px;")
        name_row.addWidget(icon)

        name = QLabel(self.tool["name"])
        name.setStyleSheet(f"""
            color: {COLORS['text_dark']};
            font-family: "{FONTS['ui']}";
            font-size: {FONTS['size_md']}px;
            font-weight: bold;
            background: transparent; border: none;
        """)
        name.setWordWrap(True)
        name_row.addWidget(name, 1)
        layout.addLayout(name_row)

        diff = QLabel(DIFF_STARS.get(self.tool["difficulty"], "Beginner"))
        diff.setStyleSheet(f"color: {COLORS['text_muted']}; background: transparent; border: none; font-size: 9px;")
        layout.addWidget(diff)

        desc = QLabel(self.tool["desc"])
        desc.setWordWrap(True)
        desc.setStyleSheet(f"""
            color: {COLORS['text_muted']};
            font-family: "{FONTS['ui']}";
            font-size: {FONTS['size_xs']}px;
            background: transparent; border: none;
        """)
        layout.addWidget(desc)

        row = QHBoxLayout()
        tutor_done = self.tool["id"] in profile.completed_tutorials
        tut_btn = QPushButton("Tutorial \u2713" if tutor_done else "Tutorial")
        tut_btn.setFixedHeight(24)
        tut_btn.setStyleSheet(f"""
            QPushButton {{
                background: {COLORS['teal_dim'] if tutor_done else COLORS['teal']};
                color: #fff;
                border: none; border-radius: 5px;
                font-size: {FONTS['size_xs']}px;
            }}
            QPushButton:hover {{ background: {COLORS['teal_light']}; }}
        """)
        tut_btn.clicked.connect(lambda: self._on_tutorial(self.tool["module"]))
        row.addWidget(tut_btn)

        run_btn = QPushButton(f"Run  \U0001FA99 {self.tool['coins']}")
        run_btn.setFixedHeight(24)
        run_btn.setStyleSheet(f"""
            QPushButton {{
                background: {COLORS['teal']};
                color: {COLORS['text_dark']};
                border: none; border-radius: 5px;
                font-size: {FONTS['size_xs']}px; font-weight: bold;
            }}
            QPushButton:hover {{ background: {COLORS['teal_light']}; }}
        """)
        run_btn.clicked.connect(lambda: self._on_launch(self.tool["module"]))
        row.addWidget(run_btn)
        layout.addLayout(row)


class TutorialDialog(QDialog):
    def __init__(self, engine: TutorialEngine, parent=None):
        super().__init__(parent)
        self.engine = engine
        self.setWindowTitle("Tutorial")
        self.resize(560, 380)
        self.setStyleSheet(f"background: {COLORS['bg_light']};")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        self.title = QLabel("")
        self.title.setStyleSheet(f"""
            color: {COLORS['teal_light']};
            font-family: "{FONTS['ui']}";
            font-size: {FONTS['size_lg']}px;
            font-weight: bold;
            background: transparent; border: none;
        """)
        layout.addWidget(self.title)

        step_label = QLabel("")
        step_label.setStyleSheet(f"color: {COLORS['text_muted']}; background: transparent; border: none;")
        layout.addWidget(step_label)

        self.progress = QProgressBar()
        self.progress.setStyleSheet(f"""
            QProgressBar {{
                background: {COLORS['bg_mid']};
                border: 1px solid {COLORS['border']};
                border-radius: 4px; height: 8px;
                text-align: center;
            }}
            QProgressBar::chunk {{
                background: {COLORS['teal']};
                border-radius: 4px;
            }}
        """)
        self.progress.setRange(0, 100)
        layout.addWidget(self.progress)

        self.body = QTextEdit()
        self.body.setReadOnly(True)
        self.body.setStyleSheet(f"""
            QTextEdit {{
                background: {COLORS['bg_mid']};
                color: {COLORS['text']};
                border: 1px solid {COLORS['border']};
                border-radius: {RADIUS_SM};
                font-family: "{FONTS['ui']}";
                font-size: {FONTS['size_md']}px;
                padding: 10px;
            }}
        """)
        layout.addWidget(self.body)

        btn_row = QHBoxLayout()
        self.prev_btn = QPushButton("\u2190 Prev")
        self.prev_btn.setStyleSheet(f"""
            QPushButton {{
                background: {COLORS['bg_dark']}; color: {COLORS['text']};
                border: none; border-radius: {RADIUS_SM};
                padding: 8px 14px; font-size: {FONTS['size_sm']}px;
            }}
            QPushButton:hover {{ background: {COLORS['hover']}; }}
        """)
        self.prev_btn.clicked.connect(self._prev)
        btn_row.addWidget(self.prev_btn)

        btn_row.addStretch()

        self.next_btn = QPushButton("Next \u2192")
        self.next_btn.setStyleSheet(f"""
            QPushButton {{
                background: {COLORS['coral']}; color: #fff;
                border: none; border-radius: {RADIUS_SM};
                padding: 8px 16px; font-size: {FONTS['size_sm']}px;
                font-weight: bold;
            }}
            QPushButton:hover {{ background: {COLORS['coral_deep']}; }}
        """)
        self.next_btn.clicked.connect(self._next)
        btn_row.addWidget(self.next_btn)

        close_btn = QPushButton("Skip")
        close_btn.setStyleSheet(f"""
            QPushButton {{
                background: {COLORS['bg_dark']}; color: {COLORS['text_muted']};
                border: none; border-radius: {RADIUS_SM};
                padding: 8px 14px; font-size: {FONTS['size_sm']}px;
            }}
            QPushButton:hover {{ background: {COLORS['hover']}; }}
        """)
        close_btn.clicked.connect(self.reject)
        btn_row.addWidget(close_btn)

        layout.addLayout(btn_row)

        self.engine.set_callbacks(
            on_step=self._render_step,
            on_complete=self._on_complete,
        )
        self._render_step(self.engine.get_current_step())

    def _render_step(self, step):
        if step is None:
            self.accept()
            return
        self.title.setText(step["tutorial_name"])
        self.body.setText(step["text"])
        self.progress.setValue(int(step["progress"] * 100))
        self.next_btn.setText("Finish \u2728" if step["step_index"] >= step["steps_total"] else "Next \u2192")
        self.prev_btn.setEnabled(step["step_index"] > 1)

    def _next(self):
        self.engine.next_step()

    def _prev(self):
        self.engine.previous_step()

    def _on_complete(self, info):
        self.accept()


class DepthsWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("The Depths - Cybersecurity Hub")
        self.resize(1080, 720)
        self.setStyleSheet(f"QMainWindow {{ background: {COLORS['bg_light']}; }}")
        self.profile = Profile()
        self.tutorial_engine = TutorialEngine(self.profile)
        self._active_category = "All"
        self._windows = {}

        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(10)

        header = QHBoxLayout()
        title = QLabel("\U0001FA93  The Depths")
        title.setStyleSheet(f"""
            color: {COLORS['teal_light']};
            font-family: "{FONTS['ui']}";
            font-size: {FONTS['size_xl']}px;
            font-weight: bold;
            background: transparent; border: none;
        """)
        header.addWidget(title)
        header.addStretch()
        self.badge = CoinBadge(self.profile)
        header.addWidget(self.badge)
        layout.addLayout(header)

        bar = QFrame()
        bar.setStyleSheet("background: transparent; border: none;")
        bar_layout = QHBoxLayout(bar)
        bar_layout.setContentsMargins(0, 0, 0, 0)
        bar_layout.setSpacing(6)
        self._cat_buttons = [("All", self._make_cat_button("All"))]
        bar_layout.addWidget(self._cat_buttons[0][1])
        for cat in CATEGORIES:
            btn = self._make_cat_button(cat[2])
            self._cat_buttons.append((cat[2], btn))
            bar_layout.addWidget(btn)
        bar_layout.addStretch()
        layout.addWidget(bar)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("""
            QScrollArea { background: transparent; border: none; }
            QScrollArea > QWidget > QWidget { background: transparent; }
        """)
        self.grid_container = QWidget()
        self.grid = QGridLayout(self.grid_container)
        self.grid.setContentsMargins(0, 0, 0, 0)
        self.grid.setSpacing(10)
        scroll.setWidget(self.grid_container)
        layout.addWidget(scroll)

        self._populate_grid()

    def _make_cat_button(self, label):
        btn = QPushButton(label)
        btn.setCheckable(True)
        btn.setChecked(False)
        btn.setFixedHeight(30)
        btn.setStyleSheet(f"""
            QPushButton {{
                background: {COLORS['bg_mid']}; color: {COLORS['text']};
                border: 1px solid {COLORS['border']}; border-radius: 15px;
                padding: 0 14px; font-size: {FONTS['size_sm']}px;
            }}
            QPushButton:hover {{ background: {COLORS['hover']}; }}
            QPushButton:checked {{
                background: {COLORS['teal']}; color: #fff;
                border: none; font-weight: bold;
            }}
        """)
        btn.clicked.connect(lambda _, b=btn, lab=label: self._filter_category(b, lab))
        return btn

    def _filter_category(self, btn, label):
        self._active_category = label
        for lbl, b in self._cat_buttons:
            b.setChecked(lbl == label)
        self._populate_grid()

    def _populate_grid(self):
        while self.grid.count():
            item = self.grid.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()

        cat_label_to_id = {label: cid for cid, icon, label, color in CATEGORIES}
        row, col = 0, 0
        for tool in TOOLS:
            if self._active_category != "All":
                if cat_label_to_id.get(self._active_category, self._active_category) != tool[2]:
                    continue
            info = get_tool_info(tool[0])
            card = ToolCard(info, self.profile, self._launch_tool, self._open_tutorial)
            self.grid.addWidget(card, row, col)
            col += 1
            if col >= 4:
                col = 0
                row += 1

    def _launch_tool(self, tool_module):
        self.profile.record_tool_use(tool_module)
        self.profile.add_coins(5)
        try:
            mod = __import__(f"apps.depths.tools.{tool_module}", fromlist=["run"])
        except ImportError:
            self._open_tutorial(tool_module)
            return
        if hasattr(mod, "run"):
            window = mod.run(self)
            if window is not None:
                self._windows[tool_module] = window
        self.badge.update_display()

    def _open_tutorial(self, tool_module):
        if tool_module in self.profile.completed_tutorials:
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.information(self, "Already Done", "You've already completed this tutorial.")
            return
        started = self.tutorial_engine.start_tutorial(tool_module)
        if not started:
            return
        dlg = TutorialDialog(self.tutorial_engine, self)
        dlg.exec()
        self.badge.update_display()
        self._populate_grid()


def main():
    from PySide6.QtWidgets import QApplication
    app = QApplication(sys.argv)
    win = DepthsWindow()
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
