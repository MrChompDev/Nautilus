#!/usr/bin/env python3
"""
Kraken AI — zero-cost, local-first agentic engine and multi-agent workforce.

Entry-point shim: `python3 kraken.py [args]` (or `kraken` when installed).
Delegates to apps/kraken/cli.py.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from apps.kraken.cli import main  # noqa: E402

if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        print("\n[interrupted]")
        raise SystemExit(130) from None
