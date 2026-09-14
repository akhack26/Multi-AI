"""
tools/system_info_tool.py

Read-only system information. Never dangerous - it doesn't change
anything on the host. Uses `psutil` if available for RAM/CPU/disk detail,
and falls back to the standard library only if psutil isn't installed
(kept optional so ISHA still runs with a minimal footprint).
"""

import os
import platform
import shutil

from tools.base_tool import BaseTool, ToolResult
from core.paths import BASE_DIR


class SystemInfoTool(BaseTool):
    name = "system_info"
    description = "Report OS, CPU, RAM, and disk space for the host PC and the ISHA drive."
    dangerous = False

    def run(self, **kwargs) -> ToolResult:
        lines = [
            f"OS: {platform.system()} {platform.release()} ({platform.machine()})",
            f"Python: {platform.python_version()}",
            f"ISHA project location: {BASE_DIR}",
        ]

        try:
            usage = shutil.disk_usage(BASE_DIR)
            gb = 1024 ** 3
            lines.append(
                f"Drive space (ISHA location): "
                f"{usage.used / gb:.1f} GB used / {usage.total / gb:.1f} GB total "
                f"({usage.free / gb:.1f} GB free)"
            )
        except OSError:
            pass

        try:
            import psutil
            lines.append(f"CPU cores (logical): {psutil.cpu_count(logical=True)}")
            lines.append(f"CPU usage: {psutil.cpu_percent(interval=0.2)}%")
            vm = psutil.virtual_memory()
            lines.append(
                f"RAM: {vm.used / (1024**3):.1f} GB used / {vm.total / (1024**3):.1f} GB total "
                f"({vm.percent}%)"
            )
        except ImportError:
            lines.append(f"CPU cores (logical): {os.cpu_count()}")
            lines.append("Install 'psutil' for live CPU/RAM usage stats.")

        return ToolResult(success=True, output="\n".join(lines))
