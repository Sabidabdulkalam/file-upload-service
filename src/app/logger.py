"""
central logger factory.
- Provides a single logger setup for console + file logging.
- Uses a rotating file handler to avoid unbounded log growth.
- Safe to import from anywhere (no duplicate handlers).
"""

from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

# Local config import
from . import config

_LOGGER_NAME = "file_upload_service"
_configured = False


def get_logger(name: str | None = None) -> logging.Logger:
    """
    Return a logger configured with:
      - Console handler (human-friendly format)
      - Rotating file handler (500KB per file, keep 3 backups)

    Args:
        name: optional name for the logger; defaults to the app root.

    Usage:
        log = get_logger(__name__)
        log.info("something happened")
    """
    global _configured

    logger_name = name or _LOGGER_NAME
    logger = logging.getLogger(logger_name)

    if _configured:
        return logger

    # Ensure log folder exists
    config.LOGS_DIR.mkdir(parents=True, exist_ok=True)

    logger.setLevel(logging.INFO)

    # Console output
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    ch.setFormatter(logging.Formatter("[%(levelname)s] %(message)s"))

    # File output
    fh_path: Path = config.LOGS_DIR / "app.log"
    fh = RotatingFileHandler(fh_path, maxBytes=512_000, backupCount=3)
    fh.setLevel(logging.INFO)
    fh.setFormatter(logging.Formatter(
        "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
    ))

    logger.addHandler(ch)
    logger.addHandler(fh)

    _configured = True
    return logger