"""Nautilus OS - App Registry

Central manifest mapping app names to their modules, classes, and icons.
Replaces the hardcoded if/elif chain in main.py.
"""

import importlib

APP_MANIFEST = {
    "Surfline": {
        "module": "apps.surfline.app",
        "class": "SurflineWindow",
        "icon": "jellyfish.svg",
        "desc": "Web Browser",
        "category": "core",
    },
    "Abyssal": {
        "module": "apps.abyssal.app",
        "class": "AbyssalWindow",
        "icon": "anglerfish.svg",
        "desc": "Code Editor",
        "category": "core",
    },
    "Kraken": {
        "module": "apps.kraken.app",
        "class": "KrakenWindow",
        "icon": "octopus.svg",
        "desc": "AI Assistant",
        "category": "core",
    },
    "Logbook": {
        "module": "apps.logbook.app",
        "class": "LogbookWindow",
        "icon": "turtle.svg",
        "desc": "Markdown Notes",
        "category": "core",
    },
    "Trench": {
        "module": "apps.trench.app",
        "class": "TrenchWindow",
        "icon": "narwhal.svg",
        "desc": "Document Editor",
        "category": "core",
    },
    "Manta": {
        "module": "apps.manta.app",
        "class": "MantaWindow",
        "icon": "manta.svg",
        "desc": "Presentations",
        "category": "core",
    },
    "Coral": {
        "module": "apps.coral.app",
        "class": "CoralWindow",
        "icon": "crab.svg",
        "desc": "Spreadsheets",
        "category": "core",
    },
    "Drift": {
        "module": "apps.drift.app",
        "class": "DriftWindow",
        "icon": "seahorse.svg",
        "desc": "Email Client",
        "category": "core",
    },
    "Depths": {
        "module": "apps.depths.app",
        "class": "DepthsWindow",
        "icon": "depths.svg",
        "desc": "Cybersecurity Hub",
        "category": "tools",
    },
    "Arcade": {
        "module": "apps.arcade.app",
        "class": "ArcadeWindow",
        "icon": "arcade.svg",
        "desc": "Game Arcade",
        "category": "tools",
    },
    "Mariner": {
        "module": "apps.mariner.app",
        "class": "MarinerWindow",
        "icon": "mariner.svg",
        "desc": "Calculator",
        "category": "utility",
    },
    "Tide": {
        "module": "apps.tide.app",
        "class": "TideWindow",
        "icon": "tide.svg",
        "desc": "Terminal",
        "category": "utility",
    },
    "Harbor": {
        "module": "apps.harbor.app",
        "class": "HarborWindow",
        "icon": "harbor.svg",
        "desc": "File Manager",
        "category": "utility",
    },
    "Current": {
        "module": "apps.current.app",
        "class": "CurrentWindow",
        "icon": "current.svg",
        "desc": "System Monitor",
        "category": "utility",
    },
    "Anchor": {
        "module": "apps.anchor.app",
        "class": "AnchorWindow",
        "icon": "anchor.svg",
        "desc": "Settings",
        "category": "utility",
    },
    "Riptide": {
        "module": "apps.riptide.app",
        "class": "RiptideWindow",
        "icon": "riptide.svg",
        "desc": "Music Player",
        "category": "media",
    },
}

DOCK_APPS = [
    "Surfline", "Abyssal", "Kraken", "Logbook",
    "Trench", "Manta", "Coral", "Drift",
    "Depths", "Arcade", "Tide", "Current",
]


def get_manifest():
    return APP_MANIFEST


def get_app_info(app_name):
    return APP_MANIFEST.get(app_name)


def get_dock_apps():
    return [
        {"name": name, **APP_MANIFEST[name]}
        for name in DOCK_APPS
        if name in APP_MANIFEST
    ]


def launch_app(app_name, shell):
    info = APP_MANIFEST.get(app_name)
    if info is None:
        return None
    mod = importlib.import_module(info["module"])
    cls = getattr(mod, info["class"])
    window = cls()
    window.show()
    return window
