"""
ai/orchestrator.py

The AI Orchestrator sits between the agents/router and the backend layer.
Responsibilities:
  - Pick an available backend (llama_cpp, then ollama, per config fallback order)
  - Ask the ModelManager which GGUF file a given agent role needs
  - Load/unload ("swap") models on demand so we never require every model
    to be resident in RAM at once - crucial on a 64GB USB / modest host PC.
  - Provide a single generate_for_role() call agents use, independent of
    whatever backend happens to be active.
"""

from typing import Dict, List, Optional

from ai.model_manager import ModelManager
from backends.base import BackendBase, BackendError
from backends.llama_cpp_backend import LlamaCppBackend
from backends.ollama_backend import OllamaBackend
from core.config import Config
from core.logger import get_logger

log = get_logger("orchestrator")

_BACKEND_REGISTRY = {
    "llama_cpp": LlamaCppBackend,
    "ollama": OllamaBackend,
}


class OrchestratorError(Exception):
    pass


class Orchestrator:
    def __init__(self, config: Config):
        self.config = config
        self.model_manager = ModelManager()
        self.backend: Optional[BackendBase] = None
        self._active_role: Optional[str] = None
        self._select_backend()

    # ------------------------------------------------------------------ #
    # Backend selection
    # ------------------------------------------------------------------ #
    def _select_backend(self) -> None:
        preferred = self.config.get("backend.preferred", "llama_cpp")
        fallback_order = self.config.get("backend.fallback_order", [preferred])
        candidates = [preferred] + [b for b in fallback_order if b != preferred]

        for name in candidates:
            cls = _BACKEND_REGISTRY.get(name)
            if cls is None:
                continue
            instance = self._instantiate_backend(name, cls)
            if instance and instance.is_available():
                self.backend = instance
                log.info("Using backend: %s", name)
                return

        log.warning(
            "No inference backend is currently available. "
            "Install llama-cpp-python (see requirements/) or run a local Ollama server."
        )
        self.backend = None

    def _instantiate_backend(self, name: str, cls) -> Optional[BackendBase]:
        if name == "llama_cpp":
            cfg = self.config.get("backend.llama_cpp", {}) or {}
            return LlamaCppBackend(
                n_ctx=cfg.get("n_ctx", 4096),
                n_threads=cfg.get("n_threads"),
                n_gpu_layers=cfg.get("n_gpu_layers", 0),
            )
        if name == "ollama":
            cfg = self.config.get("backend.ollama", {}) or {}
            if not cfg.get("enabled", False):
                return None
            return OllamaBackend(host=cfg.get("host", "http://localhost:11434"))
        return None

    def backend_status(self) -> str:
        if self.backend is None:
            return "No backend available (see README troubleshooting)."
        return f"Backend: {self.backend.name} | model loaded: {self.backend.is_model_loaded()}"

    # ------------------------------------------------------------------ #
    # Model swapping
    # ------------------------------------------------------------------ #
    def ensure_role_loaded(self, role: str) -> None:
        """Load the model required for `role`, unloading any other active model first."""
        if self.backend is None:
            raise OrchestratorError(
                "No inference backend available. Install llama-cpp-python or enable Ollama."
            )

        if self._active_role == role and self.backend.is_model_loaded():
            return  # already the active model, no swap needed

        info = self.model_manager.get(role)
        if info is None:
            raise OrchestratorError(f"Unknown agent role '{role}' (not in config/models.json).")
        if not info.present:
            raise OrchestratorError(
                f"Model for role '{role}' is not installed.\n"
                f"Missing file: models/{info.file}\n"
                f"Suggested: {info.display_name} (~{info.approx_size_gb} GB)\n"
                f"Get it from: {info.download_hint}"
            )

        log.info("Swapping active model -> role '%s' (%s)", role, info.file)
        self.backend.load_model(info.path, n_ctx=info.context_length)
        self._active_role = role

    # ------------------------------------------------------------------ #
    # Generation
    # ------------------------------------------------------------------ #
    def generate_for_role(
        self,
        role: str,
        messages: List[Dict[str, str]],
        max_tokens: int = 512,
        temperature: float = 0.7,
    ) -> str:
        self.ensure_role_loaded(role)
        try:
            chunks = list(
                self.backend.chat(
                    messages, max_tokens=max_tokens, temperature=temperature, stream=False
                )
            )
        except BackendError as e:
            raise OrchestratorError(str(e)) from e
        return "".join(chunks).strip()

    def shutdown(self) -> None:
        if self.backend is not None:
            self.backend.unload_model()
