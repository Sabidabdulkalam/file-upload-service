"""
central, minimal configuration.
We keep configuration tiny and import-safe so any module can use it without
side effects. Paths are resolved relative to the project root.
"""

from __future__ import annotations
from pathlib import Path

# Project root is two levels up from this file (src/app/config.py)
BASE_DIR: Path = Path(__file__).resolve().parents[2]

# Runtime folders — created on demand elsewhere
UPLOADS_DIR: Path = BASE_DIR / "uploads"
LOGS_DIR: Path = BASE_DIR / "logs"
DATA_DIR: Path = BASE_DIR / "data"

# Allowed file extensions for "uploads" (case-insensitive).
ALLOWED_EXTENSIONS = {".txt", ".csv"}