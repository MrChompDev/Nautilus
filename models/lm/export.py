"""Shared int8 weight export helpers for Nautilus models."""

import numpy as np


def quantize_rows(w: np.ndarray) -> dict:
    """Per-row int8 quantization of a weight matrix."""
    w = w.astype(np.float32)
    flat = w.reshape(w.shape[0], -1)
    mins = flat.min(axis=1, keepdims=True)
    maxs = flat.max(axis=1, keepdims=True)
    scale = (maxs - mins) / 255.0
    scale = np.where(scale == 0, 1e-8, scale)
    q = np.round((flat - mins) / scale).astype(np.uint8)
    return {"shape": w.shape, "q": q, "mins": mins.astype(np.float32), "scale": scale.astype(np.float32)}


def entry_to_struct(entry: dict) -> np.ndarray:
    """Convert an export entry to a single-row structured array."""
    shape = tuple(entry["shape"])
    if "q" in entry:
        qshape = entry["q"].shape
        dtype = [
            ("shape", "i8", (len(shape),)),
            ("q", "u1", qshape),
            ("mins", "f4", (qshape[0], 1)),
            ("scale", "f4", (qshape[0], 1)),
        ]
    else:
        dtype = [("shape", "i8", (len(shape),)), ("vals", "f4", entry["vals"].shape)]
    arr = np.zeros(1, dtype=dtype)
    arr["shape"][0] = np.asarray(shape, dtype=np.int64)
    if "q" in entry:
        arr["q"][0] = entry["q"]
        arr["mins"][0] = entry["mins"]
        arr["scale"][0] = entry["scale"]
    else:
        arr["vals"][0] = entry["vals"]
    return arr


def save_weights(path: str, payload: dict[str, dict]):
    structs = {name: entry_to_struct(entry) for name, entry in payload.items()}
    np.savez_compressed(path, **structs)


def load_struct(v: np.ndarray) -> np.ndarray:
    """Dequantize a stored structured array back to float32."""
    shape = tuple(v["shape"][0])
    if "q" in v.dtype.names:
        flat = v["q"].astype(np.float32) * v["scale"] + v["mins"]
        return flat.reshape(shape)
    return v["vals"].reshape(shape)
