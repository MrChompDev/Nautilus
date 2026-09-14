"""Kraken — multi-model AI CLI (coding, writing, pentest, imggen, + remote providers)."""

from models.kraken.config import Auth, Config
from models.kraken.providers import (
    ChatMsg,
    ChatResult,
    ModelRef,
    ToolCall,
    bootstrap,
    get_provider,
    model_catalog,
    provider_ids,
    resolve_model,
)
from models.kraken.router import available_models, route
from models.kraken.session import Session

__all__ = [
    "Auth", "Config", "ChatMsg", "ChatResult", "ModelRef", "ToolCall",
    "bootstrap", "get_provider", "model_catalog", "provider_ids", "resolve_model",
    "available_models", "route", "Session",
]
__version__ = "2.0.0"