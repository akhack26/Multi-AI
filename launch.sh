#!/usr/bin/env bash
# ISHA Multi AI - Portable Launcher (Linux/macOS)
# Resolves everything relative to this script's own location, so it works
# identically no matter where the drive is mounted.

set -e
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$DIR"

echo "============================================"
echo "  ISHA Multi AI - Portable Local Assistant"
echo "  Running from: $DIR"
echo "============================================"
echo

PYTHON_CMD=""
if command -v python3 >/dev/null 2>&1; then
    PYTHON_CMD=python3
elif command -v python >/dev/null 2>&1; then
    PYTHON_CMD=python
else
    echo "[ERROR] Python 3.10+ was not found on PATH. Please install it first."
    exit 1
fi

echo "Using Python command: $PYTHON_CMD"
echo "Checking dependencies (installs only what's missing)..."
"$PYTHON_CMD" -m pip install --quiet --disable-pip-version-check -r requirements/requirements.txt || true

"$PYTHON_CMD" main.py
