#!/usr/bin/env python3
"""
Nautilus — Application Smoke Test
Launches every registered app standalone (offscreen) with a watchdog,
verifies it stays alive for N seconds, then terminates it.

Usage:  py -3.13 tests/smoke_test.py [--duration 4] [--app cinema]
"""

import sys
import os
import time
import subprocess
import argparse

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from core.launcher import APP_MANIFEST  # noqa: E402

# Apps that require heavy native deps not installed in this environment.
KNOWN_BROKEN = {}


def smoke_app(app_id: str, duration: float) -> bool:
    entry = os.path.join(PROJECT_ROOT, APP_MANIFEST[app_id].entry)
    env = dict(os.environ)
    env["QT_QPA_PLATFORM"] = "offscreen"
    try:
        proc = subprocess.Popen(
            [sys.executable, entry],
            cwd=PROJECT_ROOT,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            env=env,
        )
    except OSError as e:
        print(f"[FAIL] {app_id}: could not spawn: {e}")
        return False

    time.sleep(duration)
    if proc.poll() is not None:
        print(f"[FAIL] {app_id}: exited early rc={proc.poll()}")
        return False

    proc.terminate()
    try:
        proc.wait(timeout=5)
    except subprocess.TimeoutExpired:
        proc.kill()
    print(f"[ OK ] {app_id}")
    return True


def main():
    parser = argparse.ArgumentParser(description="Nautilus app smoke test")
    parser.add_argument("--duration", type=float, default=4.0)
    parser.add_argument("--app", default=None, help="test a single app id")
    args = parser.parse_args()

    apps = [args.app] if args.app else list(APP_MANIFEST.keys())
    results = {}
    for app_id in apps:
        if app_id in KNOWN_BROKEN:
            print(f"[SKIP] {app_id}: {KNOWN_BROKEN[app_id]}")
            results[app_id] = None
            continue
        results[app_id] = smoke_app(app_id, args.duration)

    print("\n=== RESULTS ===")
    failed = 0
    for app_id, ok in results.items():
        status = "SKIP" if ok is None else ("PASS" if ok else "FAIL")
        if ok is False:
            failed += 1
        print(f"  {status:<4} {app_id}")
    print(f"{len(results) - failed - sum(1 for v in results.values() if v is None)}/{len([k for k in results if k not in KNOWN_BROKEN])} passed")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
