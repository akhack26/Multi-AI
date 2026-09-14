"""
tools/base_tool.py

Every tool ISHA can call to interact with the host PC implements this
interface. The `dangerous` flag drives the Permission/Validation Layer:
anything destructive or system-altering requires explicit confirmation
before it runs, per the project's design rule:

    User -> ISHA -> Local AI -> Tool/Action Request -> Permission/Validation
    Layer -> Windows Tool -> Result -> Local AI -> ISHA Response -> TTS

The LLM never executes actions directly - it can only *request* a tool
call, which this layer validates/confirms before touching the real system.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict


@dataclass
class ToolResult:
    success: bool
    output: str
    error: str = ""


class ToolError(Exception):
    pass


class BaseTool(ABC):
    name: str = "base_tool"
    description: str = "Base tool"
    dangerous: bool = False  # True => requires confirmation before running

    @abstractmethod
    def run(self, **kwargs) -> ToolResult:
        raise NotImplementedError

    def describe_call(self, **kwargs) -> str:
        """Human-readable one-liner shown in the confirmation prompt."""
        args = ", ".join(f"{k}={v!r}" for k, v in kwargs.items())
        return f"{self.name}({args})"
