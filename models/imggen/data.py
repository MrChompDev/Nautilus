"""Nautilus ImageGen — synthetic Nautilus-style artwork dataset.

Procedurally renders abstract ocean wallpapers in the six OS theme palettes
(32×32, normalized to [-1,1]). The tiny diffusion model learns this exact
distribution, so its generations stay on-theme. Every sample is a fresh
random draw, so the dataset is unlimited and costs nothing.
"""

import numpy as np

STYLE_PALETTES = {
    "abyss": {"deep": (8, 22, 38), "mid": (14, 34, 56), "accent": (0, 242, 194), "glow": (0, 201, 160), "light": (110, 164, 184)},
    "aurora": {"deep": (5, 13, 20), "mid": (10, 30, 45), "accent": (255, 127, 80), "glow": (0, 242, 194), "light": (255, 165, 2)},
    "tide": {"deep": (6, 20, 34), "mid": (16, 44, 66), "accent": (0, 200, 160), "glow": (60, 140, 170), "light": (140, 200, 220)},
    "storm": {"deep": (2, 8, 14), "mid": (8, 20, 32), "accent": (120, 160, 190), "glow": (40, 70, 96), "light": (170, 190, 210)},
    "kelp": {"deep": (4, 20, 14), "mid": (10, 40, 28), "accent": (0, 200, 83), "glow": (60, 160, 100), "light": (150, 230, 180)},
    "stars": {"deep": (2, 6, 12), "mid": (8, 16, 30), "accent": (255, 255, 255), "glow": (90, 140, 200), "light": (220, 235, 255)},
}

KEYWORDS = (
    "abyss aurora tide storm kelp stars dark deep light calm wavy stormy glow neon "
    "pastel waves sea ocean night dawn foam splash current drift sparkle churn"
).split()

TEXT_VOCAB = KEYWORDS


def text_style_vector(text: str, dim: int = 64, seed: int = 7) -> np.ndarray:
    """Deterministic bag-of-words -> dense style vector (hashed projection)."""
    rng = np.random.RandomState(seed)
    proj = rng.normal(0.0, 1.0, size=(len(TEXT_VOCAB), dim)).astype(np.float32)
    words = text.lower().split()
    bow = np.zeros(len(TEXT_VOCAB), dtype=np.float32)
    for w in words:
        for i, kw in enumerate(TEXT_VOCAB):
            if kw in w or w in kw:
                bow[i] += 1.0
    return bow @ proj


def _hex_to_rgb(c):
    c = c.lstrip("#")
    return tuple(int(c[i : i + 2], 16) for i in (0, 2, 4))


def sample_art(style_key: str, seed: int, size: int = 32) -> np.ndarray:
    """Render one 32×32 abstract ocean wallpaper for a style."""
    pal = STYLE_PALETTES.get(style_key, STYLE_PALETTES["abyss"])
    rng = np.random.RandomState(seed % (2**31))
    S = size
    y = np.linspace(0.0, 1.0, S)[:, None]
    x = np.linspace(0.0, 1.0, S)[None, :]

    deep = np.array(pal["deep"], dtype=np.float32)
    mid = np.array(pal["mid"], dtype=np.float32)
    accent = np.array(pal["accent"], dtype=np.float32)
    glow = np.array(pal["glow"], dtype=np.float32)
    light = np.array(pal["light"], dtype=np.float32)

    grad = deep[None, :] * (1 - y) + mid[None, :] * y

    img = np.zeros((S, S, 3), dtype=np.float32)
    img += grad

    # 2-3 overlapping sine waves near the bottom half
    n_waves = rng.randint(2, 4)
    for _ in range(n_waves):
        amp = rng.uniform(0.04, 0.14)
        freq = rng.uniform(1.5, 4.0)
        phase = rng.uniform(0, 6.28)
        base = rng.uniform(0.55, 0.9)
        thickness = rng.uniform(0.012, 0.03)
        color = accent if rng.rand() < 0.7 else glow
        wave = np.sin(freq * 2 * np.pi * x + phase) * amp + base
        dist = np.abs(y - wave)
        energy = np.exp(-((dist / thickness) ** 2)) * (1 - y) ** 1.5
        img += color[None, None, :] * (energy[..., None] * rng.uniform(0.5, 1.0))

    # glow motes (soft blobs)
    n_motes = rng.randint(8, 22)
    for _ in range(n_motes):
        cx = rng.uniform(0, 1)
        cy = rng.uniform(0, 1)
        r = rng.uniform(0.04, 0.16)
        strength = rng.uniform(0.15, 0.5)
        color = light if rng.rand() < 0.5 else glow
        d = np.sqrt(((x - cx) / r) ** 2 + ((y - cy) / r) ** 2)
        img += color[None, None, :] * (np.exp(-(d**2))[..., None] * strength)

    # speckle stars / foam
    n_specks = rng.randint(0, 60)
    for _ in range(n_specks):
        sx = rng.randint(0, S)
        sy = rng.randint(0, S)
        img[sy, sx] += light * rng.uniform(0.3, 0.9)

    img = np.clip(img, 0, 255)
    img = img / 127.5 - 1.0
    return img.astype(np.float32)


def style_for_text(text: str) -> str:
    low = text.lower()
    for kw in KEYWORDS:
        if kw in low:
            return kw
    return "abyss"


def make_dataset(n: int, size: int = 32, seed: int = 42, style_dim: int = 64) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Return (images, style_vectors, style_key_idx)."""
    keys = list(STYLE_PALETTES)
    rng = np.random.RandomState(seed)
    proj = rng.normal(0.0, 1.0, size=(len(TEXT_VOCAB), style_dim)).astype(np.float32)
    imgs = np.empty((n, size, size, 3), dtype=np.float32)
    styles = np.empty((n, style_dim), dtype=np.float32)
    for i in range(n):
        key = keys[i % len(keys)]
        imgs[i] = sample_art(key, rng.randint(0, 2**31), size)
        bow = np.zeros(len(TEXT_VOCAB), dtype=np.float32)
        bow[KEYWORDS.index(key)] = 1.0
        bow[KEYWORDS.index(rng.choice(["glow", "light", "deep", "calm"]))] += 0.5
        styles[i] = bow @ proj
    return imgs, styles, np.arange(n)
