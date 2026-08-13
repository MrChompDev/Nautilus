"""
Embedded Command Shell - Terminal panel widget.
Pipes I/O to system terminal threads.
"""
import os
import platform

from PySide6.QtCore import QProcess, Qt, Signal
from PySide6.QtGui import QKeyEvent, QTextCursor
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from apps.Surfline.src.theme import COLORS, FONTS


class TerminalInput(QLineEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.history = []
        self.history_index = -1
        self.prompt_text = ">_ "
        self.setStyleSheet(f"""
            QLineEdit {{
                background: {COLORS['terminal_bg']};
                color: {COLORS['accent']};
                border: none;
                border-top: 1px solid {COLORS['border']};
                font-family: "{FONTS['mono']}", "{FONTS['fallback_mono']}";
                font-size: {FONTS['size_sm']}px;
                padding: 4px 8px;
                selection-background-color: {COLORS['selection']};
            }}
        """)
        self.setPlaceholderText(f"{self.prompt_text}Enter command...")

    def keyPressEvent(self, event: QKeyEvent):
        if event.key() in (Qt.Key_Return, Qt.Key_Enter):
            text = self.text().strip()
            if text:
                self.history.append(text)
                self.history_index = len(self.history)
            self.command_entered.emit(text)
            self.clear()
        elif event.key() == Qt.Key_Up:
            if self.history and self.history_index > 0:
                self.history_index -= 1
                self.setText(self.history[self.history_index])
        elif event.key() == Qt.Key_Down:
            if self.history_index < len(self.history) - 1:
                self.history_index += 1
                self.setText(self.history[self.history_index])
            else:
                self.history_index = len(self.history)
                self.clear()
        else:
            super().keyPressEvent(event)

    command_entered = Signal(str)


class TerminalWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.process = None
        self.setup_ui()
        self.start_shell()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        header = QHBoxLayout()
        header.setContentsMargins(8, 4, 8, 4)
        header_label = QLabel("TERMINAL")
        header_label.setStyleSheet(f"""
            QLabel {{
                color: {COLORS['accent']};
                font-family: "{FONTS['mono']}", "{FONTS['fallback_mono']}";
                font-size: {FONTS['size_xs']}px;
                font-weight: bold;
                letter-spacing: 2px;
            }}
        """)
        header.addWidget(header_label)
        header.addStretch()

        self.process_info = QLabel("shell: ready")
        self.process_info.setStyleSheet(f"""
            QLabel {{
                color: {COLORS['text_muted']};
                font-family: "{FONTS['mono']}", "{FONTS['fallback_mono']}";
                font-size: {FONTS['size_xs']}px;
            }}
        """)
        header.addWidget(self.process_info)
        layout.addLayout(header)

        self.output = QTextEdit()
        self.output.setReadOnly(True)
        self.output.setStyleSheet(f"""
            QTextEdit {{
                background: {COLORS['terminal_bg']};
                color: {COLORS['terminal_text']};
                border: none;
                font-family: "{FONTS['mono']}", "{FONTS['fallback_mono']}";
                font-size: {FONTS['size_sm']}px;
                padding: 4px 8px;
                selection-background-color: {COLORS['selection']};
            }}
        """)
        layout.addWidget(self.output)

        self.input = TerminalInput()
        self.input.command_entered.connect(self.execute_command)
        layout.addWidget(self.input)

        self.setMinimumHeight(120)

    def start_shell(self):
        self.process = QProcess(self)
        self.process.setProcessChannelMode(QProcess.MergedChannels)
        self.process.readyReadStandardOutput.connect(self.read_output)
        self.process.finished.connect(self.on_process_finished)

        if platform.system() == "Windows":
            self.process.start("cmd.exe")
            self.process_info.setText("shell: cmd.exe")
        else:
            shell = os.environ.get("SHELL", "/bin/bash")
            self.process.start(shell)
            self.process_info.setText(f"shell: {shell}")

        self.append_output("Surfline Terminal v1.0\n")
        self.append_output(f"Platform: {platform.system()} {platform.machine()}\n")
        self.append_output(f"Shell: {self.process.program()}\n")
        self.append_output("---\n")

    def execute_command(self, command: str):
        if not command.strip():
            return

        if command.strip().lower() in ("exit", "quit"):
            self.process.kill()
            self.append_output("[session terminated]\n")
            return

        self.append_output(f"{self.input.prompt_text}{command}\n")

        if platform.system() == "Windows":
            self.process.write((command + "\r\n").encode("utf-8", errors="replace"))
        else:
            self.process.write((command + "\n").encode("utf-8", errors="replace"))

    def read_output(self):
        data = self.process.readAllStandardOutput()
        if data:
            text = bytes(data.data()).decode("utf-8", errors="replace")
            self.append_output(text)

    def on_process_finished(self, exit_code, exit_status):
        self.append_output(f"\n[process exited with code {exit_code}]\n")
        self.process_info.setText("shell: exited")
        self.start_shell()

    def append_output(self, text: str):
        self.output.moveCursor(QTextCursor.MoveOperation.End)
        self.output.insertPlainText(text)
        self.output.moveCursor(QTextCursor.MoveOperation.End)
        sb = self.output.verticalScrollBar()
        sb.setValue(sb.maximum())

    def closeEvent(self, event):
        if self.process and self.process.state() == QProcess.Running:
            self.process.kill()
            self.process.waitForFinished(1000)
        event.accept()
