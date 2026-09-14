"""
tools/app_launcher_tool.py

Launches an application on the host PC. Always marked dangerous - starting
an arbitrary program is exactly the kind of action the design's Permission/
Validation Layer exists to gate. An optional whitelist (config.json ->
tools.app_launch_whitelist) can restrict this to a known-safe set of names.
"""

import os
import platform
import shutil
import subprocess
from typing import List, Optional

from tools.base_tool import BaseTool, ToolResult, ToolError


class LaunchAppTool(BaseTool):
    name = "launch_app"
    description = "Launch an application/executable on the host PC."
    dangerous = True

    def __init__(self, whitelist: Optional[List[str]] = None):
        # Empty whitelist = allow anything (still gated by confirmation).
        self.whitelist = [w.lower() for w in (whitelist or [])]

    def run(self, app: str, args: Optional[List[str]] = None, **kwargs) -> ToolResult:
        args = args or []

        if self.whitelist and app.lower() not in self.whitelist:
            return ToolResult(
                success=False, output="",
                error=f"'{app}' is not on the app_launch_whitelist in config.json.",
            )

        system = platform.system()
        try:
            if system == "Windows":
                # os.startfile handles both full paths and registered app names.
                os.startfile(app)  # type: ignore[attr-defined]
            else:
                resolved = shutil.which(app) or app
                subprocess.Popen([resolved, *args])
            return ToolResult(success=True, output=f"Launched: {app} {' '.join(args)}".strip())
        except FileNotFoundError as e:
            return ToolResult(success=False, output="", error=f"Application not found: {app} ({e})")
        except OSError as e:
            return ToolResult(success=False, output="", error=f"Failed to launch '{app}': {e}")

    def describe_call(self, **kwargs) -> str:
        app = kwargs.get("app", "?")
        args = kwargs.get("args", []) or []
        return f"launch_app(app={app!r}, args={args})"
