"""Nautilus LM — inference engine (pure NumPy, no torch at runtime).

Loads an int8-exported model + BPE tokenizer and generates text.
Weights are dequantized to float32 once on load for speed.
"""

import json
import math
import os
import time

import numpy as np

_ERF = np.frompyfunc(math.erf, 1, 1)


def gelu(x):
    return 0.5 * x * (1.0 + _ERF(x / np.sqrt(2.0)).astype(np.float32))


class Model:
    """Minimal GPT forward pass over float32 numpy weights."""

    def __init__(self, weights: dict, cfg: dict):
        self.cfg = cfg
        self.w = weights
        self.n_head = cfg["n_head"]
        self.n_embd = cfg["n_embd"]
        self.block_size = cfg["block_size"]
        self._mask = None

    # ── weight loading helpers ────────────────────────────────────
    @staticmethod
    def load(model_dir: str) -> "Model":
        from models.lm.export import load_struct

        with open(os.path.join(model_dir, "config.json")) as f:
            cfg = json.load(f)
        arr = np.load(os.path.join(model_dir, "weights.npz"))
        weights = {}
        for key in arr.files:
            v = arr[key]
            if v.dtype.names:
                weights[key] = load_struct(v)
            else:
                weights[key] = v
        return Model(weights, cfg)

    def causal_mask(self, T):
        if self._mask is None or self._mask.shape[0] < T:
            m = np.tril(np.ones((self.block_size, self.block_size), dtype=np.float32))
            self._mask = m
        return self._mask[:T, :T]

    # ── forward ───────────────────────────────────────────────────
    def forward(self, idx: np.ndarray) -> np.ndarray:
        cfg = self.cfg
        w = self.w
        T = idx.shape[0]
        x = w["tok_emb.weight"][idx] + w["pos_emb"][0, :T]
        mask = self.causal_mask(T)
        for i in range(cfg["n_layer"]):
            ln1w = w[f"blocks.{i}.ln1.weight"]
            ln1b = w[f"blocks.{i}.ln1.bias"]
            h = self._layernorm(x, ln1w, ln1b)
            qkv = h @ w[f"blocks.{i}.attn.c_attn.weight"].T
            C = cfg["n_embd"]
            q, k, v = qkv[:, :C], qkv[:, C : 2 * C], qkv[:, 2 * C :]
            nh, hd = cfg["n_head"], C // cfg["n_head"]
            q = q.reshape(T, nh, hd).transpose(1, 0, 2)
            k = k.reshape(T, nh, hd).transpose(1, 0, 2)
            v = v.reshape(T, nh, hd).transpose(1, 0, 2)
            att = q @ k.transpose(0, 2, 1) / np.sqrt(hd)
            att = att - (1.0 - mask[None]) * 1e9
            att = self._softmax(att)
            y = att @ v
            y = y.transpose(1, 0, 2).reshape(T, C)
            x = x + y @ w[f"blocks.{i}.attn.c_proj.weight"].T
            ln2w = w[f"blocks.{i}.ln2.weight"]
            ln2b = w[f"blocks.{i}.ln2.bias"]
            h = self._layernorm(x, ln2w, ln2b)
            gate = gelu(h @ w[f"blocks.{i}.mlp.gate.weight"].T)
            up = h @ w[f"blocks.{i}.mlp.up.weight"].T
            x = x + (gate * up) @ w[f"blocks.{i}.mlp.down.weight"].T
        x = self._layernorm(x, w["ln_f.weight"], w["ln_f.bias"])
        return x @ w["lm_head.weight"].T

    @staticmethod
    def _layernorm(x, weight, bias):
        mu = x.mean(axis=-1, keepdims=True)
        var = x.var(axis=-1, keepdims=True)
        return (x - mu) / np.sqrt(var + 1e-5) * weight + bias

    @staticmethod
    def _softmax(x):
        e = np.exp(x - x.max(axis=-1, keepdims=True))
        return e / e.sum(axis=-1, keepdims=True)

    # ── sampling ──────────────────────────────────────────────────
    def generate(
        self,
        tokens,
        max_new_tokens=120,
        temperature=0.7,
        top_k=40,
        top_p=0.9,
        stop=None,
        stream=None,
    ) -> str:
        idx = list(tokens)
        bs = self.block_size
        out_ids = []
        stop = stop or []
        for _ in range(max_new_tokens):
            ctx = np.asarray(idx[-bs:], dtype=np.int64)
            logits = self.forward(ctx)[-1]
            logits = logits / max(temperature, 1e-4)
            if top_k and top_k > 0:
                k = min(top_k, logits.size)
                thresh = np.partition(logits, -k)[-k]
                logits[logits < thresh] = -1e9
            probs = self._softmax(logits)
            if top_p and top_p < 1.0:
                order = np.argsort(-probs)
                cum = np.cumsum(probs[order])
                keep = order[cum <= top_p]
                probs[~np.isin(np.arange(probs.size), keep)] = 0.0
                probs /= probs.sum()
            tok = int(np.random.choice(probs.size, p=probs))
            idx.append(tok)
            out_ids.append(tok)
            if stream:
                stream(tok)
            if tok in stop:
                break
        return out_ids


class LM:
    """Tokenizer + model + helpers bound together."""

    def __init__(self, model_dir: str):
        from models.lm.bpe import BPETokenizer

        self.tok = BPETokenizer().load(os.path.join(model_dir, "bpe.json"))
        self.model = Model.load(model_dir)
        with open(os.path.join(model_dir, "model.json")) as f:
            self.meta = json.load(f)

    @property
    def model_id(self) -> str:
        return self.meta.get("id", "?")

    def count_tokens(self, text: str) -> int:
        return len(self.tok.encode(text))

    def encode(self, text: str):
        return self.tok.encode(text)

    def decode(self, ids) -> str:
        return self.tok.decode(ids)

    def respond(self, prompt: str, max_new_tokens=160, temperature=0.7, top_k=40, stream=None) -> str:
        stop_ids = [self.tok.encode("\n\n>>>")[0], self.tok.encode("\n<|end|>")[0]] if False else []
        start = time.time()
        out_ids = self.model.generate(
            self.tok.encode(prompt),
            max_new_tokens=max_new_tokens,
            temperature=temperature,
            top_k=top_k,
            stop=stop_ids,
            stream=stream,
        )
        dt = time.time() - start
        text = self.tok.decode(out_ids)
        tok_rate = len(out_ids) / dt if dt > 0 else 0.0
        return {"text": text, "tokens": len(out_ids), "seconds": round(dt, 2), "tok_s": round(tok_rate, 1)}

    def complete(self, prompt: str, max_new_tokens=200, **kw) -> str:
        return self.respond(prompt, max_new_tokens=max_new_tokens, **kw)["text"]
