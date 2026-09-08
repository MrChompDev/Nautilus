"""Custom-encrypted password vault for Surfline.

Pure-Python implementation (stdlib only) — no third-party crypto.
Uses PBKDF2-HMAC-SHA256 for key derivation and a CTR-mode stream
cipher with HMAC-SHA256 as the PRF to build the keystream.
"""

import hashlib
import hmac
import json
import os
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent.parent
VAULT_PATH = _ROOT / "data" / "vault.bin"
SALT_PATH = _ROOT / "data" / "vault.salt"

ITERATIONS = 100_000
_KEY_LEN = 32
_BLOCK_SIZE = 32   # SHA256 output size


def _derive_key(passphrase: str, salt: bytes) -> bytes:
    return hashlib.pbkdf2_hmac("sha256", passphrase.encode(), salt, ITERATIONS, dklen=_KEY_LEN)


def _keystream(key: bytes, length: int) -> bytes:
    """Generate a CTR-mode keystream of the given length using HMAC-SHA256."""
    out = b""
    counter = 0
    while len(out) < length:
        block = hmac.new(key, counter.to_bytes(8, "big"), hashlib.sha256).digest()
        out += block
        counter += 1
    return out[:length]


def _encrypt(key: bytes, plaintext: bytes) -> bytes:
    iv = os.urandom(8)
    keystream = _keystream(key + iv, len(plaintext))
    ciphertext = bytes(a ^ b for a, b in zip(plaintext, keystream))
    tag = hmac.new(key, iv + ciphertext, hashlib.sha256).digest()
    return iv + tag + ciphertext


def _decrypt(key: bytes, blob: bytes) -> bytes:
    iv = blob[:8]
    tag = blob[8:40]
    ciphertext = blob[40:]
    expected = hmac.new(key, iv + ciphertext, hashlib.sha256).digest()
    if not hmac.compare_digest(tag, expected):
        raise ValueError("Invalid passphrase or corrupted vault")
    keystream = _keystream(key + iv, len(ciphertext))
    return bytes(a ^ b for a, b in zip(ciphertext, keystream))


def vault_exists() -> bool:
    return VAULT_PATH.exists()


def create_vault(passphrase: str) -> None:
    VAULT_PATH.parent.mkdir(parents=True, exist_ok=True)
    salt = os.urandom(16)
    SALT_PATH.write_bytes(salt)
    key = _derive_key(passphrase, salt)
    store = {"version": 1, "entries": []}
    blob = _encrypt(key, json.dumps(store).encode())
    VAULT_PATH.write_bytes(blob)


def _load_store(passphrase: str) -> dict:
    if not vault_exists():
        raise ValueError("Vault not created yet")
    salt = SALT_PATH.read_bytes()
    key = _derive_key(passphrase, salt)
    blob = VAULT_PATH.read_bytes()
    return json.loads(_decrypt(key, blob))


def verify_passphrase(passphrase: str) -> bool:
    try:
        _load_store(passphrase)
        return True
    except Exception:
        return False


def _save_store(passphrase: str, store: dict) -> None:
    salt = SALT_PATH.read_bytes()
    key = _derive_key(passphrase, salt)
    VAULT_PATH.write_bytes(_encrypt(key, json.dumps(store).encode()))


def add_entry(passphrase: str, site: str, username: str, password: str) -> None:
    store = _load_store(passphrase)
    store["entries"].append({"site": site, "username": username, "password": password})
    _save_store(passphrase, store)


def list_entries(passphrase: str) -> list[dict]:
    return _load_store(passphrase)["entries"]


def update_entry(passphrase: str, index: int, site: str, username: str, password: str) -> None:
    store = _load_store(passphrase)
    if 0 <= index < len(store["entries"]):
        store["entries"][index] = {"site": site, "username": username, "password": password}
        _save_store(passphrase, store)


def delete_entry(passphrase: str, index: int) -> None:
    store = _load_store(passphrase)
    if 0 <= index < len(store["entries"]):
        store["entries"].pop(index)
        _save_store(passphrase, store)


def find_entry(passphrase: str, site: str) -> dict | None:
    site = site.lower()
    for e in list_entries(passphrase):
        if e["site"].lower() in site or site in e["site"].lower():
            return e
    return None