"""Nautilus ImageGen — tiny conditional diffusion U-Net (torch, CPU).

A ~150K-param FiLM-conditioned U-Net that denoises 32×32 RGB art given a
style vector and a diffusion time step. Small enough to train in minutes on
CPU and to run in pure NumPy afterwards.
"""

import os

import numpy as np
import torch
import torch.nn as nn


def default_unet_cfg():
    return {"size": 32, "ch": 32, "ch_mid": 64, "style_dim": 64, "time_dim": 16}


def _film(x, gamma, beta):
    return x * gamma[..., None, None] + beta[..., None, None]


class ConvBlock(nn.Module):
    def __init__(self, cin, cout):
        super().__init__()
        self.conv = nn.Conv2d(cin, cout, 3, padding=1, bias=False)
        self.gn = nn.GroupNorm(4, cout)
        self.gamma = nn.Linear(96, cout)
        self.beta = nn.Linear(96, cout)

    def forward(self, x, cond):
        h = self.conv(x)
        h = self.gn(h)
        h = torch.nn.functional.silu(h)
        h = _film(h, self.gamma(cond), self.beta(cond))
        return h


class TinyUNet(nn.Module):
    def __init__(self, cfg=None):
        super().__init__()
        self.cfg = cfg or default_unet_cfg()
        c, cm = self.cfg["ch"], self.cfg["ch_mid"]
        self.time_mlp = nn.Sequential(
            nn.Linear(1, self.cfg["time_dim"]), nn.SiLU(), nn.Linear(self.cfg["time_dim"], self.cfg["time_dim"])
        )
        self.style_proj = nn.Linear(self.cfg["style_dim"], 80)
        self.down1 = ConvBlock(3, c)
        self.down2 = ConvBlock(c, cm)
        self.mid = ConvBlock(cm, cm)
        self.up2 = ConvBlock(cm + cm, cm)
        self.up1 = ConvBlock(cm + c, c)
        self.out = nn.Conv2d(c, 3, 3, padding=1)

    def forward(self, x, t, style):
        t_emb = self.time_mlp(t)
        s_emb = self.style_proj(style)
        cond = torch.cat([t_emb, s_emb], dim=1)
        h1 = self.down1(x, cond)
        h2 = self.down2(h1, cond)
        m = self.mid(h2, cond)
        u2 = self.up2(torch.cat([m, h2], dim=1), cond)
        u1 = self.up1(torch.cat([u2, h1], dim=1), cond)
        return self.out(u1)


# ── diffusion schedule (cosine) ─────────────────────────────────
def betas_for_alpha_bar(n_steps: int = 200, s: float = 0.008) -> np.ndarray:
    steps = np.arange(n_steps + 1) / n_steps
    alpha_bar = np.cos((steps + s) / (1 + s) * np.pi / 2) ** 2
    alpha_bar = alpha_bar / alpha_bar[0]
    betas = 1 - alpha_bar[1:] / alpha_bar[:-1]
    return np.clip(betas, 1e-5, 0.999)


def export_int8(model: nn.Module, out_dir: str):
    os.makedirs(out_dir, exist_ok=True)
    import json

    from models.lm.export import quantize_rows, save_weights

    with open(os.path.join(out_dir, "config.json"), "w") as f:
        json.dump(model.cfg, f)

    payload = {}
    for name, param in model.state_dict().items():
        if param.ndim <= 1 or ("gn" in name and "weight" in name):
            payload[name] = {"shape": param.shape, "vals": param.detach().numpy().astype(np.float32)}
        else:
            payload[name] = quantize_rows(param.detach().numpy())
    save_weights(os.path.join(out_dir, "weights.npz"), payload)
    return out_dir
