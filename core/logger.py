"""
core/logger.py

Simple, dependency-free logging setup. Logs to both console and a rotating
log file inside the portable logs/ directory (never a system temp path).
"""

import logging
import os
from logging.handlers import RotatingFileHandler

from core.paths import LOGS_DIR

_LOG_FILE = os.path.join(LOGS_DIR, "isha.log")

_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
_DATEFMT = "%Y-%m-%d %H:%M:%S"

_configured = False


def _configure_root():
    global _configured
    if _configured:
        return
    os.makedirs(LOGS_DIR, exist_ok=True)

    root = logging.getLogger("isha")
    root.setLevel(logging.DEBUG)

    formatter = logging.Formatter(_FORMAT, datefmt=_DATEFMT)

    console = logging.StreamHandler()
    console.setLevel(logging.INFO)
    console.setFormatter(formatter)
    root.addHandler(console)

    try:
        file_handler = RotatingFileHandler(
            _LOG_FILE, maxBytes=2 * 1024 * 1024, backupCount=3, encoding="utf-8"
        )
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        root.addHandler(file_handler)
    except OSError:
        # If the USB drive is briefly unavailable/read-only, don't crash -
        # just run with console-only logging.
        pass

    _configured = True


def get_logger(name: str) -> logging.Logger:
    """Get a namespaced logger, e.g. get_logger('router')."""
    _configure_root()
    return logging.getLogger(f"isha.{name}")
