"""Nautilus LM — byte-level BPE tokenizer (pure Python + NumPy).

Training: basic incremental merge over a representative sample.
Encoding: vectorized NumPy per-round merge (O(n*depth), fast on big corpora).
Deterministic, so a model always maps to the same vocab.
"""

import json
import os

import numpy as np

_SHIFT = 16


def _pair_key(a, b):
    return (int(a) << _SHIFT) | int(b)


def _pair_from_key(k):
    return (k >> _SHIFT, k & ((1 << _SHIFT) - 1))


def _stats(ids: np.ndarray) -> dict:
    """Counts of consecutive pairs, keyed by _pair_key."""
    if ids.size < 2:
        return {}
    keys = (ids[:-1] << _SHIFT) | ids[1:]
    unique, counts = np.unique(keys, return_counts=True)
    return dict(zip(unique.tolist(), counts.tolist(), strict=True))


def _merge_vec(ids: np.ndarray, pair: tuple, idx: int) -> np.ndarray:
    """Left-to-right non-overlapping merge of `pair` -> `idx`, vectorized."""
    p0, p1 = pair
    n = ids.size
    match = (ids[:-1] == p0) & (ids[1:] == p1)
    m8 = match.astype(np.int8)
    diff = np.diff(np.concatenate([[0], m8, [0]]))
    starts = np.nonzero(diff == 1)[0]
    ends = np.nonzero(diff == -1)[0]
    valid = np.zeros(match.size, bool)
    for s, e in zip(starts, ends, strict=True):
        valid[s:e:2] = True
    if not valid.any():
        return ids
    valid_set = np.zeros(n, bool)
    valid_set[np.nonzero(valid)[0]] = True
    del_pos = np.nonzero(valid)[0] + 1
    kept = np.ones(n, bool)
    kept[del_pos] = False
    kept_idx = np.nonzero(kept)[0]
    out = ids[kept_idx].copy()
    out[valid_set[kept_idx]] = idx
    return out


class BPETokenizer:
    """Byte-level BPE with a 256-byte base + learned merges."""

    def __init__(self):
        self.merges: dict[tuple, int] = {}
        self.vocab: dict[int, bytes] = {}

    @property
    def vocab_size(self) -> int:
        return 256 + len(self.merges)

    # ── training ─────────────────────────────────────────────────
    def train(self, text: str, vocab_size: int = 4096):
        num_merges = vocab_size - 256
        ids = np.frombuffer(text.encode("utf-8"), dtype=np.uint8).astype(np.int64)
        self.merges = {}
        self.vocab = {i: bytes([i]) for i in range(256)}
        for _ in range(num_merges):
            stats = _stats(ids)
            if not stats:
                break
            key = max(stats, key=stats.get)
            pair = _pair_from_key(key)
            idx = 256 + len(self.merges)
            ids = _merge_vec(ids, pair, idx)
            self.merges[pair] = idx
            self.vocab[idx] = self.vocab[pair[0]] + self.vocab[pair[1]]
        return self

    # ── encode / decode ──────────────────────────────────────────
    def encode(self, text: str) -> list[int]:
        if not self.merges:
            return list(text.encode("utf-8"))
        ids = np.frombuffer(text.encode("utf-8"), dtype=np.uint8).astype(np.int64)
        rank_map = {_pair_key(*k): v for k, v in self.merges.items()}
        while ids.size >= 2:
            stats = _stats(ids)
            if not stats:
                break
            best_key = None
            best_rank = 1 << 30
            for key in stats:
                rank = rank_map.get(key)
                if rank is not None and rank < best_rank:
                    best_rank = rank
                    best_key = key
            if best_key is None:
                break
            ids = _merge_vec(ids, _pair_from_key(best_key), rank_map[best_key])
        return ids.tolist()

    def decode(self, ids: list[int]) -> str:
        return b"".join(self.vocab.get(i, b"") for i in ids).decode("utf-8", errors="replace")

    # ── persistence ──────────────────────────────────────────────
    def save(self, path: str):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        payload = {
            "merges": [[int(a), int(b), int(idx)] for (a, b), idx in self.merges.items()],
        }
        with open(path, "w", encoding="utf-8") as f:
            json.dump(payload, f)

    def load(self, path: str):
        with open(path, encoding="utf-8") as f:
            payload = json.load(f)
        self.merges = {}
        self.vocab = {i: bytes([i]) for i in range(256)}
        for a, b, idx in payload["merges"]:
            pair = (a, b)
            self.merges[pair] = idx
            self.vocab[idx] = self.vocab[a] + self.vocab[b]
        return self
