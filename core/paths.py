"""
core/paths.py

Central, portable path resolution for ISHA Multi AI.

CRITICAL RULE: Every path in this project must be derived from the location
of this source file (i.e. the project root), NEVER from a hard-coded drive
letter, username, or the current working directory. This is what makes the
whole project work identically whether it lives on C:\\, D:\\, E:\\ or a
USB drive mounted as F:\\, G:\\, etc. on someone else's PC.

Do not import os.getcwd() anywhere else in the project for locating project
files - always go through this module.
"""

import os

# core/paths.py -> core/ -> project root (one level up from this file)
_THIS_FILE = os.path.abspath(__file__)
_CORE_DIR = os.path.dirname(_THIS_FILE)
BASE_DIR = os.path.dirname(_CORE_DIR)


def rel(*parts: str) -> str:
    """Join path parts relative to the project's base directory."""
    return os.path.join(BASE_DIR, *parts)


# Standard project directories (created on import if missing so a fresh
# copy of the project onto a USB drive "just works").
CONFIG_DIR = rel("config")
MODELS_DIR = rel("models")
LOGS_DIR = rel("logs")
DATA_DIR = rel("data")
MEMORY_DIR = rel("data", "memory")
AGENTS_DIR = rel("agents")
TOOLS_DIR = rel("tools")

_REQUIRED_DIRS = (CONFIG_DIR, MODELS_DIR, LOGS_DIR, DATA_DIR, MEMORY_DIR)


def ensure_project_dirs() -> None:
    """Create any missing standard directories. Safe to call repeatedly."""
    for d in _REQUIRED_DIRS:
        os.makedirs(d, exist_ok=True)


def is_outside_project(path: str) -> bool:
    """
    Return True if the given absolute path is NOT inside the project's
    BASE_DIR. Used by tools to warn/confirm before touching files that live
    outside the portable project tree (e.g. on the host PC's C: drive).
    """
    try:
        abs_path = os.path.abspath(path)
        common = os.path.commonpath([abs_path, BASE_DIR])
        return common != BASE_DIR
    except ValueError:
        # commonpath raises ValueError on different drives (Windows) -
        # different drive always means "outside the project".
        return True


ensure_project_dirs()
