"""
Nautilus OS — Centralized Structured Logging System

Thread-safe, color-coded, file-rotating logger integrated across all subsystems.
Categories: CORE, LAUNCHER, THEME, IPC, APP, SYSTEM, PERF
"""

import logging
import logging.handlers
import os
import sys
import threading
from datetime import datetime
from typing import Optional

# ═══════════════════════════════════════════════════════════════
#  CONFIGURATION
# ═══════════════════════════════════════════════════════════════

LOG_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "logs")
MAX_LOG_SIZE = 5 * 1024 * 1024  # 5 MB per file
BACKUP_COUNT = 7                 # Keep 7 rotated files
CONSOLE_ENABLED = True
FILE_ENABLED = True
DEFAULT_LEVEL = "DEBUG"

# ANSI color codes for console output
COLOR_MAP = {
    "DEBUG":    "\033[36m",  # Cyan
    "INFO":     "\033[32m",  # Green
    "WARN":     "\033[33m",  # Yellow
    "ERROR":    "\033[31m",  # Red
    "CRITICAL": "\033[35m",  # Magenta
    "SYSTEM":   "\033[34m",  # Blue
    "RESET":    "\033[0m",
    "DIM":      "\033[2m",
    "BOLD":     "\033[1m",
}

# Category prefixes
CATEGORIES = {
    "CORE":     "CORE",
    "LAUNCHER": "LNCH",
    "THEME":    "THME",
    "IPC":      "IPC ",
    "APP":      "APP ",
    "SYSTEM":   "SYST",
    "PERF":     "PERF",
    "UI":       "UI  ",
    "NET":      "NET ",
}


# ═══════════════════════════════════════════════════════════════
#  CUSTOM FORMATTER
# ═══════════════════════════════════════════════════════════════

class NautilusFormatter(logging.Formatter):
    """Custom formatter with Nautilus-style timestamp and category coloring."""

    def __init__(self, use_color: bool = False):
        super().__init__()
        self._use_color = use_color

    def format(self, record: logging.LogRecord) -> str:
        now = datetime.fromtimestamp(record.created)
        timestamp = now.strftime("%H:%M:%S") + f".{int(now.microsecond / 1000):03d}"

        level = record.levelname[:4].upper()
        if level == "WARN":
            level = "WARN"

        category = getattr(record, "category", "CORE")

        if self._use_color:
            reset = COLOR_MAP["RESET"]
            dim = COLOR_MAP["DIM"]
            lvl_color = COLOR_MAP.get(record.levelname, "")
            ts = f"{dim}{timestamp}{reset}"
            lvl = f"{lvl_color}{level:<5}{reset}"
            cat = f"{lvl_color}[{category}]{reset}"
            msg = record.getMessage()
            return f"{ts} {lvl} {cat} {msg}"
        else:
            return f"{timestamp} {level:<5} [{category}] {record.getMessage()}"


# ═══════════════════════════════════════════════════════════════
#  LOGGER FACTORY
# ═══════════════════════════════════════════════════════════════

class NautilusLogger:
    """Centralized logger for Nautilus OS subsystems."""

    _instance: Optional["NautilusLogger"] = None
    _lock = threading.Lock()
    _initialized = False

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if NautilusLogger._initialized:
            return
        NautilusLogger._initialized = True

        self._loggers: dict[str, logging.Logger] = {}
        self._setup_root()

    def _setup_root(self):
        """Setup root Nautilus logger with file + console handlers."""
        os.makedirs(LOG_DIR, exist_ok=True)

        self._root = logging.getLogger("nautilus")
        self._root.setLevel(getattr(logging, DEFAULT_LEVEL))

        # ── File Handler ──
        if FILE_ENABLED:
            log_path = os.path.join(LOG_DIR, "nautilus.log")
            fh = logging.handlers.RotatingFileHandler(
                log_path,
                maxBytes=MAX_LOG_SIZE,
                backupCount=BACKUP_COUNT,
                encoding="utf-8",
            )
            fh.setLevel(logging.DEBUG)
            fh.setFormatter(NautilusFormatter(use_color=False))
            self._root.addHandler(fh)

        # ── Console Handler ──
        if CONSOLE_ENABLED:
            # Windows consoles default to cp1252 and choke on the Unicode
            # banner glyphs (═, ⚓, ⏻). Reconfigure to UTF-8 with a lossy
            # fallback so logging never crashes regardless of stream encoding.
            try:
                sys.stdout.reconfigure(encoding="utf-8", errors="replace")
            except (AttributeError, OSError):
                pass
            ch = logging.StreamHandler(sys.stdout)
            ch.setLevel(logging.DEBUG)
            ch.setFormatter(NautilusFormatter(use_color=True))
            self._root.addHandler(ch)

    def get(self, category: str = "CORE") -> logging.Logger:
        """Get or create a logger for a specific subsystem category."""
        cat = CATEGORIES.get(category.upper(), category[:4].upper())

        if cat not in self._loggers:
            logger = self._root.getChild(cat)
            # Attach category to log records via a filter
            cat_filter = _CategoryFilter(cat)
            logger.addFilter(cat_filter)
            self._loggers[cat] = logger

        return self._loggers[cat]

    def set_level(self, level: str):
        """Change global log level at runtime."""
        self._root.setLevel(getattr(logging, level.upper()))


class _CategoryFilter(logging.Filter):
    """Injects category into log records."""

    def __init__(self, category: str):
        super().__init__()
        self._category = category

    def filter(self, record: logging.LogRecord) -> bool:
        record.category = self._category
        return True


# ═══════════════════════════════════════════════════════════════
#  CONVENIENCE GLOBAL ACCESSOR
# ═══════════════════════════════════════════════════════════════

def get_logger(category: str = "CORE") -> logging.Logger:
    """Get a Nautilus logger for the given category.

    Usage:
        log = get_logger("LAUNCHER")
        log.info("Starting application...")
        log.error("Failed to launch", exc_info=True)
    """
    return NautilusLogger().get(category)


# ═══════════════════════════════════════════════════════════════
#  STARTUP / SHUTDOWN LOGGING
# ═══════════════════════════════════════════════════════════════

def log_startup():
    """Log system startup banner."""
    log = get_logger("SYSTEM")
    log.info("══════════════════════════════════════════════════")
    log.info("  ⚓  NAUTILUS OS  v1.0  —  System Boot")
    log.info(f"  Timestamp : {datetime.now().isoformat()}")
    log.info(f"  Platform  : {sys.platform}")
    log.info(f"  Python    : {sys.version.split()[0]}")
    log.info(f"  PID       : {os.getpid()}")
    log.info("══════════════════════════════════════════════════")


def log_shutdown():
    """Log system shutdown."""
    log = get_logger("SYSTEM")
    log.info("══════════════════════════════════════════════════")
    log.info("  ⏻  NAUTILUS OS  —  System Shutdown")
    log.info("══════════════════════════════════════════════════")


def log_app_launch(app_id: str, pid: int):
    """Log application launch."""
    log = get_logger("LAUNCHER")
    log.info(f"App launched: {app_id} (PID {pid})")


def log_app_exit(app_id: str, exit_code: int = 0):
    """Log application exit."""
    log = get_logger("LAUNCHER")
    if exit_code == 0:
        log.info(f"App exited cleanly: {app_id}")
    else:
        log.warning(f"App exited with code {exit_code}: {app_id}")


def log_perf(operation: str, elapsed_ms: float):
    """Log a performance metric."""
    log = get_logger("PERF")
    log.debug(f"{operation}: {elapsed_ms:.2f} ms")
