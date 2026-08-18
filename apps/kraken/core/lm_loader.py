"""Kraken AI — LM loader helper.

Resolves the import of models.lm.engine.LM correctly even when
apps.kraken.models shadows the top-level models/ package.
"""

from __future__ import annotations

import importlib
import os
import sys


def _project_root() -> str:
    """Walk up from this file to the project root (where models/ lives)."""
    return os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(
        os.path.dirname(os.path.abspath(__file__))
    ))))


def load_lm(trained_dir: str):
    """Load models.lm.engine.LM from a trained model directory.

    Ensures the project root is on sys.path so models.lm resolves
    to the top-level models/ package, not apps.kraken.models/.
    """
    root = _project_root()
    if root not in sys.path:
        sys.path.insert(0, root)

    # Force a fresh import to avoid the stale apps.kraken.models binding
    mod_name = "models.lm.engine"
    if mod_name in sys.modules:
        mod = sys.modules[mod_name]
    else:
        mod = importlib.import_module(mod_name)

    return mod.LM(trained_dir)
