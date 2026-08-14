"""
Nautilus OS — AI Asset Generator (local LM Studio / OpenAI-compatible backend)

Generates the desktop wallpaper and app icons with a local image model
(Qwen-Image) served by LM Studio, cached to assets/ alongside the
programmatic generators. core/wallpaper.py and core/icons.py remain the
fallback — this module writes the same output paths so the shell picks
the AI assets up automatically.

Requires an image model loaded in the LM Studio server:
    POST http://localhost:1234/v1/images/generations

CLI:
    python3 -m core.ai_assets --wallpaper              # regenerate wallpaper
    python3 -m core.ai_assets --wallpaper -W 1920 -H 1080
    python3 -m core.ai_assets --icons                  # all app icons (512px -> 128px)
    python3 -m core.ai_assets --icons --model qwen-image --yes

Configuration (env):
    NAUTILUS_LM_URL      base URL, default http://localhost:1234/v1
    NAUTILUS_AI_MODEL    explicit model id (else auto-discovered)
"""

import argparse
import base64
import json
import os
import sys
import urllib.error
import urllib.request

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSETS_DIR = os.path.join(PROJECT_ROOT, "assets")
LOGOS_DIR = os.path.join(ASSETS_DIR, "logos")
WALLPAPER_PATH = os.path.join(ASSETS_DIR, "wallpaper.png")

LM_BASE_URL = os.environ.get("NAUTILUS_LM_URL", "http://localhost:1234/v1")
MODEL_HINT = os.environ.get("NAUTILUS_AI_MODEL", "")

# Largest generation budget for the wallpaper (Qwen-Image trains around 2MP;
# stay comfortably under with room for the model's native multiples-of-16).
MAX_GEN_AREA = 1_400_000

STYLE = (
    "Flat minimalist vector app icon, deep abyssal navy blue background (#050D14), "
    "glowing seafoam (#00F2C2) accents with coral (#FF7F50) and amber (#FFA502) "
    "highlights, subtle bioluminescent glow, centered composition, clean geometric "
    "shapes, no text, no letters, no watermark"
)

ICON_PROMPTS = {
    "abyssal": STYLE + ", open code editor angle brackets { } with a slash",
    "surfline": STYLE + ", ocean wave curling over",
    "riptide": STYLE + ", audio equalizer waveform bars",
    "cinema": STYLE + ", film frame with a play triangle",
    "logbook": STYLE + ", open notebook with a pen",
    "mariner": STYLE + ", compass rose with mathematical symbols",
    "current": STYLE + ", rising telemetry pulse line on a subtle grid",
    "harbor": STYLE + ", file folder with an anchor",
    "tide": STYLE + ", terminal window with a command prompt cursor",
    "anchor": STYLE + ", settings gear",
    "kraken": STYLE + ", sea monster kraken head with tentacles",
    "nautilus": STYLE + ", nautilus shell spiral",
    "reef": STYLE + ", coral message bubble with typing dots",
    "anchor_display": STYLE + ", computer monitor",
    "anchor_network": STYLE + ", globe with an orbit ring",
    "anchor_audio": STYLE + ", speaker emitting sound waves",
    "anchor_theme": STYLE + ", paint palette",
    "anchor_about": STYLE + ", information badge icon",
}

WALLPAPER_PROMPT = (
    "Ultra-wide deep ocean desktop wallpaper, abyssal theme, dark navy gradient "
    "from near-black at the top to deep teal at the bottom, glowing bioluminescent "
    "seafoam light streaks, faint stars above a calm sea, subtle depth waves, "
    "minimalist elegant composition, dark and moody, high detail, 16:9"
)

ICON_GEN_SIZE = 512
ICON_OUT_SIZE = 128


# ═══════════════════════════════════════════════════════════════
#  HTTP (stdlib urllib — matches kraken engine conventions)
# ═══════════════════════════════════════════════════════════════

def _headers() -> dict:
    return {
        "Content-Type": "application/json",
        "Accept": "application/json",
    }


def _post_json(path: str, payload: dict, timeout: int = 600):
    url = LM_BASE_URL.rstrip("/") + path
    data = json.dumps(payload).encode("utf-8")
    try:
        with urllib.request.urlopen(
            urllib.request.Request(url, data=data, headers=_headers(), method="POST"),
            timeout=timeout,
        ) as resp:
            return json.loads(resp.read().decode("utf-8", "replace"))
    except urllib.error.HTTPError as e:
        raise RuntimeError(
            f"LM Studio returned HTTP {e.code} ({e.reason}): {e.read().decode('utf-8', 'replace')[:300]}"
        ) from e
    except urllib.error.URLError as e:
        raise RuntimeError(
            f"Cannot reach LM Studio at {LM_BASE_URL} — is the server running with "
            f"an image model loaded? ({e.reason})"
        ) from e


def _get_json(path: str, timeout: int = 5):
    url = LM_BASE_URL.rstrip("/") + path
    try:
        with urllib.request.urlopen(urllib.request.Request(url), timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8", "replace"))
    except urllib.error.URLError as e:
        raise RuntimeError(
            f"Cannot reach LM Studio at {LM_BASE_URL} — is the server running? ({e.reason})"
        ) from e


# ═══════════════════════════════════════════════════════════════
#  Model discovery
# ═══════════════════════════════════════════════════════════════

def list_models() -> list[str]:
    body = _get_json("/models")
    return [m.get("id", "") for m in body.get("data", []) if m.get("id")]


def discover_model() -> str:
    if MODEL_HINT:
        return MODEL_HINT
    models = list_models()
    if not models:
        raise RuntimeError(
            f"LM Studio at {LM_BASE_URL} reports no loaded models — load Qwen-Image first"
        )
    for m in models:
        if "qwen" in m.lower() and "image" in m.lower():
            return m
    for m in models:
        if "image" in m.lower():
            return m
    return models[0]


# ═══════════════════════════════════════════════════════════════
#  Generation
# ═══════════════════════════════════════════════════════════════

def _fetch_image_bytes(entry: dict) -> bytes:
    if entry.get("b64_json"):
        return base64.b64decode(entry["b64_json"])
    url = entry.get("url")
    if not url:
        raise RuntimeError(f"Generation response had no b64_json or url: {entry}")
    with urllib.request.urlopen(url, timeout=60) as resp:
        return resp.read()


def generate_image_bytes(prompt: str, size: str, model: str | None = None,
                         timeout: int = 900) -> bytes:
    """POST /v1/images/generations and return the raw PNG bytes."""
    model = model or discover_model()
    payload = {
        "model": model,
        "prompt": prompt,
        "size": size,
        "n": 1,
        "response_format": "b64_json",
    }
    body = _post_json("/images/generations", payload, timeout=timeout)
    data = body.get("data") or []
    if not data:
        raise RuntimeError(f"Generation response had no data: {body}")
    return _fetch_image_bytes(data[0])


def _gen_size_for(target_w: int, target_h: int, max_area: int = MAX_GEN_AREA) -> tuple[int, int]:
    """Largest multiple-of-16 dimensions with the target aspect within max_area."""
    w, h = target_w, target_h
    if w * h > max_area:
        scale = (max_area / (w * h)) ** 0.5
        w, h = int(w * scale), int(h * scale)
    w -= w % 16
    h -= h % 16
    return max(w, 16), max(h, 16)


def _save_scaled(img_bytes: bytes, out_path: str, out_w: int, out_h: int) -> str:
    from PySide6.QtGui import QImage, Qt

    img = QImage.fromData(img_bytes)
    if img.isNull():
        raise RuntimeError("Model returned unreadable image data")
    scaled = img.scaled(out_w, out_h, Qt.IgnoreAspectRatio, Qt.SmoothTransformation)
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    if not scaled.save(out_path, "PNG"):
        raise RuntimeError(f"Failed to save {out_path}")
    return out_path


def generate_wallpaper(width: int = 1920, height: int = 1080,
                       model: str | None = None, prompt: str | None = None,
                       force: bool = False) -> str:
    """Generate the AI wallpaper at screen resolution, cached to assets/wallpaper.png."""
    if os.path.exists(WALLPAPER_PATH) and not force:
        return WALLPAPER_PATH
    gen_w, gen_h = _gen_size_for(width, height)
    size = f"{gen_w}x{gen_h}"
    print(f"[ai_assets] wallpaper {size} -> {width}x{height}")
    data = generate_image_bytes(prompt or WALLPAPER_PROMPT, size, model)
    return _save_scaled(data, WALLPAPER_PATH, width, height)


def generate_icons(model: str | None = None, force: bool = False) -> list[str]:
    """Generate every app icon at 512px and downscale to the 128px cache."""
    size = f"{ICON_GEN_SIZE}x{ICON_GEN_SIZE}"
    written = []
    for app_id, prompt in ICON_PROMPTS.items():
        out = os.path.join(LOGOS_DIR, f"{app_id}.png")
        if os.path.exists(out) and not force:
            print(f"[ai_assets] skip  {app_id} (cached)")
            continue
        print(f"[ai_assets] icon  {app_id} ...")
        try:
            data = generate_image_bytes(prompt, size, model)
            _save_scaled(data, out, ICON_OUT_SIZE, ICON_OUT_SIZE)
            written.append(out)
        except RuntimeError as e:
            print(f"[ai_assets] FAIL  {app_id}: {e}", file=sys.stderr)
    return written


# ═══════════════════════════════════════════════════════════════
#  CLI
# ═══════════════════════════════════════════════════════════════

def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        prog="python3 -m core.ai_assets",
        description="Generate Nautilus wallpaper + app icons with a local LM Studio image model.",
    )
    ap.add_argument("--wallpaper", action="store_true", help="regenerate the desktop wallpaper")
    ap.add_argument("--icons", action="store_true", help="regenerate all app icons")
    ap.add_argument("-W", "--width", type=int, default=1920, help="wallpaper target width")
    ap.add_argument("-H", "--height", type=int, default=1080, help="wallpaper target height")
    ap.add_argument("-m", "--model", default=MODEL_HINT or None, help="explicit model id")
    ap.add_argument("--prompt", default=None, help="override wallpaper prompt")
    ap.add_argument("-f", "--force", action="store_true", help="regenerate even if cached")
    ap.add_argument("-y", "--yes", action="store_true", help="skip confirmation prompts")
    args = ap.parse_args(argv)

    if not args.wallpaper and not args.icons:
        args.wallpaper = True

    if not args.icons:
        try:
            model = args.model or discover_model()
        except RuntimeError as e:
            print(f"[ai_assets] {e}", file=sys.stderr)
            return 1
        print(f"[ai_assets] model: {model}")
        generate_wallpaper(args.width, args.height, model, args.prompt, args.force)
        print(f"[ai_assets] wallpaper -> {WALLPAPER_PATH}")
        return 0

    if args.icons:
        if args.wallpaper and not args.yes:
            if input("Generate all 18 app icons too? [y/N] ").strip().lower() not in ("y", "yes"):
                return 0
        try:
            model = args.model or discover_model()
        except RuntimeError as e:
            print(f"[ai_assets] {e}", file=sys.stderr)
            return 1
        print(f"[ai_assets] model: {model}")
        generate_icons(model, args.force)
        print("[ai_assets] icons -> assets/logos/")
    return 0


if __name__ == "__main__":
    sys.exit(main())
