"""
tools/file_tools.py

File operation tools: read, write, list, delete. Paths may be relative
(resolved against the project's data/ folder by default) or absolute, but
every operation runs through basic safety checks:
  - refuses to touch a small set of obviously critical system locations
  - warns (via the `dangerous` flag + confirmation layer) before writing/
    deleting anything outside the project folder
  - delete is always marked dangerous and requires confirmation
"""

import os
import shutil
from typing import Optional

from tools.base_tool import BaseTool, ToolResult, ToolError
from core.paths import DATA_DIR, BASE_DIR, is_outside_project

_BLOCKED_SUBSTRINGS = [
    os.sep + "windows" + os.sep,
    os.sep + "system32",
    os.sep + "boot",
    os.sep + "program files",
]


def _resolve(path: str) -> str:
    """Relative paths resolve against data/; absolute paths pass through."""
    if os.path.isabs(path):
        resolved = path
    else:
        resolved = os.path.join(DATA_DIR, path)
    resolved = os.path.abspath(resolved)

    lowered = resolved.lower()
    for blocked in _BLOCKED_SUBSTRINGS:
        if blocked in lowered:
            raise ToolError(f"Refusing to touch a protected system path: {resolved}")
    return resolved


class ReadFileTool(BaseTool):
    name = "read_file"
    description = "Read the text contents of a file."
    dangerous = False

    def run(self, path: str, **kwargs) -> ToolResult:
        try:
            full_path = _resolve(path)
        except ToolError as e:
            return ToolResult(success=False, output="", error=str(e))
        if not os.path.isfile(full_path):
            return ToolResult(success=False, output="", error=f"File not found: {full_path}")
        try:
            with open(full_path, "r", encoding="utf-8", errors="replace") as f:
                content = f.read()
            return ToolResult(success=True, output=content)
        except OSError as e:
            return ToolResult(success=False, output="", error=str(e))


class WriteFileTool(BaseTool):
    name = "write_file"
    description = "Write (create or overwrite) a text file."
    # Writing outside the project is flagged dangerous; writing inside data/ is not.
    dangerous = True

    def run(self, path: str, content: str, **kwargs) -> ToolResult:
        try:
            full_path = _resolve(path)
        except ToolError as e:
            return ToolResult(success=False, output="", error=str(e))
        try:
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            with open(full_path, "w", encoding="utf-8") as f:
                f.write(content)
            return ToolResult(success=True, output=f"Wrote {len(content)} bytes to {full_path}")
        except OSError as e:
            return ToolResult(success=False, output="", error=str(e))

    def describe_call(self, **kwargs) -> str:
        path = kwargs.get("path", "?")
        content = kwargs.get("content", "")
        outside = " (OUTSIDE PROJECT FOLDER)" if is_outside_project(_safe_resolve_preview(path)) else ""
        return f"write_file(path={path!r}{outside}, {len(content)} bytes)"


class ListDirTool(BaseTool):
    name = "list_dir"
    description = "List files and folders inside a directory."
    dangerous = False

    def run(self, path: str = ".", **kwargs) -> ToolResult:
        try:
            full_path = _resolve(path)
        except ToolError as e:
            return ToolResult(success=False, output="", error=str(e))
        if not os.path.isdir(full_path):
            return ToolResult(success=False, output="", error=f"Not a directory: {full_path}")
        try:
            entries = sorted(os.listdir(full_path))
            listing = "\n".join(entries) if entries else "(empty directory)"
            return ToolResult(success=True, output=listing)
        except OSError as e:
            return ToolResult(success=False, output="", error=str(e))


class DeleteFileTool(BaseTool):
    name = "delete_file"
    description = "Permanently delete a file. ALWAYS requires confirmation."
    dangerous = True

    def run(self, path: str, **kwargs) -> ToolResult:
        try:
            full_path = _resolve(path)
        except ToolError as e:
            return ToolResult(success=False, output="", error=str(e))
        if not os.path.isfile(full_path):
            return ToolResult(success=False, output="", error=f"File not found: {full_path}")
        try:
            os.remove(full_path)
            return ToolResult(success=True, output=f"Deleted {full_path}")
        except OSError as e:
            return ToolResult(success=False, output="", error=str(e))


def _safe_resolve_preview(path: str) -> str:
    """Like _resolve but never raises - used only for the confirmation preview text."""
    try:
        return _resolve(path)
    except ToolError:
        return path
