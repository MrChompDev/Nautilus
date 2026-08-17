#!/usr/bin/env python3
"""Generate all four sea-creature SVG logos.

Usage: python apps/kraken/logos/generate.py
"""

import os

_LOGO_DIR = os.path.dirname(os.path.abspath(__file__))

LOGOS = {
    "kraken": {
        "color": "#00F2C2",
        "bg": "#081626",
        "desc": "Octopus with tentacles — coding model",
    },
    "leviathan": {
        "color": "#7B68EE",
        "bg": "#081626",
        "desc": "Sea serpent — writing model",
    },
    "charybdis": {
        "color": "#FF6B9D",
        "bg": "#081626",
        "desc": "Whirlpool vortex — image/video model",
    },
    "megalodon": {
        "color": "#FF4444",
        "bg": "#081626",
        "desc": "Shark — pentest model",
    },
}


def generate_all():
    for name in LOGOS:
        svg_path = os.path.join(_LOGO_DIR, f"{name}.svg")
        if os.path.exists(svg_path):
            print(f"  [exists] {name}.svg")
        else:
            print(f"  [skip]   {name}.svg — create manually or use the provided SVGs")


if __name__ == "__main__":
    print("Kraken AI — Logo Generator")
    print(f"Logo dir: {_LOGO_DIR}\n")
    generate_all()
    print("\nDone.")
