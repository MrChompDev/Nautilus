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
    echo "No python found. Install Python 3.11+ (64-bit) first."
    exit 1
fi

if [ ! -d ".venv" ]; then
    echo "Creating venv..."
    "$PY" -m venv .venv
fi

echo "Checking dependencies..."
.venv/bin/python -c "import PySide6" 2>/dev/null \
    || .venv/bin/python -m pip install --quiet -r requirements.txt

# Debian / Pi OS systems need these once (ignored on other distros):
if [ -f /etc/debian_version ] && ! dpkg -s libnss3 >/dev/null 2>&1; then
    echo "Installing system libs for Qt WebEngine (may ask for your password)..."
    sudo apt update -y
    sudo apt install -y libnss3 libasound2 libxkbcommon0 libxkbcommon-x11-0 \
        libgl1 libegl1 libdbus-1-3 fonts-noto-core fonts-jetbrains-mono
fi

exec .venv/bin/python core/main.py "$@"
