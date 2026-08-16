"""
Nautilus OS — Authentication & Account System
Local JSON-backed account storage with password hashing and login dialog.

Stores accounts in:  data/accounts.json
Auto-login via:      data/session.json
"""

import hashlib
import hmac
import json
import os
import secrets
import time
from datetime import datetime

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(PROJECT_ROOT, "data")
ACCOUNTS_FILE = os.path.join(DATA_DIR, "accounts.json")
SESSION_FILE = os.path.join(DATA_DIR, "session.json")
SECURITY_LOG = os.path.join(DATA_DIR, "security_log.jsonl")

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QBrush, QColor, QFont, QLinearGradient, QPainter, QPixmap
from PySide6.QtWidgets import (
    QCheckBox,
    QDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QStackedWidget,
    QVBoxLayout,
)

try:
    from core import wallpapers
    from core.icons import get_logo
    from core.logger import get_logger
    from core.theme import COLORS, FONTS, SPACING, hex_to_rgba
    _log = get_logger("SYSTEM")
    _log.info("Auth system initialized")
    _HAS_CORE = True
except ImportError:
    _HAS_CORE = False
    COLORS = {
        "abyss_navy": "#081626", "slate_navy": "#0E2238", "deep_navy": "#050D14",
        "void_black": "#02060A", "seafoam": "#00F2C2", "seafoam_dim": "#00C9A0",
        "seafoam_deep": "#004D40", "coral": "#FF7F50", "hd_white": "#EEF4F8",
        "text_secondary": "#8BA4B8", "text_muted": "#506070", "border": "#152D44",
        "surface_hover": "#132A40",
    }
    FONTS = {"mono": "JetBrains Mono", "ui": "Segoe UI", "size_xs": 10, "size_sm": 11,
             "size_md": 12, "size_lg": 13, "size_xl": 14, "size_xxl": 16}
    SPACING = {"xs": 2, "sm": 4, "md": 8, "lg": 12, "xl": 16, "xxl": 24}
    wallpapers = None

    def hex_to_rgba(hex_str: str, alpha: int = 255) -> str:
        value = hex_str.lstrip("#")
        r = int(value[0:2], 16)
        g = int(value[2:4], 16)
        b = int(value[4:6], 16)
        return f"rgba({r}, {g}, {b}, {alpha})"

    def get_logo(app_id: str, size: int = None):
        return None


def _glass(alpha: int = 205) -> str:
    return hex_to_rgba(COLORS["slate_navy"], alpha)


def _edge() -> str:
    return hex_to_rgba(COLORS["seafoam"], 48)


def _sheen() -> str:
    return "rgba(238, 244, 248, 26)"


# ═══════════════════════════════════════════════════════════════
#  ACCOUNT STORAGE ENGINE
# ═══════════════════════════════════════════════════════════════

def _ensure_data_dir():
    os.makedirs(DATA_DIR, exist_ok=True)


def _load_accounts() -> dict:
    _ensure_data_dir()
    if os.path.exists(ACCOUNTS_FILE):
        with open(ACCOUNTS_FILE, encoding="utf-8") as f:
            return json.load(f)
    return {}


def _save_accounts(accounts: dict):
    _ensure_data_dir()
    fd = os.open(ACCOUNTS_FILE, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        json.dump(accounts, f, indent=2)
    os.chmod(ACCOUNTS_FILE, 0o600)


# ═══════════════════════════════════════════════════════════════
#  PASSWORD HASHING & POLICY
# ═══════════════════════════════════════════════════════════════

PBKDF2_ITERATIONS = 200_000
PBKDF2_PREFIX = "pbkdf2$"
SESSION_TTL_DAYS = 14
LOGIN_MAX_ATTEMPTS = 5
LOCKOUT_SECONDS = 60
LOCKOUT_ESCALATION = 300


def password_policy_ok(password: str) -> tuple:
    """Validate password strength. Returns (ok: bool, message: str)."""
    if len(password) < 8:
        return False, "Password must be at least 8 characters"
    if not any(c.isalpha() for c in password):
        return False, "Password must contain at least one letter"
    if not any(c.isdigit() for c in password):
        return False, "Password must contain at least one number"
    return True, ""


def _pbkdf2_hash(password: str, salt_hex: str = None) -> tuple:
    """PBKDF2-HMAC-SHA256 verifier. Returns (verifier_string, salt_hex)."""
    if salt_hex is None:
        salt_hex = secrets.token_hex(16)
    dk = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"),
        bytes.fromhex(salt_hex), PBKDF2_ITERATIONS
    )
    return f"{PBKDF2_PREFIX}{PBKDF2_ITERATIONS}${salt_hex}${dk.hex()}", salt_hex


def _verify_password(account: dict, password: str) -> bool:
    """Verify a password against either the new PBKDF2 or legacy SHA-256 format."""
    stored = account.get("password_hash", "")
    if stored.startswith(PBKDF2_PREFIX):
        try:
            _, iters_s, salt_hex, expected = stored.split("$")
            dk = hashlib.pbkdf2_hmac(
                "sha256", password.encode("utf-8"),
                bytes.fromhex(salt_hex), int(iters_s)
            )
            return hmac.compare_digest(dk.hex(), expected)
        except (ValueError, TypeError):
            return False
    # Legacy format (pre-hardening): sha256(salt + password), salt stored separately
    salt = account.get("salt", "")
    if not salt or stored in ("testhash", "", None):
        return False
    return hmac.compare_digest(_hash_password(password, salt)[0], stored)


def _hash_password(password: str, salt: str = None) -> tuple:
    """Legacy SHA-256 + salt (kept only to migrate pre-hardening accounts)."""
    if salt is None:
        salt = secrets.token_hex(16)
    combined = salt + password
    h = hashlib.sha256(combined.encode("utf-8")).hexdigest()
    return h, salt


def _security_event(event: str, username: str = "", detail: str = ""):
    """Append an event to the local security log (consumed by blue-team monitor)."""
    try:
        os.makedirs(DATA_DIR, exist_ok=True)
        with open(SECURITY_LOG, "a", encoding="utf-8") as f:
            f.write(json.dumps({
                "ts": datetime.now().isoformat(),
                "event": event,
                "username": username,
                "detail": detail,
            }) + "\n")
    except OSError:
        pass


# ═══════════════════════════════════════════════════════════════
#  ACCOUNT STORAGE ENGINE
# ═══════════════════════════════════════════════════════════════

def create_account(username: str, password: str, display_name: str = "") -> bool:
    """Create a new user account. Returns True on success, False if username exists."""
    ok, msg = password_policy_ok(password)
    if not ok:
        raise ValueError(msg)
    accounts = _load_accounts()
    username_lower = username.lower()

    if username_lower in accounts:
        return False

    verifier, salt = _pbkdf2_hash(password)

    accounts[username_lower] = {
        "username": username,
        "display_name": display_name or username,
        "password_hash": verifier,
        "salt": salt,
        "created_at": datetime.now().isoformat(),
        "last_login": None,
        "failed_attempts": 0,
        "lockout_until": None,
    }
    _save_accounts(accounts)
    _security_event("account_created", username_lower)
    return True


def verify_login(username: str, password: str) -> dict | None:
    """Verify credentials with lockout protection. Returns account dict or None."""
    accounts = _load_accounts()
    username_lower = username.lower()

    account = accounts.get(username_lower)
    if not account:
        return None

    # ── Lockout check (blocked attempts still count toward escalation) ──
    lockout_until = account.get("lockout_until")
    if lockout_until:
        try:
            if float(lockout_until) > time.time():
                attempts = int(account.get("failed_attempts", 0)) + 1
                account["failed_attempts"] = attempts
                if attempts >= LOGIN_MAX_ATTEMPTS * 2:
                    account["lockout_until"] = str(time.time() + LOCKOUT_ESCALATION)
                accounts[username_lower] = account
                _save_accounts(accounts)
                _security_event("login_blocked_locked", username_lower)
                return None
        except (TypeError, ValueError):
            pass

    if not _verify_password(account, password):
        attempts = int(account.get("failed_attempts", 0)) + 1
        account["failed_attempts"] = attempts
        # Counter keeps climbing past the first lockout (blocked attempts also
        # increment above) so the 300s escalation at 2x threshold is reachable.
        if attempts >= LOGIN_MAX_ATTEMPTS:
            lock_for = (LOCKOUT_SECONDS if attempts < LOGIN_MAX_ATTEMPTS * 2
                        else LOCKOUT_ESCALATION)
            account["lockout_until"] = str(time.time() + lock_for)
            _security_event("account_locked", username_lower,
                            f"{lock_for}s after {attempts} failed attempts")
        accounts[username_lower] = account
        _save_accounts(accounts)
        _security_event("login_failed", username_lower)
        return None

    # ── Success: reset counters, upgrade legacy hash, update login time ──
    account["failed_attempts"] = 0
    account["lockout_until"] = None
    if not str(account.get("password_hash", "")).startswith(PBKDF2_PREFIX):
        verifier, salt = _pbkdf2_hash(password)  # fresh salt for the upgraded verifier
        account["password_hash"] = verifier
        account["salt"] = salt
    account["last_login"] = datetime.now().isoformat()
    accounts[username_lower] = account
    _save_accounts(accounts)
    _security_event("login_success", username_lower)

    return account


def save_session(username: str, remember: bool = False):
    """Save a cryptographically-bound session for auto-login.

    A random 256-bit token is written to session.json and only its SHA-256
    hash is stored on the account, so merely editing the file cannot forge a
    session — the token must come from a genuine login.
    """
    _ensure_data_dir()
    if remember:
        accounts = _load_accounts()
        username_lower = username.lower()
        if username_lower not in accounts:
            return
        token = secrets.token_urlsafe(32)
        accounts[username_lower]["session_token_hash"] = \
            hashlib.sha256(token.encode("utf-8")).hexdigest()
        accounts[username_lower]["session_created_at"] = datetime.now().isoformat()
        _save_accounts(accounts)
        with open(SESSION_FILE, "w", encoding="utf-8") as f:
            json.dump({
                "username": username_lower,
                "token": token,
                "created_at": datetime.now().isoformat(),
            }, f)
        os.chmod(SESSION_FILE, 0o600)
    elif os.path.exists(SESSION_FILE):
        os.remove(SESSION_FILE)


def load_session() -> str | None:
    """Validate a saved session token. Returns username or None."""
    if not os.path.exists(SESSION_FILE):
        return None
    try:
        with open(SESSION_FILE, encoding="utf-8") as f:
            data = json.load(f)
        username = data.get("username")
        token = data.get("token")
        if not username or not token:
            return None
        accounts = _load_accounts()
        account = accounts.get(username.lower())
        if not account:
            return None
        expected = account.get("session_token_hash", "")
        if not expected:
            return None
        if not hmac.compare_digest(
            hashlib.sha256(token.encode("utf-8")).hexdigest(), expected
        ):
            _security_event("session_forgery_rejected", username.lower())
            return None
        created = account.get("session_created_at")
        if created:
            try:
                if time.time() - datetime.fromisoformat(created).timestamp() > SESSION_TTL_DAYS * 86400:
                    return None  # expired
            except ValueError:
                return None
        return username
    except Exception:
        return None


def clear_session():
    """Remove the saved session (logout)."""
    if os.path.exists(SESSION_FILE):
        try:
            os.remove(SESSION_FILE)
        except OSError:
            pass


def get_account(username: str) -> dict | None:
    """Get account info by username."""
    accounts = _load_accounts()
    return accounts.get(username.lower())


def get_avatar_initials(display_name: str) -> str:
    """Get avatar initials from display name (max 2 chars)."""
    parts = display_name.split()
    if len(parts) >= 2:
        return (parts[0][0] + parts[-1][0]).upper()
    return display_name[:2].upper()


# ═══════════════════════════════════════════════════════════════
#  AVATAR GENERATOR
# ═══════════════════════════════════════════════════════════════

def generate_avatar(initials: str, size: int = 100) -> QPixmap:
    """Generate a circular avatar pixmap with gradient background."""
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.transparent)

    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing)

    # Gradient circle background
    gradient = QLinearGradient(0, 0, size, size)
    gradient.setColorAt(0.0, QColor(COLORS["seafoam_deep"]))
    gradient.setColorAt(1.0, QColor(COLORS["seafoam"]))
    painter.setBrush(QBrush(gradient))
    painter.setPen(Qt.NoPen)
    painter.drawEllipse(4, 4, size - 8, size - 8)

    # Initials text
    font = QFont(FONTS["mono"])
    font.setPointSize(int(size * 0.35))
    font.setBold(True)
    painter.setFont(font)
    painter.setPen(QColor(COLORS["void_black"]))
    painter.drawText(pixmap.rect(), Qt.AlignCenter, initials)

    painter.end()
    return pixmap


# ═══════════════════════════════════════════════════════════════
#  LOGIN DIALOG
#  Full-screen frameless gate that floats over the live wallpaper,
#  mirroring the desktop's glass + ocean aesthetic.
# ═══════════════════════════════════════════════════════════════

_GLASS_CARD = f"""
    background: {_glass(205)};
    border: 1px solid {_edge()};
    border-top: 1px solid {_sheen()};
    border-radius: 18px;
"""

_FIELD_SS = f"""
    QLineEdit {{
        background: {hex_to_rgba(COLORS["deep_navy"], 200)}; color: {COLORS["hd_white"]};
        border: 1px solid {COLORS["border"]}; padding: 11px 14px;
        font-family: "{FONTS["mono"]}"; font-size: {FONTS["size_md"]}px;
        border-radius: 8px;
    }}
    QLineEdit:focus {{
        border-color: {COLORS["seafoam"]}; background: {COLORS["void_black"]};
    }}
"""

_LABEL_SS = f"""
    color: {COLORS["text_muted"]}; font-family: '{FONTS["mono"]}';
    font-size: {FONTS["size_xs"]}px; letter-spacing: 2px;
"""

_PRIMARY_BTN_SS = f"""
    QPushButton {{
        background: {COLORS["seafoam_deep"]}; color: {COLORS["seafoam"]};
        border: 1px solid {COLORS["seafoam"]}; padding: 12px;
        font-family: "{FONTS["mono"]}"; font-size: {FONTS["size_md"]}px;
        font-weight: bold; letter-spacing: 3px; border-radius: 8px;
    }}
    QPushButton:hover {{ background: {COLORS["seafoam"]}; color: {COLORS["void_black"]}; }}
    QPushButton:pressed {{ background: {COLORS["seafoam_dim"]}; }}
"""

_GHOST_BTN_SS = f"""
    QPushButton {{ background: transparent; color: {COLORS["text_secondary"]};
        border: none; font-family: "{FONTS["ui"]}"; font-size: {FONTS["size_sm"]}px; }}
    QPushButton:hover {{ color: {COLORS["seafoam"]}; }}
"""


class LoginDialog(QDialog):
    """Full-screen Nautilus OS login/register gate over the live wallpaper."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._logged_in_user = None
        self._logged_in_account = None

        self.setWindowTitle("Nautilus OS — Login")
        self.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint)
        self.setMouseTracking(True)

        # Wallpaper background + ambient animation, exactly like the desktop.
        self._base = QPixmap()
        self._ambient = None
        self._anim_theme = None

        self._anim_timer = QTimer(self)
        self._anim_timer.setInterval(40)
        self._anim_timer.timeout.connect(self._tick_ambient)

        self._setup_ui()
        self._load_wallpaper()
        self._check_auto_login()
        self.showFullScreen()

    # ── painting: live wallpaper + ambient layer ──

    def paintEvent(self, event):
        painter = QPainter(self)
        if not self._base.isNull():
            painter.drawPixmap(self.rect(), self._base)
        else:
            painter.fillRect(self.rect(), QColor(COLORS["abyss_navy"]))
        # Legibility scrim so the glass card reads cleanly on any wallpaper.
        painter.fillRect(self.rect(), QColor(5, 10, 16, 110))
        if self._ambient is not None:
            self._ambient.draw(painter)
        painter.end()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._load_wallpaper()

    def _tick_ambient(self):
        if self._ambient is not None:
            self._ambient.advance(0.04)
        self.update()

    def _load_wallpaper(self):
        theme = wallpapers.get_theme() if _HAS_CORE else "abyss"
        try:
            path = wallpapers.resolve_wallpaper(
                theme, max(self.width(), 16), max(self.height(), 16),
            )
        except Exception:
            path = None
        self._base = QPixmap()
        if path and os.path.exists(path):
            pm = QPixmap(path)
            if not pm.isNull():
                w = self.width() if self.width() > 0 else pm.width()
                h = self.height() if self.height() > 0 else pm.height()
                self._base = pm.scaled(w, h, Qt.IgnoreAspectRatio,
                                       Qt.SmoothTransformation)
        animated = wallpapers.get_animated() if _HAS_CORE else True
        if animated:
            accent = wallpapers.theme_accent(theme) if _HAS_CORE else (0, 242, 194)
            size_changed = (self._ambient is None
                            or self._ambient._w != max(self.width(), 16)
                            or self._ambient._h != max(self.height(), 16))
            theme_changed = self._anim_theme != theme
            if self._ambient is None or size_changed or theme_changed:
                self._ambient = wallpapers.AmbientLayer(
                    max(self.width(), 16), max(self.height(), 16), accent=accent,
                )
                self._anim_theme = theme
            self._anim_timer.start()
        else:
            self._ambient = None
            self._anim_timer.stop()
        self.update()

    # ── UI construction ──

    def _setup_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(28, 20, 28, 20)
        outer.setSpacing(0)

        # ── Top bar: clock (right) ──
        top = QHBoxLayout()
        top.addStretch(1)
        self._clock_lbl = QLabel("")
        self._clock_lbl.setStyleSheet(f"""
            color: {COLORS["hd_white"]}; font-family: "{FONTS["mono"]}";
            font-size: 22px; font-weight: bold; background: transparent;
        """)
        top.addWidget(self._clock_lbl)
        self._date_lbl = QLabel("")
        self._date_lbl.setStyleSheet(f"""
            color: {COLORS["seafoam"]}; font-family: "{FONTS["mono"]}";
            font-size: {FONTS["size_sm"]}px; letter-spacing: 2px; background: transparent;
        """)
        top.addWidget(self._date_lbl)
        top.addSpacing(SPACING["md"])
        outer.addLayout(top)

        outer.addStretch(2)

        # ── Brand header (above the card) ──
        brand = QVBoxLayout()
        brand.setSpacing(SPACING["xs"])
        brand.setAlignment(Qt.AlignCenter)
        if _HAS_CORE:
            logo_pix = get_logo("nautilus").pixmap(72, 72)
            logo_lbl = QLabel()
            logo_lbl.setPixmap(logo_pix)
            logo_lbl.setAlignment(Qt.AlignCenter)
            logo_lbl.setStyleSheet("background: transparent;")
            brand.addWidget(logo_lbl)
        else:
            anchor = QLabel("\u2693")
            anchor.setAlignment(Qt.AlignCenter)
            anchor.setStyleSheet(f"color: {COLORS['seafoam']}; font-size: 48px; background: transparent;")
            brand.addWidget(anchor)
        brand.addSpacing(SPACING["md"])

        title = QLabel("NAUTILUS OS")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet(f"""
            color: {COLORS["seafoam"]}; font-family: "{FONTS["mono"]}";
            font-size: {FONTS["size_xxl"] + 2}px; font-weight: bold;
            letter-spacing: 8px; background: transparent;
        """)
        brand.addWidget(title)

        subtitle = QLabel("Sign in to your desktop")
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setStyleSheet(f"""
            color: {COLORS["text_secondary"]}; font-size: {FONTS["size_sm"]}px;
            background: transparent;
        """)
        brand.addWidget(subtitle)
        brand.addSpacing(SPACING["xl"])
        outer.addLayout(brand)

        # ── Centered glass card with login/register stack ──
        row = QHBoxLayout()
        row.addStretch(1)
        card = QFrame()
        card.setStyleSheet(_GLASS_CARD)
        card.setFixedWidth(440)
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(SPACING["xl"] + 8, SPACING["xl"],
                                       SPACING["xl"] + 8, SPACING["xl"])
        card_layout.setSpacing(SPACING["md"])

        self._stack = QStackedWidget()
        self._stack.setStyleSheet("background: transparent;")
        self._stack.addWidget(self._build_login_page())
        self._stack.addWidget(self._build_register_page())
        card_layout.addWidget(self._stack)

        self._error_label = QLabel("")
        self._error_label.setAlignment(Qt.AlignCenter)
        self._error_label.setWordWrap(True)
        self._error_label.setStyleSheet(f"""
            color: {COLORS["coral"]}; font-family: "{FONTS["mono"]}";
            font-size: {FONTS["size_xs"]}px; padding: 4px; min-height: 18px;
        """)
        card_layout.addWidget(self._error_label)

        row.addWidget(card)
        row.addStretch(1)
        outer.addLayout(row)

        outer.addStretch(3)

        # ── Bottom bar: watermark ──
        bottom = QHBoxLayout()
        watermark = QLabel("NAUTILUS OS  ·  v1.0")
        watermark.setStyleSheet(f"""
            color: {COLORS["text_muted"]}; font-family: "{FONTS["mono"]}";
            font-size: {FONTS["size_xs"]}px; letter-spacing: 3px; background: transparent;
        """)
        bottom.addWidget(watermark)
        bottom.addStretch(1)
        theme_hint = QLabel("")
        if _HAS_CORE:
            theme_hint.setText(f"  {wallpapers.get_theme().upper()}  ")
        theme_hint.setStyleSheet(f"""
            color: {COLORS["text_muted"]}; font-family: "{FONTS["mono"]}";
            font-size: {FONTS["size_xs"]}px; letter-spacing: 2px; background: transparent;
        """)
        bottom.addWidget(theme_hint)
        outer.addLayout(bottom)

        self._update_clock()
        clock = QTimer(self)
        clock.timeout.connect(self._update_clock)
        clock.start(1000)

    def _update_clock(self):
        self._clock_lbl.setText(time.strftime("%H:%M"))
        self._date_lbl.setText("   " + time.strftime("%a %d %b %Y").upper())

    def _build_login_page(self) -> QFrame:
        page = QFrame()
        page.setStyleSheet("background: transparent;")
        layout = QVBoxLayout(page)
        layout.setSpacing(SPACING["md"])

        lbl_u = QLabel("USERNAME")
        lbl_u.setStyleSheet(_LABEL_SS)
        layout.addWidget(lbl_u)

        self._login_user = QLineEdit()
        self._login_user.setPlaceholderText("Enter username")
        self._login_user.setStyleSheet(_FIELD_SS)
        layout.addWidget(self._login_user)

        lbl_p = QLabel("PASSWORD")
        lbl_p.setStyleSheet(_LABEL_SS)
        layout.addWidget(lbl_p)

        self._login_pass = QLineEdit()
        self._login_pass.setPlaceholderText("Enter password")
        self._login_pass.setEchoMode(QLineEdit.Password)
        self._login_pass.setStyleSheet(_FIELD_SS)
        self._login_pass.returnPressed.connect(self._do_login)
        layout.addWidget(self._login_pass)

        # Show-password toggle + remember-me row
        toggles = QHBoxLayout()
        toggles.setSpacing(SPACING["md"])
        self._show_pass_cb = QCheckBox("Show password")
        self._show_pass_cb.setStyleSheet(f"color: {COLORS['text_secondary']}; font-family: '{FONTS['mono']}'; font-size: {FONTS['size_xs']}px;")
        self._show_pass_cb.toggled.connect(
            lambda on: self._login_pass.setEchoMode(
                QLineEdit.Normal if on else QLineEdit.Password)
        )
        toggles.addWidget(self._show_pass_cb)

        self._remember_cb = QCheckBox("Remember me (auto-login)")
        self._remember_cb.setStyleSheet(f"color: {COLORS['text_secondary']}; font-family: '{FONTS['mono']}'; font-size: {FONTS['size_xs']}px;")
        toggles.addWidget(self._remember_cb)
        toggles.addStretch(1)
        layout.addLayout(toggles)

        layout.addSpacing(SPACING["sm"])

        login_btn = QPushButton("SIGN IN")
        login_btn.setStyleSheet(_PRIMARY_BTN_SS)
        login_btn.clicked.connect(self._do_login)
        layout.addWidget(login_btn)

        switch = QPushButton("Create new account")
        switch.setStyleSheet(_GHOST_BTN_SS)
        switch.clicked.connect(lambda: self._stack.setCurrentIndex(1))
        layout.addWidget(switch)

        return page

    def _build_register_page(self) -> QFrame:
        page = QFrame()
        page.setStyleSheet("background: transparent;")
        layout = QVBoxLayout(page)
        layout.setSpacing(SPACING["md"])

        title = QLabel("CREATE ACCOUNT")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet(f"color: {COLORS['seafoam']}; font-family: '{FONTS['mono']}'; font-size: {FONTS['size_md']}px; font-weight: bold;")
        layout.addWidget(title)

        lbl_d = QLabel("DISPLAY NAME")
        lbl_d.setStyleSheet(_LABEL_SS)
        layout.addWidget(lbl_d)

        self._reg_display = QLineEdit()
        self._reg_display.setPlaceholderText("Your name")
        self._reg_display.setStyleSheet(_FIELD_SS)
        layout.addWidget(self._reg_display)

        lbl_u = QLabel("USERNAME")
        lbl_u.setStyleSheet(_LABEL_SS)
        layout.addWidget(lbl_u)

        self._reg_user = QLineEdit()
        self._reg_user.setPlaceholderText("Choose username")
        self._reg_user.setStyleSheet(_FIELD_SS)
        layout.addWidget(self._reg_user)

        lbl_p = QLabel("PASSWORD")
        lbl_p.setStyleSheet(_LABEL_SS)
        layout.addWidget(lbl_p)

        self._reg_pass = QLineEdit()
        self._reg_pass.setPlaceholderText("Choose password (min 8 chars, letters + numbers)")
        self._reg_pass.setEchoMode(QLineEdit.Password)
        self._reg_pass.setStyleSheet(_FIELD_SS)
        self._reg_pass.returnPressed.connect(self._do_register)
        layout.addWidget(self._reg_pass)

        layout.addSpacing(SPACING["sm"])

        reg_btn = QPushButton("CREATE ACCOUNT")
        reg_btn.setStyleSheet(_PRIMARY_BTN_SS)
        reg_btn.clicked.connect(self._do_register)
        layout.addWidget(reg_btn)

        switch = QPushButton("\u2190  Back to sign in")
        switch.setStyleSheet(_GHOST_BTN_SS)
        switch.clicked.connect(lambda: self._stack.setCurrentIndex(0))
        layout.addWidget(switch)

        return page

    def _do_login(self):
        username = self._login_user.text().strip()
        password = self._login_pass.text()

        if not username or not password:
            self._error_label.setText("Please enter username and password")
            return

        account = verify_login(username, password)
        if account:
            save_session(account["username"], self._remember_cb.isChecked())
            self._logged_in_user = account["username"]
            self._logged_in_account = account
            self.accept()
        else:
            self._error_label.setText("Invalid username or password")
            self._login_pass.selectAll()

    def _do_register(self):
        username = self._reg_user.text().strip()
        password = self._reg_pass.text()
        display = self._reg_display.text().strip() or username

        if not username or len(username) < 2:
            self._error_label.setText("Username must be at least 2 characters")
            return

        ok, policy_msg = password_policy_ok(password)
        if not ok:
            self._error_label.setText(policy_msg)
            return

        try:
            if create_account(username, password, display):
                # Auto-login after registration
                account = verify_login(username, password)
                self._logged_in_user = username
                self._logged_in_account = account
                self.accept()
            else:
                self._error_label.setText("Username already exists")
        except ValueError as e:
            self._error_label.setText(str(e))

    def _check_auto_login(self):
        """Try auto-login from saved session."""
        saved_user = load_session()
        if saved_user and get_account(saved_user):
            self._logged_in_user = saved_user
            self._logged_in_account = get_account(saved_user)
            self.accept()

    def get_logged_in_user(self) -> str | None:
        return self._logged_in_user

    def get_account(self) -> dict | None:
        return self._logged_in_account
