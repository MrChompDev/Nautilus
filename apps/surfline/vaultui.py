"""Surfline password vault UI (PySide6)"""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from apps.surfline.vault import (
    add_entry,
    create_vault,
    delete_entry,
    list_entries,
    update_entry,
    vault_exists,
    verify_passphrase,
)
from core.theme import COLORS, FONTS, RADIUS_SM

_INPUT_STYLE = f"""
QLineEdit {{
    background: {COLORS['bg_light']};
    color: {COLORS['text_dark']};
    border: 1px solid {COLORS['border']};
    border-radius: {RADIUS_SM};
    padding: 6px 10px;
    font-size: {FONTS['size_md']}px;
}}
QLineEdit:focus {{
    border: 1px solid {COLORS['coral']};
}}
"""

_BTN_STYLE = f"""
QPushButton {{
    background: {COLORS['coral']};
    color: #ffffff;
    border: none;
    border-radius: {RADIUS_SM};
    padding: 8px 16px;
    font-size: {FONTS['size_sm']}px;
    font-weight: bold;
}}
QPushButton:hover {{
    background: {COLORS['coral_deep']};
}}
QPushButton:disabled {{
    background: {COLORS['border']};
}}
"""

_GRAY_BTN = f"""
QPushButton {{
    background: {COLORS['bg_dark']}; color: {COLORS['text_dark']};
    border: none; border-radius: {RADIUS_SM}; padding: 8px 16px;
    font-size: {FONTS['size_sm']}px;
}}
QPushButton:hover {{ background: {COLORS['hover']}; }}
"""


class PassphraseDialog(QDialog):
    def __init__(self, create_mode: bool, parent=None):
        super().__init__(parent)
        self.create_mode = create_mode
        self.accepted_passphrase = None
        self.setWindowTitle("Create Vault" if create_mode else "Unlock Vault")
        self.setFixedWidth(360)
        self.setStyleSheet(f"background: {COLORS['bg_light']}")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(12)

        title = "Create Password Vault" if create_mode else "Enter Passphrase"
        heading = QLabel(f"<h2 style='color:{COLORS['text_dark']};'> {title}</h2>")
        heading.setAlignment(Qt.AlignCenter)
        layout.addWidget(heading)

        if create_mode:
            hint = QLabel("Set a passphrase. It encrypts your saved passwords.")
            hint.setStyleSheet(f"color: {COLORS['text_muted']};")
            hint.setAlignment(Qt.AlignCenter)
            layout.addWidget(hint)

        self.pass_input = QLineEdit()
        self.pass_input.setEchoMode(QLineEdit.Password)
        self.pass_input.setPlaceholderText("Passphrase")
        self.pass_input.setStyleSheet(_INPUT_STYLE)
        layout.addWidget(self.pass_input)

        self.confirm_input = None
        if create_mode:
            self.confirm_input = QLineEdit()
            self.confirm_input.setEchoMode(QLineEdit.Password)
            self.confirm_input.setPlaceholderText("Confirm passphrase")
            self.confirm_input.setStyleSheet(_INPUT_STYLE)
            layout.addWidget(self.confirm_input)

        btn_row = QHBoxLayout()
        unlock_btn = QPushButton("Create Vault" if create_mode else "Unlock")
        unlock_btn.setStyleSheet(_BTN_STYLE)
        unlock_btn.clicked.connect(self._on_ok)
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setStyleSheet(_GRAY_BTN)
        cancel_btn.clicked.connect(self.reject)
        btn_row.addWidget(unlock_btn)
        btn_row.addWidget(cancel_btn)
        layout.addLayout(btn_row)

        self.pass_input.returnPressed.connect(self._on_ok)

    def _on_ok(self):
        p1 = self.pass_input.text()
        if not p1:
            return
        if self.create_mode:
            p2 = self.confirm_input.text() if self.confirm_input else ""
            if p1 != p2:
                QMessageBox.warning(self, "Mismatch", "Passphrases do not match.")
                return
        self.accepted_passphrase = p1
        self.accept()


def ensure_account(owner) -> str | None:
    """Open the lock window, return the passphrase or None if cancelled."""
    dlg = PassphraseDialog(create_mode=not vault_exists(), parent=owner)
    if dlg.exec() != QDialog.Accepted:
        return None
    passphrase = dlg.accepted_passphrase
    if not vault_exists():
        create_vault(passphrase)
        return passphrase
    if verify_passphrase(passphrase):
        return passphrase
    QMessageBox.warning(owner, "Wrong passphrase", "Incorrect passphrase. Try again.")
    return None


class SavePasswordDialog(QDialog):
    def __init__(self, site: str, username_hint: str = "", parent=None):
        super().__init__(parent)
        self.setWindowTitle("Save Password")
        self.setFixedWidth(400)
        self.setStyleSheet(f"background: {COLORS['bg_light']}")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(10)

        site_label = QLabel("Site")
        site_label.setStyleSheet(f"color: {COLORS['text_muted']};")
        layout.addWidget(site_label)

        self.site_input = QLineEdit(site)
        self.site_input.setStyleSheet(_INPUT_STYLE)
        layout.addWidget(self.site_input)

        user_label = QLabel("Username / Email")
        user_label.setStyleSheet(f"color: {COLORS['text_muted']};")
        layout.addWidget(user_label)

        self.user_input = QLineEdit(username_hint)
        self.user_input.setStyleSheet(_INPUT_STYLE)
        layout.addWidget(self.user_input)

        pass_label = QLabel("Password")
        pass_label.setStyleSheet(f"color: {COLORS['text_muted']};")
        layout.addWidget(pass_label)

        self.pass_input = QLineEdit()
        self.pass_input.setEchoMode(QLineEdit.Password)
        self.pass_input.setStyleSheet(_INPUT_STYLE)
        layout.addWidget(self.pass_input)

        btn_row = QHBoxLayout()
        save_btn = QPushButton("Save")
        save_btn.setStyleSheet(_BTN_STYLE)
        save_btn.clicked.connect(self._save)
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setStyleSheet(_GRAY_BTN)
        cancel_btn.clicked.connect(self.reject)
        btn_row.addWidget(save_btn)
        btn_row.addWidget(cancel_btn)
        layout.addLayout(btn_row)

    def _save(self):
        if not (self.site_input.text().strip() and self.pass_input.text()):
            QMessageBox.warning(self, "Missing info", "Site and password are required.")
            return
        self.accept()

    def values(self) -> tuple[str, str, str]:
        return (self.site_input.text().strip(),
                self.user_input.text().strip(),
                self.pass_input.text())


class VaultWindow(QMainWindow):
    def __init__(self, passphrase: str, parent=None):
        super().__init__(parent)
        self.passphrase = passphrase
        self.setWindowTitle("Password Vault")
        self.resize(620, 460)
        self.setStyleSheet(f"background: {COLORS['bg_light']}")

        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        header = QLabel(f"<h2 style='color:{COLORS['text_dark']};'>Password Vault</h2>")
        layout.addWidget(header)

        self.table = QTableWidget(0, 3)
        self.table.setHorizontalHeaderLabels(["Site", "Username", "Password"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setStyleSheet(f"""
            QTableWidget {{
                background: {COLORS['bg_mid']}; color: {COLORS['text_dark']};
                border: 1px solid {COLORS['border']}; border-radius: {RADIUS_SM};
                font-size: {FONTS['size_md']}px;
            }}
            QHeaderView::section {{
                background: {COLORS['bg_dark']}; color: {COLORS['text_dark']};
                border: none; padding: 6px;
                font-weight: bold;
            }}
        """)
        layout.addWidget(self.table)

        btn_row = QHBoxLayout()
        add_btn = QPushButton("+ Add")
        add_btn.setStyleSheet(_BTN_STYLE)
        add_btn.clicked.connect(self._add_entry)
        edit_btn = QPushButton("Edit")
        edit_btn.setStyleSheet(_GRAY_BTN)
        edit_btn.clicked.connect(self._edit_entry)
        del_btn = QPushButton("Delete")
        del_btn.setStyleSheet(_GRAY_BTN)
        del_btn.clicked.connect(self._delete_entry)
        close_btn = QPushButton("Close")
        close_btn.setStyleSheet(_GRAY_BTN)
        close_btn.clicked.connect(self.close)
        btn_row.addWidget(add_btn)
        btn_row.addWidget(edit_btn)
        btn_row.addWidget(del_btn)
        btn_row.addStretch()
        btn_row.addWidget(close_btn)
        layout.addLayout(btn_row)

        self._reload()

    def _reload(self):
        entries = list_entries(self.passphrase)
        self.table.setRowCount(len(entries))
        for i, e in enumerate(entries):
            self.table.setItem(i, 0, QTableWidgetItem(e["site"]))
            self.table.setItem(i, 1, QTableWidgetItem(e["username"]))
            masked = "•" * len(e["password"])
            self.table.setItem(i, 2, QTableWidgetItem(masked))

    def _add_entry(self):
        dlg = SavePasswordDialog("", parent=self)
        if dlg.exec() == QDialog.Accepted:
            site, user, pw = dlg.values()
            add_entry(self.passphrase, site, user, pw)
            self._reload()

    def _edit_entry(self):
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.information(self, "Select row", "Select an entry to edit.")
            return
        entries = list_entries(self.passphrase)
        e = entries[row]
        dlg = SavePasswordDialog(e["site"], e["username"], parent=self)
        dlg.pass_input.setText(e["password"])
        if dlg.exec() == QDialog.Accepted:
            site, user, pw = dlg.values()
            update_entry(self.passphrase, row, site, user, pw)
            self._reload()

    def _delete_entry(self):
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.information(self, "Select row", "Select an entry to delete.")
            return
        if QMessageBox.question(self, "Delete", "Delete this entry?") == QMessageBox.Yes:
            delete_entry(self.passphrase, row)
            self._reload()