"""Tests for the memory manager (short-term window + long-term persistence)."""

import os
import sys
import unittest
import shutil

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from memory.memory_manager import MemoryManager
from core.paths import MEMORY_DIR


class TestMemoryManager(unittest.TestCase):
    SESSION = "unittest_session"

    def setUp(self):
        path = os.path.join(MEMORY_DIR, f"{self.SESSION}.json")
        if os.path.exists(path):
            os.remove(path)
        self.mm = MemoryManager(short_term_turns=3, persist_long_term=True)

    def tearDown(self):
        path = os.path.join(MEMORY_DIR, f"{self.SESSION}.json")
        if os.path.exists(path):
            os.remove(path)

    def test_short_term_window_caps(self):
        for i in range(5):
            self.mm.add_turn(self.SESSION, "user", f"message {i}")
        short_term = self.mm.get_short_term(self.SESSION)
        # deque maxlen=3 -> only last 3 retained
        self.assertEqual(len(short_term), 3)
        self.assertEqual(short_term[-1]["content"], "message 4")

    def test_long_term_persists(self):
        self.mm.add_turn(self.SESSION, "user", "remember this fact: sky is blue")
        loaded = self.mm.load_long_term(self.SESSION)
        self.assertEqual(len(loaded), 1)
        self.assertIn("sky is blue", loaded[0]["content"])

    def test_search_long_term(self):
        self.mm.add_turn(self.SESSION, "user", "my favorite color is green")
        self.mm.add_turn(self.SESSION, "assistant", "noted, green it is")
        self.mm.add_turn(self.SESSION, "user", "unrelated message")
        results = self.mm.search_long_term(self.SESSION, "green")
        self.assertEqual(len(results), 2)

    def test_clear_short_term(self):
        self.mm.add_turn(self.SESSION, "user", "hi")
        self.mm.clear_short_term(self.SESSION)
        self.assertEqual(self.mm.get_short_term(self.SESSION), [])


if __name__ == "__main__":
    unittest.main()
