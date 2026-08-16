"""Nautilus ImageGen — pure-NumPy inference engine.

Loads the int8 diffusion model, denoises 32×32 art from a text prompt, upsizes
to wallpaper resolution, writes PNGs, and renders animated video via ffmpeg.
"""

import json
import math
import os
import struct
import subprocess
import tempfile
import zlib

import numpy as np

from models.imggen.data import text_style_vector


def _load_weights(model_dir: str) -> dict:
    from models.lm.export import load_struct

    arr = np.load(os.path.join(model_dir, "weights.npz"))
    out = {}
    for key in arr.files:
        v = arr[key]
        if v.dtype.names:
            out[key] = load_struct(v)
        else:
            out[key] = v
    return out


def _conv2d(x, w, pad=1):
    """x: (C,H,W) float32, w: (O,C,3,3). Returns (O,H',W')."""
    out_ch, c_in, kh, kw = w.shape
    n, c, h, ww = x.shape
    xp = np.pad(x, ((0, 0), (0, 0), (pad, pad), (pad, pad)))
    out = np.zeros((n, out_ch, h, ww), dtype=np.float32)
    for oi in range(out_ch):
        acc = np.zeros((n, h, ww), dtype=np.float32)
        for ci in range(c_in):
            for di in range(kh):
                for dj in range(kw):
                    acc += xp[:, ci, di : di + h, dj : dj + ww] * w[oi, ci, di, dj]
        out[:, oi] = acc
    return out


def _group_norm(x, w, b, groups=4):
    n, c, h, ww = x.shape
    x = x.reshape(n, groups, c // groups, h, ww)
    mu = x.mean(axis=(2, 3, 4), keepdims=True)
    var = x.var(axis=(2, 3, 4), keepdims=True)
    x = (x - mu) / np.sqrt(var + 1e-5)
    x = x.reshape(n, c, h, ww)
    return x * w.reshape(1, -1, 1, 1) + b.reshape(1, -1, 1, 1)


def _silu(x):
    return x * (1.0 / (1.0 + np.exp(-x)))


class TinyUNetNumpy:
    def __init__(self, model_dir: str):
        self.w = _load_weights(model_dir)
        with open(os.path.join(model_dir, "config.json")) as f:
            self.cfg = json.load(f)

    def _film_block(self, name, h, cond):
        w = self.w
        h = _conv2d(h, w[f"{name}.conv.weight"])
        h = _group_norm(h, w[f"{name}.gn.weight"], w[f"{name}.gn.bias"])
        h = _silu(h)
        gamma = cond @ w[f"{name}.gamma.weight"].T + w[f"{name}.gamma.bias"]
        beta = cond @ w[f"{name}.beta.weight"].T + w[f"{name}.beta.bias"]
        return h * gamma[..., None, None] + beta[..., None, None]

    def forward(self, x, t, style):
        w = self.w
        t = np.asarray(t, dtype=np.float32).reshape(-1, 1)
        t_emb = np.tanh(t @ w["time_mlp.0.weight"].T + w["time_mlp.0.bias"])
        t_emb = np.tanh(t_emb @ w["time_mlp.2.weight"].T + w["time_mlp.2.bias"])
        s_emb = np.tanh(style @ w["style_proj.weight"].T + w["style_proj.bias"])
        cond = np.concatenate([t_emb, s_emb], axis=1)
        h1 = self._film_block("down1", x, cond)
        h2 = self._film_block("down2", h1, cond)
        m = self._film_block("mid", h2, cond)
        u2 = self._film_block("up2", np.concatenate([m, h2], axis=1), cond)
        u1 = self._film_block("up1", np.concatenate([u2, h1], axis=1), cond)
        return _conv2d(u1, w["out.weight"]) + w["out.bias"].reshape(1, -1, 1, 1)


class ImageGen:
    def __init__(self, model_dir: str):
        self.model_dir = model_dir
        self.unet = TinyUNetNumpy(model_dir)
        with open(os.path.join(model_dir, "model.json")) as f:
            self.meta = json.load(f)
        self.n_steps = int(self.meta.get("n_steps", 200))
        self._schedule = None

    @property
    def schedule(self):
        if self._schedule is None:
            betas = np.zeros(self.n_steps, dtype=np.float32)
            for i in range(self.n_steps):
                t = i / self.n_steps
                a1 = np.cos(0.5 * np.pi * t) ** 2
                a2 = np.cos(0.5 * np.pi * (t + 1.0 / self.n_steps)) ** 2
                betas[i] = min(1 - a2 / a1, 0.999)
            betas = np.clip(betas, 1e-4, 0.999).astype(np.float32)
            alphas = 1 - betas
            abar = np.cumprod(alphas)
            self._schedule = (betas, alphas, abar)
        return self._schedule

    def denoise(self, x, style_vec, t_start=None, steps=None):
        """Full (or partial) DDPM reverse pass from x at t_start."""
        betas, alphas, abar = self.schedule
        if t_start is None:
            t_start = self.n_steps
        if steps is None:
            steps = self.n_steps
        idx = np.linspace(0, t_start - 1, steps).astype(int)
        x = x.copy()
        for i in reversed(idx):
            t = i / self.n_steps
            pred = self.unet.forward(x, np.asarray(t, dtype=np.float32).reshape(1, 1), style_vec)
            a = alphas[i]
            b = betas[i]
            ab = abar[i]
            mu = (x - (b / np.sqrt(max(1 - ab, 1e-6))) * pred) / np.sqrt(a)
            if i > 0:
                x = mu + np.sqrt(b) * np.random.randn(*x.shape).astype(np.float32)
            else:
                x = mu
        return np.clip(x, -1, 1)

    # ── public API ─────────────────────────────────────────────
    def generate(self, prompt: str, size: int = 512, seed: int | None = None, steps: int = 50):
        if seed is not None:
            np.random.seed(seed)
        style_vec = text_style_vector(prompt).reshape(1, -1)
        x = np.random.randn(1, 3, 32, 32).astype(np.float32)
        art = self.denoise(x, style_vec, steps=steps)[0]
        arr = _to_uint8(art)
        return upscale(arr, size)

    def frames(self, prompt: str, count: int = 30, seed: int | None = None, steps: int = 40):
        """Return a list of uint8 RGB (32,32,3) frames with gentle motion."""
        if seed is not None:
            np.random.seed(seed)
        style_vec = text_style_vector(prompt).reshape(1, -1)
        betas, alphas, abar = self.schedule
        base = self.generate(prompt, 32, seed, steps=steps)
        base_n = (base.astype(np.float32) / 127.5) - 1.0
        frames = []
        n_frames = count
        for k in range(n_frames):
            t_k = int(0.25 * self.n_steps + 0.15 * self.n_steps * math.sin(2 * math.pi * k / max(n_frames - 1, 1)))
            t_k = max(4, min(self.n_steps - 1, t_k))
            z = np.random.randn(1, 3, 32, 32).astype(np.float32)
            ab = abar[t_k]
            x = np.sqrt(ab) * base_n[None] + np.sqrt(1 - ab) * z
            art = self.denoise(x, style_vec, t_start=t_k, steps=steps)[0]
            frames.append(_to_uint8(art))
        return frames

    def video(self, prompt: str, out_path: str, seconds: int = 4, fps: int = 12, size: int = 512, seed: int | None = None, steps: int = 40):
        """Render an animated mp4 from rolling diffusion frames (via ffmpeg)."""
        frames = self.frames(prompt, count=seconds * fps, seed=seed, steps=steps)
        big = [upscale(f, size) for f in frames]
        return _write_mp4(big, out_path, fps)


# ── image helpers ───────────────────────────────────────────────
def _to_uint8(art: np.ndarray) -> np.ndarray:
    a = ((art + 1.0) * 127.5).astype(np.float32)
    a = np.clip(a, 0, 255).transpose(1, 2, 0)
    return a.astype(np.uint8)


def upscale(img: np.ndarray, target: int) -> np.ndarray:
    """Bilinear upscale of an (H,W,3) uint8 image to `target` square."""
    h, w, _ = img.shape
    if h == target and w == target:
        return img
    f = target / h
    xs = np.minimum((np.arange(target) + 0.5) / f - 0.5, h - 1)
    x0 = xs.astype(int)
    x1 = np.minimum(x0 + 1, h - 1)
    wx = (xs - x0)[:, None]
    ys = np.minimum((np.arange(target) + 0.5) / f - 0.5, w - 1)
    y0 = ys.astype(int)
    y1 = np.minimum(y0 + 1, w - 1)
    wy = (ys - y0)[None, :, None]
    img = img.astype(np.float32)
    top = img[x0][:, y0] * (1 - wy) + img[x0][:, y1] * wy
    bot = img[x1][:, y0] * (1 - wy) + img[x1][:, y1] * wy
    out = top * (1 - wx) + bot * wx
    return np.clip(out, 0, 255).astype(np.uint8)


def save_png(path: str, img: np.ndarray):
    """Write an RGB (H,W,3) uint8 image as PNG using only stdlib."""
    h, w, _ = img.shape
    raw = bytearray()
    for y in range(h):
        raw.append(0)
        raw.extend(img[y].tobytes())
    compressed = zlib.compress(bytes(raw), 6)

    def chunk(ctype: bytes, data: bytes) -> bytes:
        c = struct.pack(">I", len(data)) + ctype + data
        crc = zlib.crc32(ctype + data) & 0xFFFFFFFF
        return c + struct.pack(">I", crc)

    png = b"\x89PNG\r\n\x1a\n"
    png += chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0))
    png += chunk(b"IDAT", compressed)
    png += chunk(b"IEND", b"")
    with open(path, "wb") as f:
        f.write(png)


def _write_mp4(frames: list[np.ndarray], out_path: str, fps: int) -> str:
    with tempfile.TemporaryDirectory() as tmp:
        for i, f in enumerate(frames):
            save_png(os.path.join(tmp, f"f{i:04d}.png"), f)
        subprocess.run(
            ["ffmpeg", "-y", "-framerate", str(fps), "-i", os.path.join(tmp, "f%04d.png"),
             "-vf", "format=yuv420p", "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", out_path],
            check=True, capture_output=True,
        )
    return out_path
