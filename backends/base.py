"""
backends/base.py

Abstract interface every inference backend must implement. This is the
contract that lets the rest of ISHA (orchestrator, agents) stay completely
ignorant of whether it's talking to llama.cpp, Ollama, or something else
added later - the backend can be swapped without touching any other module.
"""

from abc import ABC, abstractmethod
from typing import Dict, Generator, List, Optional


class BackendError(Exception):
    """Raised for any backend-level failure (load failure, generation error, etc.)."""


class BackendBase(ABC):
    name: str = "base"

    @abstractmethod
    def is_available(self) -> bool:
        """Return True if this backend's dependencies/runtime are usable at all."""
        raise NotImplementedError

    @abstractmethod
    def load_model(self, model_path: str, **kwargs) -> None:
        """Load/activate a specific model file. Raises BackendError on failure."""
        raise NotImplementedError

    @abstractmethod
    def unload_model(self) -> None:
        """Free the currently loaded model (important for the 'swap models' flow)."""
        raise NotImplementedError

    @abstractmethod
    def is_model_loaded(self) -> bool:
        raise NotImplementedError

    @abstractmethod
    def chat(
        self,
        messages: List[Dict[str, str]],
        max_tokens: int = 512,
        temperature: float = 0.7,
        stream: bool = False,
    ) -> Generator[str, None, None]:
        """
        messages: list of {"role": "system"|"user"|"assistant", "content": str}
        Yields text chunks. For non-streaming backends, yield exactly once
        with the full response.
        """
        raise NotImplementedError

    def generate(self, prompt: str, **kwargs) -> str:
        """Convenience non-chat single-prompt helper built on top of chat()."""
        chunks = list(self.chat([{"role": "user", "content": prompt}], **kwargs))
        return "".join(chunks)
