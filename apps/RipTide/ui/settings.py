"""Riptide Audio - PySide6 Settings View"""
from __future__ import annotations

import os
import webbrowser

from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtWidgets import (
    QDialog,
    QFormLayout,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from apps.RipTide import config
from apps.RipTide.auth.soundcloud import SoundCloudOAuth
from apps.RipTide.auth.spotify import SpotifyOAuth
from apps.RipTide.auth.youtube import YouTubeOAuth
from apps.RipTide.database.db import Database
from apps.RipTide.models import Account, Platform
from apps.RipTide.ui.styles import Colors

C = Colors

PLATFORM_BUTTON_STYLES = {
    Platform.SPOTIFY: ("#1db954", "#000000"),
    Platform.YOUTUBE: ("#ff0000", "#ffffff"),
    Platform.SOUNDCLOUD: ("#ff5500", "#ffffff"),
}

PLATFORM_DASHBOARDS = {
    Platform.SPOTIFY: "https://developer.spotify.com/dashboard",
    Platform.YOUTUBE: "https://console.cloud.google.com/apis/credentials",
    Platform.SOUNDCLOUD: "https://soundcloud.com/developers/apps",
}

PLATFORM_STEPS = {
    Platform.SPOTIFY: [
        "1. Click 'Create App' on the Spotify Developer Dashboard",
        "2. Name it anything (e.g. 'Riptide Audio')",
        "3. Under Redirect URIs, add EXACTLY:  http://127.0.0.1:8765/callback",
        "4. Click Save, then copy the Client ID",
        "5. No Client Secret needed for this app",
    ],
    Platform.YOUTUBE: [
        "1. Create a project (or use existing) in Google Cloud Console",
        "2. Enable 'YouTube Data API v3' in the API Library",
        "3. Go to APIs & Services > Credentials",
        "4. Create OAuth Client ID > Desktop App",
        "5. Copy the Client ID and Client Secret",
    ],
    Platform.SOUNDCLOUD: [
        "1. Create a new app on the SoundCloud Developer page",
        "2. Under Redirect URI, add EXACTLY:  http://127.0.0.1:8765/callback",
        "3. Copy the Client ID and Client Secret",
    ],
}


class OAuthWorker(QThread):
    """Runs the blocking OAuth browser+local-server flow off the GUI thread."""

    finished_ok = Signal(object)
    failed = Signal(str)

    def __init__(self, oauth, parent=None):
        super().__init__(parent)
        self._oauth = oauth

    def run(self):
        try:
            account = self._oauth.authenticate()
            if account:
                self.finished_ok.emit(account)
            else:
                self.failed.emit("OAuth flow returned no account.")
        except Exception as e:
            self.failed.emit(str(e))


class AccountCard(QFrame):
    parent_disconnect_requested = Signal(object)

    def __init__(self, account: Account, parent=None):
        super().__init__(parent)
        self.account = account
        self.setObjectName("card")
        self.setFixedHeight(60)

        lay = QHBoxLayout(self)
        lay.setContentsMargins(12, 6, 12, 6)
        lay.setSpacing(10)

        badge = QLabel(account.platform.display_name[0])
        badge.setFixedSize(36, 36)
        badge.setAlignment(Qt.AlignCenter)
        badge.setStyleSheet(
            f"background-color: {account.platform.color}; color: #ffffff; "
            f"font-size: 14px; font-weight: bold; border-radius: 18px;")
        lay.addWidget(badge)

        text = QVBoxLayout()
        text.setSpacing(0)
        name = QLabel(account.display_name[:32])
        name.setStyleSheet(f"color: {C.TEXT_PRIMARY}; font-weight: bold; background: transparent;")
        text.addWidget(name)
        detail = QLabel(f"{account.platform.display_name}  \u00b7  @{account.username[:24]}"
                        if account.username else account.platform.display_name)
        detail.setStyleSheet(f"color: {C.TEXT_SECONDARY}; font-size: 10px; background: transparent;")
        text.addWidget(detail)
        lay.addLayout(text, 1)

        status = QLabel("Connected")
        status.setStyleSheet(f"color: {C.SUCCESS}; background: transparent;")
        lay.addWidget(status)

        disconnect = QPushButton("Disconnect")
        disconnect.setObjectName("danger_btn")
        disconnect.clicked.connect(self._confirm_disconnect)
        lay.addWidget(disconnect)

    def _confirm_disconnect(self):
        answer = QMessageBox.question(
            self, "Disconnect Account", f"Disconnect {self.account.label}?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if answer == QMessageBox.Yes:
            self.parent_disconnect_requested.emit(self.account)


class CredentialsDialog(QDialog):
    """Collect Client ID / Secret for a platform before OAuth."""

    def __init__(self, platform: Platform, parent=None):
        super().__init__(parent)
        self.platform = platform
        self.client_id = ""
        self.client_secret = ""
        self.setWindowTitle(f"Connect {platform.display_name}")
        self.resize(560, 520)
        self._setup_ui()

    def _setup_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(16, 16, 16, 16)
        root.setSpacing(10)

        header = QLabel(f"  {self.platform.display_name} Setup")
        header.setStyleSheet(
            f"color: {self.platform.color}; font-size: 15px; font-weight: bold;")
        root.addWidget(header)

        steps = QLabel("\n".join(f"  {s}" for s in PLATFORM_STEPS.get(self.platform, [])))
        steps.setWordWrap(True)
        steps.setStyleSheet(f"color: {C.TEXT_SECONDARY}; background: transparent;")
        root.addWidget(steps)

        open_btn = QPushButton(f"Open {self.platform.display_name} Dashboard")
        url = PLATFORM_DASHBOARDS.get(self.platform, "")
        open_btn.clicked.connect(lambda: webbrowser.open(url))
        root.addWidget(open_btn)

        form = QFormLayout()
        self._id_field = QLineEdit()
        existing_id = getattr(config, f"{self.platform.name}_CLIENT_ID", "")
        if existing_id:
            self._id_field.setText(existing_id)
        form.addRow("Client ID:", self._id_field)

        self._secret_field = None
        if self.platform != Platform.SPOTIFY:
            self._secret_field = QLineEdit()
            self._secret_field.setEchoMode(QLineEdit.Password)
            existing_secret = getattr(config, f"{self.platform.name}_CLIENT_SECRET", "")
            if existing_secret:
                self._secret_field.setText(existing_secret)
            form.addRow("Client Secret:", self._secret_field)
        root.addLayout(form)

        redirect = QLabel(
            "Redirect URI to add when creating the app:\n"
            "  http://127.0.0.1:8765/callback")
        redirect.setStyleSheet(f"color: {C.ACCENT}; font-weight: bold; background: transparent;")
        root.addWidget(redirect)

        btns = QHBoxLayout()
        btns.addStretch()
        cancel = QPushButton("Cancel")
        cancel.clicked.connect(self.reject)
        btns.addWidget(cancel)
        ok = QPushButton("Save & Connect")
        ok.setObjectName("accent_btn")
        ok.clicked.connect(self._save)
        btns.addWidget(ok)
        root.addLayout(btns)

    def _save(self):
        client_id = self._id_field.text().strip()
        if not client_id:
            QMessageBox.warning(self, "Missing Credentials", "Client ID is required.")
            return
        self.client_id = client_id
        self.client_secret = (
            self._secret_field.text().strip() if self._secret_field else "not_needed"
        )
        self.accept()


class SettingsView(QWidget):
    def __init__(self, db: Database, parent=None):
        super().__init__(parent)
        self._db = db
        self._oauth_handlers = {
            Platform.SPOTIFY: SpotifyOAuth(),
            Platform.YOUTUBE: YouTubeOAuth(),
            Platform.SOUNDCLOUD: SoundCloudOAuth(),
        }
        self._oauth_worker = None
        self.on_accounts_changed = None
        self._setup_ui()
        self.refresh_accounts()

    def _setup_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(16, 12, 16, 12)
        root.setSpacing(8)

        title = QLabel("Settings")
        title.setObjectName("page_title")
        root.addWidget(title)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        content = QWidget()
        body = QVBoxLayout(content)
        body.setContentsMargins(8, 8, 8, 8)
        body.setSpacing(10)

        # ── Connected accounts ──
        accts = QLabel("Connected Accounts")
        accts.setObjectName("section_title")
        body.addWidget(accts)

        self._accounts_box = QVBoxLayout()
        self._accounts_wrap = QWidget()
        self._accounts_wrap.setLayout(self._accounts_box)
        body.addWidget(self._accounts_wrap)

        sep1 = QFrame()
        sep1.setFrameShape(QFrame.HLine)
        sep1.setStyleSheet(f"color: {C.BORDER}; background-color: {C.BORDER};")
        body.addWidget(sep1)

        # ── Add account ──
        add_label = QLabel("Add New Account")
        add_label.setStyleSheet(f"color: {C.ACCENT}; font-size: 14px; font-weight: bold; background: transparent;")
        body.addWidget(add_label)

        for platform in Platform:
            row = QHBoxLayout()
            badge = QLabel(platform.display_name[0])
            badge.setFixedSize(40, 40)
            badge.setAlignment(Qt.AlignCenter)
            badge.setStyleSheet(
                f"background-color: {platform.color}22; color: {platform.color}; "
                f"font-size: 15px; font-weight: bold; border: 2px solid {platform.color}; "
                f"border-radius: 20px;")
            row.addWidget(badge)

            col = QVBoxLayout()
            btn_color, btn_fg = PLATFORM_BUTTON_STYLES.get(platform, (C.BG_TERTIARY, C.TEXT_PRIMARY))
            connect = QPushButton(f"Connect {platform.display_name}")
            connect.setFixedSize(280, 36)
            connect.setStyleSheet(
                f"background-color: {btn_color}; color: {btn_fg}; font-size: 12px; "
                f"font-weight: bold; border: none; border-radius: 4px;")
            connect.clicked.connect(lambda _, p=platform: self._connect_account(p))
            col.addWidget(connect)

            has_creds = bool(getattr(config, f"{platform.name}_CLIENT_ID", ""))
            hint = "Ready to connect" if has_creds else "Free - needs 2 min setup (see instructions)"
            hint_lbl = QLabel(hint)
            hint_lbl.setStyleSheet(
                f"color: {C.SUCCESS if has_creds else C.TEXT_MUTED}; "
                f"font-size: 9px; background: transparent;")
            col.addWidget(hint_lbl)
            row.addLayout(col)
            row.addStretch()
            body.addLayout(row)

        sep2 = QFrame()
        sep2.setFrameShape(QFrame.HLine)
        sep2.setStyleSheet(f"color: {C.BORDER}; background-color: {C.BORDER};")
        body.addWidget(sep2)

        # ── About ──
        about = QLabel("About")
        about.setObjectName("section_title")
        body.addWidget(about)
        ver = QLabel(f"Riptide Audio v{config.APP_VERSION}")
        ver.setStyleSheet(f"color: {C.TEXT_SECONDARY}; background: transparent;")
        body.addWidget(ver)
        tagline = QLabel("One interface to rule all your streams and sounds.")
        tagline.setStyleSheet(f"color: {C.TEXT_MUTED}; font-size: 10px; font-style: italic; background: transparent;")
        body.addWidget(tagline)

        body.addStretch()
        scroll.setWidget(content)
        root.addWidget(scroll, 1)

    def refresh_accounts(self) -> None:
        self._clear_layout(self._accounts_box)
        accounts = self._db.get_accounts()
        if not accounts:
            empty = QLabel("  No accounts connected yet.")
            empty.setStyleSheet(f"color: {C.TEXT_MUTED}; background: transparent;")
            self._accounts_box.addWidget(empty)
            return
        for account in accounts:
            card = AccountCard(account)
            card.parent_disconnect_requested.connect(self._disconnect_account)
            self._accounts_box.addWidget(card)

    # ── Connection flow ──

    def _connect_account(self, platform: Platform) -> None:
        has_creds = bool(getattr(config, f"{platform.name}_CLIENT_ID", ""))
        if not has_creds:
            dlg = CredentialsDialog(platform, self)
            if dlg.exec() != QDialog.Accepted:
                return
            self._apply_credentials(platform, dlg.client_id, dlg.client_secret)

        oauth = self._oauth_handlers.get(platform)
        if not oauth:
            return

        self._oauth_worker = OAuthWorker(oauth, self)
        self._oauth_worker.finished_ok.connect(self._on_oauth_success)
        self._oauth_worker.failed.connect(self._on_oauth_failed)
        self._oauth_worker.start()

    def _apply_credentials(self, platform: Platform, client_id: str, client_secret: str) -> None:
        os.environ[f"RIPTIDE_{platform.name}_CLIENT_ID"] = client_id
        os.environ[f"RIPTIDE_{platform.name}_CLIENT_SECRET"] = client_secret
        setattr(config, f"{platform.name}_CLIENT_ID", client_id)
        setattr(config, f"{platform.name}_CLIENT_SECRET", client_secret)

    def _on_oauth_success(self, account: Account) -> None:
        self._db.upsert_account(account)
        self.refresh_accounts()
        if self.on_accounts_changed:
            self.on_accounts_changed()

    def _on_oauth_failed(self, error: str) -> None:
        QMessageBox.warning(
            self, "Connection Failed",
            f"Failed to connect.\n\n{error}\n\n"
            "Make sure you copied the correct Client ID and approved the login.")

    def _disconnect_account(self, account: Account) -> None:
        self._db.delete_account(account.id)
        self.refresh_accounts()
        if self.on_accounts_changed:
            self.on_accounts_changed()

    @staticmethod
    def _clear_layout(layout) -> None:
        while layout.count():
            item = layout.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()
