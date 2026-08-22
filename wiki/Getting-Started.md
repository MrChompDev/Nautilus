# Getting Started

## Requirements

| Requirement | Minimum |
| :--- | :--- |
| Python | **3.11+ 64-bit** (PySide6 requires 64-bit; project targets 3.13) |
| Disk | ~1 GB free |
| Display | 1080p capable; OpenGL/GLES needed by Qt WebEngine (Surfline) |
| RAM | 2 GB works, 8 GB recommended for Pi-class targets |

## Installation

### 1. Clone

```sh
git clone https://github.com/anomalyco/Nautilus.git
cd Nautilus
```

### 2. Install Python dependencies

Linux / Raspberry Pi OS (venv recommended):

```sh
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -r requirements.txt
```

Windows (must use 64-bit Python):

```sh
py -3.13 -m pip install -r requirements.txt
```

### 3. System packages (Debian / Raspberry Pi OS)

Qt WebEngine needs a few native libraries:

```sh
sudo apt update
sudo apt install -y \
  libnss3 libasound2 libxkbcommon0 libxkbcommon-x11-0 \
  libgl1 libegl1 libdbus-1-3 fonts-noto-core
```

### 4. Recommended font

The theme references JetBrains Mono for monospace UI text:

```sh
sudo apt install -y fonts-jetbrains-mono
```

## Running

From the repository root:

```sh
python3 core/main.py        # Linux / Pi
py -3.13 core/main.py       # Windows
```

You should see the Nautilus shell window (1280×720): a top bar with the logo
and clock, a "Nautilus OS" title card in the center, and a floating dock at the
bottom with three buttons — **Surfline**, **Abyssal**, **Kraken**. Only Surfline
launches an app right now; the other two print to stdout (see
[Shell](Shell.md)).

Run Surfline standalone:

```sh
python3 apps/surfline/app.py    # note: no main() guard yet — import launches nothing,
                                # launch via the shell or add an entry point
```

See also [Architecture](Architecture.md) and [Repository Layout](Repository-Layout.md).
