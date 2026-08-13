import os
import subprocess

from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QBrush, QColor, QFont
from PySide6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSplitter,
    QTabWidget,
    QTextEdit,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

from apps.Abyssal.src.ui.styles import AbyssalTheme


class GitCommandWorker(QThread):
    output_received = Signal(str)
    error_received = Signal(str)
    finished = Signal(int, bool)
    progress = Signal(str)

    def __init__(self, command: list[str], cwd: str = None):
        super().__init__()
        self.command = command
        self.cwd = cwd or os.getcwd()
        self._process = None

    def run(self):
        try:
            self._process = subprocess.Popen(
                self.command,
                cwd=self.cwd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                stdin=subprocess.PIPE,
                text=True,
                bufsize=1
            )
            stdout_queue = []
            stderr_queue = []
            
            def read_stdout():
                for line in iter(self._process.stdout.readline, ''):
                    stdout_queue.append(line)
                    self.output_received.emit(line.rstrip())
            
            def read_stderr():
                for line in iter(self._process.stderr.readline, ''):
                    stderr_queue.append(line)
                    self.error_received.emit(line.rstrip())
            
            import threading
            thread_stdout = threading.Thread(target=read_stdout)
            thread_stderr = threading.Thread(target=read_stderr)
            thread_stdout.daemon = True
            thread_stderr.daemon = True
            thread_stdout.start()
            thread_stderr.start()
            
            return_code = self._process.wait()
            
            for line in stdout_queue:
                self.output_received.emit(line.rstrip())
            for line in stderr_queue:
                self.error_received.emit(line.rstrip())
            
            self.finished.emit(return_code, return_code == 0)
            
        except Exception as e:
            self.error_received.emit(f"Error: {e!s}")
            self.finished.emit(-1, False)

    def cancel(self):
        if self._process:
            self._process.terminate()
            self._process.wait()


class GitStatusItem(QTreeWidgetItem):
    def __init__(self, status: dict, parent=None):
        super().__init__(parent)
        self.status_data = status
        file_path = status['path']
        staged = status['staged']
        unstaged = status['unstaged']

        if file_path.startswith(':'):
            icon = "🌱"
            status_text = " Untracked"
            color = AbyssalTheme.TEXT_DIM
        elif staged and unstaged:
            icon = "🔴"
            status_text = " Modified"
            color = AbyssalTheme.CORAL
        elif staged and not unstaged:
            icon = "🟢"
            status_text = " Added"
            color = AbyssalTheme.ACCENT
        elif not staged and unstaged:
            icon = "🟡"
            status_text = " Modified"
            color = AbyssalTheme.YELLOW
        elif status.get('is_dir', False):
            icon = "📁"
            status_text = " Directory"
            color = AbyssalTheme.TEXT
        else:
            icon = "✅"
            status_text = " Staged"
            color = AbyssalTheme.TEXT

        self.setText(0, f"{icon}  {file_path}{status_text}")
        self.setToolTip(0, file_path)
        self.setForeground(0, QBrush(QColor(color)))

    def get_status(self) -> dict:
        return self.status_data

    def set_diff_text(self, diff_text: str):
        self._diff = diff_text
        self.setToolTip(0, f"{self.status_data['path']}\n\n{diff_text}")


class GitDiffView(QTextEdit):
    def __init__(self):
        super().__init__()
        self.setReadOnly(True)
        self.setFont(QFont("JetBrains Mono", 10))
        self.setStyleSheet(f"""
            QTextEdit {{
                background-color: {AbyssalTheme.BG};
                color: {AbyssalTheme.TEXT};
                border: none;
                padding: 10px;
            }}
            QScrollBar:vertical {{
                background: {AbyssalTheme.PANEL};
                width: 10px;
                margin: 0;
            }}
            QScrollBar::handle:vertical {{
                background: {AbyssalTheme.SCROLLBAR_HANDLE};
                min-height: 30px;
                border-radius: 5px;
            }}
        """)

    def set_diff(self, diff_text: str, file_path: str = ""):
        self.clear()
        self.append(f"=== {file_path} ===\n")
        self.append(diff_text)


class GitLogEntry(QTreeWidgetItem):
    def __init__(self, commit: dict, parent=None):
        super().__init__(parent)
        self.commit_data = commit
        short_hash = commit['hash'][:7]
        author = commit['author']
        date = commit['date']
        message = commit['message']

        self.setText(0, f"{short_hash}  {author}  {date}")
        self.setText(1, message)
        self.setToolTip(1, message)
        self.setToolTip(0, f"Author: {author}\nEmail: {commit['email']}\n\nFull Hash: {commit['hash']}\n\nMessage: {message}")

    def get_commit(self) -> dict:
        return self.commit_data


class GitBranchItem(QTreeWidgetItem):
    def __init__(self, branch: dict, parent=None):
        super().__init__(parent)
        self.branch_data = branch
        name = branch['name']
        is_current = branch['current']
        hash = branch['hash'][:7]
        ahead = branch['ahead']
        behind = branch['behind']

        if is_current:
            icon = "★"
            color = AbyssalTheme.ACCENT
            name = f" {name} ← current"
        elif ahead > 0 and behind > 0:
            icon = "↔"
            color = AbyssalTheme.BLUE
        elif ahead > 0:
            icon = "↑"
            color = AbyssalTheme.GREEN
        elif behind > 0:
            icon = "↓"
            color = AbyssalTheme.YELLOW
        else:
            icon = "○"
            color = AbyssalTheme.TEXT_DIM

        self.setText(0, f"  {icon}  {name}")
        self.setText(1, hash)
        self.setForeground(0, QBrush(QColor(color)))
        self.setToolTip(0, f"Branch: {branch['name']}\nHash: {branch['hash']}\nAhead: {branch['ahead']}\nBehind: {branch['behind']}\nRemote: {branch['remote']}")

    def get_branch(self) -> dict:
        return self.branch_data


class GitStatusPanel(QWidget):
    status_changed = Signal()

    def __init__(self, git_repo_path: str, parent=None):
        super().__init__(parent)
        self.git_repo_path = git_repo_path
        self._status_items = []
        self._setup_ui()
        self._refresh_status()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Toolbar
        toolbar = QWidget()
        toolbar.setFixedHeight(36)
        toolbar.setStyleSheet(f"background-color: {AbyssalTheme.PANEL_ALT}; border-bottom: 1px solid {AbyssalTheme.BORDER};")
        toolbar_layout = QHBoxLayout(toolbar)
        toolbar_layout.setContentsMargins(8, 4, 8, 4)

        self.refresh_btn = self._create_button("🔄", "Refresh Status")
        self.refresh_btn.clicked.connect(self._refresh_status)
        toolbar_layout.addWidget(self.refresh_btn)

        toolbar_layout.addStretch()

        toolbar_layout.addWidget(QLabel(" Git Status"))
        toolbar_layout.setAlignment(QLabel, Qt.AlignRight)

        layout.addWidget(toolbar)

        # Status tree
        self.status_tree = QTreeWidget()
        self.status_tree.setHeaderLabels(["", "File"])
        self.status_tree.setColumnWidth(0, 40)
        self.status_tree.setColumnWidth(1, 300)
        self.status_tree.setStyleSheet(f"""
            QTreeWidget {{
                background-color: {AbyssalTheme.PANEL};
                color: {AbyssalTheme.TEXT};
                border: none;
                outline: none;
            }}
            QTreeWidget::item {{
                padding: 4px 8px;
                border-bottom: 1px solid {AbyssalTheme.BORDER};
                min-height: 24px;
            }}
            QTreeWidget::item:selected {{
                background-color: {AbyssalTheme.SELECTION};
            }}
        """)
        self.status_tree.itemClicked.connect(self._on_status_click)
        layout.addWidget(self.status_tree)

        # Actions
        actions = QWidget()
        actions.setFixedHeight(50)
        actions.setStyleSheet(f"background-color: {AbyssalTheme.PANEL_ALT}; border-top: 1px solid {AbyssalTheme.BORDER};")
        actions_layout = QHBoxLayout(actions)
        actions_layout.setContentsMargins(8, 8, 8, 8)
        actions_layout.setSpacing(8)

        self.stage_all_btn = self._create_button("Stage All", "Stage all changes")
        self.stage_all_btn.clicked.connect(self._stage_all)
        actions_layout.addWidget(self.stage_all_btn)

        self.unstage_all_btn = self._create_button("Unstage All", "Unstage all changes")
        self.unstage_all_btn.clicked.connect(self._unstage_all)
        actions_layout.addWidget(self.unstage_all_btn)

        self.discard_all_btn = self._create_button("Discard", "Discard all changes")
        self.discard_all_btn.clicked.connect(self._discard_all)
        self.discard_all_btn.setStyleSheet(self._destructive_button_style())
        actions_layout.addWidget(self.discard_all_btn)

        actions_layout.addStretch()

        layout.addWidget(actions)

        # Status label
        self.status_label = QLabel("Ready")
        self.status_label.setFixedHeight(24)
        self.status_label.setStyleSheet(f"""
            background-color: {AbyssalTheme.PANEL_ALT};
            color: {AbyssalTheme.TEXT_DIM};
            padding: 0 8px;
            font-size: 10px;
            border-top: 1px solid {AbyssalTheme.BORDER};
        """)
        layout.addWidget(self.status_label)

    def _create_button(self, text: str, tooltip: str) -> QPushButton:
        btn = QPushButton(text)
        btn.setToolTip(tooltip)
        btn.setFixedHeight(30)
        btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {AbyssalTheme.PANEL};
                color: {AbyssalTheme.TEXT};
                border: 1px solid {AbyssalTheme.BORDER};
                border-radius: 3px;
                padding: 4px 12px;
                font-size: 10px;
                font-weight: bold;
            }}
            QPushButton:hover {{ background-color: {AbyssalTheme.PANEL_HOVER}; }}
            QPushButton:pressed {{ background-color: {AbyssalTheme.PANEL_ACTIVE}; }}
        """)
        return btn

    def _destructive_button_style(self) -> str:
        return f"""
            QPushButton {{
                background-color: {AbyssalTheme.CORAL};
                color: {AbyssalTheme.BG};
                border: 1px solid {AbyssalTheme.CORAL};
                border-radius: 3px;
                padding: 4px 12px;
                font-size: 10px;
                font-weight: bold;
            }}
            QPushButton:hover {{ background-color: #FF8A65; }}
        """

    def _run_command(self, command: list[str]) -> tuple[str, int]:
        try:
            result = subprocess.run(
                command,
                cwd=self.git_repo_path,
                capture_output=True,
                text=True,
                check=False
            )
            return result.stdout.strip(), result.stderr.strip()
        except Exception as e:
            return "", f"Error: {e!s}"

    def _refresh_status(self):
        self.status_tree.clear()
        self.status_label.setText("Loading git status...")
        
        stdout, stderr = self._run_command(["git", "status", "--porcelain"])
        
        if stderr:
            QMessageBox.warning(self, "Git Error", stderr)
            self.status_label.setText(f"Error: {stderr}")
            return

        lines = stdout.split('\n')
        folders = set()
        for line in lines:
            if not line:
                continue
            
            index_status = line[0]
            worktree_status = line[1] if len(line) > 1 else " "
            status_code = worktree_status if worktree_status != " " else index_status
            file_path = line[3:].strip() if len(line) > 3 else line[1:].strip()
            is_dir = os.path.isdir(os.path.join(self.git_repo_path, file_path)) and not file_path.endswith('.py')

            entry = {
                'path': file_path,
                'status': status_code,
                'staged': index_status not in (' ', '?'),
                'unstaged': worktree_status not in (' ', '?'),
                'is_dir': is_dir,
            }
            
            if is_dir:
                folders.add(file_path)
            elif '\n' in file_path or '\r' in file_path:
                continue
            
            self._status_items.append(entry)

        for folder in sorted(folders):
            item = GitStatusItem({
                'path': folder,
                'staged': False,
                'unstaged': False,
                'is_dir': True
            }, self.status_tree)
            self.status_tree.addTopLevelItem(item)

        for entry in sorted(self._status_items, key=lambda x: x['path']):
            if not entry['is_dir']:
                item = GitStatusItem(entry, self.status_tree)
                self.status_tree.addTopLevelItem(item)

        self.status_label.setText(f"{len(self._status_items)} changes")
        self.status_changed.emit()

    def _stage_all(self):
        stdout, stderr = self._run_command(["git", "add", "."])
        if stderr:
            QMessageBox.warning(self, "Stage Error", stderr)
        else:
            self._refresh_status()
            self.status_label.setText("All changes staged")

    def _unstage_all(self):
        stdout, stderr = self._run_command(["git", "reset"])
        if stderr:
            QMessageBox.warning(self, "Unstage Error", stderr)
        else:
            self._refresh_status()
            self.status_label.setText("All changes unstaged")

    def _discard_all(self):
        reply = QMessageBox.question(
            self, "Discard Changes",
            "This will permanently discard all unstaged changes. Continue?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            stdout, stderr = self._run_command(["git", "checkout", "--"])
            if stderr:
                QMessageBox.warning(self, "Discard Error", stderr)
            else:
                self._refresh_status()
                self.status_label.setText("All changes discarded")

    def _on_status_click(self, item: GitStatusItem):
        if item.status_data.get('is_dir', False):
            return
        
        file_path = item.status_data['path']
        stdout, stderr = self._run_command(["git", "diff", "--cached", file_path])
        if stderr:
            QMessageBox.warning(self, "Diff Error", stderr)
            return
        
        item.set_diff_text(stdout)
        self.status_label.setText(f"Diff: {os.path.basename(file_path)}")


class GitLogPanel(QWidget):
    def __init__(self, git_repo_path: str, parent=None):
        super().__init__(parent)
        self.git_repo_path = git_repo_path
        self._commits = []
        self._setup_ui()
        self._refresh_log()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Toolbar
        toolbar = QWidget()
        toolbar.setFixedHeight(36)
        toolbar.setStyleSheet(f"background-color: {AbyssalTheme.PANEL_ALT}; border-bottom: 1px solid {AbyssalTheme.BORDER};")
        toolbar_layout = QHBoxLayout(toolbar)
        toolbar_layout.setContentsMargins(8, 4, 8, 4)

        title = QLabel(" Git Log")
        title.setStyleSheet(f"color: {AbyssalTheme.TEXT_DIM}; font-size: 11px; font-weight: bold;")
        toolbar_layout.addWidget(title)

        toolbar_layout.addStretch()

        self.refresh_btn = self._create_button("🔄", "Refresh Log")
        self.refresh_btn.clicked.connect(self._refresh_log)
        toolbar_layout.addWidget(self.refresh_btn)

        layout.addWidget(toolbar)

        # Search
        search_layout = QHBoxLayout()
        search_layout.setContentsMargins(8, 4, 8, 4)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search commits...")
        self.search_input.setStyleSheet(f"""
            QLineEdit {{
                background-color: {AbyssalTheme.BG};
                color: {AbyssalTheme.TEXT};
                border: 1px solid {AbyssalTheme.BORDER};
                border-radius: 3px;
                padding: 4px 8px;
                font-size: 11px;
            }}
            QLineEdit:focus {{ border-color: {AbyssalTheme.ACCENT}; }}
        """)
        self.search_input.textChanged.connect(self._filter_log)
        search_layout.addWidget(self.search_input)

        layout.addLayout(search_layout)

        # Log tree
        self.log_tree = QTreeWidget()
        self.log_tree.setHeaderLabels(["Hash", "Message"])
        self.log_tree.setColumnWidth(0, 100)
        self.log_tree.setStyleSheet(f"""
            QTreeWidget {{
                background-color: {AbyssalTheme.PANEL};
                color: {AbyssalTheme.TEXT};
                border: none;
                outline: none;
            }}
            QTreeWidget::item {{
                padding: 4px 8px;
                border-bottom: 1px solid {AbyssalTheme.BORDER};
                min-height: 24px;
            }}
            QTreeWidget::item:selected {{
                background-color: {AbyssalTheme.SELECTION};
            }}
        """)
        layout.addWidget(self.log_tree)

        # Actions
        actions = QWidget()
        actions.setFixedHeight(50)
        actions.setStyleSheet(f"background-color: {AbyssalTheme.PANEL_ALT}; border-top: 1px solid {AbyssalTheme.BORDER};")
        actions_layout = QHBoxLayout(actions)
        actions_layout.setContentsMargins(8, 8, 8, 8)
        actions_layout.setSpacing(8)

        self.reset_btn = self._create_button("Reset", "Reset to commit")
        self.reset_btn.clicked.connect(self._reset_to_commit)
        actions_layout.addWidget(self.reset_btn)

        self.reset_soft_btn = self._create_button("Reset Soft", "Soft reset")
        self.reset_soft_btn.clicked.connect(self._reset_soft)
        actions_layout.addWidget(self.reset_soft_btn)

        actions_layout.addStretch()

        layout.addWidget(actions)

        # Status label
        self.status_label = QLabel("Ready")
        self.status_label.setFixedHeight(24)
        self.status_label.setStyleSheet(f"""
            background-color: {AbyssalTheme.PANEL_ALT};
            color: {AbyssalTheme.TEXT_DIM};
            padding: 0 8px;
            font-size: 10px;
            border-top: 1px solid {AbyssalTheme.BORDER};
        """)
        layout.addWidget(self.status_label)

    def _create_button(self, text: str, tooltip: str) -> QPushButton:
        btn = QPushButton(text)
        btn.setToolTip(tooltip)
        btn.setFixedHeight(30)
        btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {AbyssalTheme.PANEL};
                color: {AbyssalTheme.TEXT};
                border: 1px solid {AbyssalTheme.BORDER};
                border-radius: 3px;
                padding: 4px 12px;
                font-size: 10px;
                font-weight: bold;
            }}
            QPushButton:hover {{ background-color: {AbyssalTheme.PANEL_HOVER}; }}
            QPushButton:pressed {{ background-color: {AbyssalTheme.PANEL_ACTIVE}; }}
        """)
        return btn

    def _run_command(self, command: list[str]) -> tuple[str, int]:
        try:
            result = subprocess.run(
                command,
                cwd=self.git_repo_path,
                capture_output=True,
                text=True,
                check=False
            )
            return result.stdout.strip(), result.stderr.strip()
        except Exception as e:
            return "", f"Error: {e!s}"

    def _refresh_log(self):
        self.log_tree.clear()
        self.status_label.setText("Loading git log...")
        
        stdout, stderr = self._run_command(["git", "log", "--oneline", "--graph", "--decorate", "--all", "--date=short", "--pretty=format:%H|%an|%ad|%s"])
        
        if stderr:
            QMessageBox.warning(self, "Git Error", stderr)
            self.status_label.setText(f"Error: {stderr}")
            return

        lines = stdout.split('\n')
        for line in lines:
            if not line:
                continue
            
            parts = line.split('|', 3)
            if len(parts) < 4:
                continue
            
            commit = {
                'hash': parts[0],
                'author': parts[1],
                'date': parts[2],
                'message': parts[3]
            }
            self._commits.append(commit)

        for commit in sorted(self._commits, key=lambda x: x['hash'], reverse=True)[:100]:
            email = ""
            stdout, stderr = self._run_command(["git", "log", "--format=%e", "-1", commit['hash']])
            if stdout:
                email = stdout.strip()
            
            commit['email'] = email
            item = GitLogEntry(commit, self.log_tree)
            self.log_tree.addTopLevelItem(item)

        self.status_label.setText(f"{len(self._commits)} commits")

    def _filter_log(self, text: str):
        if not text:
            for i in range(self.log_tree.topLevelItemCount()):
                self.log_tree.topLevelItem(i).setHidden(False)
        else:
            text = text.lower()
            for i in range(self.log_tree.topLevelItemCount()):
                item = self.log_tree.topLevelItem(i)
                commit = item.get_commit()
                hide = (
                    text not in commit['hash'].lower() and
                    text not in commit['author'].lower() and
                    text not in commit['message'].lower()
                )
                item.setHidden(hide)

    def _reset_to_commit(self):
        item = self.log_tree.currentItem()
        if not item:
            QMessageBox.warning(self, "Warning", "Please select a commit first")
            return
        
        commit = item.get_commit()
        reply = QMessageBox.question(
            self, "Reset to Commit",
            f"Reset HEAD to {commit['hash'][:7]}? This will permanently discard commits after this point.",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            stdout, stderr = self._run_command(["git", "reset", "--hard", commit['hash']])
            if stderr:
                QMessageBox.warning(self, "Reset Error", stderr)
            else:
                self._refresh_log()
                self.status_label.setText(f"Reset to {commit['hash'][:7]}")

    def _reset_soft(self):
        item = self.log_tree.currentItem()
        if not item:
            QMessageBox.warning(self, "Warning", "Please select a commit first")
            return
        
        commit = item.get_commit()
        reply = QMessageBox.question(
            self, "Reset Soft",
            f"Soft reset HEAD to {commit['hash'][:7]}? This will undo commits but keep changes.",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            stdout, stderr = self._run_command(["git", "reset", "--soft", commit['hash']])
            if stderr:
                QMessageBox.warning(self, "Reset Error", stderr)
            else:
                self._refresh_log()
                self.status_label.setText(f"Soft reset to {commit['hash'][:7]}")


class GitBranchPanel(QWidget):
    def __init__(self, git_repo_path: str, parent=None):
        super().__init__(parent)
        self.git_repo_path = git_repo_path
        self._branches = []
        self._setup_ui()
        self._refresh_branches()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Toolbar
        toolbar = QWidget()
        toolbar.setFixedHeight(36)
        toolbar.setStyleSheet(f"background-color: {AbyssalTheme.PANEL_ALT}; border-bottom: 1px solid {AbyssalTheme.BORDER};")
        toolbar_layout = QHBoxLayout(toolbar)
        toolbar_layout.setContentsMargins(8, 4, 8, 4)

        title = QLabel(" Git Branches")
        title.setStyleSheet(f"color: {AbyssalTheme.TEXT_DIM}; font-size: 11px; font-weight: bold;")
        toolbar_layout.addWidget(title)

        toolbar_layout.addStretch()

        self.refresh_btn = self._create_button("🔄", "Refresh Branches")
        self.refresh_btn.clicked.connect(self._refresh_branches)
        toolbar_layout.addWidget(self.refresh_btn)

        layout.addWidget(toolbar)

        # Create branch
        create_widget = QWidget()
        create_widget.setFixedHeight(40)
        create_widget.setStyleSheet(f"background-color: {AbyssalTheme.PANEL_ALT};")
        create_layout = QHBoxLayout(create_widget)
        create_layout.setContentsMargins(8, 4, 8, 4)

        self.new_branch_input = QLineEdit()
        self.new_branch_input.setPlaceholderText("New branch name...")
        self.new_branch_input.setStyleSheet(f"""
            QLineEdit {{
                background-color: {AbyssalTheme.BG};
                color: {AbyssalTheme.TEXT};
                border: 1px solid {AbyssalTheme.BORDER};
                border-radius: 3px;
                padding: 4px 8px;
                font-size: 10px;
            }}
        """)
        create_layout.addWidget(self.new_branch_input)

        self.new_branch_btn = self._create_button("Create", "Create new branch")
        self.new_branch_btn.clicked.connect(self._create_branch)
        create_layout.addWidget(self.new_branch_btn)

        layout.addWidget(create_widget)

        # Branch tree
        self.branch_tree = QTreeWidget()
        self.branch_tree.setHeaderLabels(["Branch", "Hash"])
        self.branch_tree.setColumnWidth(0, 150)
        self.branch_tree.setStyleSheet(f"""
            QTreeWidget {{
                background-color: {AbyssalTheme.PANEL};
                color: {AbyssalTheme.TEXT};
                border: none;
                outline: none;
            }}
            QTreeWidget::item {{
                padding: 4px 8px;
                border-bottom: 1px solid {AbyssalTheme.BORDER};
                min-height: 24px;
            }}
            QTreeWidget::item:selected {{
                background-color: {AbyssalTheme.SELECTION};
            }}
        """)
        layout.addWidget(self.branch_tree)

        # Actions
        actions = QWidget()
        actions.setFixedHeight(50)
        actions.setStyleSheet(f"background-color: {AbyssalTheme.PANEL_ALT}; border-top: 1px solid {AbyssalTheme.BORDER};")
        actions_layout = QHBoxLayout(actions)
        actions_layout.setContentsMargins(8, 8, 8, 8)
        actions_layout.setSpacing(8)

        self.merge_btn = self._create_button("Merge", "Merge branch")
        self.merge_btn.clicked.connect(self._merge_branch)
        actions_layout.addWidget(self.merge_btn)

        self.delete_btn = self._create_button("Delete", "Delete branch")
        self.delete_btn.setStyleSheet(self._destructive_button_style())
        self.delete_btn.clicked.connect(self._delete_branch)
        actions_layout.addWidget(self.delete_btn)

        actions_layout.addStretch()

        layout.addWidget(actions)

        # Status label
        self.status_label = QLabel("Ready")
        self.status_label.setFixedHeight(24)
        self.status_label.setStyleSheet(f"""
            background-color: {AbyssalTheme.PANEL_ALT};
            color: {AbyssalTheme.TEXT_DIM};
            padding: 0 8px;
            font-size: 10px;
            border-top: 1px solid {AbyssalTheme.BORDER};
        """)
        layout.addWidget(self.status_label)

    def _create_button(self, text: str, tooltip: str) -> QPushButton:
        btn = QPushButton(text)
        btn.setToolTip(tooltip)
        btn.setFixedHeight(30)
        btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {AbyssalTheme.PANEL};
                color: {AbyssalTheme.TEXT};
                border: 1px solid {AbyssalTheme.BORDER};
                border-radius: 3px;
                padding: 4px 12px;
                font-size: 10px;
                font-weight: bold;
            }}
            QPushButton:hover {{ background-color: {AbyssalTheme.PANEL_HOVER}; }}
            QPushButton:pressed {{ background-color: {AbyssalTheme.PANEL_ACTIVE}; }}
        """)
        return btn

    def _destructive_button_style(self) -> str:
        return f"""
            QPushButton {{
                background-color: {AbyssalTheme.CORAL};
                color: {AbyssalTheme.BG};
                border: 1px solid {AbyssalTheme.CORAL};
                border-radius: 3px;
                padding: 4px 12px;
                font-size: 10px;
                font-weight: bold;
            }}
            QPushButton:hover {{ background-color: #FF8A65; }}
        """

    def _run_command(self, command: list[str]) -> tuple[str, int]:
        try:
            result = subprocess.run(
                command,
                cwd=self.git_repo_path,
                capture_output=True,
                text=True,
                check=False
            )
            return result.stdout.strip(), result.stderr.strip()
        except Exception as e:
            return "", f"Error: {e!s}"

    def _refresh_branches(self):
        self.branch_tree.clear()
        self.status_label.setText("Loading branches...")
        
        stdout, stderr = self._run_command(["git", "branch", "-a", "--contains", "HEAD"])
        
        if stderr:
            QMessageBox.warning(self, "Git Error", stderr)
            self.status_label.setText(f"Error: {stderr}")
            return

        current_line = None
        for line in stdout.split('\n'):
            if not line:
                continue
            
            is_current = line.startswith("*")
            branch_name = line.replace("* ", "").strip()
            
            if is_current:
                current_line = branch_name
                continue
            
            branch_info = {
                'name': branch_name,
                'current': False,
                'hash': "",
                'ahead': 0,
                'behind': 0,
                'remote': branch_name.startswith("origin/"),
            }
            
            stdout_hash, _ = self._run_command(["git", "rev-parse", branch_name])
            if stdout_hash:
                branch_info['hash'] = stdout_hash.strip()
            
            self._branches.append(branch_info)

        for branch in self._branches:
            item = GitBranchItem(branch, self.branch_tree)
            self.branch_tree.addTopLevelItem(item)

        if current_line:
            for i in range(self.branch_tree.topLevelItemCount()):
                item = self.branch_tree.topLevelItem(i)
                if item.branch_data['name'] == current_line:
                    item.setSelected(True)
                    break

        self.status_label.setText(f"{len(self._branches)} branches")

    def _create_branch(self):
        branch_name = self.new_branch_input.text().strip()
        if not branch_name:
            QMessageBox.warning(self, "Warning", "Please enter a branch name")
            return

        stdout, stderr = self._run_command(["git", "branch", branch_name])
        if stderr:
            QMessageBox.warning(self, "Create Error", stderr)
        else:
            self._refresh_branches()
            self.new_branch_input.clear()
            self.status_label.setText(f"Created branch: {branch_name}")

    def _merge_branch(self):
        item = self.branch_tree.currentItem()
        if not item:
            QMessageBox.warning(self, "Warning", "Please select a branch first")
            return
        
        branch = item.get_branch()
        if branch['current']:
            QMessageBox.warning(self, "Warning", "Cannot merge current branch")
            return
        
        reply = QMessageBox.question(
            self, "Merge Branch",
            f"Merge {branch['name']} into current branch?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            stdout, stderr = self._run_command(["git", "merge", branch['name']])
            if stderr:
                QMessageBox.warning(self, "Merge Error", stderr)
            else:
                self._refresh_branches()
                self.status_label.setText(f"Merged {branch['name']}")

    def _delete_branch(self):
        item = self.branch_tree.currentItem()
        if not item:
            QMessageBox.warning(self, "Warning", "Please select a branch first")
            return
        
        branch = item.get_branch()
        if branch['current']:
            QMessageBox.warning(self, "Warning", "Cannot delete current branch")
            return
        
        reply = QMessageBox.question(
            self, "Delete Branch",
            f"Permanently delete branch {branch['name']}?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            stdout, stderr = self._run_command(["git", "branch", "-d", branch['name']])
            if stderr:
                QMessageBox.warning(self, "Delete Error", stderr)
            else:
                self._refresh_branches()
                self.status_label.setText(f"Deleted branch: {branch['name']}")


class GitDiffPanel(QWidget):
    def __init__(self, git_repo_path: str, parent=None):
        super().__init__(parent)
        self.git_repo_path = git_repo_path
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Toolbar
        toolbar = QWidget()
        toolbar.setFixedHeight(36)
        toolbar.setStyleSheet(f"background-color: {AbyssalTheme.PANEL_ALT}; border-bottom: 1px solid {AbyssalTheme.BORDER};")
        toolbar_layout = QHBoxLayout(toolbar)
        toolbar_layout.setContentsMargins(8, 4, 8, 4)

        title = QLabel(" Git Diff")
        title.setStyleSheet(f"color: {AbyssalTheme.TEXT_DIM}; font-size: 11px; font-weight: bold;")
        toolbar_layout.addWidget(title)

        toolbar_layout.addStretch()

        self.refresh_btn = self._create_button("🔄", "Refresh Diff")
        self.refresh_btn.clicked.connect(self._refresh_diff)
        toolbar_layout.addWidget(self.refresh_btn)

        layout.addWidget(toolbar)

        # Diff splitter
        splitter = QSplitter(Qt.Vertical)
        splitter.setHandleWidth(1)

        self.status_tree = QTreeWidget()
        self.status_tree.setHeaderLabels(["", "File"])
        self.status_tree.setColumnWidth(0, 40)
        self.status_tree.setColumnWidth(1, 300)
        self.status_tree.setStyleSheet(f"""
            QTreeWidget {{
                background-color: {AbyssalTheme.PANEL};
                color: {AbyssalTheme.TEXT};
                border: none;
                outline: none;
            }}
            QTreeWidget::item {{
                padding: 4px 8px;
                border-bottom: 1px solid {AbyssalTheme.BORDER};
                min-height: 24px;
            }}
            QTreeWidget::item:selected {{
                background-color: {AbyssalTheme.SELECTION};
            }}
        """)
        self.status_tree.itemClicked.connect(self._on_status_click)

        self.diff_view = GitDiffView()

        splitter.addWidget(self.status_tree)
        splitter.addWidget(self.diff_view)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 2)

        layout.addWidget(splitter)

        # Actions
        actions = QWidget()
        actions.setFixedHeight(50)
        actions.setStyleSheet(f"background-color: {AbyssalTheme.PANEL_ALT}; border-top: 1px solid {AbyssalTheme.BORDER};")
        actions_layout = QHBoxLayout(actions)
        actions_layout.setContentsMargins(8, 8, 8, 8)
        actions_layout.setSpacing(8)

        self.stash_btn = self._create_button("Stash", "Stash changes")
        self.stash_btn.clicked.connect(self._stash_changes)
        actions_layout.addWidget(self.stash_btn)

        self.reapply_btn = self._create_button("Reapply", "Reapply stash")
        self.reapply_btn.clicked.connect(self._reapply_stash)
        actions_layout.addWidget(self.reapply_btn)

        actions_layout.addStretch()

        layout.addWidget(actions)

        # Status label
        self.status_label = QLabel("Ready")
        self.status_label.setFixedHeight(24)
        self.status_label.setStyleSheet(f"""
            background-color: {AbyssalTheme.PANEL_ALT};
            color: {AbyssalTheme.TEXT_DIM};
            padding: 0 8px;
            font-size: 10px;
            border-top: 1px solid {AbyssalTheme.BORDER};
        """)
        layout.addWidget(self.status_label)

        self._refresh_diff()

    def _create_button(self, text: str, tooltip: str) -> QPushButton:
        btn = QPushButton(text)
        btn.setToolTip(tooltip)
        btn.setFixedHeight(30)
        btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {AbyssalTheme.PANEL};
                color: {AbyssalTheme.TEXT};
                border: 1px solid {AbyssalTheme.BORDER};
                border-radius: 3px;
                padding: 4px 12px;
                font-size: 10px;
                font-weight: bold;
            }}
            QPushButton:hover {{ background-color: {AbyssalTheme.PANEL_HOVER}; }}
            QPushButton:pressed {{ background-color: {AbyssalTheme.PANEL_ACTIVE}; }}
        """)
        return btn

    def _run_command(self, command: list[str]) -> tuple[str, int]:
        try:
            result = subprocess.run(
                command,
                cwd=self.git_repo_path,
                capture_output=True,
                text=True,
                check=False
            )
            return result.stdout.strip(), result.stderr.strip()
        except Exception as e:
            return "", f"Error: {e!s}"

    def _refresh_diff(self):
        self.status_tree.clear()
        self.status_label.setText("Loading changes...")
        
        stdout, stderr = self._run_command(["git", "status", "--porcelain"])
        
        if stderr:
            QMessageBox.warning(self, "Git Error", stderr)
            self.status_label.setText(f"Error: {stderr}")
            return

        files = []
        for line in stdout.split('\n'):
            if not line:
                continue
            
            status_code = line[0]
            file_path = line[1:].strip()
            
            files.append({
                'path': file_path,
                'status': status_code,
            })

        for item in files:
            git_item = GitStatusItem(item, self.status_tree)
            self.status_tree.addTopLevelItem(git_item)

        self.status_label.setText(f"{len(files)} files with changes")

    def _on_status_click(self, item: GitStatusItem):
        file_path = item.status_data['path']
        status = item.status_data['status']
        
        if status in ' MADRCXU':
            diff_type = status
            stdout, stderr = self._run_command(["git", "diff", diff_type, file_path])
            if stderr:
                QMessageBox.warning(self, "Diff Error", stderr)
                return
        else:
            stdout, stderr = self._run_command(["git", "diff", file_path])
            if stderr:
                QMessageBox.warning(self, "Diff Error", stderr)
                return
        
        item.set_diff_text(stdout if stdout else "(no changes)")
        self.status_label.setText(f"Diff: {os.path.basename(file_path)}")

    def _stash_changes(self):
        name, ok = QInputDialog.getText(self, "Stash Name", "Stash name (optional):")
        
        if ok and name:
            stdout, stderr = self._run_command(["git", "stash", "push", "-m", name])
        else:
            stdout, stderr = self._run_command(["git", "stash", "push"])
        
        if stderr:
            QMessageBox.warning(self, "Stash Error", stderr)
        else:
            self._refresh_diff()
            self.status_label.setText("Stashed changes")

    def _reapply_stash(self):
        stdout, stderr = self._run_command(["git", "stash", "pop"])
        if stderr:
            QMessageBox.warning(self, "Stash Error", stderr)
        else:
            self._refresh_diff()
            self.status_label.setText("Reapplied stash")


class GitCommitDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Git Commit")
        self.setFixedWidth(500)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)

        # Message
        msg_label = QLabel("Commit Message:")
        msg_label.setStyleSheet(f"color: {AbyssalTheme.TEXT_DIM}; font-size: 10px;")
        layout.addWidget(msg_label)

        self.message_input = QTextEdit()
        self.message_input.setPlaceholderText("Enter commit message...")
        self.message_input.setStyleSheet(f"""
            QTextEdit {{
                background-color: {AbyssalTheme.BG};
                color: {AbyssalTheme.TEXT};
                border: 1px solid {AbyssalTheme.BORDER};
                border-radius: 3px;
                padding: 4px 8px;
                font-size: 10px;
            }}
        """)
        layout.addWidget(self.message_input)

        # Author
        author_label = QLabel("Author (optional):")
        author_label.setStyleSheet(f"color: {AbyssalTheme.TEXT_DIM}; font-size: 10px;")
        layout.addWidget(author_label)

        self.author_input = QLineEdit()
        self.author_input.setStyleSheet(f"""
            QLineEdit {{
                background-color: {AbyssalTheme.BG};
                color: {AbyssalTheme.TEXT};
                border: 1px solid {AbyssalTheme.BORDER};
                border-radius: 3px;
                padding: 4px 8px;
                font-size: 10px;
            }}
        """)
        layout.addWidget(self.author_input)

        # Co-author
        coauthor_label = QLabel("Co-author (optional):")
        coauthor_label.setStyleSheet(f"color: {AbyssalTheme.TEXT_DIM}; font-size: 10px;")
        layout.addWidget(coauthor_label)

        self.coauthor_input = QLineEdit()
        self.coauthor_input.setStyleSheet(f"""
            QLineEdit {{
                background-color: {AbyssalTheme.BG};
                color: {AbyssalTheme.TEXT};
                border: 1px solid {AbyssalTheme.BORDER};
                border-radius: 3px;
                padding: 4px 8px;
                font-size: 10px;
            }}
        """)
        layout.addWidget(self.coauthor_input)

        # Actions
        action_layout = QHBoxLayout()
        action_layout.setSpacing(8)

        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        cancel_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {AbyssalTheme.PANEL};
                color: {AbyssalTheme.TEXT};
                border: 1px solid {AbyssalTheme.BORDER};
                border-radius: 3px;
                padding: 4px 12px;
                font-size: 10px;
            }}
        """)
        action_layout.addWidget(cancel_btn)

        commit_btn = QPushButton("Commit")
        commit_btn.clicked.connect(self._commit)
        commit_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {AbyssalTheme.ACCENT};
                color: {AbyssalTheme.BG};
                border: 1px solid {AbyssalTheme.ACCENT};
                border-radius: 3px;
                padding: 4px 12px;
                font-size: 10px;
                font-weight: bold;
            }}
        """)
        action_layout.addWidget(commit_btn)

        layout.addLayout(action_layout)

    def _commit(self):
        message = self.message_input.toPlainText().strip()
        if not message:
            QMessageBox.warning(self, "Warning", "Please enter a commit message")
            return

        author = self.author_input.text().strip()
        coauthor = self.coauthor_input.text().strip()

        # Build commit args
        args = ["git", "commit", "-m", message]
        
        if author:
            args.extend(["--author", author])
        
        if coauthor:
            args.extend(["-c", coauthor])

        try:
            result = subprocess.run(
                args,
                cwd=self.parent().git_repo_path if hasattr(self.parent(), 'git_repo_path') else os.getcwd(),
                capture_output=True,
                text=True,
                check=False
            )
            
            if result.returncode == 0:
                self.accept()
            else:
                QMessageBox.warning(self, "Commit Error", result.stderr)
        except Exception as e:
            QMessageBox.warning(self, "Commit Error", str(e))


class GitPushDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Git Push")
        self.setFixedWidth(500)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)

        info_label = QLabel("Push changes to remote repository")
        info_label.setStyleSheet(f"color: {AbyssalTheme.TEXT_DIM}; font-size: 10px;")
        layout.addWidget(info_label)

        # Remote
        remote_label = QLabel("Remote (optional):")
        remote_label.setStyleSheet(f"color: {AbyssalTheme.TEXT_DIM}; font-size: 10px;")
        layout.addWidget(remote_label)

        self.remote_input = QLineEdit()
        self.remote_input.setStyleSheet(f"""
            QLineEdit {{
                background-color: {AbyssalTheme.BG};
                color: {AbyssalTheme.TEXT};
                border: 1px solid {AbyssalTheme.BORDER};
                border-radius: 3px;
                padding: 4px 8px;
                font-size: 10px;
            }}
        """)
        layout.addWidget(self.remote_input)

        # Branch
        branch_label = QLabel("Branch (optional):")
        branch_label.setStyleSheet(f"color: {AbyssalTheme.TEXT_DIM}; font-size: 10px;")
        layout.addWidget(branch_label)

        self.branch_input = QLineEdit()
        self.branch_input.setStyleSheet(f"""
            QLineEdit {{
                background-color: {AbyssalTheme.BG};
                color: {AbyssalTheme.TEXT};
                border: 1px solid {AbyssalTheme.BORDER};
                border-radius: 3px;
                padding: 4px 8px;
                font-size: 10px;
            }}
        """)
        layout.addWidget(self.branch_input)

        # Actions
        action_layout = QHBoxLayout()
        action_layout.setSpacing(8)

        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        cancel_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {AbyssalTheme.PANEL};
                color: {AbyssalTheme.TEXT};
                border: 1px solid {AbyssalTheme.BORDER};
                border-radius: 3px;
                padding: 4px 12px;
                font-size: 10px;
            }}
        """)
        action_layout.addWidget(cancel_btn)

        push_btn = QPushButton("Push")
        push_btn.clicked.connect(self._push)
        push_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {AbyssalTheme.BLUE};
                color: {AbyssalTheme.BG};
                border: 1px solid {AbyssalTheme.BLUE};
                border-radius: 3px;
                padding: 4px 12px;
                font-size: 10px;
                font-weight: bold;
            }}
        """)
        action_layout.addWidget(push_btn)

        layout.addLayout(action_layout)

    def _push(self):
        remote = self.remote_input.text().strip()
        branch = self.branch_input.text().strip()
        
        args = ["git", "push"]
        
        if remote:
            args.extend([remote])
        
        if branch:
            args.extend(["--set-upstream", branch])

        try:
            result = subprocess.run(
                args,
                cwd=self.parent().git_repo_path if hasattr(self.parent(), 'git_repo_path') else os.getcwd(),
                capture_output=True,
                text=True,
                check=False
            )
            
            if result.returncode == 0:
                self.accept()
            else:
                QMessageBox.warning(self, "Push Error", result.stderr)
        except Exception as e:
            QMessageBox.warning(self, "Push Error", str(e))


class GitIntegrationPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(f"background-color: {AbyssalTheme.BG};")
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.git_repo_path = self._find_git_repo()
        if self.git_repo_path:
            self._setup_ui()
        else:
            self._setup_no_repo_ui()

    def _find_git_repo(self) -> str | None:
        current = os.getcwd()
        while current != os.path.dirname(current):
            git_path = os.path.join(current, ".git")
            if os.path.exists(git_path):
                return current
            current = os.path.dirname(current)
        return None

    def _setup_no_repo_ui(self):
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)
        
        label = QLabel("Not a Git repository")
        label.setStyleSheet(f"color: {AbyssalTheme.TEXT_DIM}; font-size: 12px;")
        layout.addWidget(label)
        
        message = QLabel("Open a folder that contains a .git directory to use Git features.")
        message.setStyleSheet(f"color: {AbyssalTheme.TEXT_MUTED}; font-size: 10px;")
        layout.setAlignment(message, Qt.AlignCenter)
        layout.addWidget(message)

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.tab_widget = QTabWidget()
        self.tab_widget.setStyleSheet(f"""
            QTabWidget::pane {{
                border: none;
                background-color: {AbyssalTheme.BG};
            }}
            QTabWidget::tab-bar {{
                background-color: {AbyssalTheme.PANEL};
                height: 36px;
            }}
            QTabWidget::tab {{
                background-color: transparent;
                color: {AbyssalTheme.TEXT_DIM};
                padding: 8px 16px;
                font-size: 11px;
                font-weight: bold;
            }}
            QTabWidget::tab:selected {{
                background-color: {AbyssalTheme.PANEL_ACTIVE};
                color: {AbyssalTheme.TEXT};
                border-bottom: 2px solid {AbyssalTheme.ACCENT};
            }}
            QTabWidget::tab:hover {{
                background-color: {AbyssalTheme.PANEL_HOVER};
            }}
        """)

        self.status_panel = GitStatusPanel(self.git_repo_path)
        self.log_panel = GitLogPanel(self.git_repo_path)
        self.branch_panel = GitBranchPanel(self.git_repo_path)
        self.diff_panel = GitDiffPanel(self.git_repo_path)

        self.tab_widget.addTab(self.status_panel, "Status")
        self.tab_widget.addTab(self.log_panel, "Log")
        self.tab_widget.addTab(self.branch_panel, "Branch")
        self.tab_widget.addTab(self.diff_panel, "Diff")

        layout.addWidget(self.tab_widget)

        # Actions bar
        actions_widget = QWidget()
        actions_widget.setFixedHeight(50)
        actions_widget.setStyleSheet(f"background-color: {AbyssalTheme.PANEL}; border-top: 1px solid {AbyssalTheme.BORDER};")
        actions_layout = QHBoxLayout(actions_widget)
        actions_layout.setContentsMargins(8, 8, 8, 8)
        actions_layout.setSpacing(8)

        self.commit_btn = self._create_button("✓ Commit", "Commit changes")
        self.commit_btn.clicked.connect(self._show_commit_dialog)
        actions_layout.addWidget(self.commit_btn)

        self.push_btn = self._create_button("↑ Push", "Push changes")
        self.push_btn.clicked.connect(self._show_push_dialog)
        actions_layout.addWidget(self.push_btn)

        self.fetch_btn = self._create_button("⬇ Fetch", "Fetch updates")
        self.fetch_btn.clicked.connect(self._fetch)
        actions_layout.addWidget(self.fetch_btn)

        self.pull_btn = self._create_button("⬍ Pull", "Pull updates")
        self.pull_btn.clicked.connect(self._pull)
        actions_layout.addWidget(self.pull_btn)

        actions_layout.addStretch()

        layout.addWidget(actions_widget)

    def _create_button(self, text: str, tooltip: str) -> QPushButton:
        btn = QPushButton(text)
        btn.setToolTip(tooltip)
        btn.setFixedHeight(36)
        btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {AbyssalTheme.PANEL};
                color: {AbyssalTheme.TEXT};
                border: 1px solid {AbyssalTheme.BORDER};
                border-radius: 3px;
                padding: 4px 12px;
                font-size: 10px;
                font-weight: bold;
            }}
            QPushButton:hover {{ background-color: {AbyssalTheme.PANEL_HOVER}; }}
            QPushButton:pressed {{ background-color: {AbyssalTheme.PANEL_ACTIVE}; }}
        """)
        return btn

    def _setup_no_repo_ui(self):
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)
        
        label = QLabel("Not a Git repository")
        label.setStyleSheet(f"color: {AbyssalTheme.TEXT_DIM}; font-size: 12px;")
        layout.addWidget(label)
        
        message = QLabel("Open a folder that contains a .git directory to use Git features.")
        message.setStyleSheet(f"color: {AbyssalTheme.TEXT_MUTED}; font-size: 10px;")
        layout.setAlignment(message, Qt.AlignCenter)
        layout.addWidget(message)

    def _show_commit_dialog(self):
        if not self.git_repo_path:
            return
        
        dialog = GitCommitDialog(self)
        if dialog.exec() == QDialog.Accepted:
            self._refresh_tabs()

    def _show_push_dialog(self):
        if not self.git_repo_path:
            return
        
        dialog = GitPushDialog(self)
        if dialog.exec() == QDialog.Accepted:
            self._refresh_tabs()

    def _fetch(self):
        stdout, stderr = self._run_command(["git", "fetch", "--all"])
        if stderr:
            QMessageBox.warning(self, "Fetch Error", stderr)
        else:
            QMessageBox.information(self, "Fetch", "Fetch completed")
            self._refresh_tabs()

    def _pull(self):
        reply = QMessageBox.question(
            self, "Pull Changes",
            "This will overwrite local changes with remote changes. Continue?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            stdout, stderr = self._run_command(["git", "pull", "--rebase"])
            if stderr:
                QMessageBox.warning(self, "Pull Error", stderr)
            else:
                self._refresh_tabs()

    def _run_command(self, command: list[str]) -> tuple[str, int]:
        try:
            result = subprocess.run(
                command,
                cwd=self.git_repo_path,
                capture_output=True,
                text=True,
                check=False
            )
            return result.stdout.strip(), result.stderr.strip()
        except Exception as e:
            return "", f"Error: {e!s}"

    def _refresh_tabs(self):
        if hasattr(self, 'status_panel'):
            self.status_panel._refresh_status()
        if hasattr(self, 'log_panel'):
            self.log_panel._refresh_log()
        if hasattr(self, 'branch_panel'):
            self.branch_panel._refresh_branches()
        if hasattr(self, 'diff_panel'):
            self.diff_panel._refresh_diff()


if __name__ == "__main__":
    import sys

    from PySide6.QtWidgets import QApplication
    
    app = QApplication(sys.argv)
    window = QWidget()
    window.resize(800, 600)
    window.setWindowTitle("Git Integration Panel")
    
    git_panel = GitIntegrationPanel()
    layout = QVBoxLayout(window)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.addWidget(git_panel)
    
    window.show()
    sys.exit(app.exec())
