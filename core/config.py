"""
core/config.py

Loads config/config.json (portable app settings). If the user has not yet
copied config.example.json to config.json, we transparently fall back to
the example so ISHA still runs out of the box on a fresh USB copy.
"""

import json
import os
import shutil
from typing import Any, Dict

from core.paths import CONFIG_DIR
from core.logger import get_logger

log = get_logger("config")

_CONFIG_PATH = os.path.join(CONFIG_DIR, "config.json")
_EXAMPLE_PATH = os.path.join(CONFIG_DIR, "config.example.json")
_MODELS_REGISTRY_PATH = os.path.join(CONFIG_DIR, "models.json")


def _deep_get(d: dict, dotted_key: str, default=None):
    node = d
    for part in dotted_key.split("."):
        if not isinstance(node, dict) or part not in node:
            return default
        node = node[part]
    return node


class Config:
    """Thin wrapper around the loaded JSON config with dotted-key access."""

    def __init__(self, data: Dict[str, Any], source_path: str):
        self._data = data
        self.source_path = source_path

    def get(self, dotted_key: str, default=None):
        return _deep_get(self._data, dotted_key, default)

    def as_dict(self) -> Dict[str, Any]:
        return self._data

    def __repr__(self):
        return f"<Config loaded_from={self.source_path!r}>"


def load_config() -> Config:
    if not os.path.exists(_CONFIG_PATH):
        if os.path.exists(_EXAMPLE_PATH):
            try:
                shutil.copyfile(_EXAMPLE_PATH, _CONFIG_PATH)
                log.info("No config.json found - created one from config.example.json")
            except OSError:
                log.warning(
                    "Could not write config.json (read-only drive?). "
                    "Running directly from config.example.json instead."
                )
                with open(_EXAMPLE_PATH, "r", encoding="utf-8") as f:
                    return Config(json.load(f), _EXAMPLE_PATH)
        else:
            raise FileNotFoundError(
                "Neither config/config.json nor config/config.example.json exist. "
                "The project appears to be corrupted/incomplete."
            )

    with open(_CONFIG_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    return Config(data, _CONFIG_PATH)


def load_model_registry() -> Dict[str, Any]:
    """Load config/models.json describing which GGUF file each agent role needs."""
    with open(_MODELS_REGISTRY_PATH, "r", encoding="utf-8") as f:
        return json.load(f)
