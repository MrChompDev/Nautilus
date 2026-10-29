#!/usr/bin/env python3
"""Builds a downloadable, testable release zip of Nautilus OS.

Usage:
    python3 scripts/build_release.py                       # dist/Nautilus-OS-<version>.zip
    python3 scripts/build_release.py --with-models         # adds the trained Kraken models (no checkpoints)
    python3 scripts/build_release.py --out dist/custom.zip

The zip contains a runnable copy of the project (launchers included) with a
top-level "Nautilus/" folder, so testers can unzip and double-click run.sh /
run.bat. Heavy junk (git history, venvs, caches, training corpora, checkpoint
history) is never bundled.
"""

import argparse
import os
import zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ZIP_NAME = "Nautilus"

# Everything that must be in the bundle for it to actually run / be testable.
REQUIRED_FILES = [
    "core",
    "apps",
    "assets",
    "agents",
    "kraken",
    "tests",
    "wiki",
    "docs",
    "models",  # code; heavy sub-paths are stripped by the rules below
    "requirements.txt",
    "run.sh",
    "run.bat",
    "pyproject.toml",
    "ruff.toml",
    "README.md",
    "LICENSE",
    "TODO.md",
    "PLAN.md",
    "PROJECT_BRAIN.py",
]

# Directory names that are runtime/build noise and must never ship.
SKIP_DIRS = {
    "__pycache__",
    ".ruff_cache",
    ".mypy_cache",
    "logs",
    "pipcache",
    "profiles",
}

CRITICAL_FILES = ("requirements.txt", "run.sh", "run.bat")


def _skip_dir(dirname: str) -> bool:
    return dirname in SKIP_DIRS or dirname.startswith(".venv")


def _wanted(relpath: str, with_models: bool) -> bool:
    """Decide if relpath (repo-relative, using os separators) goes in the zip."""
    parts = relpath.split(os.sep)
    top = parts[0]
    if top not in REQUIRED_FILES or top.startswith("."):
        return False

    if parts[0:2] == ["models", "trained"]:
        # Local Kraken models only ship with --with-models, and never with the
        # huge per-step checkpoint history of an already-final model.
        return with_models and "checkpoints" not in parts

    if parts[0:2] == ["models", "data"]:
        return False  # training corpora — not needed to test the OS

    if "checkpoints" in parts:
        return False

    return True


def build_zip(out_path: str, with_models: bool) -> int:
    entries: list[tuple[str, str]] = []  # (repo-relative, zip-relative)
    for name in sorted(REQUIRED_FILES):
        src = os.path.join(ROOT, name)
        if not os.path.exists(src):
            print(f"  [skip] missing: {name}")
            continue
        if os.path.isfile(src):
            entries.append((name, name))
            continue
        for dirpath, dirnames, filenames in os.walk(src):
            dirnames[:] = sorted(d for d in dirnames if not _skip_dir(d))
            for fname in sorted(filenames):
                rel = os.path.relpath(os.path.join(dirpath, fname), ROOT)
                if _wanted(rel, with_models):
                    entries.append((rel, rel))

    missing = [f for f in CRITICAL_FILES if f not in dict(entries)]
    if missing:
        raise SystemExit(f"bundle would miss critical files: {missing}")

    entries.sort(key=lambda e: e[1])
    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    with zipfile.ZipFile(out_path, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
        for rel, arc in entries:
            zf.write(os.path.join(ROOT, rel), os.path.join(ZIP_NAME, arc.replace(os.sep, "/")))
    size_mb = os.path.getsize(out_path) / (1024 * 1024)
    print(f"Wrote {out_path}  ({len(entries)} files, {size_mb:.1f} MB)")
    return len(entries)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--version", default="dev", help="version string used in the filename")
    ap.add_argument("--with-models", action="store_true", help="bundle trained Kraken models (no checkpoint history)")
    ap.add_argument("--out", default=None, help="output path (default dist/Nautilus-OS-<version>.zip)")
    args = ap.parse_args()

    out = args.out or os.path.join(ROOT, "dist", f"Nautilus-OS-{args.version}.zip")
    build_zip(out, args.with_models)


if __name__ == "__main__":
    main()
