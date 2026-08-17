"""Charybdis — image/video generation engine.

Pure-Python visual creation: procedural art, pixel synthesis, pattern
generation, and neural-style transfer concepts. No external dependencies.
"""

from __future__ import annotations

import hashlib
import math
import os
import struct
from collections.abc import Callable

import numpy as np

from apps.kraken.core.engine import BaseEngine, EngineResponse

# ── Image primitives (pure NumPy) ─────────────────────────────────

def _gradient(w: int, h: int, c1: list, c2: list, axis: int = 0) -> np.ndarray:
    """Linear gradient between two RGB colors."""
    t = np.linspace(0, 1, h if axis == 0 else w).reshape(-1, 1, 1) if axis == 0 else np.linspace(0, 1, w).reshape(1, -1, 1)
    c1 = np.array(c1[:3], dtype=np.float32)
    c2 = np.array(c2[:3], dtype=np.float32)
    grad = (1 - t) * c1 + t * c2
    if axis == 0:
        grad = np.broadcast_to(grad, (h, w, 3))
    else:
        grad = np.broadcast_to(grad, (h, w, 3))
    return np.clip(grad, 0, 255).astype(np.uint8)


def _plasma(w: int, h: int, seed: int = 0, scale: float = 0.02) -> np.ndarray:
    """Perlin-like plasma pattern."""
    rng = np.random.RandomState(seed)
    noise = rng.randn(h // 8 + 2, w // 8 + 2).astype(np.float32)
    # Bilinear upsample
    x = np.linspace(0, noise.shape[1] - 1, w)
    y = np.linspace(0, noise.shape[0] - 1, h)
    xi = np.clip(x.astype(int), 0, noise.shape[1] - 2)
    yi = np.clip(y.astype(int), 0, noise.shape[0] - 2)
    xf = x - xi
    yf = y - yi
    img = np.zeros((h, w, 3), dtype=np.float32)
    for c in range(3):
        top = noise[yi[:, None], xi[None, :]] * (1 - xf[None, :]) + noise[yi[:, None], xi[None, :] + 1] * xf[None, :]
        bot = noise[yi[:, None] + 1, xi[None, :]] * (1 - xf[None, :]) + noise[yi[:, None] + 1, xi[None, :] + 1] * xf[None, :]
        val = top * (1 - yf[:, None]) + bot * yf[:, None]
        img[:, :, c] = val
    img = (img - img.min()) / (img.max() - img.min() + 1e-8)
    return (img * 255).astype(np.uint8)


def _mandelbrot(w: int, h: int, max_iter: int = 64) -> np.ndarray:
    """Fractal mandelbrot set as an image."""
    x = np.linspace(-2.5, 1.0, w)
    y = np.linspace(-1.2, 1.2, h)
    C = x[None, :] + 1j * y[:, None]
    Z = np.zeros_like(C)
    img = np.zeros((h, w), dtype=np.float32)
    for i in range(max_iter):
        mask = np.abs(Z) < 4
        Z[mask] = Z[mask] ** 2 + C[mask]
        img[mask] = i
    img = img / max_iter
    # Colorize with ocean palette
    r = (np.sin(img * 3.14 * 2) * 127 + 128).astype(np.uint8)
    g = (np.sin(img * 3.14 * 3 + 1) * 127 + 128).astype(np.uint8)
    b = (np.cos(img * 3.14 * 2) * 127 + 128).astype(np.uint8)
    return np.stack([r, g, b], axis=-1)


def _ocean_waves(w: int, h: int, seed: int = 0) -> np.ndarray:
    """Abstract ocean wave pattern."""
    rng = np.random.RandomState(seed)
    img = np.zeros((h, w, 3), dtype=np.float32)
    for _ in range(rng.randint(3, 8)):
        freq = rng.uniform(0.005, 0.03)
        phase = rng.uniform(0, 2 * math.pi)
        amp = rng.uniform(0.3, 1.0)
        y_coords = np.arange(h).reshape(-1, 1)
        x_coords = np.arange(w).reshape(1, -1)
        wave = np.sin(x_coords * freq + y_coords * freq * 0.5 + phase) * amp
        color = rng.uniform(0.2, 0.8, 3).astype(np.float32)
        for c in range(3):
            img[:, :, c] += wave * color[c]
    img = (img - img.min()) / (img.max() - img.min() + 1e-8)
    return (img * 255).astype(np.uint8)


def _pixel_creature(w: int, h: int, creature: str = "kraken", seed: int = 0) -> np.ndarray:
    """Generate a small pixel-art sea creature and upscale."""
    rng = np.random.RandomState(seed + hash(creature) % 10000)
    # Generate a random symmetrical pixel pattern
    gw, gh = 16, 16
    half = rng.randint(0, 2, (gh, gw // 2 + 1)).astype(np.float32)
    grid = np.concatenate([half, half[:, :-1][:, ::-1]], axis=1)
    # Apply creature-specific color
    colors = {
        "kraken": [(0, 242, 194), (0, 77, 64)],
        "leviathan": [(123, 104, 238), (46, 26, 110)],
        "charybdis": [(255, 107, 157), (107, 26, 58)],
        "megalodon": [(255, 68, 68), (107, 26, 26)],
    }
    c1, c2 = colors.get(creature, [(0, 242, 194), (0, 77, 64)])
    img = np.zeros((gh, gw, 3), dtype=np.uint8)
    for y in range(gh):
        for x in range(gw):
            if grid[y, x] > 0.5:
                img[y, x] = c1
            else:
                img[y, x] = c2
    # Upscale with nearest-neighbor
    scale = max(w // gw, h // gh, 1)
    img = np.repeat(np.repeat(img, scale, axis=0), scale, axis=1)
    # Crop to target size
    if img.shape[0] > h:
        img = img[:h]
    if img.shape[1] > w:
        img = img[:, :w]
    return img


def _save_png(img: np.ndarray, path: str):
    """Save a uint8 RGB array as PNG using only stdlib + numpy."""
    import zlib
    h, w = img.shape[:2]
    raw = b""
    for y in range(h):
        raw += b"\x00" + img[y].tobytes()
    compressed = zlib.compress(raw)

    def chunk(tag, data):
        c = tag + data
        return struct.pack(">I", len(data)) + c + struct.pack(">I", zlib.crc32(c) & 0xFFFFFFFF)

    ihdr = struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0)
    with open(path, "wb") as f:
        f.write(b"\x89PNG\r\n\x1a\n")
        f.write(chunk(b"IHDR", ihdr))
        f.write(chunk(b"IDAT", compressed))
        f.write(chunk(b"IEND", b""))


# ── Charybdis engine ─────────────────────────────────────────────

PROMPTS_TO_VISUAL = {
    "ocean": _ocean_waves,
    "wave": _ocean_waves,
    "plasma": _plasma,
    "fractal": _mandelbrot,
    "mandelbrot": _mandelbrot,
}


class CharybdisEngine(BaseEngine):
    model_id = "charybdis"

    def __init__(self, cfg):
        self.cfg = cfg

    def respond(
        self,
        messages: list[dict],
        temperature: float = 0.7,
        max_tokens: int = 4096,
        stream: Callable[[str], None] | None = None,
        workspace: str | None = None,
    ) -> EngineResponse:
        t0 = self._tick()
        user_msg = ""
        for m in reversed(messages):
            if m.get("role") == "user":
                user_msg = m.get("content", "")
                break

        lower = user_msg.lower()
        seed = int(hashlib.md5(user_msg.encode()).hexdigest()[:8], 16) % 100000
        w, h = 512, 512

        # Determine what to generate
        img = None
        visual_type = "procedural"

        if any(k in lower for k in ("fractal", "mandelbrot", "infinity")):
            img = _mandelbrot(w, h)
            visual_type = "fractal"
        elif any(k in lower for k in ("ocean", "wave", "sea", "underwater")):
            img = _ocean_waves(w, h, seed)
            visual_type = "ocean waves"
        elif any(k in lower for k in ("plasma", "energy", "chaos")):
            img = _plasma(w, h, seed)
            visual_type = "plasma"
        elif any(k in lower for k in ("kraken", "leviathan", "charybdis", "megalodon", "creature", "monster")):
            creature = "kraken"
            for c in ("kraken", "leviathan", "charybdis", "megalodon"):
                if c in lower:
                    creature = c
                    break
            img = _pixel_creature(w, h, creature, seed)
            visual_type = f"pixel {creature}"
        elif any(k in lower for k in ("gradient", "color", "palette")):
            img = _gradient(w, h, [0, 242, 194], [123, 104, 238], axis=0)
            visual_type = "gradient"
        else:
            # Default: ocean-themed plasma
            img = _ocean_waves(w, h, seed)
            visual_type = "procedural ocean"

        # Save to workspace
        out_dir = os.path.join(workspace or os.getcwd(), "generated")
        os.makedirs(out_dir, exist_ok=True)
        filename = f"charybdis_{seed}.png"
        out_path = os.path.join(out_dir, filename)
        _save_png(img, out_path)

        text = (
            f"[Charybdis — Visual Generated]\n\n"
            f"Type: {visual_type}\n"
            f"Size: {img.shape[1]}x{img.shape[0]}\n"
            f"Saved: {out_path}\n"
            f"Seed: {seed}\n\n"
            f"Describe what you see, or request changes "
            f"(e.g. 'make it blue', 'try a fractal', 'generate a kraken')."
        )
        if stream:
            for ch in text:
                stream(ch)
            stream("\x00")

        return EngineResponse(text=text, elapsed=self._done(t0), model_id=self.model_id)
