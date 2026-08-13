"""
Kraken AI — API key store and discovery.

Keys are resolved with the following precedence (highest wins):

  1. `~/.kraken/keys.json`   — managed via `kraken keys add|remove`
  2. `~/.env`                — plain KEY=VALUE file in the user's home
  3. process environment     — e.g. OPENAI_API_KEY, ANTHROPIC_API_KEY

Every key lives in the user's own files (0600) and is never logged or sent
anywhere except to the provider endpoint the user configured.
"""

import json
import os

# Env var names (in priority order) that feed each cloud provider.
ENV_VARS = {
    "openai": ("OPENAI_API_KEY",),
    "anthropic": ("ANTHROPIC_API_KEY",),
    "gemini": ("GEMINI_API_KEY", "GOOGLE_API_KEY"),
    "groq": ("GROQ_API_KEY",),
    "openrouter": ("OPENROUTER_API_KEY",),
    "mistral": ("MISTRAL_API_KEY",),
    "deepseek": ("DEEPSEEK_API_KEY",),
    "together": ("TOGETHER_API_KEY",),
}

# Reverse map: env var name → provider (used for ~/.env parsing).
_ENV_TO_PROVIDER = {name: prov for prov, names in ENV_VARS.items() for name in names}


def keys_path(home_dir: str) -> str:
    return os.path.join(home_dir, "keys.json")


def _read_env_file(path: str) -> dict[str, str]:
    """Parse a simple KEY=VALUE .env file (no shell expansion)."""
    out: dict[str, str] = {}
    try:
        with open(path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, _, value = line.partition("=")
                out[key.strip()] = value.strip().strip('"').strip("'")
    except OSError:
        pass
    return out


def load_keys(home_dir: str, env: dict[str, str] | None = None,
              env_file: str | None = None) -> dict[str, str]:
    """Resolve the effective API key per provider for this machine.

    `env` overrides `os.environ` (test seam); `env_file` overrides the
    default `~/.env` location (test seam).
    """
    env = os.environ if env is None else env
    env_file = os.path.join(os.path.expanduser("~"), ".env") if env_file is None else env_file
    keys: dict[str, str] = {}

    for provider, names in ENV_VARS.items():
        for name in names:
            val = env.get(name)
            if val:
                keys[provider] = val
                break

    for name, val in _read_env_file(env_file).items():
        provider = _ENV_TO_PROVIDER.get(name.strip().upper())
        if provider and val:
            keys[provider] = val

    try:
        with open(keys_path(home_dir), encoding="utf-8") as f:
            stored = json.load(f)
        if isinstance(stored, dict):
            for prov, val in stored.items():
                if val:
                    keys[str(prov)] = str(val)
    except (OSError, ValueError, TypeError):
        pass
    return keys


def get_key(home_dir: str, provider: str) -> str | None:
    return load_keys(home_dir).get(provider)


def save_keys(home_dir: str, keys: dict[str, str]) -> str:
    """Write the key store (0600) and return the path."""
    os.makedirs(home_dir, exist_ok=True)
    path = keys_path(home_dir)
    cleaned = {k: v for k, v in keys.items() if k and v}
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(cleaned, f, indent=2, sort_keys=True)
    finally:
        pass
    try:
        os.chmod(path, 0o600)
    except OSError:
        pass
    return path


def mask_key(key: str) -> str:
    """Show only the first and last four characters of a secret."""
    if len(key) <= 8:
        return "*" * len(key)
    return f"{key[:4]}…{key[-4:]}"
