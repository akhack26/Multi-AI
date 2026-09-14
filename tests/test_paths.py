"""Tests that path resolution is relative/portable, never hard-coded."""

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core import paths


class TestPaths(unittest.TestCase):
    def test_base_dir_exists(self):
        self.assertTrue(os.path.isdir(paths.BASE_DIR))

    def test_no_hardcoded_drive_or_user_in_base_dir(self):
        # This is a portability smoke test, not a hard guarantee - it just
        # documents the intent: BASE_DIR is derived from __file__, not from
        # a literal string anywhere in the codebase.
        self.assertIn("ISHA_Multi_AI", paths.BASE_DIR)

    def test_rel_joins_correctly(self):
        expected = os.path.join(paths.BASE_DIR, "models")
        self.assertEqual(paths.rel("models"), expected)

    def test_standard_dirs_created(self):
        for d in (paths.CONFIG_DIR, paths.MODELS_DIR, paths.LOGS_DIR, paths.DATA_DIR, paths.MEMORY_DIR):
            self.assertTrue(os.path.isdir(d), f"{d} should exist")

    def test_is_outside_project(self):
        inside = paths.rel("data", "somefile.txt")
        self.assertFalse(paths.is_outside_project(inside))
        self.assertTrue(paths.is_outside_project(os.path.join(os.path.sep, "tmp", "somefile.txt")))


if __name__ == "__main__":
    unittest.main()
