"""
backends/llama_cpp_backend.py

Primary offline-first backend, built on the `llama-cpp-python` package
(Python bindings for llama.cpp). This is what actually runs GGUF models
fully locally with no network access required.

The import of llama_cpp is deliberately lazy (done inside __init__/load_model)
so that the rest of ISHA can start up, show status, and explain what's
missing even on a machine where llama-cpp-python isn't installed yet.
"""

import os
import multiprocessing
from typing import Dict, Generator, List, Optional

from backends.base import BackendBase, BackendError
from core.logger import get_logger

log = get_logger("backend.llama_cpp")


class LlamaCppBackend(BackendBase):
    name = "llama_cpp"

    def __init__(self, n_ctx: int = 4096, n_threads: Optional[int] = None, n_gpu_layers: int = 0):
        self.n_ctx = n_ctx
        self.n_threads = n_threads or max(1, multiprocessing.cpu_count() - 1)
        self.n_gpu_layers = n_gpu_layers
        self._llm = None
        self._loaded_path: Optional[str] = None

    def is_available(self) -> bool:
        try:
            import llama_cpp  # noqa: F401
            return True
        except ImportError:
            return False

    def load_model(self, model_path: str, **kwargs) -> None:
        if not os.path.isfile(model_path):
            raise BackendError(f"Model file not found on disk: {model_path}")

        try:
            from llama_cpp import Llama
        except ImportError as e:
            raise BackendError(
                "llama-cpp-python is not installed. Run: "
                "pip install -r requirements/requirements.txt "
                "(see README.md troubleshooting section for platform-specific wheels)."
            ) from e

        if self._loaded_path == model_path and self._llm is not None:
            return  # already loaded, nothing to do

        self.unload_model()

        n_ctx = kwargs.get("n_ctx", self.n_ctx)
        n_threads = kwargs.get("n_threads", self.n_threads)
        n_gpu_layers = kwargs.get("n_gpu_layers", self.n_gpu_layers)

        log.info(
            "Loading model '%s' (n_ctx=%s, n_threads=%s, n_gpu_layers=%s)",
            os.path.basename(model_path), n_ctx, n_threads, n_gpu_layers,
        )
        try:
            self._llm = Llama(
                model_path=model_path,
                n_ctx=n_ctx,
                n_threads=n_threads,
                n_gpu_layers=n_gpu_layers,
                verbose=False,
            )
        except Exception as e:  # llama_cpp raises plain Exception/OSError on load failure
            self._llm = None
            self._loaded_path = None
            raise BackendError(f"Failed to load model '{model_path}': {e}") from e

        self._loaded_path = model_path

    def unload_model(self) -> None:
        if self._llm is not None:
            log.info("Unloading model '%s'", os.path.basename(self._loaded_path or ""))
            del self._llm
            self._llm = None
            self._loaded_path = None

    def is_model_loaded(self) -> bool:
        return self._llm is not None

    def chat(
        self,
        messages: List[Dict[str, str]],
        max_tokens: int = 512,
        temperature: float = 0.7,
        stream: bool = False,
    ) -> Generator[str, None, None]:
        if self._llm is None:
            raise BackendError("No model is currently loaded in the llama_cpp backend.")

        try:
            if stream:
                for chunk in self._llm.create_chat_completion(
                    messages=messages,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    stream=True,
                ):
                    delta = chunk["choices"][0]["delta"].get("content")
                    if delta:
                        yield delta
            else:
                result = self._llm.create_chat_completion(
                    messages=messages,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    stream=False,
                )
                yield result["choices"][0]["message"]["content"]
        except Exception as e:
            raise BackendError(f"Generation failed: {e}") from e
