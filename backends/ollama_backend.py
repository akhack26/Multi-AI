"""
backends/ollama_backend.py

Optional backend for hosts that already have Ollama installed and running
(http://localhost:11434). Useful as a fallback/alternative to llama.cpp -
same abstract interface, so the orchestrator doesn't care which is active.

Note: Ollama manages its own model store (usually outside the portable
project), so this backend is inherently less "pure-USB-portable" than the
llama_cpp backend, which loads GGUF files directly from models/. It's kept
purely optional for users who prefer it on a given host PC.
"""

import json
from typing import Dict, Generator, List, Optional

from backends.base import BackendBase, BackendError
from core.logger import get_logger

log = get_logger("backend.ollama")

DEFAULT_HOST = "http://localhost:11434"


class OllamaBackend(BackendBase):
    name = "ollama"

    def __init__(self, host: str = DEFAULT_HOST):
        self.host = host.rstrip("/")
        self._model_name: Optional[str] = None

    def is_available(self) -> bool:
        try:
            import requests
        except ImportError:
            return False
        try:
            resp = requests.get(f"{self.host}/api/tags", timeout=1.5)
            return resp.status_code == 200
        except Exception:
            return False

    def load_model(self, model_path: str, **kwargs) -> None:
        """
        For Ollama, 'model_path' is actually the Ollama model *tag*
        (e.g. 'llama3.2:3b'), not a GGUF file path - Ollama manages its own
        model storage. We just verify it's available server-side.
        """
        import requests

        try:
            resp = requests.get(f"{self.host}/api/tags", timeout=5)
            resp.raise_for_status()
            tags = [m["name"] for m in resp.json().get("models", [])]
        except Exception as e:
            raise BackendError(f"Could not reach Ollama server at {self.host}: {e}") from e

        if model_path not in tags:
            raise BackendError(
                f"Ollama model '{model_path}' not found on server. "
                f"Available: {tags}. Run `ollama pull {model_path}` on the host first."
            )
        self._model_name = model_path

    def unload_model(self) -> None:
        self._model_name = None

    def is_model_loaded(self) -> bool:
        return self._model_name is not None

    def chat(
        self,
        messages: List[Dict[str, str]],
        max_tokens: int = 512,
        temperature: float = 0.7,
        stream: bool = False,
    ) -> Generator[str, None, None]:
        import requests

        if not self._model_name:
            raise BackendError("No Ollama model selected. Call load_model() first.")

        payload = {
            "model": self._model_name,
            "messages": messages,
            "stream": stream,
            "options": {"temperature": temperature, "num_predict": max_tokens},
        }

        try:
            resp = requests.post(
                f"{self.host}/api/chat", json=payload, timeout=120, stream=stream
            )
            resp.raise_for_status()
        except Exception as e:
            raise BackendError(f"Ollama request failed: {e}") from e

        if stream:
            for line in resp.iter_lines():
                if not line:
                    continue
                data = json.loads(line)
                content = data.get("message", {}).get("content")
                if content:
                    yield content
        else:
            data = resp.json()
            yield data.get("message", {}).get("content", "")
