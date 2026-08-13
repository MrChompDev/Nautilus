"""Reef Messenger — local-first mail + chat for Nautilus OS.

Everything works offline against a local store; IMAP/SMTP accounts are an
optional layer. Threads do network I/O; the UI is never blocked.
"""

import os
import sys
import time

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, PROJECT_ROOT)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PySide6.QtCore import Qt, QThread, Signal  # noqa: E402
from PySide6.QtWidgets import (  # noqa: E402
    QApplication,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QSplitter,
    QTextBrowser,
    QVBoxLayout,
    QWidget,
)

from apps.Reef.engine import Account, MailStore, Message, fetch_inbox, send_mail  # noqa: E402
from core.qt_env import setup_qt_environment  # noqa: E402
from core.theme import COLORS, FONTS, SPACING  # noqa: E402

LOCAL_FOLDER = ("Local", "local")


class RefreshWorker(QThread):
    """Fetch an account's inbox off the UI thread."""

    finished_ok = Signal(list)
    failed = Signal(str)

    def __init__(self, account, limit=50, parent=None):
        super().__init__(parent)
        self._account = account
        self._limit = limit

    def run(self):
        try:
            messages = fetch_inbox(self._account, limit=self._limit)
            self.finished_ok.emit(messages)
        except Exception as e:  # noqa: BLE001
            self.failed.emit(str(e))


class SendWorker(QThread):
    """Send via SMTP off the UI thread."""

    sent = Signal(str, str, str)
    failed = Signal(str)

    def __init__(self, account, to, subject, body, parent=None):
        super().__init__(parent)
        self._account = account
        self._to = to
        self._subject = subject
        self._body = body

    def run(self):
        try:
            send_mail(self._account, self._to, self._subject, self._body)
            self.sent.emit(self._to, self._subject, self._body)
        except Exception as e:  # noqa: BLE001
            self.failed.emit(str(e))


class ComposeDialog(QDialog):
    def __init__(self, title="Compose", show_to=True, parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setMinimumSize(520, 420)

        layout = QVBoxLayout(self)
        layout.setSpacing(SPACING["md"])

        form = QFormLayout()
        form.setSpacing(SPACING["md"])
        self.to_edit = QLineEdit()
        self.subject_edit = QLineEdit()
        if show_to:
            form.addRow("To", self.to_edit)
        form.addRow("Subject", self.subject_edit)
        layout.addLayout(form)

        self.body_edit = QPlainTextEdit()
        self.body_edit.setPlaceholderText("Write your message...")
        self.body_edit.setStyleSheet(_input_style())
        layout.addWidget(self.body_edit, 1)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.button(QDialogButtonBox.StandardButton.Ok).setText("Send")
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        self._apply_styles()

    def _apply_styles(self):
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {COLORS['slate_navy']};
                color: {COLORS['hd_white']};
                font-family: "{FONTS['ui']}";
                font-size: {FONTS['size_md']}px;
            }}
            QLabel {{ color: {COLORS['text_secondary']}; }}
            QLineEdit, QPlainTextEdit {{
                background-color: {COLORS['void_black']};
                color: {COLORS['hd_white']};
                border: 1px solid {COLORS['border']};
                border-radius: 4px;
                padding: 6px;
            }}
            QPushButton {{
                background-color: {COLORS['seafoam_deep']};
                color: {COLORS['hd_white']};
                border: none;
                border-radius: 4px;
                padding: 6px 16px;
            }}
            QPushButton:hover {{ background-color: {COLORS['seafoam']}; color: {COLORS['void_black']}; }}
        """)


class AccountDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add Mail Account")
        self.setMinimumWidth(460)

        layout = QVBoxLayout(self)
        layout.setSpacing(SPACING["md"])

        form = QFormLayout()
        form.setSpacing(SPACING["md"])
        self.label_edit = QLineEdit()
        self.label_edit.setPlaceholderText("e.g. Gmail, Work")
        self.email_edit = QLineEdit()
        self.email_edit.setPlaceholderText("you@example.com")
        self.password_edit = QLineEdit()
        self.password_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.imap_edit = QLineEdit()
        self.imap_edit.setPlaceholderText("imap.example.com")
        self.smtp_edit = QLineEdit()
        self.smtp_edit.setPlaceholderText("smtp.example.com")
        form.addRow("Label", self.label_edit)
        form.addRow("Email", self.email_edit)
        form.addRow("Password", self.password_edit)
        form.addRow("IMAP host", self.imap_edit)
        form.addRow("SMTP host", self.smtp_edit)
        layout.addLayout(form)

        hint = QLabel(
            "Credentials are stored locally in ~/.reef. "
            "Mail is optional — the Local thread always works offline."
        )
        hint.setWordWrap(True)
        hint.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: {FONTS['size_xs']}px;")
        layout.addWidget(hint)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        self.setStyleSheet(f"""
            QDialog {{
                background-color: {COLORS['slate_navy']};
                color: {COLORS['hd_white']};
                font-family: "{FONTS['ui']}";
                font-size: {FONTS['size_md']}px;
            }}
            QLabel {{ color: {COLORS['text_secondary']}; }}
            QLineEdit {{
                background-color: {COLORS['void_black']};
                color: {COLORS['hd_white']};
                border: 1px solid {COLORS['border']};
                border-radius: 4px;
                padding: 6px;
            }}
            QPushButton {{
                background-color: {COLORS['seafoam_deep']};
                color: {COLORS['hd_white']};
                border: none;
                border-radius: 4px;
                padding: 6px 16px;
            }}
            QPushButton:hover {{ background-color: {COLORS['seafoam']}; color: {COLORS['void_black']}; }}
        """)


def _input_style():
    return f"""
        QPlainTextEdit, QLineEdit {{
            background-color: {COLORS['void_black']};
            color: {COLORS['hd_white']};
            border: 1px solid {COLORS['border']};
            border-radius: 4px;
            font-family: "{FONTS['mono']}";
            font-size: {FONTS['size_sm']}px;
        }}
    """


class ReefWindow(QMainWindow):
    def __init__(self, store: MailStore | None = None):
        super().__init__()
        self.setWindowTitle("Reef — Messenger")
        self.setMinimumSize(960, 600)
        self.resize(1200, 760)

        self.store = store or MailStore()
        self.accounts = self.store.load_accounts()
        self.messages: list = []
        self._workers = []

        self._setup_ui()
        self._rebuild_folder_list()

    # ── UI ────────────────────────────────────────────

    def _setup_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        central.setStyleSheet(f"""
            QWidget {{
                background-color: {COLORS['abyss_navy']};
                color: {COLORS['hd_white']};
                font-family: "{FONTS['ui']}";
                font-size: {FONTS['size_md']}px;
            }}
        """)

        root = QVBoxLayout(central)
        root.setContentsMargins(SPACING["lg"], SPACING["lg"], SPACING["lg"], SPACING["lg"])
        root.setSpacing(SPACING["md"])

        # Title
        title = QLabel("\U0001f30a  REEF  //  Messenger")
        title.setStyleSheet(
            f"color: {COLORS['seafoam']}; font-family: \"{FONTS['ui']}\"; "
            f"font-size: {FONTS['size_lg']}px; font-weight: bold; letter-spacing: 2px;"
        )
        root.addWidget(title)

        splitter = QSplitter(Qt.Horizontal)
        splitter.setHandleWidth(1)

        # Left pane — folders/accounts
        left = QWidget()
        left_layout = QVBoxLayout(left)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(SPACING["sm"])

        self.folder_list = QListWidget()
        self.folder_list.setStyleSheet(_pane_style())
        self.folder_list.currentRowChanged.connect(self._on_folder_selected)
        left_layout.addWidget(self.folder_list, 1)

        left_buttons = QHBoxLayout()
        left_buttons.setSpacing(SPACING["sm"])
        add_btn = QPushButton("+ Account")
        add_btn.clicked.connect(self._add_account)
        self.refresh_btn = QPushButton("\u27f3 Refresh")
        self.refresh_btn.clicked.connect(self._refresh_selected)
        left_buttons.addWidget(add_btn)
        left_buttons.addWidget(self.refresh_btn)
        left_layout.addLayout(left_buttons)

        splitter.addWidget(left)

        # Middle pane — message list
        self.message_list = QListWidget()
        self.message_list.setStyleSheet(_pane_style())
        self.message_list.currentItemChanged.connect(self._on_message_selected)
        splitter.addWidget(self.message_list)

        # Right pane — viewer
        right = QWidget()
        right_layout = QVBoxLayout(right)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(SPACING["sm"])

        self.viewer = QTextBrowser()
        self.viewer.setOpenExternalLinks(True)
        self.viewer.setStyleSheet(f"""
            QTextBrowser {{
                background-color: {COLORS['void_black']};
                color: {COLORS['hd_white']};
                border: 1px solid {COLORS['border']};
                border-radius: 4px;
                padding: {SPACING['md']}px;
                font-family: "{FONTS['ui']}";
                font-size: {FONTS['size_md']}px;
            }}
        """)
        right_layout.addWidget(self.viewer, 1)

        right_buttons = QHBoxLayout()
        right_buttons.setSpacing(SPACING["sm"])
        compose_btn = QPushButton("\u270e Compose")
        compose_btn.clicked.connect(self._compose)
        reply_btn = QPushButton("\u21a9 Reply")
        reply_btn.clicked.connect(self._reply)
        self.status_label = QLabel("Ready")
        self.status_label.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: {FONTS['size_xs']}px;")
        right_buttons.addWidget(compose_btn)
        right_buttons.addWidget(reply_btn)
        right_buttons.addStretch()
        right_buttons.addWidget(self.status_label)
        right_layout.addLayout(right_buttons)

        splitter.addWidget(right)
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)
        splitter.setStretchFactor(2, 2)

        root.addWidget(splitter, 1)

    # ── folder list ───────────────────────────────────

    def _rebuild_folder_list(self):
        self.folder_list.blockSignals(True)
        self.folder_list.clear()

        item = QListWidgetItem("\U0001f30a  Local Thread")
        item.setData(Qt.ItemDataRole.UserRole, LOCAL_FOLDER)
        item.setToolTip("Offline local conversation — always available")
        self.folder_list.addItem(item)

        for acc in self.accounts:
            head = QListWidgetItem(f"——— {acc.label} ———")
            head.setFlags(Qt.ItemFlag.NoItemFlags)
            head.setForeground(Qt.GlobalColor.gray)
            self.folder_list.addItem(head)

            inbox = QListWidgetItem(f"\u2709  Inbox  ·  {acc.email}")
            inbox.setData(Qt.ItemDataRole.UserRole, (acc.label, "inbox"))
            inbox.setToolTip(f"IMAP: {acc.imap_host or 'not configured'}")
            self.folder_list.addItem(inbox)

            sent = QListWidgetItem(f"\u21e7  Sent  ·  {acc.label}")
            sent.setData(Qt.ItemDataRole.UserRole, (acc.label, "sent"))
            self.folder_list.addItem(sent)

        self.folder_list.blockSignals(False)
        if self.folder_list.count():
            self.folder_list.setCurrentRow(0)

    def _on_folder_selected(self, row: int):
        if row < 0:
            return
        item = self.folder_list.item(row)
        target = item.data(Qt.ItemDataRole.UserRole)
        if not target:
            return
        self._selected = target
        self._show_folder(target)
        if target[1] == "inbox":
            self._refresh_selected()

    def _account_by_label(self, label: str):
        for acc in self.accounts:
            if acc.label == label:
                return acc
        return None

    # ── message list ─────────────────────────────────

    def _show_folder(self, target):
        account, folder = target
        self.messages = [
            m for m in self.store.load_messages()
            if m.account == account and m.folder == folder
        ]
        self.message_list.blockSignals(True)
        self.message_list.clear()
        for m in sorted(self.messages, key=lambda x: x.date or "", reverse=True):
            tag = "● " if not m.read else "  "
            subj = m.subject if len(m.subject) <= 42 else m.subject[:39] + "..."
            text = f"{tag}{subj}"
            it = QListWidgetItem(text)
            it.setData(Qt.ItemDataRole.UserRole, m.id)
            it.setToolTip(f"{m.sender or m.recipient}\n{m.date}")
            if not m.read:
                it.setForeground(Qt.GlobalColor.white)
            self.message_list.addItem(it)
        self.message_list.blockSignals(False)
        self.viewer.setHtml("")
        self.status_label.setText(f"{len(self.messages)} messages")

    def _on_message_selected(self, current, _previous):
        if not current:
            return
        mid = current.data(Qt.ItemDataRole.UserRole)
        for m in self.messages:
            if m.id == mid:
                self._render_message(m)
                break

    def _render_message(self, m):
        self.viewer.setHtml(
            f"""
            <h2 style="color:#00F2C2;margin:0;">{_html_escape(m.subject)}</h2>
            <p style="color:#8BA3B8;font-size:11px;">
              From: {_html_escape(m.sender)}<br>
              To: {_html_escape(m.recipient)}<br>
              Date: {_html_escape(m.date)}
            </p>
            <hr style="border-color:#0E2238;">
            <div style="color:#E8F1F8;white-space:pre-wrap;">{_html_escape(m.body)}</div>
            """
        )

    # ── actions ───────────────────────────────────────

    def _add_account(self):
        dlg = AccountDialog(self)
        if dlg.exec() != QDialog.DialogCode.Accepted:
            return
        acc = Account(
            label=dlg.label_edit.text().strip() or "Mail",
            email=dlg.email_edit.text().strip(),
            password=dlg.password_edit.text(),
            imap_host=dlg.imap_edit.text().strip(),
            smtp_host=dlg.smtp_edit.text().strip(),
        )
        if not acc.email:
            QMessageBox.warning(self, "Reef", "Email address is required.")
            return
        self.accounts.append(acc)
        self.store.save_accounts(self.accounts)
        self._rebuild_folder_list()
        self.status_label.setText(f"Added account {acc.label}")

    def _refresh_selected(self):
        target = getattr(self, "_selected", LOCAL_FOLDER)
        account_label, folder = target
        if folder != "inbox":
            self._show_folder(target)
            return
        acc = self._account_by_label(account_label)
        if not acc or not acc.imap_host:
            self.status_label.setText("No IMAP host configured")
            return
        self.refresh_btn.setEnabled(False)
        self.status_label.setText(f"Syncing {acc.label} inbox...")
        worker = RefreshWorker(acc)
        worker.finished_ok.connect(self._on_refreshed)
        worker.failed.connect(self._on_refresh_failed)
        worker.finished.connect(lambda: self.refresh_btn.setEnabled(True))
        self._workers.append(worker)
        worker.start()

    def _on_refreshed(self, messages):
        self.store.upsert_messages(messages)
        self.status_label.setText(f"Synced {len(messages)} new")
        target = getattr(self, "_selected", LOCAL_FOLDER)
        self._show_folder(target)

    def _on_refresh_failed(self, err):
        self.status_label.setText(f"Sync failed: {err[:60]}")

    def _compose(self):
        target = getattr(self, "_selected", LOCAL_FOLDER)
        account_label, folder = target
        if account_label == "Local":
            dlg = ComposeDialog("New Local Message", show_to=False, parent=self)
            if dlg.exec() != QDialog.DialogCode.Accepted:
                return
            msg = self.store.append_local("You", dlg.body_edit.toPlainText())
            if dlg.subject_edit.text().strip():
                msg.subject = dlg.subject_edit.text().strip()
                self.store.upsert_messages([msg])
            self._show_folder(target)
            self.status_label.setText("Saved to Local thread")
            return

        acc = self._account_by_label(account_label)
        if not acc or not acc.smtp_host:
            self.status_label.setText("No SMTP host configured")
            return
        dlg = ComposeDialog(f"New Message — {acc.label}", parent=self)
        if dlg.exec() != QDialog.DialogCode.Accepted:
            return
        to = dlg.to_edit.text().strip()
        subject = dlg.subject_edit.text().strip()
        body = dlg.body_edit.toPlainText()
        if not to:
            QMessageBox.warning(self, "Reef", "Recipient required.")
            return

        self.status_label.setText("Sending...")
        worker = SendWorker(acc, to, subject, body)
        worker.sent.connect(
            lambda to=to, subject=subject, body=body: self._on_sent(
                account_label, to, subject, body
            )
        )
        worker.failed.connect(self._on_send_failed)
        self._workers.append(worker)
        worker.start()

    def _on_sent(self, account_label, to, subject, body):
        self.store.upsert_messages(
            [
                Message(
                    id=f"s-{account_label}-{time.time()}",
                    account=account_label,
                    folder="sent",
                    subject=subject or "(no subject)",
                    recipient=to,
                    date=time.strftime("%a, %d %b %Y %H:%M"),
                    body=body,
                    read=True,
                )
            ]
        )
        self.status_label.setText("Sent")
        target = getattr(self, "_selected", LOCAL_FOLDER)
        self._show_folder(target)

    def _on_send_failed(self, err):
        self.status_label.setText(f"Send failed: {err[:60]}")

    def _reply(self):
        current = self.message_list.currentItem()
        if not current:
            return
        mid = current.data(Qt.ItemDataRole.UserRole)
        target = getattr(self, "_selected", LOCAL_FOLDER)
        original = next((m for m in self.messages if m.id == mid), None)
        if not original:
            return
        dlg = ComposeDialog(f"Reply — {original.subject}", parent=self)
        dlg.to_edit.setText(original.sender if target[1] != "local" else "Local")
        dlg.subject_edit.setText(("Re: " + original.subject) if not original.subject.startswith("Re:") else original.subject)
        dlg.body_edit.setPlainText(f"\n\n—\n{original.sender} wrote:\n{original.body}")
        if dlg.exec() != QDialog.DialogCode.Accepted:
            return
        if target[1] == "local":
            self.store.append_local("You", dlg.body_edit.toPlainText())
            self._show_folder(target)
            self.status_label.setText("Saved to Local thread")
            return
        acc = self._account_by_label(target[0])
        if not acc or not acc.smtp_host:
            self.status_label.setText("No SMTP host configured")
            return
        to = dlg.to_edit.text().strip()
        subject = dlg.subject_edit.text().strip()
        body = dlg.body_edit.toPlainText()
        self.status_label.setText("Sending...")
        worker = SendWorker(acc, to, subject, body)
        worker.sent.connect(
            lambda to=to, subject=subject, body=body: self._on_sent(
                target[0], to, subject, body
            )
        )
        worker.failed.connect(self._on_send_failed)
        self._workers.append(worker)
        worker.start()


def _html_escape(text: str) -> str:
    return (
        str(text)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


def _pane_style():
    return f"""
        QListWidget {{
            background-color: {COLORS['void_black']};
            color: {COLORS['hd_white']};
            border: 1px solid {COLORS['border']};
            border-radius: 4px;
            font-family: "{FONTS['ui']}";
            font-size: {FONTS['size_md']}px;
            padding: 4px;
        }}
        QListWidget::item {{
            padding: 6px 8px;
            border-radius: 4px;
        }}
        QListWidget::item:hover {{
            background-color: {COLORS['surface_hover']};
        }}
        QListWidget::item:selected {{
            background-color: {COLORS['seafoam_deep']};
            color: {COLORS['hd_white']};
        }}
        QPushButton {{
            background-color: {COLORS['slate_navy']};
            color: {COLORS['seafoam']};
            border: 1px solid {COLORS['border']};
            border-radius: 4px;
            padding: 6px 10px;
            font-family: "{FONTS['ui']}";
            font-size: {FONTS['size_sm']}px;
        }}
        QPushButton:hover {{ background-color: {COLORS['seafoam_deep']}; }}
        QPushButton:disabled {{ color: {COLORS['text_muted']}; }}
    """


def main():
    setup_qt_environment()
    app = QApplication(sys.argv)
    window = ReefWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
