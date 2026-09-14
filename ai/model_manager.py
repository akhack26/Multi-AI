"""
ai/model_manager.py

Knows what models *should* exist (from config/models.json) and checks what
actually exists inside the portable models/ folder. Never assumes a model
is present - every agent role degrades gracefully with a clear message if
its GGUF file is missing, instead of crashing.
"""

import os
from dataclasses import dataclass
from typing import Dict, Optional

from core.paths import MODELS_DIR
from core.config import load_model_registry
from core.logger import get_logger

log = get_logger("model_manager")


@dataclass
class ModelInfo:
    role: str
    file: str
    display_name: str
    approx_size_gb: float
    context_length: int
    download_hint: str
    min_ram_gb: float
    path: str
    present: bool


class ModelManager:
    """
    Loads config/models.json, checks disk, and reports readiness per role.
    Only one model is kept "active"/loaded in the backend at a time by
    default, since a 64GB USB / a typical host PC's RAM cannot comfortably
    hold several multi-billion-parameter models simultaneously. See
    ai/orchestrator.py for the load/unload (swap) logic that uses this.
    """

    def __init__(self):
        self.registry = load_model_registry()
        self.models: Dict[str, ModelInfo] = {}
        self.refresh()

    def refresh(self) -> None:
        """Re-scan the models/ directory. Call after the user drops in a new file."""
        self.models = {}
        for role, spec in self.registry.get("roles", {}).items():
            filename = spec["file"]
            full_path = os.path.join(MODELS_DIR, filename)
            present = os.path.isfile(full_path)
            self.models[role] = ModelInfo(
                role=role,
                file=filename,
                display_name=spec.get("display_name", filename),
                approx_size_gb=spec.get("approx_size_gb", 0.0),
                context_length=spec.get("context_length", 4096),
                download_hint=spec.get("download_hint", ""),
                min_ram_gb=spec.get("min_ram_gb", 0.0),
                path=full_path,
                present=present,
            )
        missing = [m.role for m in self.models.values() if not m.present]
        if missing:
            log.warning("Missing model files for roles: %s (see models/README.md)", missing)

    def get(self, role: str) -> Optional[ModelInfo]:
        return self.models.get(role)

    def is_ready(self, role: str) -> bool:
        info = self.get(role)
        return bool(info and info.present)

    def missing_report(self) -> str:
        """Human-readable summary of what's missing and where to put it."""
        lines = []
        for role, info in self.models.items():
            if info.present:
                continue
            lines.append(
                f"- [{role}] missing '{info.file}'\n"
                f"    Place it in: models/{info.file}\n"
                f"    Suggested model: {info.display_name} (~{info.approx_size_gb} GB)\n"
                f"    Where to get it: {info.download_hint}"
            )
        if not lines:
            return "All configured models are present."
        return "The following models are not yet installed:\n" + "\n".join(lines)

    def status_table(self) -> str:
        rows = ["ROLE       STATUS      SIZE(GB)  FILE"]
        for role, info in self.models.items():
            status = "READY" if info.present else "MISSING"
            rows.append(f"{role:<10} {status:<11} {info.approx_size_gb:<9} {info.file}")
        return "\n".join(rows)
