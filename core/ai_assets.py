"""
Nautilus OS — AI Asset Generator (local ComfyUI backend)

Generates the desktop wallpapers and app icons with a local FLUX.2-klein
image model served by a ComfyUI server, cached to assets/ alongside the
programmatic generators. core/wallpaper.py and core/icons.py remain the
fallback — this module writes the same output paths so the shell picks
the AI assets up automatically.

Requires a running ComfyUI server (CPU or GPU) with the flux2-klein
weights installed and the ComfyUI-GGUF node:
    POST http://localhost:8188/prompt

CLI:
    python3 -m core.ai_assets --wallpaper [THEME]    # one wallpaper (default abyss)
    python3 -m core.ai_assets --wallpapers           # every theme
    python3 -m core.ai_assets --icons                # all app icons (512px -> 128px)
    python3 -m core.ai_assets --check                # audit cached icons, flag poor ones
    python3 -m core.ai_assets --check --fix          # audit + regenerate flagged icons

Configuration (env):
    NAUTILUS_COMFY_URL   base URL, default http://localhost:8188
    NAUTILUS_AI_MODEL    explicit diffusion model filename (else auto-discovered)
"""

import argparse
import json
import os
import secrets
import sys
import time
import urllib.error
import urllib.request

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSETS_DIR = os.path.join(PROJECT_ROOT, "assets")
LOGOS_DIR = os.path.join(ASSETS_DIR, "logos")
WALLPAPERS_DIR = os.path.join(ASSETS_DIR, "wallpapers")

COMFY_BASE_URL = os.environ.get("NAUTILUS_COMFY_URL", "http://localhost:8188")
MODEL_HINT = os.environ.get("NAUTILUS_AI_MODEL", "")

# Sampling settings for the distilled klein model (4 steps, no CFG).
STEPS = 4
CFG = 1.0
SAMPLER = "euler"

# Largest generation budget for the wallpaper (stay under the model's
# native comfort zone; the result is upscaled to screen resolution).
MAX_GEN_AREA = 1_400_000

STYLE = (
    "Premium flat vector app icon, dark rounded-square tile in deep slate navy "
    "(#0E2238) with a thin glowing seafoam (#00F2C2) border, one bold bright centered "
    "glyph in seafoam with coral (#FF7F50) and amber (#FFA502) accent details, soft "
    "inner glow, crisp geometric shapes, strong contrast, minimalist, no text, no "
    "letters, no watermark"
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

WALLPAPER_PROMPTS = {
    "abyss": (
        "Ultra-wide deep ocean desktop wallpaper, abyssal theme, dark navy gradient "
        "from near-black at the top to deep teal at the bottom, glowing bioluminescent "
        "seafoam light streaks, faint stars above a calm sea, subtle depth waves, "
        "minimalist elegant composition, dark and moody, high detail, 16:9"
    ),
    "aurora": (
        "Ultra-wide polar night ocean desktop wallpaper, aurora borealis glowing in "
        "seafoam teal and soft green over a calm dark sea, subtle stars, faint reflection "
        "of the aurora on the water, minimalist elegant, dark and moody, high detail, 16:9"
    ),
    "tide": (
        "Ultra-wide underwater desktop wallpaper, warm coral reef scene at dusk, soft amber "
        "and coral bioluminescent glow, gentle bubbles rising, deep teal water gradient, "
        "minimalist elegant composition, calm and moody, high detail, 16:9"
    ),
    "storm": (
        "Ultra-wide midnight storm ocean desktop wallpaper, churning deep slate waves, dark "
        "storm clouds, a single faint fork of lightning, cold moody atmosphere, high contrast "
        "minimalist composition, dark and cinematic, high detail, 16:9"
    ),
    "kelp": (
        "Ultra-wide underwater desktop wallpaper, towering kelp forest rising from the dark, "
        "emerald green strands glowing with seafoam bioluminescence, rays of light from above, "
        "fine bubbles, minimalist elegant, dark and moody, high detail, 16:9"
    ),
    "stars": (
        "Ultra-wide night ocean desktop wallpaper, dense field of stars over a perfectly calm "
        "glassy sea, stars faintly mirrored on the water, deep indigo and navy gradient, "
        "minimalist elegant composition, serene and moody, high detail, 16:9"
    ),
}

ICON_GEN_SIZE = 512
ICON_OUT_SIZE = 128


# ═══════════════════════════════════════════════════════════════
#  HTTP (stdlib urllib — matches kraken engine conventions)
# ═══════════════════════════════════════════════════════════════

def _post_json(path: str, payload: dict, timeout: int = 120):
    url = COMFY_BASE_URL.rstrip("/") + path
    data = json.dumps(payload).encode("utf-8")
    try:
        with urllib.request.urlopen(
            urllib.request.Request(url, data=data,
                                   headers={"Content-Type": "application/json"}),
            timeout=timeout,
        ) as resp:
            return json.loads(resp.read().decode("utf-8", "replace"))
    except urllib.error.HTTPError as e:
        raise RuntimeError(
            f"ComfyUI returned HTTP {e.code} ({e.reason}): "
            f"{e.read().decode('utf-8', 'replace')[:400]}"
        ) from e
    except urllib.error.URLError as e:
        raise RuntimeError(
            f"Cannot reach ComfyUI at {COMFY_BASE_URL} — is the server running? ({e.reason})"
        ) from e


def _get_json(path: str, timeout: int = 30):
    url = COMFY_BASE_URL.rstrip("/") + path
    try:
        with urllib.request.urlopen(urllib.request.Request(url), timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8", "replace"))
    except urllib.error.URLError as e:
        raise RuntimeError(
            f"Cannot reach ComfyUI at {COMFY_BASE_URL} — is the server running? ({e.reason})"
        ) from e


def _fetch_bytes(path: str, timeout: int = 120) -> bytes:
    url = COMFY_BASE_URL.rstrip("/") + path
    try:
        with urllib.request.urlopen(urllib.request.Request(url), timeout=timeout) as resp:
            return resp.read()
    except urllib.error.URLError as e:
        raise RuntimeError(f"Cannot fetch {url}: {e.reason}") from e


def _combo_names(info: dict, node: str, field: str) -> list[str]:
    combo = (info.get(node, {})
             .get("input", {}).get("required", {}).get(field, []))
    names = []
    for item in combo:
        if isinstance(item, list):
            names.extend(str(f) for f in item if isinstance(f, str))
        elif isinstance(item, str):
            names.append(item)
    return names


# ═══════════════════════════════════════════════════════════════
#  Model discovery
# ═══════════════════════════════════════════════════════════════

def list_models() -> list[str]:
    """Diffusion models the server can load (UnetLoaderGGUF combo)."""
    return _combo_names(_get_json("/object_info/UnetLoaderGGUF"),
                        "UnetLoaderGGUF", "unet_name")


def discover_model() -> str:
    if MODEL_HINT:
        return MODEL_HINT
    models = list_models()
    if not models:
        raise RuntimeError(
            f"ComfyUI at {COMFY_BASE_URL} has no diffusion models — install "
            "flux-2-klein-4b GGUF into ComfyUI/models/unet/"
        )
    for m in models:
        if "klein" in m.lower():
            return m
    for m in models:
        if "flux" in m.lower():
            return m
    return models[0]


def _resolve_model(model: str | None) -> str:
    """A fuzzy --model string picks the first installed model that contains it."""
    if not model:
        return discover_model()
    models = list_models()
    for m in models:
        if model.lower() in m.lower():
            return m
    return model


def list_clips() -> list[str]:
    """Text encoders the server can load (CLIPLoader combo)."""
    return _combo_names(_get_json("/object_info/CLIPLoader"), "CLIPLoader", "clip_name")


def list_vaes() -> list[str]:
    """VAEs the server can load (VAELoader combo)."""
    return _combo_names(_get_json("/object_info/VAELoader"), "VAELoader", "vae_name")


def discover_clip() -> str:
    clips = list_clips()
    for name in clips:
        if "qwen" in name.lower():
            return name
    if clips:
        return clips[0]
    return "qwen_3_4b_fp4_flux2.safetensors"


def discover_vae() -> str:
    vaes = list_vaes()
    for name in vaes:
        if "flux2" in name.lower():
            return name
    if vaes:
        return vaes[0]
    return "flux2-vae.safetensors"


# ═══════════════════════════════════════════════════════════════
#  Generation (ComfyUI API: /prompt -> poll /history -> /view)
# ═══════════════════════════════════════════════════════════════

def _klein_workflow(prompt: str, width: int, height: int, model: str,
                    clip: str, vae: str, seed: int,
                    steps: int = STEPS, cfg: float = CFG,
                    prefix: str = "nautilus") -> dict:
    """FLUX.2-klein distilled text-to-image graph (official template wiring)."""
    return {
        "1": {"class_type": "UnetLoaderGGUF",
              "inputs": {"unet_name": model, "weight_dtype": "default"}},
        "2": {"class_type": "CLIPLoader",
              "inputs": {"clip_name": clip, "type": "flux2"}},
        "3": {"class_type": "VAELoader", "inputs": {"vae_name": vae}},
        "4": {"class_type": "CLIPTextEncode", "inputs": {"clip": ["2", 0], "text": prompt}},
        "5": {"class_type": "ConditioningZeroOut", "inputs": {"conditioning": ["4", 0]}},
        "6": {"class_type": "Flux2Scheduler",
              "inputs": {"steps": steps, "width": width, "height": height}},
        "7": {"class_type": "EmptyFlux2LatentImage",
              "inputs": {"width": width, "height": height, "batch_size": 1}},
        "8": {"class_type": "RandomNoise", "inputs": {"noise_seed": seed}},
        "9": {"class_type": "KSamplerSelect", "inputs": {"sampler_name": SAMPLER}},
        "10": {"class_type": "CFGGuider",
               "inputs": {"model": ["1", 0], "positive": ["4", 0],
                          "negative": ["5", 0], "cfg": cfg}},
        "11": {"class_type": "SamplerCustomAdvanced",
               "inputs": {"noise": ["8", 0], "guider": ["10", 0], "sampler": ["9", 0],
                          "sigmas": ["6", 0], "latent_image": ["7", 0]}},
        "12": {"class_type": "VAEDecode",
               "inputs": {"samples": ["11", 0], "vae": ["3", 0]}},
        "13": {"class_type": "SaveImage",
               "inputs": {"images": ["12", 0], "filename_prefix": prefix}},
    }


def generate_image_bytes(prompt: str, width: int, height: int,
                         model: str | None = None, seed: int | None = None,
                         timeout: int = 3600, prefix: str = "") -> bytes:
    """Queue the klein workflow and return the raw output PNG bytes."""
    model = _resolve_model(model)
    clip = discover_clip()
    vae = discover_vae()
    seed = seed if seed is not None else secrets.randbits(53)
    wf = _klein_workflow(prompt, width, height, model, clip, vae, seed)
    body = _post_json("/prompt", {"prompt": wf})
    prompt_id = body.get("prompt_id")
    if not prompt_id:
        raise RuntimeError(f"ComfyUI rejected the prompt: {body}")
    label = f"{prefix} " if prefix else ""
    print(f"[ai_assets] {label}queued {width}x{height} (model {model}, clip {clip}, "
          f"vae {vae}, seed {seed})")

    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        time.sleep(2)
        history = _get_json(f"/history/{prompt_id}")
        entry = history.get(prompt_id)
        if not entry:
            continue
        status = entry.get("status", {})
        if status.get("status_str") == "error":
            msgs = status.get("messages", [])
            raise RuntimeError(f"ComfyUI execution error: {msgs}")
        images = []
        for node_out in entry.get("outputs", {}).values():
            images.extend(node_out.get("images", []))
        if images:
            img = images[0]
            path = (f"/view?filename={img['filename']}"
                    f"&subfolder={img.get('subfolder', '')}&type={img.get('type', 'output')}")
            return _fetch_bytes(path)
    raise RuntimeError(f"Timed out after {timeout}s waiting for generation {prompt_id}")


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


# ═══════════════════════════════════════════════════════════════
#  Wallpapers
# ═══════════════════════════════════════════════════════════════

def generate_wallpaper(theme: str = "abyss", width: int = 1920, height: int = 1080,
                       model: str | None = None, prompt: str | None = None,
                       force: bool = False, seed: int | None = None) -> str:
    """Generate an AI wallpaper for a theme, cached to assets/wallpapers/<theme>.png."""
    out = os.path.join(WALLPAPERS_DIR, f"{theme}.png")
    if os.path.exists(out) and not force:
        return out
    gen_w, gen_h = _gen_size_for(width, height)
    print(f"[ai_assets] wallpaper {theme} {gen_w}x{gen_h} -> {width}x{height}")
    text = prompt or WALLPAPER_PROMPTS.get(theme, WALLPAPER_PROMPTS["abyss"])
    data = generate_image_bytes(text, gen_w, gen_h, model, seed,
                                prefix=f"nautilus-{theme}")
    return _save_scaled(data, out, width, height)


def generate_wallpapers(model: str | None = None, force: bool = False,
                        seed: int | None = None) -> list[str]:
    """Generate every wallpaper theme."""
    written = []
    for theme in WALLPAPER_PROMPTS:
        out = os.path.join(WALLPAPERS_DIR, f"{theme}.png")
        if os.path.exists(out) and not force:
            print(f"[ai_assets] skip  wallpaper {theme} (cached)")
            continue
        try:
            written.append(generate_wallpaper(theme, model=model, force=force, seed=seed))
        except RuntimeError as e:
            print(f"[ai_assets] FAIL  wallpaper {theme}: {e}", file=sys.stderr)
    return written


# ═══════════════════════════════════════════════════════════════
#  Icons
# ═══════════════════════════════════════════════════════════════

def generate_icons(model: str | None = None, force: bool = False,
                   seed: int | None = None) -> list[str]:
    """Generate every app icon at 512px and downscale to the 128px cache."""
    written = []
    for app_id, prompt in ICON_PROMPTS.items():
        out = os.path.join(LOGOS_DIR, f"{app_id}.png")
        if os.path.exists(out) and not force:
            print(f"[ai_assets] skip  {app_id} (cached)")
            continue
        print(f"[ai_assets] icon  {app_id} ...")
        try:
            data = generate_image_bytes(prompt, ICON_GEN_SIZE, ICON_GEN_SIZE, model, seed,
                                        prefix=f"nautilus-icon-{app_id}")
            _save_scaled(data, out, ICON_OUT_SIZE, ICON_OUT_SIZE)
            written.append(out)
        except RuntimeError as e:
            print(f"[ai_assets] FAIL  {app_id}: {e}", file=sys.stderr)
    return written


def analyze_image(path: str) -> dict:
    """Lightweight quality audit of a cached PNG (no window needed).

    Samples luminance/saturation statistics via QImage and returns verdicts:
    flat (too uniform), empty (no foreground), washed (too bright),
    or dark (nothing readable). Called by --check.
    """
    from PySide6.QtGui import QImage

    img = QImage(path)
    if img.isNull():
        return {"ok": False, "reason": "unreadable file"}
    w, h = img.width(), img.height()
    if w < 32 or h < 32:
        return {"ok": False, "reason": "too small"}

    step = max(1, (w * h) // 16_000)
    n = 0
    luma_sum = luma2 = 0.0
    colorful = 0
    flat = 0
    for y in range(0, h, step):
        for x in range(0, w, step):
            c = img.pixelColor(x, y)
            lum = 0.2126 * c.red() + 0.7152 * c.green() + 0.0722 * c.blue()
            n += 1
            luma_sum += lum
            luma2 += lum * lum
            mx, mn = max(c.red(), c.green(), c.blue()), min(c.red(), c.green(), c.blue())
            if mx - mn > 24:
                colorful += 1
            if mx - mn < 8:
                flat += 1
    if n == 0:
        return {"ok": False, "reason": "no pixels"}

    mean = luma_sum / n
    std = ((luma2 / n) - mean * mean) ** 0.5
    color_ratio = colorful / n
    flat_ratio = flat / n

    reasons = []
    if std < 9.0:
        reasons.append("flat")
    if color_ratio < 0.04:
        reasons.append("bland")
    if mean < 28:
        reasons.append("too dark")
    if mean > 225:
        reasons.append("washed out")
    return {
        "ok": not reasons,
        "reason": ", ".join(reasons) if reasons else "ok",
        "mean_luma": round(mean, 1),
        "std_luma": round(std, 1),
        "colorful": round(color_ratio, 3),
        "flat_ratio": round(flat_ratio, 3),
    }


def check_icons(verbose: bool = False) -> list[str]:
    """Return the list of icon ids whose cached PNG fails the quality audit."""
    bad = []
    for app_id in ICON_PROMPTS:
        path = os.path.join(LOGOS_DIR, f"{app_id}.png")
        if not os.path.exists(path):
            print(f"[ai_assets] MISS  {app_id} (no cached icon)")
            bad.append(app_id)
            continue
        report = analyze_image(path)
        ok = report["ok"]
        if not ok:
            bad.append(app_id)
        if verbose or not ok:
            print(f"[ai_assets] {'OK  ' if ok else 'BAD '} {app_id:<15} "
                  f"luma={report.get('mean_luma')} std={report.get('std_luma')} "
                  f"colorful={report.get('colorful')} flat={report.get('flat_ratio')} "
                  f"-> {report.get('reason', '')}")
    return bad


# ═══════════════════════════════════════════════════════════════
#  CLI
# ═══════════════════════════════════════════════════════════════

def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        prog="python3 -m core.ai_assets",
        description="Generate Nautilus wallpapers + app icons with a local ComfyUI / FLUX.2-klein model.",
    )
    ap.add_argument("--wallpaper", nargs="?", const="abyss", metavar="THEME",
                    help="regenerate one wallpaper theme (default: abyss)")
    ap.add_argument("--wallpapers", action="store_true", help="regenerate every wallpaper theme")
    ap.add_argument("--icons", action="store_true", help="regenerate all app icons")
    ap.add_argument("--check", action="store_true",
                    help="audit cached icons and report poor quality (--fix to regenerate)")
    ap.add_argument("--fix", action="store_true",
                    help="with --check, regenerate flagged icons")
    ap.add_argument("-W", "--width", type=int, default=1920, help="wallpaper target width")
    ap.add_argument("-H", "--height", type=int, default=1080, help="wallpaper target height")
    ap.add_argument("-m", "--model", default=MODEL_HINT or None, help="diffusion model filename / substring")
    ap.add_argument("--prompt", default=None, help="override wallpaper prompt")
    ap.add_argument("--seed", type=int, default=None, help="random seed (default: random)")
    ap.add_argument("-f", "--force", action="store_true", help="regenerate even if cached")
    ap.add_argument("-y", "--yes", action="store_true", help="skip confirmation prompts")
    args = ap.parse_args(argv)

    if not (args.wallpaper or args.wallpapers or args.icons or args.check):
        args.wallpaper = "abyss"

    # ── Audit mode (works without a server) ──
    if args.check:
        bad = check_icons(verbose=True)
        if bad and args.fix:
            print(f"[ai_assets] regenerating {len(bad)} flagged icon(s): {', '.join(bad)}")
            if not args.yes:
                if input("Continue? [y/N] ").strip().lower() not in ("y", "yes"):
                    return 1
            model = _resolve_model(args.model)
            fixed = generate_icons_where(model, bad, args.seed)
            print(f"[ai_assets] regenerated {len(fixed)}")
        elif bad:
            print(f"[ai_assets] {len(bad)} icon(s) failed audit: {', '.join(bad)} "
                  "(rerun with --fix)")
        else:
            print("[ai_assets] all icons passed audit")
        return 0

    # ── Generation mode (needs a running ComfyUI server) ──
    try:
        model = _resolve_model(args.model)
    except RuntimeError as e:
        print(f"[ai_assets] {e}", file=sys.stderr)
        return 1
    print(f"[ai_assets] model: {model}")

    if args.wallpapers:
        generate_wallpapers(model, args.force, args.seed)
        print("[ai_assets] wallpapers -> assets/wallpapers/")
    elif args.wallpaper:
        generate_wallpaper(args.wallpaper, args.width, args.height,
                           model, args.prompt, args.force, args.seed)
        print(f"[ai_assets] wallpaper {args.wallpaper} -> assets/wallpapers/")

    if args.icons:
        if (args.wallpaper or args.wallpapers) and not args.yes:
            if input("Generate all 18 app icons too? [y/N] ").strip().lower() not in ("y", "yes"):
                return 0
        generate_icons(model, args.force, args.seed)
        print("[ai_assets] icons -> assets/logos/")
    return 0


def generate_icons_where(model: str, app_ids: list[str], seed: int | None = None) -> list[str]:
    """Regenerate a specific subset of icons (used by --check --fix)."""
    written = []
    for app_id in app_ids:
        prompt = ICON_PROMPTS.get(app_id)
        if not prompt:
            continue
        out = os.path.join(LOGOS_DIR, f"{app_id}.png")
        print(f"[ai_assets] icon  {app_id} ...")
        try:
            data = generate_image_bytes(prompt, ICON_GEN_SIZE, ICON_GEN_SIZE, model, seed,
                                        prefix=f"nautilus-icon-{app_id}")
            _save_scaled(data, out, ICON_OUT_SIZE, ICON_OUT_SIZE)
            written.append(out)
        except RuntimeError as e:
            print(f"[ai_assets] FAIL  {app_id}: {e}", file=sys.stderr)
    return written


if __name__ == "__main__":
    sys.exit(main())
