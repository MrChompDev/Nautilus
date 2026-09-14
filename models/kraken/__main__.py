"""Enable `python -m kraken`."""

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from models.kraken.cli import main  # noqa: E402

if __name__ == "__main__":
    main()