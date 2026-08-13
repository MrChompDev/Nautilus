"""
Kraken AI — engine logger.

Bridges into the Nautilus structured logger when running inside the OS and
falls back to a minimal stdlib logger when Kraken runs standalone.
"""

import logging
import os
import sys

from apps.kraken.engine import __version__

_log: logging.Logger | None = None


def engine_logger() -> logging.Logger:
    """Return the Kraken engine logger (cached)."""
    global _log
    if _log is not None:
        return _log
    try:
        sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
        from core.logger import get_logger

        _log = get_logger("KRK")
    except Exception:
        _log = logging.getLogger("kraken")
        _log.addHandler(logging.NullHandler())
        _log.setLevel(logging.INFO)
    return _log


def engine_version() -> str:
    return __version__
