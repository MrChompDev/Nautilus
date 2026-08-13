"""PROJECT_BRAIN.py — Nautilus OS project knowledge map.

Read this file instead of crawling the codebase. It is the distilled brain
of the entire project: structure, architecture, key classes/functions,
conventions, and dev commands. Everything here was verified against source.

Usage:
    import PROJECT_BRAIN as brain
    brain.app("surfline")          # dict for one app
    brain.find("AbyssalMainWindow")  # locate a class/function by name
    brain.modules()                # full module inventory
    brain.manifest()               # APP_MANIFEST table
    brain.commands()               # dev commands
    brain.design_patterns()        # conventions

No dependencies beyond the stdlib. Offline. Safe to read on every session.
"""

from __future__ import annotations

import json

# ---------------------------------------------------------------------------
# 1. PROJECT IDENTITY
# ---------------------------------------------------------------------------

PROJECT = {
    "name": "Nautilus OS",
    "version": "1.0.0",
    "build": "2026.08.01",
    "blurb": "A weightless, high-density desktop environment built for low-resource performance.",
    "target_hardware": ["Raspberry Pi 500 (ARM64, 8GB)", "x86_64 Linux"],
    "python": "3.11+ (target 3.13, 64-bit required)",
    "ram_budget": "base boot < 350 MB total",
    "aesthetic": "zero border-radius (0px), cyber-terminal, seafoam #00F2C2 on abyss navy #081626",
    "license": "MIT",
    "repo": "https://github.com/anomalyco/Nautilus",
    "root_doc": "README.md (architecture + design tokens)",
    "map_doc": "PROJECT_MAP.md (folder map + entry points + patterns)",
}

# ---------------------------------------------------------------------------
# 2. TECH STACK
# ---------------------------------------------------------------------------

STACK = {
    "language": "Python 3.11+ (64-bit, target 3.13)",
    "shell_gui": "PySide6 (Qt for Python) >=6.5.0",
    "abyssal_ui": "PySide6 (README claims PyQt5 but code imports PySide6)",
    "riptide_ui": "PySide6 >=6.5.0",
    "riptide_audio": "pygame >=2.5.0",
    "telemetry": "psutil >=5.9.0 (optional)",
    "encryption": "cryptography >=42.0 (AES-256-GCM vault in Surfline)",
    "http": "requests >=2.31.0 (RipTide); urllib/QNetworkAccessManager elsewhere",
    "lint": "ruff (ruff.toml, target py313)",
    "kraken_engine": "pure stdlib (urllib, sqlite3, threading, json) — zero mandatory deps",
    "db": "SQLite (RipTide WAL, Kraken memory.db)",
}

# Shared deps live in requirements.txt; per-app deps in apps/<App>/requirements.txt
# (only apps/kraken/requirements.txt exists).

# ---------------------------------------------------------------------------
# 3. TOP-LEVEL INVENTORY
# ---------------------------------------------------------------------------

ROOT_LAYOUT = {
    "core/": "System shell, shared runtime, security toolkit (see CORE_MODULES)",
    "apps/": "11 standalone apps, one folder each (see APPS)",
    "agents/": "Example Markdown agent specs for Kraken (DatabaseArchitect.md)",
    "assets/": "Generated logos (assets/logos/) + wallpaper.png (no binary assets committed)",
    "data/": "Runtime state: accounts.json, integrity_baseline.json, security_log.jsonl",
    "logs/": "Rotating nautilus.log output",
    "docs/": "Docs (LICENSE, README, requirements)",
    "tests/": "Smoke test + Kraken unit tests",
    "kraken.py": "Kraken AI CLI entry point shim",
    "PROJECT_MAP.md": "Human-readable project map (kept in sync)",
    "PROJECT_BRAIN.py": "This file",
    "pyproject.toml": "Kraken AI packaging (kraken + kraken-gui console scripts)",
    "requirements.txt": "Shared Python dependencies",
    "ruff.toml": "Lint config",
    ".venv/": "Virtualenv",
}

# ---------------------------------------------------------------------------
# 4. APP_MANIFEST (single source of truth in core/launcher.py)
# ---------------------------------------------------------------------------

APP_MANIFEST = [
    {"id": "abyssal", "name": "Abyssal IDE", "entry": "apps/Abyssal/main.py",
     "shortcut": "Ctrl+Alt+A", "ram_mb": 80, "ui": "PySide6", "desc": "Code editor / IDE (VS Code-inspired, layered src/)"},
    {"id": "surfline", "name": "Surfline Browser", "entry": "apps/Surfline/main.py",
     "shortcut": "Ctrl+Alt+S", "ram_mb": 250, "ui": "PySide6 + QtWebEngine", "desc": "WebKit browser, ad-block, password vault, importer"},
    {"id": "riptide", "name": "Riptide Audio", "entry": "apps/RipTide/main.py",
     "shortcut": "Ctrl+Alt+R", "ram_mb": 60, "ui": "PySide6", "desc": "Multi-provider audio + SFX hub (Spotify/YouTube/SoundCloud)"},
    {"id": "cinema", "name": "Cinema", "entry": "apps/Cinema/main.py",
     "shortcut": "Ctrl+Alt+M", "ram_mb": 180, "ui": "PySide6",      "desc": "Media center (local-only library, import your own media)"},
    {"id": "logbook", "name": "Logbook", "entry": "apps/Logbook/main.py",
     "shortcut": "Ctrl+Alt+L", "ram_mb": 40, "ui": "PySide6", "desc": "Markdown notes with live preview (single file)"},
    {"id": "mariner", "name": "Mariner", "entry": "apps/Mariner/main.py",
     "shortcut": "Ctrl+Alt+E", "ram_mb": 20, "ui": "PySide6", "desc": "Scientific calculator, recursive-descent parser (single file)"},
    {"id": "current", "name": "Current Telemetry", "entry": "apps/Current/main.py",
     "shortcut": "Ctrl+Alt+C", "ram_mb": 15, "ui": "PySide6", "desc": "System telemetry monitor (single file)"},
    {"id": "harbor", "name": "Harbor File Manager", "entry": "apps/Harbor/main.py",
     "shortcut": "Ctrl+Alt+H", "ram_mb": 30, "ui": "PySide6", "desc": "Keyboard-first dual-pane file manager (single file)"},
    {"id": "tide", "name": "Tide Terminal", "entry": "apps/Tide/main.py",
     "shortcut": "Ctrl+Alt+T", "ram_mb": 25, "ui": "PySide6", "desc": "Tabbed terminal with pure-Python internal shell"},
    {"id": "anchor", "name": "Anchor Settings", "entry": "apps/anchor/main.py",
     "shortcut": "Ctrl+Alt+,", "ram_mb": 20, "ui": "PySide6", "desc": "Control center / system settings (single file)"},
    {"id": "reef", "name": "Reef Messenger", "entry": "apps/Reef/main.py",
     "shortcut": "Ctrl+Alt+Z", "ram_mb": 40, "ui": "PySide6", "desc": "Local-first messenger: offline local thread + optional IMAP/SMTP mail"},
    {"id": "kraken", "name": "Kraken AI", "entry": "apps/kraken/main.py",
     "shortcut": "Ctrl+Alt+K", "ram_mb": 120, "ui": "PySide6 (CLI too)", "desc": "Local-first agentic AI engine + workforce"},
]

# ---------------------------------------------------------------------------
# 5. CORE MODULES (core/)
# ---------------------------------------------------------------------------

# Each entry: {file, purpose, classes: {name: what}, funcs: [..], notes}
CORE_MODULES = [
    {
        "file": "core/main.py", "lines": 1139,
        "purpose": "Desktop shell entry: login -> NautilusShell (floating glass top bar, wallpaper, glass dock, launchpad, tray, shortcuts).",
        "classes": {
            "TopBar": "Floating 40px glass pill bar (full width, side gaps): logo, running-app indicators, CPU/RAM metrics pill, avatar, clock, fullscreen + shutdown buttons. QTimers: 1s clock / 3s metrics / 2s app poll. Drag-to-move.",
            "DesktopWallpaper": "Paints generated ocean wallpaper; floating glass clock/greeting card (top-left), hint + low-alpha NAUTILUS OS watermark (bottom). Right-click QMenu (launch apps, app grid, settings, terminate, shutdown).",
            "DockButton": "Icon-only 52px glass tile with seafoam running dot; polls running state every 2s.",
            "SystemDock": "Centered floating glass dock (radius 18): launchpad toggle button, separator, one DockButton per APP_MANIFEST entry, separator, date/time chip. Drag-to-move.",
            "LaunchpadOverlay": "Full-screen dim overlay (rgba(2,6,10,215)) with centered glass panel: filter QLineEdit + 5-col grid of 128x116 app tiles. Filtering via search.match_apps; Esc closes; dock button / Meta / Ctrl+Alt+G toggle.",
            "NautilusShell": "Frameless maximized shell; owns single AppLauncher; shortcuts (F11, Ctrl+Alt+F/Q/Esc, Meta/Ctrl+Alt+G launchpad); tray menu; launcher on_launch/on_exit hooks; hide-to-tray on close.",
            "SearchOverlay": "Ctrl+Space / Ctrl+Alt+Space global search (apps + local files + web handoff via Surfline).",
        },
        "funcs": ["main() — boot: log_startup -> QApplication -> palette/stylesheet -> SIGINT/TERM handlers -> ensure_all_logos() -> LoginDialog -> NautilusShell -> app.exec()"],
        "notes": "PROJECT_ROOT inserted into sys.path before core imports. setup_qt_environment() called before any PySide6 import. Lambda default-arg binding used for closures. Glass surfaces: translucent slate via hex_to_rgba(COLORS['slate_navy'], alpha) so the painted wallpaper glows through; PANEL_RADIUS 14 / DOCK_RADIUS 18."
    },
    {
        "file": "core/launcher.py", "lines": 305,
        "purpose": "APP_MANIFEST routing table + AppLauncher process lifecycle (launch/track/terminate via process groups).",
        "classes": {
            "AppEntry": "dataclass: name, entry(path), shortcut, icon(glyph), logo_id, description, memory_target_mb, process(Popen).",
            "AppLauncher": "launch() spawns [sys.executable, entry] cwd=project_root, DEVNULL, start_new_session=True (own process group); terminate() SIGTERM->killpg, 3s wait then SIGKILL; kill(); terminate_all(); is_running(); on_launch/on_exit callbacks; resolve_entry(); get_manifest().",
        },
        "funcs": ["resolve_shortcut(key_sequence) -> app_id (reverse map, case-insensitive)"],
        "notes": "APP_MANIFEST drives dock, quick-launch, menus, tray, shortcuts, launch. process-group isolation critical for Tide/Cinema subprocesses. memory_target_mb is currently a hook (unused by launcher).",
    },
    {
        "file": "core/theme.py", "lines": 773,
        "purpose": "Centralized design tokens + global QSS stylesheet.",
        "classes": {},
        "funcs": ["qcolor(hex)", "hex_to_rgba(hex, alpha)", "create_nautilus_palette() -> QPalette", "get_global_stylesheet() -> str (~590 lines QSS)"],
        "notes": "COLORS (~30 tokens): abyss_navy #081626, slate_navy #0E2238, deep_navy #050D14, void_black #02060A, seafoam #00F2C2, coral #FF7F50, amber #FFA502, emerald #00C853, hd_white #EEF4F8, text_secondary #8BA4B8, text_muted #506070, border #152D44, terminal_bg #030810, tab_* etc. FONTS: mono JetBrains Mono, ui Segoe UI. SPACING xs2..xxxl32. BORDER_RADIUS='0px'. MOST imported core module across apps (with per-app fallback dicts).",
    },
    {
        "file": "core/logger.py", "lines": 235,
        "purpose": "Thread-safe structured logger: rotating file (5MB x7) + ANSI console, category-prefixed.",
        "classes": {
            "NautilusFormatter": "HH:MM:SS.mmm LEVEL [CATEGORY] msg; colorized console, plain file.",
            "NautilusLogger": "Singleton (double-checked lock). get(category) creates per-category child loggers w/ _CategoryFilter.",
        },
        "funcs": ["get_logger(category='CORE')", "log_startup()", "log_shutdown()", "log_app_launch(app_id,pid)", "log_app_exit(app_id,exit_code)", "log_perf(operation,elapsed_ms)"],
        "notes": "CATEGORIES: CORE, LAUNCHER->LNCH, THEME->THME, IPC, APP, SYSTEM->SYST, PERF, UI, NET. Least-failure-tolerant module (imported everywhere).",
    },
    {
        "file": "core/auth.py", "lines": 641,
        "purpose": "Login dialog + JSON account store: PBKDF2 hashing, lockout, hashed sessions, full-screen login/register.",
        "classes": {
            "LoginDialog": "500x550 frameless, QStackedWidget (login/register), auto-login via load_session(). get_logged_in_user()/get_account().",
        },
        "funcs": [
            "create_account(username,password,display_name='') -> bool (raises ValueError on policy fail)",
            "verify_login(username,password) -> dict|None (lockout logic, legacy hash upgrade, logs login_success)",
            "save_session(username,remember=False) / load_session() -> str|None / clear_session()",
            "get_account(username)", "get_avatar_initials(display_name)", "generate_avatar(initials,size=100) -> QPixmap",
        ],
        "notes": "PBKDF2-HMAC-SHA256, 200k iters, verifier 'pbkdf2$<iters>$<salt>$<hex>'. Legacy sha256(salt+password) supported for migration. 5 attempts -> 60s lockout -> 300s escalation at 2x threshold. Session: 256-bit token, SHA-256 hash stored, TTL 14 days. security_log.jsonl is the cross-module contract with core/security/monitor.py. Fallback tokens if core.theme missing.",
    },
    {
        "file": "core/qt_env.py", "lines": 40,
        "purpose": "Qt plugin/DLL search-path bootstrap; MUST be called before QApplication.",
        "classes": {},
        "funcs": ["setup_qt_environment() — adds binding package dir to DLL search path + prepends plugins to QT_PLUGIN_PATH for PySide6/PyQt6/PyQt5; idempotent, no-op if absent."],
        "notes": "Boot-order contract: every entrypoint (shell + all 11 apps) calls it first, before PySide6 imports.",
    },
    {
        "file": "core/icons.py", "lines": 639,
        "purpose": "Programmatic 128x128 logo generation (QPainter) cached to assets/logos/<id>.png.",
        "classes": {},
        "funcs": ["ensure_all_logos()", "get_logo(app_id,size=None) -> QIcon (fallback: letter tile)", "get_pixmap(app_id,size=48)"],
        "notes": "_GENERATORS registry maps logo_id -> painter: abyssal, surfline, riptide, cinema, logbook, mariner, current, harbor, tide, anchor, kraken, reef, nautilus + 5 anchor sub-icons (display/network/audio/theme/about). Registry pattern = single extension point for new icons.",
    },
    {
        "file": "core/wallpaper.py", "lines": 155,
        "purpose": "Programmatic deep-ocean wallpaper at screen resolution, cached to assets/wallpaper.png. Requires active QGuiApplication.",
        "classes": {},
        "funcs": ["generate_wallpaper(width=1920,height=1080,force=False) -> str (path)"],
        "notes": "Layers: linear-gradient bg -> 160 seeded stars -> 8-spoke wheel -> anchor -> 30 bubbles -> 3 depth waves. Seeded RNG (random.Random(42)) = deterministic. Resolution-keyed cache.",
    },
    {
        "file": "core/security/cli.py", "lines": 164,
        "purpose": "argparse CLI for the opt-in red/blue team toolkit. Run: python -3.13 -m core.security.cli <cmd>",
        "classes": {},
        "funcs": ["main(argv=None)", "cmd_connections/processes/suspicious/logins/integrity/scan/sweep/myip"],
        "notes": "Subcommands: connections, processes, suspicious, logins, integrity{init,check}, scan --target --ports --force, sweep --network --force, myip. Lazy imports keep startup cheap.",
    },
    {
        "file": "core/security/scanner.py", "lines": 136,
        "purpose": "RED team: private-range-only network discovery (public requires force=True).",
        "classes": {},
        "funcs": [
            "get_local_ips() -> list", "resolve_host(host)", "ping_host(host,timeout=2) -> bool (ping w/ TCP-connect fallback)",
            "ping_sweep(network,timeout=2,force=False,max_workers=32) -> list (guards global ranges, caps 254 hosts)",
            "port_scan(host,ports=None,timeout=1.0,force=False) -> list (26-port common set, 64 workers)",
            "public_ip(timeout=8) -> str (api.ipify.org, UA Nautilus-Security/1.0)",
        ],
        "notes": "_PRIVATE_NETS: 127/8, 10/8, 172.16/12, 192.168/16, 169.254/16, ::1/128, fc00::/7. Safety enforced at API level, not just CLI.",
    },
    {
        "file": "core/security/monitor.py", "lines": 231,
        "purpose": "BLUE team: connections, processes, suspicious-tool detection, file integrity, failed-login report.",
        "classes": {},
        "funcs": [
            "write_security_event(event,username='',detail='')",
            "active_connections() -> list (netstat -ano / -tunap parsing, token-based win32 handling)",
            "running_processes() -> list", "suspicious_process_check() -> list (21 signatures: mimikatz, xordump, procdump, metasploit, xmrig...)",
            "integrity_init(paths=None, baseline=None) -> dict (hashes core/ + apps/, skips .git/__pycache__/.venv/etc)",
            "integrity_check(baseline=None) -> dict {changed, missing}",
            "failed_login_report() -> dict {locked_accounts, recent_events}",
        ],
        "notes": "Reads data/security_log.jsonl + data/accounts.json — file-format coupled to core/auth.py by design. Cross-platform via sys.platform=='win32' branches.",
    },
    {
        "file": "core/search.py", "lines": 160,
        "purpose": "Offline-first global search. Pure stdlib, no Qt.",
        "classes": {},
        "funcs": [
            "SEARCH_ENGINES dict (duckduckgo/google/bing/brave/startpage/mojeek/yahoo URL templates)",
            "get_engine()/set_engine()/get_roots()/set_roots() — JSON config at ~/.nautilus/search.json (default engine: duckduckgo)",
            "build_search_url(query, engine) — quote_plus query into engine template",
            "match_apps(query, manifest) — token-scored fuzzy app matching",
            "match_files(query, roots, limit) — os.walk name-substring search under ~/Documents, ~/Notes + custom roots",
            "search_all(query, manifest, roots) — apps + files combined (network-free)",
            "web_result(query, engine) — builds URL only; fetching is the browser's job",
        ],
        "notes": "Offline-first rule: local results never touch the network; web results only construct a URL. Engine/roots configurable, persisted JSON.",
    },
    {
        "file": "core/search_overlay.py", "lines": 140,
        "purpose": "Ctrl+Space global search overlay for the shell.",
        "classes": {
            "SearchOverlay": "QFrame popup: QLineEdit + QListWidget. Types results into [APP]/[FILE]/[WEB] rows; Enter activates — app -> AppLauncher.launch, file -> xdg-open, web -> launcher.launch('surfline', [url]). Esc closes. Shows current engine in header.",
        },
        "funcs": ["show_overlay()", "_on_text_changed(text)", "_activate(item)", "_open_path(path)", "_open_web(url)"],
        "notes": "Wired in core/main.py (NautilusShell): Ctrl+Space / Ctrl+Alt+Space toggle, centered top-third. Surfline accepts a URL argv to open directly.",
    },
]

# ---------------------------------------------------------------------------
# 6. APPS (apps/)
# ---------------------------------------------------------------------------

APPS = {
    "abyssal": {
        "desc": "Code editor / IDE. Entry apps/Abyssal/main.py -> AbyssalMainWindow (application.py, 557 ln).",
        "structure": "Two generations coexist: (1) LIVE app = direct Qt widget composition in application.py; (2) DOCUMENTED service architecture (src/core + src/services + src/models + standalone views) largely NOT wired in.",
        "live_classes": {
            "AbyssalMainWindow": "Menu bar (File/Edit/View/Go/Run/Help), ActivityBar | Sidebar | right panel (TabBar, BreadcrumbBar, FindReplaceBar, QSplitter(editor|terminal)), StatusBar, CommandPalette popup, ~15 QShortcuts. _connect_signals wires ActivityBar/Sidebar/TabBar/Palette/FindReplaceBar.",
            "AbyssalEditor": "src/ui/editor.py — QPlainTextEdit + LineNumberArea gutter, active-line highlight, bracket matching, find/replace, language detection. Signals: cursor_moved, language_changed, modification_changed.",
            "AbyssalTerminal": "src/ui/terminal.py — QProcess interactive shell, prompt, command history.",
            "AbyssalFileTree": "src/ui/file_tree.py — QFileSystemModel tree (NOT wired in).",
        },
        "engine": {
            "AbyssalHighlighter": "src/engines/highlighter.py — QSyntaxHighlighter; LANG_EXT_MAP ~35 ext; RULES for python, js/ts, c, cpp, html/xml, css, bash, json, yaml, markdown; detect_language(path); LANG_NAMES. ONLY engine wired into the live app.",
            "LSP": "src/lsp/lsp.py — self-contained, UNUSED: LSPMessage, LSPStream/TCPLSPStream, LSPConnection (send_request sync 10s timeout), LSPHandler ABC, data classes LSPPosition/LSPLocation/LSPCompletionItem/LSPHover. No __init__.py.",
        },
        "service_layer": "src/core/: event_bus (EventBus singleton + @on/@emit), command (CommandRegistry + @register_command), config (ConfigurationSchema/Service), context (ContextKeyService), keybinding (KeybindingService + _default_bindings), lifecycle (LifecycleService), service_container (ServiceContainer DI). src/services/__init__.py register_services() is the composition root but nothing calls it. services/ includes config_service (enhanced), dialog_service (stub), file_service (emits file.opened/file.saved), notification_service, terminal_service (dup of ui/terminal), theme_service.",
        "models": "src/models/: text_document.py (TextDocument over QTextDocument), editor_group.py (EditorGroup multi-doc) — only used by editor_area.py (not wired).",
        "views": "Wired: activity_bar, sidebar (stubs), tab_bar, breadcrumb, find_replace, palette, status_bar. RICH but NOT wired: file_explorer (FileExplorerTree full-featured, 12+ signals), search_panel (SearchWorker QThread), git_panel (full Git client, only file with __main__ harness), settings_panel (5-tab SettingsDialog), explorer, editor_area, panel.",
        "theme": "src/ui/styles.py AbyssalTheme — ~45 color constants (BG #050D13, ACCENT #00D4AA, TEXT #D8E2EC), get_stylesheet(). Imported by nearly every UI/view.",
        "known_issues": [
            "_build_ui() builds editor-container/terminal splitter twice",
            "StatusBar added to horizontal outer layout (renders as right column)",
            "README references nonexistent files (lexer.py, python_server.py, lsp_client.py) and claims PyQt5",
            "services/, models/, lsp/, file_tree.py, 8/15 views not wired into the running app",
            "config/workspace.json persisted but only loaded once (persistence methods never called)",
            "requirements.txt lists PyQt5 though code imports PySide6",
        ],
    },
    "surfline": {
        "desc": "Web browser. Entry apps/Surfline/main.py (64-bit / py3.13 relaunch guard) -> SurflineWindow (src/window.py:245, 1764 ln). Largest app.",
        "ram": 250,
        "features": [
            "QWebEngineView tabs + URL bar; SurflineUrlRequestInterceptor (window.py:56); QWebEngineProfile('surfline_default'); persistent cache assets/profiles/cache; UA 'Surfline/1.0 (Developer Browser; ChompOS)'",
            "src/reef_shield/__init__.py — ReefShieldFilter (EasyList-style regex ad/tracker rules) + ReefShieldUrlRequestInterceptor",
            "src/tide_sync/__init__.py — TideSyncManager + Profile: JSON settings/history/bookmarks; optional AES-256-GCM vault (PBKDF2-HMAC-SHA256 200k iters) via cryptography",
            "src/importer.py — BrowserImporter: imports bookmarks/history/passwords from Chrome/Firefox/Edge/Brave/Opera/CSV via sqlite3 + win32crypt",
            "src/dialogs.py — ImportDialog, PasswordManagerDialog, SettingsDialog",
            "src/theme.py, json_viewer.py (JsonTreeWidget), terminal.py (TerminalWidget QProcess), icons.py (SVG gen)",
        ],
    },
    "riptide": {
        "desc": "Audio hub (PySide6). Entry apps/RipTide/main.py -> MainWindow (ui/main_window.py): sidebar Dashboard/Search/Playlists/SFX Board/Settings + NowPlayingBar transport.",
        "ram": 60,
        "structure": {
            "api/": "SpotifyAPI (search/playlists/saved/recent/top/recs/player, 401-refresh + 429-retry), YouTubeAPI (Data v3, ISO-8601 duration parser), SoundCloudAPI",
            "auth/": "OAuthProvider ABC + OAuthCallbackHandler on 127.0.0.1:8765; SpotifyOAuth (PKCE/S256), YouTubeOAuth, SoundCloudOAuth",
            "audio/": "engine.py AudioEngine via pygame.mixer.music (44.1kHz/16-bit/2ch/300ms buffer), local+HTTP streaming; sfx.py SFXEngine multi-channel soundboard",
            "database/": "db.py SQLite WAL — accounts/tracks/playlists/SFX clips",
            "models/": "Platform enum (brand colors), Track, Playlist, SFXClip, Account, PlaybackState",
            "workers/": "api_workers.py DashboardWorker/SearchWorker/LibraryLoaderWorker daemon threads; results posted via _MainThreadDispatcher (queued Qt signal, object/object) -> post(func,*args)",
            "ui/": "PySide6 widgets: styles.py QSS builder + apply_dark_theme(app); widgets.py ThumbLoader(QNetwork), TrackRow (play_clicked/activated), ArtistCard, PlaylistCard, NowPlayingBar; dashboard, search (400ms debounce + platform filter), playlist, sfx_board, settings (OAuthWorker QThread + CredentialsDialog)",
        },
    },
    "cinema": {
        "desc": "Media center (local-only, offline). Entry apps/Cinema/main.py -> CinemaWindow (src/window.py:71, ~1020 ln). Sidebar: Home/Movies/Shows/Favorites/My Media/Settings. No servers. Jellyfin removed (jellyfin.py deleted).",
        "ram": 180,
        "structure": {
            "library.py": "LibraryScanner + MediaItem; folder scan w/ persistent JSON cache + .fingerprint stale check; MEDIA_EXTENSIONS",
            "player.py": "PlayerWindow fullscreen QMediaPlayer/QVideoWidget, local playback only",
            "settings.py": "CinemaSettings dataclass (media_folders, import_mode move/copy, disclaimer_accepted, favorites), atomic JSON save",
            "widgets.py": "ArtCache, ArtLoader(QThread), MediaCard (ctx menu Play/Fav/Remove-from-Library), MediaGrid (responsive), Sidebar, EmptyState, BusyBar",
        },
        "notes": "Import flow: _import_media/_import_folder -> _classify_dest (episode re [sS]\\d{1,2}[eE]\\d{1,2} -> ~/Cinema/TV/<show>, else ~/Cinema/Movies/<clean title>) -> move/copy -> rescan. Default folders ~/Cinema/{Movies,TV}. Piracy disclaimer: first-run dialog + boxes on Home/My Media/Settings. Ctrl+I import, F5 rescan, Ctrl+F search. _run_bg QThread worker for scan/import.",
    },
    "logbook": {
        "desc": "Markdown notes. SINGLE FILE apps/Logbook/main.py (528 ln) -> LogbookWindow. Notes as .md in ~/Documents/Logbook.",
        "ram": 40,
        "features": [
            "Three-pane QSplitter: notes list | markdown editor | live HTML preview",
            "_render_markdown() custom-safe renderer (headings, lists, code, hr) — no markdown lib",
            "Instant search (title + content), auto-save every 2s QTimer w/ dirty tracking",
            "Shortcuts: Ctrl+N/F/S, Ctrl+Shift+P, F2/R rename, Delete",
        ],
    },
    "mariner": {
        "desc": "Scientific calculator. SINGLE FILE apps/Mariner/main.py (614 ln) -> MarinerWindow.",
        "ram": 20,
        "features": [
            "ExpressionEvaluator — hand-written recursive-descent parser (tokenizer regex + expr/term/factor/power/atom) over whitelisted math (sin/cos/tan/log/ln/exp/sqrt/fact/gcd; pi/e/tau/phi)",
            "Unary minus, ^, ! factorial (gamma fallback), %, parens",
            "Live result preview, history tape persisted history.json (cap 200), sci-notation/INF/NaN output",
        ],
    },
    "current": {
        "desc": "Telemetry monitor. SINGLE FILE apps/Current/main.py (606 ln) -> CurrentWindow. Smallest app.",
        "ram": 15,
        "features": [
            "SystemCollector(QThread) polls 1s via psutil: CPU %/per-core/freq, RAM, swap, disk, sensors_temperatures, battery, net I/O deltas, uptime (zero-metrics fallback if psutil absent)",
            "MetricCard (label + value + 3px progress bar); ProcessTree top-100 by RSS, color-coded (coral >500MB, amber >200MB), SIGKILL/taskkill w/ confirm",
        ],
    },
    "harbor": {
        "desc": "Keyboard-first file manager. SINGLE FILE apps/Harbor/main.py (724 ln) -> HarborWindow. Dual-pane.",
        "ram": 30,
        "features": [
            "FilePane (path bar + QTreeWidget lazy dirs, back/forward/up, type-colored entries, context menu) x2 + FilePreview (text/code <=1MB else binary meta)",
            "Vim-style: j/k nav, h/l switch pane, Enter open, Backspace up, Space preview, / path-focus, F5 copy, F6 move, F7 mkdir, F8 delete",
            "Archive: zipfile + tarfile (create .zip / .tar.gz)",
        ],
    },
    "tide": {
        "desc": "Tabbed terminal. apps/Tide/shell.py = pure-Python InternalShell (no external shell); apps/Tide/main.py -> TideWindow.",
        "ram": 25,
        "features": [
            "InternalShell: tokenizer (quotes/escapes, && || ; | < > >>), pipelines, $VAR/~ expansion, 30 built-ins, direct Popen externals (shell=False, streaming), request_abort for Ctrl+C",
            "TerminalSession: CommandWorker(QThread) runs shared InternalShell with zero UI blocking; styled output out/err/sys/dim/accent; clear/exit styles",
            "QTabWidget multi-tab (closable/movable), tab title = current dir; Ctrl+T/W/C/L, Ctrl+Tab cycle, Up/Down history via shell",
        ],
    },
    "anchor": {
        "desc": "Control center / settings. SINGLE FILE apps/anchor/main.py (860 ln) -> AnchorWindow. 5 tabs: Display, Network, Audio, Theme, About.",
        "ram": 20,
        "features": [
            "DisplayPanel: resolution/scaling/refresh, appearance toggles",
            "NetworkPanel: Wi-Fi combos, real Bluetooth scan (BluetoothScanner QThread, optional bleak + PowerShell fallback), honest VPN/proxy status, PublicIpChecker QThread -> api.ipify.org",
            "AudioPanel: device/volume/balance/gain sliders, SFX toggles",
            "ThemePanel: live QColorDialog overrides of 10 Nautilus color tokens w/ reset",
            "AboutPanel: base RAM < 350 MB, v1.0.0 Build 2026.08.01",
        ],
    },
    "reef": {
        "desc": "Local-first messenger (apps/Reef). engine.py = pure-stdlib mail+store layer; main.py -> ReefWindow.",
        "ram": 40,
        "structure": {
            "engine.py": "Pure stdlib, no Qt. MailStore (JSON in ~/.reef: accounts.json/messages.json), Account/Message dataclasses, fetch_inbox via imaplib (RFC822 parse, newest N), send_mail via smtplib+STARTTLS, append_local offline thread, upsert keyed by message id.",
            "main.py": "ReefWindow: 3-pane (folder list / message list / QTextBrowser viewer). RefreshWorker + SendWorker QThreads for IMAP/SMTP (UI never blocked). ComposeDialog + AccountDialog. Local thread always works offline; mail requires configured account.",
        },
        "features": [
            "Offline-first: Local Thread composes/stores without any account or network",
            "Optional IMAP/SMTP accounts: label/email/password/hosts, stored locally in ~/.reef",
            "Inbox sync with auto-dedupe by message id; Sent folder records outbound; Reply/Compose dialogs",
        ],
    },
    "kraken": {
        "desc": "Local-first agentic AI engine + multi-agent workforce. Two surfaces share one engine package: CLI (kraken.py -> cli.py, 899 ln) and PySide6 desktop (main.py -> ui/, engine events marshalled via polled queue).",
        "ram": 120,
        "structure": {
            "engine/config.py": "KrakenConfig dataclass, JSON at ~/.kraken/config.json; DEFAULT_PROVIDERS presets (ollama/lmstudio/vllm/llamacpp + 8 cloud: openai/anthropic/gemini/groq/openrouter/mistral/deepseek/together); DEFAULT_MODEL qwen2.5-coder:14b",
            "engine/spec.py": "Markdown Agent Builder: frontmatter (name/model/tools/workforce_roles/default_mode/num_ctx/system_prompt) + body -> AgentSpec. KNOWN_TOOL_NAMES (file_read/write/delete/list, terminal_exec), KNOWN_ROLES (planner/exec/qa/worker). SpecError.",
            "engine/agent_store.py": "AgentStore catalog of .md agents in ~/.kraken/agents/; CRUD, import, resolve, role_spec(role).",
            "engine/providers.py": "ChatClient streaming over plain HTTP (OpenAI-compatible SSE, Ollama /api/chat native, Anthropic /v1/messages native). ProviderError with actionable messages. stats {tokens, streams}. list_ollama_models, ping_provider.",
            "engine/discovery.py": "find_local_models() (Ollama server+disk, LM Studio GGUF caches, llama.cpp dirs), recommend_backend(), list_api_models(), detect_provider_health().",
            "engine/keys.py": "Key resolution: ~/.kraken/keys.json > ~/.env > env vars. save_keys 0600, never logged. ENV_VARS map.",
            "engine/memory.py": "MemoryStore SQLite (~/.kraken/memory.db): remember/recall with token-based pseudo-embedding cosine, find_exact, bump_hit, stats, forget. Table memory(id,signature,embedding,fix,context,source,created_at,hits).",
            "engine/agent.py": "Agent single-loop w/ Self-Correction Loop (memory recall + model re-issue + remember). parse_tool_blocks regex <tool name=\"...\">{json}</tool>. AgentMessage/AgentEvent dataclasses. run_agent() wrapper. max_rounds=12.",
            "engine/orchestrator.py": "Workforce ('Agent Mode'): Planner -> parallel exec agents -> QA/Review -> synthesized === KRAKEN WORKFORCE REPORT ===. max_parallel=3, SubTask/Workforce dataclasses, stop()",
            "engine/tools.py": "Tool registry: file_read (512KB cap), file_write, file_delete, file_list, terminal_exec (300s timeout). PermissionGate (auto_approve/allow_force/confirm_fn), ToolContext (workspace + resolve_path), TOOL_SCHEMA, _DANGER_PATTERNS (rm -rf /, fork bomb, mkfs, dd), ToolError/PermissionDenied.",
            "engine/logger.py": "Bridges to core.logger ('KRK') or stdlib fallback.",
            "cli.py": "REPL (readline history, kraken> prompt, /slash commands), direct tasks, --agent-mode, subcommands: build, doctor, models, memory, config, agent (new/list/show/edit/remove/import/run), keys (list/show/add/set/remove), setup. _gate() approval prompts.",
            "ui/main_window.py": "KrakenWindow: chat panel + workforce tree + agent library manager; EngineWorker thread; events via queue.Queue drained by 120ms QTimer (no cross-thread Qt calls).",
            "ui/chat_panel.py": "ChatPanel: streaming transcript + keyboard-first input, submitted signal.",
            "ui/workforce_view.py": "WorkforceTree QTreeWidget: per-agent status/tokens/event trail, STATUS_COLORS map.",
        },
        "persistence": "~/.kraken/: config.json, memory.db, keys.json (0600), agents/*.md. Engine is pure stdlib — works standalone, GUI-safe via event queue.",
        "packaging": "pyproject.toml: kraken-ai 1.0.0; console scripts kraken=apps.kraken.cli:main, kraken-gui=apps.kraken.main:main; [gui] extra adds PySide6; data-files share/kraken/agents DatabaseArchitect.md.",
    },
}

# ---------------------------------------------------------------------------
# 7. TESTS, AGENTS, CONFIGS
# ---------------------------------------------------------------------------

TESTS = [
    {"file": "tests/smoke_test.py", "lines": 82,
     "purpose": "Offscreen (QT_QPA_PLATFORM=offscreen) launch/alive/kill test for every app. Flags: --duration, --app."},
    {"file": "tests/test_kraken_engine.py", "lines": 179,
     "purpose": "Kraken engine unit tests: spec parsing, memory loop, tools, safety gates. No backend required."},
    {"file": "tests/test_kraken_agents.py", "lines": 258,
     "purpose": "Agent spec validation, catalog, role lookup, CLI dispatch."},
    {"file": "tests/test_kraken_providers.py", "lines": 270,
     "purpose": "Keys, model discovery, Anthropic/Gemini wire formats."},
]

AGENTS = [
    {"file": "agents/DatabaseArchitect.md",
     "purpose": "Example Kraken agent spec (frontmatter + body). Also ships to <venv>/share/kraken/agents/ on install."},
]

# ---------------------------------------------------------------------------
# 8. DESIGN PATTERNS & CONVENTIONS
# ---------------------------------------------------------------------------

DESIGN_PATTERNS = [
    "Manifest-driven process orchestration: APP_MANIFEST (core/launcher.py) is the single registry; shell launches each app as subprocess.Popen(start_new_session=True), tracks PIDs, SIGTERM->SIGKILL teardown. Shortcuts resolve through same manifest.",
    "Centralized design tokens: core/theme.py exports COLORS/FONTS/SPACING + create_nautilus_palette() + get_global_stylesheet(). Every app imports these (with inline fallback dicts so apps run standalone).",
    "Shared runtime bootstrap (all apps): inject PROJECT_ROOT into sys.path -> core.qt_env.setup_qt_environment() -> QApplication -> Nautilus palette/stylesheet -> get_logo(app_id) icon. Runs standalone AND from the shell.",
    "Process-per-app isolation: each app is its own OS process; shell communicates via process handles + on_launch/on_exit callbacks (not in-process imports). Abyssal adds an in-app EventBus singleton (@on/@emit) for decoupled UI wiring (currently one-way; no subscribers).",
    "Kraken engine: model-agnostic OpenAI-compatible client, Markdown-driven agent specs, SQLite error-learning memory, self-correcting tool loop, orchestrator/worker workforce. Local-first, zero-cost. GUI<->engine communication exclusively via polled queue.Queue (120ms QTimer), never cross-thread Qt.",
    "Structured subsystem logging: core/logger.py NautilusLogger singleton, category prefixes (CORE/LNCH/THME/IPC/APP/SYST/PERF/UI/NET), rotating 5MBx7 file + ANSI console.",
    "Programmatic asset generation: logos (core/icons.py) and wallpaper (core/wallpaper.py) rendered with QPainter + seeded RNG, cached to assets/. Zero binary asset bloat.",
    "Data as plain files: data/accounts.json, data/security_log.jsonl, data/integrity_baseline.json — JSON/JSONL for auditability. security_log.jsonl is a deliberate cross-module contract (auth writes, monitor reads).",
    "Safety-by-default security: scanner enforces private-range gate at API level; --force flag needed for public ranges. PermissionGate for Kraken tool approval.",
    "Graceful degradation: try/except ImportError fallbacks (auth, icons, theme, kraken), psutil guards, UTF-8 console reconfigure guards, wallpaper failure fallbacks.",
    "Threading pattern: QThread/QTimer-based workers for long ops (Current SystemCollector, Cinema ArtLoader/_Worker, Tide CommandWorker, kraken EngineWorker, Harbor lazy dirs); RipTide workers + engine callbacks marshal to the GUI thread via a queued-signal _MainThreadDispatcher (api_workers.post); daemon threads for engine work.",
    "Cross-platform: sys.platform=='win32' branches in security/monitor.py, scanner ping, Tide/Abyssal shells (cmd.exe vs $SHELL), Surfline win32crypt.",
    "Atomic file writes: tmp + os.replace pattern (Cinema settings, config stores).",
]

# ---------------------------------------------------------------------------
# 9. DEV COMMANDS
# ---------------------------------------------------------------------------

DEV_COMMANDS = [
    {"cmd": "py -3.13 core/main.py", "desc": "Launch the desktop shell"},
    {"cmd": "py -3.13 apps/Abyssal/main.py", "desc": "Run an app standalone (substitute any app dir)"},
    {"cmd": "py -3.13 apps/kraken/main.py", "desc": "Run the Kraken AI desktop app"},
    {"cmd": "py -3.13 kraken.py --agent-mode \"task\"", "desc": "Kraken CLI workforce mode"},
    {"cmd": "py -3.13 kraken.py build --spec agents/DatabaseArchitect.md", "desc": "Kraken CLI: build an agent spec"},
    {"cmd": "py -3.13 tests/test_kraken_engine.py", "desc": "Kraken engine unit tests (no backend needed)"},
    {"cmd": "pip install .", "desc": "Install kraken CLI on PATH (no mandatory deps)"},
    {"cmd": "pip install \".[gui]\"", "desc": "Install kraken-gui too (adds PySide6)"},
    {"cmd": "kraken doctor / models / keys / config", "desc": "Kraken health / models / keys / config CLI"},
    {"cmd": "py -3.13 tests/smoke_test.py [--duration 4] [--app cinema]", "desc": "Offscreen smoke-test all apps"},
    {"cmd": "ruff check .", "desc": "Lint (ruff.toml, py313 target)"},
    {"cmd": "py -3.13 -m core.security.cli --help", "desc": "Security toolkit CLI"},
]

# ---------------------------------------------------------------------------
# 10. QUERY HELPERS (the point of this file)
# ---------------------------------------------------------------------------

def app(app_id: str) -> dict | None:
    """Return the knowledge-map dict for one app by its manifest id."""
    return APPS.get(app_id.lower())


def find(name: str) -> list[str]:
    """Locate a class/function/constant name across the map. Case-insensitive."""
    name = name.lower()
    hits = []
    for mod in CORE_MODULES:
        if name in mod["file"].lower():
            hits.append(f"{mod['file']} — {mod['purpose']}")
        for cname, cdesc in mod["classes"].items():
            if name in cname.lower():
                hits.append(f"{mod['file']} :: class {cname} — {cdesc}")
        for f in mod["funcs"]:
            if name in f.lower():
                hits.append(f"{mod['file']} :: {f}")
        if name in mod["notes"].lower():
            hits.append(f"{mod['file']} — note: {mod['notes']}")
    for aid, info in APPS.items():
        if name in aid:
            hits.append(f"apps/{aid} — {info['desc']}")
        for cname in (info.get("live_classes") or {}):
            if name in cname.lower():
                hits.append(f"apps/{aid} :: {cname}")
        for section in ("structure", "engine", "live_classes", "features", "known_issues", "models", "views", "service_layer", "theme"):
            sub = info.get(section)
            if isinstance(sub, dict):
                for k, v in sub.items():
                    if name in k.lower():
                        hits.append(f"apps/{aid} {section}/{k}")
                    if isinstance(v, str) and name in v.lower():
                        hits.append(f"apps/{aid} {section}/{k}: {v[:140]}")
            elif isinstance(sub, list):
                for v in sub:
                    if isinstance(v, str) and name in v.lower():
                        hits.append(f"apps/{aid} {section}: {v[:140]}")
    return hits or [f"No hits for {name!r}"]


def modules() -> list[str]:
    """Every Python module in the project (flat list)."""
    out = ["core/" + m["file"].split("/", 1)[1] for m in CORE_MODULES]
    for aid, info in APPS.items():
        out.append(f"apps/{aid} — {info['desc']}")
    out += [t["file"] for t in TESTS]
    out += ["kraken.py", "PROJECT_BRAIN.py"]
    return sorted(out)


def manifest() -> str:
    """Pretty-printed APP_MANIFEST."""
    rows = [f"  {a['id']:<10} {a['name']:<22} {a['shortcut']:<12} {a['ram_mb']:>4}MB  {a['ui']}" for a in APP_MANIFEST]
    return "\n".join(rows)


def commands() -> list[str]:
    """Dev commands as 'cmd — desc' strings."""
    return [f"  {c['cmd']}  —  {c['desc']}" for c in DEV_COMMANDS]


def design_patterns() -> list[str]:
    return [f"  • {p}" for p in DESIGN_PATTERNS]


def dump(app_id: str | None = None) -> str:
    """Dump a JSON snapshot (whole project or one app) for fast machine parsing."""
    if app_id:
        return json.dumps(APPS.get(app_id.lower(), {}), indent=2, default=str)
    payload = {
        "project": PROJECT,
        "stack": STACK,
        "apps": APPS,
        "core": CORE_MODULES,
        "tests": TESTS,
        "agents": AGENTS,
    }
    return json.dumps(payload, indent=2, default=str)


def cli() -> None:
    """`python PROJECT_BRAIN.py` prints a quick overview."""
    print("=" * 78)
    print(f"  {PROJECT['name']} — Project Brain v{PROJECT['version']}")
    print(f"  {PROJECT['blurb']}")
    print("=" * 78)
    print("\nApps registered in APP_MANIFEST:")
    print(manifest())
    print("\nCore modules:")
    for m in CORE_MODULES:
        print(f"  {m['file']} ({m['lines']} ln) — {m['purpose']}")
    print("\nTests:")
    for t in TESTS:
        print(f"  {t['file']} ({t['lines']} ln) — {t['purpose']}")
    print("\nHelper functions: app(id), find(name), modules(), manifest(),")
    print("                   commands(), design_patterns(), dump(app_id=None)")


if __name__ == "__main__":
    cli()
