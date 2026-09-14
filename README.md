# Nautilus OS

A little desktop operating system I'm building with Python with PySide6.
I'm mainly targeting the Rasberry Pi 500, and the whole look is based around the ocean: sand colours, wood tones that kind of stuff you know.

Quick heads up: this is currently in v2. I scarrped the first version and started from strach. right now we only really have SurfLine Browser working by its self and some what of the Kraken AI system. More Details in wiki/Project-History.md

## What actually works right now

- Desktop shell in 'core/main.py'. Top bar with a clock and a nice clean wallaper, dock along the bottom to launch the apps.
- Theme file in 'core/theme.py'. All colours and fonts live in the one place so I don't have to search multiple files.
- Surfline Browser in 'apps/surfline/app.py'. Basic Qt Webengine browser with a address bar that handles URLS and search, back/forward/reload/home, a simple start page and a tab bar (tabs still need some tweaking)

A few things I tried to stick to:

- Pure python + Qt, no C stuff or system services to mess with
- No hardcoded colors in widgets, everything pulls from 'core.theme'
- Everything has a nautical name. There's a glossary in wiki/Glossary.md if names get confusing.

## What you need
- Python 3.11 or newer, 64-bit. I am developing on 3.13.
- Works on Linux / Rasberry Pi OS (Hopefully haven't tested) / Windows
- You want 1080p and OpenGL for the browser to behave. 2gb RAM runs, 8GB is a not nicer.

Python packages are in 'requirements.txt'

- Pyside6 for all the UI'
- psutil, cryptograpgy, requests, pyagme are in there for apps I'm planning (telemtry, password storage, audio) bust most of that isn't wired up yet.

Rest is just stdlib.

## Getting it Running

1. Clone it:

git clone https://github.com/MrChompDev/Nautilus.git
cd Nautilus


2. Set up a venv and install:

Linux / Pi:
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -r requirements.txt

Windows (make sure you're on 64-bit Python):
py -3.13 -m pip install -r requirements.txt

3. On Debian / Pi OS you'll need some system libs for WebEngine and audio:

sudo apt update
sudo apt install -y libnss3 libasound2 libxkbcommon0 libxkbcommon-x11-0 libgl1 libegl1 libdbus-1-3 fonts-noto-core

4. I use JetBrains Mono for the mono font, optional but looks better:

sudo apt install -y fonts-jetbrains-mono

Then run it from the repo root:

python3 core/main.py

On Windows it's `py -3.13 core/main.py`

You'll get a 1280x720 window. Top bar says NAUTILUS with a live clock,
middle is just a nice wallpaper, dock at the bottom has Surfline,
Abyssal, and Kraken and other icons. Only Surfline and Kraken does anything at the moment, the others are placeholder

## Surfline

It's just a QWebEngineView with some buttons around it. Type a domain
and it adds https for you, type anything else and it throws it at Google.
Back, forward, reload, home all work. Start page has links to Google,
YouTube, GitHub, Wikipedia. Tab strip is there visually but switching
tabs properly is still TODO.

You can open it from the dock.

## Theming

Everything visual is in `core/theme.py`. If you want to reskin the OS,
that's the file to edit.

Rough palette:
Sand backgrounds around #E8DCC8 / #D4C8B0 / #C2B49A, wood browns
around #8B6F47, coral accent #FF6F61, dark text #1A1A1A. Status colours
are the usual green/yellow/red.

Fonts are Segoe UI for UI and JetBrains Mono for code-ish stuff.
Corners are 8 / 12 / 16px. Shell bars use the same colours with some
transparency for the glass look.

Full list is in wiki/Design-System.md.

## What's next

Rebuilding the old apps one by one:

- Shell - working
- Surfline - working, tabs need fixing
- Abyssal (code editor) - not started, button is there
- Kraken AI - still packaging this bit
- Riptide, Cinema, Logbook, Mariner, Current, Harbor, Tide, Anchor, Reef - all planned

Short term stuff I need to do:
- Dock doesn't stay centered on resize, it's stuck at (440, 650)
- Real tabs in Surfline, one view per tab
- Let each app run on its own with `python3 apps/<name>/main.py`
- Get tests back under `tests/`

There's a full breakdown in wiki/Roadmap.md and a checklist in TODO.md.

## Repo layout

Nautilus/
├── core/main.py - shell
├── core/theme.py - colours/fonts
├── apps/surfline/app.py - browser
├── agents/ - example Kraken agent spec
├── models/ - AI training stuff, big folder (~196MB)
├── wiki/ - docs, start at Home.md
├── docs/ - architecture docs, mostly empty for now
├── tests/ - needs restoring
├── data/ / logs/ - runtime files

## Dev notes

Lint is ruff, line length 120:

python3 -m ruff check .

If you're running headless / CI you need:

export QT_QPA_PLATFORM=offscreen
export QTWEBENGINE_DISABLE_SANDBOX=1

General rules I try to follow: use tokens from core.theme, make sure
entry points add repo root to sys.path so you can run from anywhere,
and keep QSS scoped to widget classes with hover/pressed states.

## Docs

More in `wiki/`:

- Architecture, Shell, Surfline Browser, Design System, Roadmap,
  Project History, Glossary - all in there.

MIT License, see LICENSE.

