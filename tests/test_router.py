"""Tests for the keyword-based router classification."""

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from router.router import Router


class TestRouter(unittest.TestCase):
    def setUp(self):
        self.router = Router(enabled_roles=["chat", "study", "coding", "reasoning"], default_role="chat")

    def test_coding_route(self):
        decision = self.router.classify("Can you help me debug this Python function?")
        self.assertEqual(decision.role, "coding")

    def test_study_route(self):
        decision = self.router.classify("Can you explain photosynthesis and quiz me on it?")
        self.assertEqual(decision.role, "study")

    def test_reasoning_route(self):
        decision = self.router.classify("Solve this step by step: what's the optimal strategy here?")
        self.assertEqual(decision.role, "reasoning")

    def test_default_fallback(self):
        decision = self.router.classify("Hey, how's it going today?")
        self.assertEqual(decision.role, "chat")

    def test_disabled_role_not_selected(self):
        router = Router(enabled_roles=["chat"], default_role="chat")
        decision = router.classify("Please debug my python code")
        self.assertEqual(decision.role, "chat")

    def test_tool_request_detection(self):
        self.assertTrue(Router.looks_like_tool_request("please list files in this folder"))
        self.assertFalse(Router.looks_like_tool_request("tell me a joke"))


if __name__ == "__main__":
    unittest.main()
