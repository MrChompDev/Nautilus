#!/usr/bin/env sh
# Nautilus OS — one-click launcher (Linux / Raspberry Pi OS / macOS)
# Creates a venv, installs requirements, then starts the shell.
set -e
cd "$(dirname "$0")"

if command -v python3 >/dev/null 2>&1; then
    PY=python3
elif command -v python >/dev/null 2>&1; then
    PY=python
else
    echo "ERROR: No python found. Install Python 3.11+ (64-bit) first."
    exit 1
fi

fail() {
    echo "ERROR: $1"
    echo "Tell us what happened here: https://github.com/MrChompDev/Nautilus/issues"
    exit 1
}

# Recover from a broken/partial venv (e.g. interrupted first run).
if [ -d ".venv" ] && ! [ -x ".venv/bin/python" ]; then
    echo "Found a broken .venv — rebuilding it..."
    rm -rf .venv
fi

if ! [ -x ".venv/bin/python" ]; then
    echo "Creating venv..."
    # --copies avoids symlink faliures on USB drives / exFAT / network shares.
    if ! "$PY" -m venv --copies .venv >/dev/null 2>&1; then
        echo "stdlib venv failed (common on drives without symlink support) — trying virtualenv..."
        "$PY" -m pip install --user --quiet virtualenv || \
            fail "pip could not install 'virtualenv'. Check internet access / pip availability."
        "$PY" -m virtualenv --copies .venv >/dev/null || \
            fail "Could not create a venv. On Debian / Raspberry Pi OS run: sudo apt install python3-venv python3-pip"
    fi
fi

if ! .venv/bin/python -c "import sys" >/dev/null 2>&1; then
    fail ".venv/bin/python is not runnable. Delete the .venv folder and re-run."
fi

if .venv/bin/python -c "import PySide6" >/dev/null 2>&1; then
    echo "Dependencies already installed."
else
    echo "Installing requirements (this is only slow the first time)..."
    .venv/bin/python -m pip install --quiet -r requirements.txt || {
        echo "ERROR: pip install failed. Common causes:"
        echo "  - no internet access"
        echo "  - Debian / Raspberry Pi OS: sudo apt install python3-venv python3-pip"
        echo "  - 32-bit Python detected — PySide6 needs 64-bit Python 3.11+"
        echo "Full error above. Fix it and run again."
        exit 1
    }
    echo "Install complete."
fi

# Debian / Pi OS systems need these once for WebEngine and fonts (skipped elsewhere):
if [ -f /etc/debian_version ] && ! dpkg -s libnss3 >/dev/null 2>&1; then
    echo "Installing system libs for Qt WebEngine (may ask for your password)..."
    sudo apt update -y || true
    sudo apt install -y libnss3 libasound2 libxkbcommon0 libxkbcommon-x11-0 \
        libgl1 libegl1 libdbus-1-3 fonts-noto-core fonts-jetbrains-mono || \
        echo "NOTE: system libs not installed — install them manually, the browser needs them."
fi

echo "Starting Nautilus OS..."
exec .venv/bin/python core/main.py "$@"
