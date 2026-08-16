"""Nautilus LM — compact GPT-style decoder-only transformer (torch, CPU).

Config tuned so the int8 export lands in the 20-40MB budget:
  n_embd=512, n_layer=8, n_head=8, block_size=512, vocab=4096  (~30MB int8)
Uses SwiGLU MLP + tied embeddings to keep params tight.
"""

import json
import os

import numpy as np
import torch
import torch.nn as nn

DEFAULT_CONFIG = {
    "vocab_size": 4096,
    "block_size": 512,
    "n_embd": 512,
    "n_layer": 8,
    "n_head": 8,
    "mlp_factor": 4,
    "dropout": 0.0,
}


def gelu(x):
    return 0.5 * x * (1.0 + torch.erf(x / 1.4142135623730951))


class CausalSelfAttention(nn.Module):
    def __init__(self, cfg):
        super().__init__()
        self.n_head = cfg["n_head"]
        self.n_embd = cfg["n_embd"]
        self.c_attn = nn.Linear(cfg["n_embd"], 3 * cfg["n_embd"], bias=False)
        self.c_proj = nn.Linear(cfg["n_embd"], cfg["n_embd"], bias=False)
        self.drop = nn.Dropout(cfg["dropout"])

    def forward(self, x):
        B, T, C = x.shape
        q, k, v = self.c_attn(x).split(C, dim=2)
        nh = self.n_head
        hd = C // nh
        q = q.view(B, T, nh, hd).transpose(1, 2)
        k = k.view(B, T, nh, hd).transpose(1, 2)
        v = v.view(B, T, nh, hd).transpose(1, 2)
        att = (q @ k.transpose(-2, -1)) * (hd ** -0.5)
        att = att.masked_fill(
            torch.triu(torch.ones(T, T, device=x.device, dtype=torch.bool), diagonal=1),
            float("-inf"),
        )
        att = torch.softmax(att, dim=-1)
        att = self.drop(att)
        y = att @ v
        y = y.transpose(1, 2).contiguous().view(B, T, C)
        return self.drop(self.c_proj(y))


class MLP(nn.Module):
    def __init__(self, cfg):
        super().__init__()
        n = cfg["n_embd"]
        m = n * cfg["mlp_factor"]
        self.gate = nn.Linear(n, m, bias=False)
        self.up = nn.Linear(n, m, bias=False)
        self.down = nn.Linear(m, n, bias=False)

    def forward(self, x):
        g = gelu(self.gate(x))
        u = self.up(x)
        return self.down(g * u)


class Block(nn.Module):
    def __init__(self, cfg):
        super().__init__()
        self.ln1 = nn.LayerNorm(cfg["n_embd"])
        self.attn = CausalSelfAttention(cfg)
        self.ln2 = nn.LayerNorm(cfg["n_embd"])
        self.mlp = MLP(cfg)

    def forward(self, x):
        x = x + self.attn(self.ln1(x))
        x = x + self.mlp(self.ln2(x))
        return x


class GPT(nn.Module):
    def __init__(self, cfg):
        super().__init__()
        self.cfg = cfg
        self.tok_emb = nn.Embedding(cfg["vocab_size"], cfg["n_embd"])
        self.pos_emb = nn.Parameter(torch.zeros(1, cfg["block_size"], cfg["n_embd"]))
        self.drop = nn.Dropout(cfg["dropout"])
        self.blocks = nn.ModuleList([Block(cfg) for _ in range(cfg["n_layer"])])
        self.ln_f = nn.LayerNorm(cfg["n_embd"])
        self.lm_head = nn.Linear(cfg["n_embd"], cfg["vocab_size"], bias=False)
        self.lm_head.weight = self.tok_emb.weight  # tie
        self.apply(self._init_weights)

    def _init_weights(self, m):
        if isinstance(m, nn.Linear):
            nn.init.normal_(m.weight, mean=0.0, std=0.02)
        elif isinstance(m, nn.Embedding):
            nn.init.normal_(m.weight, mean=0.0, std=0.02)
        elif isinstance(m, nn.LayerNorm):
            nn.init.ones_(m.weight)
            nn.init.zeros_(m.bias)

    def forward(self, idx, targets=None):
        B, T = idx.shape
        x = self.tok_emb(idx) + self.pos_emb[:, :T, :]
        x = self.drop(x)
        for b in self.blocks:
            x = b(x)
        x = self.ln_f(x)
        logits = self.lm_head(x)
        loss = None
        if targets is not None:
            loss = nn.functional.cross_entropy(
                logits.view(-1, logits.size(-1)), targets.view(-1)
            )
        return logits, loss

    @torch.no_grad()
    def generate(self, idx, max_new_tokens, temperature=0.8, top_k=40):
        for _ in range(max_new_tokens):
            cond = idx if idx.size(1) <= self.cfg["block_size"] else idx[:, -self.cfg["block_size"]:]
            logits, _ = self(cond)
            logits = logits[:, -1, :] / max(temperature, 1e-4)
            if top_k and top_k > 0:
                v, _ = torch.topk(logits, min(top_k, logits.size(-1)))
                logits[logits < v[:, [-1]]] = float("-inf")
            probs = torch.softmax(logits, dim=-1)
            idx = torch.cat([idx, torch.multinomial(probs, num_samples=1)], dim=1)
        return idx

    # ── int8 export ──────────────────────────────────────────────
    def export_int8(self, out_dir: str):
        """Save quantized int8 weights + config + norms for the NumPy engine."""
        from models.lm.export import quantize_rows, save_weights

        os.makedirs(out_dir, exist_ok=True)
        with open(os.path.join(out_dir, "config.json"), "w") as f:
            json.dump(self.cfg, f)

        payload = {}
        for name, param in self.state_dict().items():
            if param.ndim <= 1 or "bias" in name or "ln" in name and "weight" in name:
                payload[name] = {"shape": param.shape, "vals": param.detach().numpy().astype(np.float32)}
            else:
                payload[name] = quantize_rows(param.detach().numpy())
        save_weights(os.path.join(out_dir, "weights.npz"), payload)
        return out_dir
