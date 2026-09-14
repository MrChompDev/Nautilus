"""Kraken — top-level entry shim so `python -m kraken` works from the repo root.

The real implementation lives in `models/kraken/`; this package only wires it
into the module path.
"""

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from models.kraken.router import available_models, route  # noqa: E402
from models.kraken.session import Session  # noqa: E402

__version__ = "1.0.0"
__all__ = ["available_models", "route", "Session", "__version__"]