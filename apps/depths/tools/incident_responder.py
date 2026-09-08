"""Incident Responder - The Depths"""

import os
import sys

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

from apps.depths.tools._ui import BTN_STYLE, GREEN, OUT_STYLE, YELLOW, hline, make_header
from core.theme import COLORS, FONTS

# Incident response phases from NIST 800-61
PHASES = [
    ("1. Preparation", "Establish a response team, define roles, and prepare tools and playbooks."),
    ("2. Detection & Analysis", "Detect the incident, triage, and perform analysis to confirm and scope it."),
    ("3. Containment", "Stop the spread. Isolate affected systems, preserve evidence, block IOCs."),
    ("4. Eradication", "Remove the root cause. Patch vulnerabilities, delete malware, clean systems."),
    ("5. Recovery", "Restore systems to normal operation, strengthen defenses, validate integrity."),
    ("6. Lessons Learned", "Document what happened, improve processes, update playbooks."),
]


class IncidentResponderWindow(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.phase = 0
        self.setWindowTitle("Incident Responder - The Depths")
        self.resize(680, 560)
        self.setStyleSheet(f"QMainWindow {{ background: {COLORS['bg_light']}; }}")

        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(10)

        layout.addWidget(make_header(
            "\U0001F916 Incident Responder",
            "Walk through the incident response lifecycle (NIST 800-61)"
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
