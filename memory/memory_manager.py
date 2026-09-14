"""
memory/memory_manager.py

Two-tier memory:
  - Short-term: the last N turns per session, kept in RAM, fed into every
    prompt as conversation context.
  - Long-term: every turn is also appended to a per-session JSON file under
    data/memory/, so history survives restarts. A simple keyword search
    (`search_long_term`) lets agents optionally recall older context without
    needing a vector database - deliberately kept dependency-free and fully
    offline. This can be swapped for an embedding-based store later without
    changing the public interface.
"""

import json
import os
import time
from collections import deque
from typing import Deque, Dict, List

from core.paths import MEMORY_DIR
from core.logger import get_logger

log = get_logger("memory")


class MemoryManager:
    def __init__(self, short_term_turns: int = 12, persist_long_term: bool = True,
                 max_long_term_entries: int = 2000):
        self.short_term_turns = short_term_turns
        self.persist_long_term = persist_long_term
        self.max_long_term_entries = max_long_term_entries
        self._short_term: Dict[str, Deque[dict]] = {}

    # ------------------------------------------------------------------ #
    # Short-term (in-RAM sliding window)
    # ------------------------------------------------------------------ #
    def get_short_term(self, session_id: str) -> List[dict]:
        return list(self._short_term.get(session_id, deque()))

    def add_turn(self, session_id: str, role: str, content: str) -> None:
        buf = self._short_term.setdefault(session_id, deque(maxlen=self.short_term_turns))
        turn = {"role": role, "content": content}
        buf.append(turn)
        if self.persist_long_term:
            self._append_long_term(session_id, role, content)

    def clear_short_term(self, session_id: str) -> None:
        self._short_term.pop(session_id, None)

    # ------------------------------------------------------------------ #
    # Long-term (persisted JSON, append-only with soft cap)
    # ------------------------------------------------------------------ #
    def _long_term_path(self, session_id: str) -> str:
        safe_id = "".join(c for c in session_id if c.isalnum() or c in ("-", "_")) or "default"
        return os.path.join(MEMORY_DIR, f"{safe_id}.json")

    def _append_long_term(self, session_id: str, role: str, content: str) -> None:
        path = self._long_term_path(session_id)
        entries = self._load_long_term_raw(path)
        entries.append({"role": role, "content": content, "ts": time.time()})
        if len(entries) > self.max_long_term_entries:
            entries = entries[-self.max_long_term_entries:]
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(entries, f, ensure_ascii=False, indent=2)
        except OSError:
            log.warning("Could not persist memory to %s (drive read-only or full?)", path)

    def _load_long_term_raw(self, path: str) -> List[dict]:
        if not os.path.isfile(path):
            return []
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except (OSError, json.JSONDecodeError):
            return []

    def load_long_term(self, session_id: str) -> List[dict]:
        return self._load_long_term_raw(self._long_term_path(session_id))

    def search_long_term(self, session_id: str, query: str, limit: int = 5) -> List[dict]:
        query_lower = query.lower()
        matches = [
            e for e in self._load_long_term_raw(self._long_term_path(session_id))
            if query_lower in e.get("content", "").lower()
        ]
        return matches[-limit:]
