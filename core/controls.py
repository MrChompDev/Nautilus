"""
Nautilus OS — control/button icon helper.

Uniform access to the AI-generated control glyphs in assets/controls with a
QStyle standard-icon fallback so nothing crashes if an asset is missing.
Shell and apps use `control_icon(...)`/`control_pixmap(...)` instead of
hard-coded text glyphs or ad-hoc QStyle lookups.
"""

import os

from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QIcon, QPixmap
from PySide6.QtWidgets import QApplication, QStyle

from core.ai_assets import CONTROL_PROMPTS, CONTROLS_DIR

# QStyle fallback per control name (only when no PNG asset exists).
_FALLBACKS = {
    "play": QStyle.StandardPixmap.SP_MediaPlay,
    "pause": QStyle.StandardPixmap.SP_MediaPause,
    "stop": QStyle.StandardPixmap.SP_MediaStop,
    "skip_forward": QStyle.StandardPixmap.SP_MediaSkipForward,
    "skip_back": QStyle.StandardPixmap.SP_MediaSkipBackward,
    "restart": QStyle.StandardPixmap.SP_BrowserReload,
    "refresh": QStyle.StandardPixmap.SP_BrowserReload,
    "close": QStyle.StandardPixmap.SP_TitleBarCloseButton,
    "minimize": QStyle.StandardPixmap.SP_TitleBarMinButton,
    "maximize": QStyle.StandardPixmap.SP_TitleBarMaxButton,
    "restore": QStyle.StandardPixmap.SP_TitleBarNormalButton,
    "chevron_up": QStyle.StandardPixmap.SP_ArrowUp,
    "chevron_down": QStyle.StandardPixmap.SP_ArrowDown,
    "chevron_left": QStyle.StandardPixmap.SP_ArrowLeft,
    "chevron_right": QStyle.StandardPixmap.SP_ArrowRight,
    "arrow_up": QStyle.StandardPixmap.SP_ArrowUp,
    "arrow_down": QStyle.StandardPixmap.SP_ArrowDown,
    "arrow_left": QStyle.StandardPixmap.SP_ArrowLeft,
    "arrow_right": QStyle.StandardPixmap.SP_ArrowRight,
    "search": QStyle.StandardPixmap.SP_FileDialogContentsView,
    "folder": QStyle.StandardPixmap.SP_DirIcon,
    "file": QStyle.StandardPixmap.SP_FileIcon,
    "trash": QStyle.StandardPixmap.SP_TrashIcon,
    "info": QStyle.StandardPixmap.SP_MessageBoxInformation,
    "warning": QStyle.StandardPixmap.SP_MessageBoxWarning,
    "error": QStyle.StandardPixmap.SP_MessageBoxCritical,
    "home": QStyle.StandardPixmap.SP_DirHomeIcon,
    "settings": QStyle.StandardPixmap.SP_FileDialogDetailedView,
    "dialog_ok": QStyle.StandardPixmap.SP_DialogOkButton,
    "dialog_cancel": QStyle.StandardPixmap.SP_DialogCancelButton,
    "dialog_apply": QStyle.StandardPixmap.SP_DialogApplyButton,
    "computer": QStyle.StandardPixmap.SP_ComputerIcon,
    "desktop": QStyle.StandardPixmap.SP_DesktopIcon,
    "drive": QStyle.StandardPixmap.SP_DriveHDIcon,
    "dir_open": QStyle.StandardPixmap.SP_DirOpenIcon,
    "link": QStyle.StandardPixmap.SP_FileLinkIcon,
    "message": QStyle.StandardPixmap.SP_MessageBoxInformation,
    "dir_closed": QStyle.StandardPixmap.SP_DirClosedIcon,
    "dir_link": QStyle.StandardPixmap.SP_DirLinkIcon,
}


def control_path(name: str) -> str | None:
    """Absolute path to a cached control icon PNG, or None."""
    path = os.path.join(CONTROLS_DIR, f"{name}.png")
    return path if os.path.isfile(path) else None


def has_control(name: str) -> bool:
    return name in CONTROL_PROMPTS and control_path(name) is not None


def _style() -> QStyle:
    return QApplication.style()


def control_pixmap(name: str, size: int = 24) -> QPixmap:
    """Return the control icon as a pixmap, falling back to QStyle."""
    path = control_path(name)
    if path:
        pm = QPixmap(path)
        if not pm.isNull():
            return pm.scaled(
                size, size, Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
    standard = _FALLBACKS.get(name)
    if standard is not None:
        pm = _style().standardIcon(standard).pixmap(QSize(size, size))
        if not pm.isNull():
            return pm
    return QPixmap(size, size)


def control_icon(name: str) -> QIcon:
    """Return the control as a QIcon, falling back to QStyle standard icons."""
    path = control_path(name)
    if path:
        icon = QIcon(path)
        if not icon.isNull():
            return icon
    standard = _FALLBACKS.get(name)
    if standard is not None:
        icon = _style().standardIcon(standard)
        if not icon.isNull():
            return icon
    return QIcon()


def ensure_all_controls() -> list[str]:
    """Generate any missing control icons via the ComfyUI pipeline."""
    missing = [n for n in CONTROL_PROMPTS if control_path(n) is None]
    if not missing:
        return []
    from core.ai_assets import generate_controls

    return generate_controls()
