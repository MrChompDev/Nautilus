"""
Nautilus OS - Application Launcher & IPC Router
Manages app manifest, process lifecycle, keyboard shortcuts, and launch routing.
"""

import os
import signal
import subprocess
import sys
from collections.abc import Callable
from dataclasses import dataclass, field

from core.logger import get_logger


@dataclass
class AppEntry:
    """Descriptor for a Nautilus application."""
    name: str
    entry: str          # Relative path to main.py from project root
    shortcut: str       # Global keyboard shortcut
    icon: str = ""      # Unicode icon glyph
    logo_id: str = ""   # Icon generator ID
    description: str = ""
    memory_target_mb: int = 0
    process: subprocess.Popen | None = field(default=None, repr=False)


# ═══════════════════════════════════════════════════════════════
#  APP MANIFEST — Master launch routing table
# ═══════════════════════════════════════════════════════════════

APP_MANIFEST: dict[str, AppEntry] = {
    "abyssal": AppEntry(
        name="Abyssal IDE",
        entry="apps/Abyssal/main.py",
        shortcut="Ctrl+Alt+A",
        icon="⬡",
        logo_id="abyssal",
        description="Multi-language code editor with syntax highlighting and integrated terminal",
        memory_target_mb=80,
    ),
    "surfline": AppEntry(
        name="Surfline Browser",
        entry="apps/Surfline/main.py",
        shortcut="Ctrl+Alt+S",
        icon="🌊",
        logo_id="surfline",
        description="High-density WebKit browser with dark mode and low-overhead tabs",
        memory_target_mb=250,
    ),
    "riptide": AppEntry(
        name="Riptide Audio",
        entry="apps/RipTide/main.py",
        shortcut="Ctrl+Alt+R",
        icon="🎵",
        logo_id="riptide",
        description="Universal audio hub with multi-provider streaming and SFX soundboard",
        memory_target_mb=60,
    ),
    "cinema": AppEntry(
        name="Cinema",
        entry="apps/Cinema/main.py",
        shortcut="Ctrl+Alt+M",
        icon="🎬",
        logo_id="cinema",
        description="Local-only media center: import your own movies & shows, full-screen playback",
        memory_target_mb=180,
    ),
    "logbook": AppEntry(
        name="Logbook",
        entry="apps/Logbook/main.py",
        shortcut="Ctrl+Alt+L",
        icon="📓",
        logo_id="logbook",
        description="Markdown notes with live preview, instant search, and auto-save",
        memory_target_mb=40,
    ),
    "mariner": AppEntry(
        name="Mariner",
        entry="apps/Mariner/main.py",
        shortcut="Ctrl+Alt+E",
        icon="🧮",
        logo_id="mariner",
        description="Scientific calculator with expression parser, history tape, and navigation helpers",
        memory_target_mb=20,
    ),
    "current": AppEntry(
        name="Current Telemetry",
        entry="apps/current/main.py",
        shortcut="Ctrl+Alt+C",
        icon="📊",
        logo_id="current",
        description="Real-time CPU, RAM, thermal, and process tree monitoring",
        memory_target_mb=15,
    ),
    "harbor": AppEntry(
        name="Harbor File Manager",
        entry="apps/harbor/main.py",
        shortcut="Ctrl+Alt+H",
        icon="📁",
        logo_id="harbor",
        description="Keyboard-first dual-pane file manager with inline previews",
        memory_target_mb=30,
    ),
    "tide": AppEntry(
        name="Tide Terminal",
        entry="apps/tide/main.py",
        shortcut="Ctrl+Alt+T",
        icon="⌨",
        logo_id="tide",
        description="GPU-accelerated multi-tab terminal emulator with IPC hooks",
        memory_target_mb=25,
    ),
    "anchor": AppEntry(
        name="Anchor Settings",
        entry="apps/anchor/main.py",
        shortcut="Ctrl+Alt+,",
        icon="⚙",
        logo_id="anchor",
        description="Control center for display, network, audio, and theme configuration",
        memory_target_mb=20,
    ),
    "kraken": AppEntry(
        name="Kraken AI",
        entry="apps/kraken/main.py",
        shortcut="Ctrl+Alt+K",
        icon="🧠",
        logo_id="kraken",
        description="Local-first agentic AI engine: chat with single agents or a parallel multi-agent workforce",
        memory_target_mb=120,
    ),
    "reef": AppEntry(
        name="Reef Messenger",
        entry="apps/Reef/main.py",
        shortcut="Ctrl+Alt+Z",
        icon="🐚",
        logo_id="reef",
        description="Local-first messenger: offline local thread + optional IMAP/SMTP mail",
        memory_target_mb=40,
    ),
}


# ═══════════════════════════════════════════════════════════════
#  LAUNCHER ENGINE
# ═══════════════════════════════════════════════════════════════

class AppLauncher:
    """Manages application lifecycle: launch, track, and terminate."""

    def __init__(self, project_root: str):
        self._project_root = project_root
        self._running: dict[str, subprocess.Popen] = {}
        self._on_launch_callbacks: list[Callable] = []
        self._on_exit_callbacks: list[Callable] = []

    @property
    def project_root(self) -> str:
        return self._project_root

    @property
    def running_apps(self) -> dict[str, subprocess.Popen]:
        return dict(self._running)

    def resolve_entry(self, app_id: str) -> str:
        """Resolve app entry point to an absolute path."""
        entry = APP_MANIFEST[app_id]
        return os.path.join(self._project_root, entry.entry)

    def launch(self, app_id: str, extra_args: list = None) -> subprocess.Popen | None:
        """Launch an application by its manifest ID.

        Returns the Popen process handle, or None if already running.
        """
        log = get_logger("LAUNCHER")

        if app_id not in APP_MANIFEST:
            log.error(f"Unknown app requested: {app_id}")
            return None

        if app_id in self._running:
            proc = self._running[app_id]
            if proc.poll() is None:
                log.debug(f"{app_id} already running (PID {proc.pid})")
                return None
            log.debug(f"{app_id} stale process cleaned up")
            del self._running[app_id]

        entry_path = self.resolve_entry(app_id)
        if not os.path.exists(entry_path):
            log.error(f"Entry not found: {entry_path}")
            return None

        args = [sys.executable, entry_path]
        if extra_args:
            args.extend(extra_args)

        try:
            proc = subprocess.Popen(
                args,
                cwd=self._project_root,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                start_new_session=True,
            )
            self._running[app_id] = proc
            log.info(f"Launched {APP_MANIFEST[app_id].name} (PID {proc.pid})")

            for cb in self._on_launch_callbacks:
                try:
                    cb(app_id, proc)
                except Exception as e:
                    log.error(f"Launch callback failed: {e}")

            return proc

        except Exception as e:
            log.error(f"Failed to launch {app_id}: {e}")
            return None

    def terminate(self, app_id: str) -> bool:
        """Gracefully terminate an application."""
        log = get_logger("LAUNCHER")
        if app_id not in self._running:
            return False

        proc = self._running[app_id]
        if proc.poll() is not None:
            del self._running[app_id]
            return True

        try:
            if sys.platform == "win32":
                proc.terminate()
            else:
                os.killpg(os.getpgid(proc.pid), signal.SIGTERM)
            proc.wait(timeout=3)
        except subprocess.TimeoutExpired:
            log.warning(f"{app_id} didn't respond, force-killing")
            proc.kill()
        except Exception as e:
            log.error(f"Error terminating {app_id}: {e}")

        del self._running[app_id]
        log.info(f"Terminated {APP_MANIFEST[app_id].name}")

        for cb in self._on_exit_callbacks:
            try:
                cb(app_id)
            except Exception as e:
                log.error(f"Exit callback failed: {e}")

        return True

    def kill(self, app_id: str) -> bool:
        """Force kill an application (SIGKILL)."""
        log = get_logger("LAUNCHER")
        if app_id not in self._running:
            return False

        proc = self._running[app_id]
        if proc.poll() is not None:
            del self._running[app_id]
            return True

        try:
            proc.kill()
            proc.wait(timeout=1)
        except Exception as e:
            log.error(f"Error killing {app_id}: {e}")

        del self._running[app_id]
        log.info(f"Force-killed {APP_MANIFEST[app_id].name}")
        return True

    def terminate_all(self):
        """Terminate all running applications."""
        log = get_logger("LAUNCHER")
        count = len(self._running)
        for app_id in list(self._running.keys()):
            self.terminate(app_id)
        log.info(f"Terminated all {count} running apps")

    def is_running(self, app_id: str) -> bool:
        """Check if an app is currently running."""
        if app_id not in self._running:
            return False
        proc = self._running[app_id]
        return proc.poll() is None

    def on_launch(self, callback: Callable):
        """Register a callback invoked when an app launches."""
        self._on_launch_callbacks.append(callback)

    def on_exit(self, callback: Callable):
        """Register a callback invoked when an app exits."""
        self._on_exit_callbacks.append(callback)

    def get_manifest(self) -> dict[str, AppEntry]:
        """Return a copy of the app manifest."""
        return dict(APP_MANIFEST)


# ═══════════════════════════════════════════════════════════════
#  GLOBAL SHORTCUT RESOLVER
# ═══════════════════════════════════════════════════════════════

def resolve_shortcut(key_sequence: str) -> str | None:
    """Given a key sequence like 'Ctrl+Alt+A', return the matching app_id."""
    for app_id, entry in APP_MANIFEST.items():
        if entry.shortcut.lower() == key_sequence.lower():
            return app_id
    return None
