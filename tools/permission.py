"""
tools/permission.py

The Permission/Validation Layer. Sits between the router/agents and actual
tool execution. This is what makes it safe for the LLM to *request*
actions without the LLM ever being able to directly execute anything on
the host PC.

By default, confirmation is gathered via input() on the console (suitable
for the CLI launcher). A GUI front-end can instead pass in a callback that
shows a real dialog - swap it via `set_confirmation_callback`.
"""

from typing import Callable, Optional

from tools.base_tool import BaseTool, ToolResult, ToolError
from core.logger import get_logger

log = get_logger("permission")

ConfirmCallback = Callable[[str], bool]


def _console_confirm(message: str) -> bool:
    try:
        answer = input(f"\n[ISHA] Confirm action?\n  {message}\n  Proceed? (y/N): ").strip().lower()
    except EOFError:
        return False
    return answer in ("y", "yes")


class PermissionManager:
    def __init__(self, require_confirmation_for_dangerous: bool = True,
                 confirm_callback: Optional[ConfirmCallback] = None):
        self.require_confirmation = require_confirmation_for_dangerous
        self.confirm_callback: ConfirmCallback = confirm_callback or _console_confirm

    def set_confirmation_callback(self, callback: ConfirmCallback) -> None:
        self.confirm_callback = callback

    def execute(self, tool: BaseTool, **kwargs) -> ToolResult:
        description = tool.describe_call(**kwargs)

        if tool.dangerous and self.require_confirmation:
            approved = self.confirm_callback(description)
            if not approved:
                log.info("User denied dangerous tool call: %s", description)
                return ToolResult(success=False, output="", error="Action cancelled by user.")

        log.info("Executing tool: %s", description)
        try:
            return tool.run(**kwargs)
        except ToolError as e:
            log.warning("Tool error: %s", e)
            return ToolResult(success=False, output="", error=str(e))
        except Exception as e:  # last-resort safety net - a tool must never crash ISHA
            log.exception("Unexpected tool failure")
            return ToolResult(success=False, output="", error=f"Unexpected error: {e}")
