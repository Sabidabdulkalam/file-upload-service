"""
- Provides a single logger setup for console + file logging.
- Uses a rotating file handler to avoid unbounded log growth.
- Configure handlers on the ROOT logger so all module loggers work.
"""

from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
from src.app import config

_CONFIGURED = False
_APP_LOGGER_NAME = "file_upload_service"


def _configure_root_once() -> None:
    global _CONFIGURED
    if _CONFIGURED:
        return

    # Ensure log folder exists
    config.LOGS_DIR.mkdir(parents=True, exist_ok=True)
    log_path: Path = config.LOGS_DIR / "app.log"

    root = logging.getLogger()      # ROOT LOGGER
    root.setLevel(logging.INFO)

    # Console handler
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    ch.setFormatter(logging.Formatter("[%(levelname)s] %(message)s"))

    # File handler (rotating)
    fh = RotatingFileHandler(
        filename=str(log_path),
        maxBytes=512_000,
        backupCount=3,
        encoding="utf-8",
    )
    fh.setLevel(logging.INFO)
    fh.setFormatter(logging.Formatter(
        "%(asctime)s %(levelname)s %(name)s: %(message)s"
    ))

    # Avoid duplicate handlers if reloaded
    if not any(isinstance(h, RotatingFileHandler) for h in root.handlers):
        root.addHandler(ch)
        root.addHandler(fh)

    _CONFIGURED = True


def get_logger(name: str | None = None) -> logging.Logger:
    """
    Get a module logger. Handlers are installed on the ROOT logger once,
    so any module logger will propagate there automatically.
    """
    _configure_root_once()
    logger_name = name or _APP_LOGGER_NAME
    logger = logging.getLogger(logger_name)
    logger.propagate = True
    return logger
