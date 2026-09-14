"""
router/router.py

The AI Router/Orchestrator front-door: decides which agent should handle a
given piece of user input. Implemented as a fast, fully offline keyword +
heuristic classifier (no extra model call needed just to route), with a
clean extension point if you later want to swap in an embedding/model-based
classifier instead.
"""

from dataclasses import dataclass
from typing import Dict, List

from core.logger import get_logger

log = get_logger("router")


@dataclass
class RouteDecision:
    role: str
    confidence: float
    matched_keywords: List[str]


# Ordered so more specific roles are checked before the general chat catch-all.
_KEYWORDS: Dict[str, List[str]] = {
    "coding": [
        "code", "function", "bug", "debug", "compile", "error trace", "stack trace",
        "python", "javascript", "java ", "c++", "c#", "html", "css", "sql", "api",
        "refactor", "syntax", "script", "algorithm", "class ", "variable", "regex",
        "git ", "github", "exception", "traceback", "unit test", "programming",
    ],
    "reasoning": [
        "solve", "prove", "calculate", "logic", "step by step", "reason through",
        "math problem", "equation", "puzzle", "optimi", "strategy", "plan out",
        "pros and cons", "decision", "trade-off", "tradeoff", "why does", "derive",
    ],
    "study": [
        "explain", "summarize", "summarise", "study", "quiz me", "flashcard",
        "homework", "exam", "definition", "define ", "what is", "what are",
        "difference between", "teach me", "notes on", "revise", "revision",
        "chapter", "syllabus",
    ],
}

_TOOL_KEYWORDS = [
    "open the file", "read the file", "write a file", "delete the file",
    "list files", "list directory", "launch ", "open app", "start the app",
    "system info", "cpu usage", "memory usage", "disk space", "open notepad",
]


class Router:
    def __init__(self, enabled_roles: List[str], default_role: str = "chat"):
        self.enabled_roles = set(enabled_roles) | {default_role}
        self.default_role = default_role

    def classify(self, text: str) -> RouteDecision:
        lowered = text.lower()

        best_role = self.default_role
        best_matches: List[str] = []

        for role, keywords in _KEYWORDS.items():
            if role not in self.enabled_roles:
                continue
            matches = [kw for kw in keywords if kw in lowered]
            if len(matches) > len(best_matches):
                best_role = role
                best_matches = matches

        confidence = min(1.0, 0.4 + 0.15 * len(best_matches)) if best_matches else 0.3
        decision = RouteDecision(role=best_role, confidence=confidence, matched_keywords=best_matches)
        log.debug("Routed input to '%s' (confidence=%.2f, matches=%s)",
                   decision.role, decision.confidence, decision.matched_keywords)
        return decision

    @staticmethod
    def looks_like_tool_request(text: str) -> bool:
        lowered = text.lower()
        return any(kw in lowered for kw in _TOOL_KEYWORDS)
