"""Nautilus OS - Project Knowledge Map

Distilled architecture of the entire codebase. Verified against source.
Run: python3 PROJECT_BRAIN.py  # quick overview
"""

import json
import sys
from pathlib import Path

# ─── Core Architecture ───
SHELL_ENTRY = "core/main.py:NautilusShell"
THEME = "core/theme.py"
LAUNCHER = "core/launcher.py"

# ─── Apps Registry (from core/launcher.py:APP_MANIFEST) ───
APPS = {
    "Surfline":   {"module": "apps.surfline.app",       "class": "SurflineWindow",   "icon": "jellyfish.svg",  "desc": "Web Browser",        "category": "core"},
    "Abyssal":    {"module": "apps.abyssal.app",        "class": "AbyssalWindow",    "icon": "anglerfish.svg", "desc": "Code Editor",        "category": "core"},
    "Kraken":     {"module": "apps.kraken.app",         "class": "KrakenWindow",     "icon": "octopus.svg",    "desc": "AI Assistant",       "category": "core"},
    "Logbook":    {"module": "apps.logbook.app",        "class": "LogbookWindow",    "icon": "turtle.svg",     "desc": "Markdown Notes",     "category": "core"},
    "Trench":     {"module": "apps.trench.app",         "class": "TrenchWindow",     "icon": "narwhal.svg",    "desc": "Document Editor",    "category": "core"},
    "Manta":      {"module": "apps.manta.app",          "class": "MantaWindow",      "icon": "manta.svg",      "desc": "Presentations",      "category": "core"},
    "Coral":      {"module": "apps.coral.app",          "class": "CoralWindow",      "icon": "crab.svg",       "desc": "Spreadsheets",       "category": "core"},
    "Drift":      {"module": "apps.drift.app",          "class": "DriftWindow",      "icon": "seahorse.svg",   "desc": "Email Client",       "category": "core"},
    "Depths":     {"module": "apps.depths.app",         "class": "DepthsWindow",     "icon": "depths.svg",     "desc": "Cybersecurity Hub",    "category": "tools"},
    "Arcade":     {"module": "apps.arcade.app",         "class": "ArcadeWindow",     "icon": "arcade.svg",     "desc": "Game Arcade",        "category": "tools"},
    "Mariner":    {"module": "apps.mariner.app",        "class": "MarinerWindow",    "icon": "mariner.svg",    "desc": "Calculator",         "category": "utility"},
    "Tide":       {"module": "apps.tide.app",           "class": "TideWindow",       "icon": "tide.svg",       "desc": "Terminal",           "category": "utility"},
    "Harbor":     {"module": "apps.harbor.app",         "class": "HarborWindow",     "icon": "harbor.svg",     "desc": "File Manager",       "category": "utility"},
    "Current":    {"module": "apps.current.app",        "class": "CurrentWindow",    "icon": "current.svg",    "desc": "System Monitor",     "category": "utility"},
    "Anchor":     {"module": "apps.anchor.app",         "class": "AnchorWindow",     "icon": "anchor.svg",     "desc": "Settings",           "category": "utility"},
    "Riptide":    {"module": "apps.riptide.app",        "class": "RiptideWindow",    "icon": "riptide.svg",    "desc": "Music Player",       "category": "media"},
}

DOCK_APPS = [
    "Surfline", "Abyssal", "Kraken", "Logbook",
    "Trench", "Manta", "Coral", "Drift",
    "Depths", "Arcade", "Tide", "Current",
]

# ─── Theme Tokens (from core/theme.py) ───
THEME_TOKENS = {
    "COLORS": {
        # Backgrounds (deep navy)
        "bg_light": "#0F1E2E", "bg_mid": "#152A3E", "bg_dark": "#0A1628",
        # Teal accents
        "teal": "#0E7C94", "teal_light": "#17A5BC", "teal_dim": "#0A5F72",
        # Ice/sky accents
        "ice": "#90C8D8", "ice_light": "#B8E0EC", "ice_dim": "#6CAEBE",
        # Coral (warm accent)
        "coral": "#FF6F61", "coral_dim": "#FF8E80", "coral_deep": "#E55B50",
        # Text (cool-tinted)
        "text": "#C8DAE4", "text_dark": "#E8F0F4", "text_muted": "#6882A0",
        # Status
        "success": "#3DC98A", "warning": "#FFB74D", "error": "#FF5252",
        # Surfaces
        "hover": "#1A3048", "pressed": "#0D1A2A", "selected": "#1A5068",
        # Borders
        "border": "#1E3A52", "border_light": "#2A4A60", "border_dark": "#14283A",
        # Legacy aliases
        "wood": "#0A5F72", "wood_light": "#17A5BC", "wood_dark": "#0A1628",
        # Gamification
        "gold": "#FFD700", "gold_dim": "#B8960F", "xp_blue": "#4FC3F7",
        # Cybersec status
        "scan_green": "#00E676", "alert_red": "#FF1744", "stealth": "#7C4DFF", "warning_alt": "#FF9100",
        # Arcade
        "arcade_pink": "#FF4081", "arcade_cyan": "#00E5FF",
    },
    "FONTS": {
        "ui": "Segoe UI", "mono": "JetBrains Mono",
        "size_xs": 10, "size_sm": 12, "size_md": 14, "size_lg": 16,
        "size_xl": 18, "size_xxl": 20, "size_title": 24,
    },
    "RADIUS": {"sm": "8px", "md": "12px", "lg": "16px"},
}

# ─── Kraken AI Engine (models/kraken/) ───
KRAKEN_ENGINE = {
    "cli": "models/kraken/cli.py",
    "agent": "models/kraken/agent.py",
    "commands": "models/kraken/commands.py",
    "mcp": "models/kraken/mcp.py",
    "providers": "models/kraken/providers.py",
    "config": "models/kraken/config.py",
    "session": "models/kraken/session.py",
    "router": "models/kraken/router.py",
    "description": "Local-first agentic engine, pure stdlib. CLI + PySide6 GUI. Engine never touches Qt (event queue).",
}

# ─── Image Gen Engine (models/imggen/) ───
IMGEN_ENGINE = {
    "engine": "models/imggen/engine.py",
    "train": "models/imggen/train.py",
    "model": "models/imggen/model.py",
    "generate": "models/imggen/generate.py",
    "data": "models/imggen/data.py",
}

# ─── LM Engine (models/lm/) ───
LM_ENGINE = {
    "bpe": "models/lm/bpe.py",
    "export": "models/lm/export.py",
    "make_corpora": "models/lm/make_corpora.py",
    "cli": "models/lm/cli.py",
    "engine": "models/lm/engine.py",
    "train": "models/lm/train.py",
    "model": "models/lm/model.py",
}

# ─── Depths Tools (apps/depths/tools/) ───
DEPTHS_TOOLS = {
    "security_headers": "apps/depths/tools/security_headers.py",
    "cert_search": "apps/depths/tools/cert_search.py",
    "packet_injector": "apps/depths/tools/packet_injector.py",
    "wifi_analyzer": "apps/depths/tools/wifi_analyzer.py",
    "social_mapper": "apps/depths/tools/social_mapper.py",
    "rsa_playground": "apps/depths/tools/rsa_playground.py",
    "caesar_wheel": "apps/depths/tools/caesar_wheel.py",
    "hash_cracker": "apps/depths/tools/hash_cracker.py",
    "cipher_challenges": "apps/depths/tools/cipher_challenges.py",
    "timeline_builder": "apps/depths/tools/timeline_builder.py",
    "steganography": "apps/depths/tools/steganography.py",
    "disk_analyzer": "apps/depths/tools/disk_analyzer.py",
    "memory_forensics": "apps/depths/tools/memory_forensics.py",
    "malware_sandbox": "apps/depths/tools/malware_sandbox.py",
    "threat_hunter": "apps/depths/tools/threat_hunter.py",
    "incident_responder": "apps/depths/tools/incident_responder.py",
    "firewall_manager": "apps/depths/tools/firewall_manager.py",
    "log_analyzer": "apps/depths/tools/log_analyzer.py",
    "sql_injector": "apps/depths/tools/sql_injector.py",
    "payload_craft": "apps/depths/tools/payload_craft.py",
    "hash_analyzer": "apps/depths/tools/hash_analyzer.py",
    "password_cracker": "apps/depths/tools/password_cracker.py",
    "exploit_builder": "apps/depths/tools/exploit_builder.py",
    "vuln_scanner": "apps/depths/tools/vuln_scanner.py",
    "packet_capture": "apps/depths/tools/packet_capture.py",
    "subdomain_finder": "apps/depths/tools/subdomain_finder.py",
    "dns_enum": "apps/depths/tools/dns_enum.py",
    "whois_lookup": "apps/depths/tools/whois_lookup.py",
    "network_map": "apps/depths/tools/network_map.py",
    "port_scanner": "apps/depths/tools/port_scanner.py",
}

# ─── Design Patterns / Conventions ───
DESIGN_PATTERNS = [
    "Every app bootstrap: inject project root into sys.path → QApplication → theme stylesheet",
    "Widgets never hardcode colors/fonts/radii; all read from core.theme",
    "Entry points add repo root to sys.path so modules run from any cwd",
    "Scope QSS rules to widget classes; style normal/:hover/:pressed states",
    "App classes follow *Window naming (SurflineWindow, KrakenWindow, etc.)",
    "Dock apps defined in DOCK_APPS list, launched via core.launcher.launch_app()",
    "Theme uses rgba for glass effects (alpha ~180/255 on surfaces)",
    "Gamification profile in core/profile.py (XP, level, coins, daily login)",
    "Surfline: Qt WebEngine + AdBlocker + password vault + search integration",
    "Depths: 25+ cybersecurity tools under apps/depths/tools/, each a standalone class",
]

# ─── Dev Commands ───
COMMANDS = {
    "lint": "ruff check .",
    "shell": "python3 core/main.py  # or: py -3.13 core/main.py (Windows)",
    "tests": "python3 tests/smoke_test.py  # and python3 tests/test_kraken_*.py",
    "headless_ci": "export QT_QPA_PLATFORM=offscreen && export QTWEBENGINE_DISABLE_SANDBOX=1",
}

# ─── Query API ───
def app(name: str) -> dict:
    """Return knowledge dict for one app."""
    return APPS.get(name, {"error": f"App '{name}' not found"})

def find(symbol: str) -> dict:
    """Locate any class/function by name across known files."""
    results = []
    # Check apps
    for aname, ainfo in APPS.items():
        if symbol.lower() in ainfo["class"].lower() or symbol.lower() in aname.lower():
            results.append({"type": "app_class", "app": aname, "class": ainfo["class"], "file": ainfo["module"].replace(".", "/") + ".py"})
    # Check shell components
    shell_symbols = ["TopBar", "AppButton", "Dock", "WallpaperWidget", "NautilusShell", "TopBar", "AppButton", "Dock", "WallpaperWidget", "NautilusShell"]
    for s in shell_symbols:
        if symbol.lower() in s.lower():
            results.append({"type": "shell_component", "class": s, "file": "core/main.py"})
    # Check theme tokens
    for cat, tokens in THEME_TOKENS.items():
        for k in tokens:
            if symbol.lower() in k.lower():
                results.append({"type": "theme_token", "category": cat, "key": k, "value": tokens[k]})
    # Check Depths tools
    for tname, tfile in DEPTHS_TOOLS.items():
        if symbol.lower() in tname.lower():
            results.append({"type": "depths_tool", "name": tname, "file": tfile})
    return {"query": symbol, "matches": results}

def manifest() -> dict:
    """Return APP_MANIFEST routing table."""
    return {"apps": APPS, "dock_order": DOCK_APPS}

def commands() -> dict:
    """Return dev commands."""
    return COMMANDS

def design_patterns() -> list:
    """Return conventions."""
    return DESIGN_PATTERNS

def dump() -> dict:
    """JSON snapshot for fast machine parsing."""
    return {
        "shell": SHELL_ENTRY,
        "theme": THEME,
        "launcher": LAUNCHER,
        "apps": APPS,
        "dock_apps": DOCK_APPS,
        "theme_tokens": THEME_TOKENS,
        "kraken_engine": KRAKEN_ENGINE,
        "imggen_engine": IMGEN_ENGINE,
        "lm_engine": LM_ENGINE,
        "depths_tools": DEPTHS_TOOLS,
        "design_patterns": DESIGN_PATTERNS,
        "commands": COMMANDS,
    }

# ─── CLI ───
if __name__ == "__main__":
    if len(sys.argv) > 1:
        cmd = sys.argv[1]
        if cmd == "app" and len(sys.argv) > 2:
            print(json.dumps(app(sys.argv[2]), indent=2))
        elif cmd == "find" and len(sys.argv) > 2:
            print(json.dumps(find(sys.argv[2]), indent=2))
        elif cmd == "manifest":
            print(json.dumps(manifest(), indent=2))
        elif cmd == "commands":
            print(json.dumps(commands(), indent=2))
        elif cmd == "patterns":
            print(json.dumps(design_patterns(), indent=2))
        elif cmd == "dump":
            print(json.dumps(dump(), indent=2))
        else:
            print("Usage: python3 PROJECT_BRAIN.py [app <name> | find <symbol> | manifest | commands | patterns | dump]")
    else:
        # Quick overview
        d = dump()
        print(f"Nautilus OS — Project Brain")
        print(f"  Shell: {d['shell']}")
        print(f"  Theme: {d['theme']}")
        print(f"  Launcher: {d['launcher']}")
        print(f"  Apps registered: {len(d['apps'])}")
        print(f"  Dock apps: {len(d['dock_apps'])}")
        print(f"  Theme token categories: {list(d['theme_tokens'].keys())}")
        print(f"  Kraken engine: {d['kraken_engine']['description'][:60]}...")
        print(f"  Depths tools: {len(d['depths_tools'])}")
        print(f"  Design patterns: {len(d['design_patterns'])}")
        print(f"  Commands: {list(d['commands'].keys())}")
        print(f"\nRun: python3 PROJECT_BRAIN.py dump  # full JSON snapshot")