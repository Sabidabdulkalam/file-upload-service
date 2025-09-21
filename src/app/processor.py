"""
open stored file, count lines & words, update record.

Design goals:
- Robust text decoding (try utf-8, utf-8-sig; fallback latin-1; final ignore).
- Clear logging at start/end.
- Update FileRecord with counts and status 'PROCESSED'.
- User-safe exceptions for common failures.
"""

from __future__ import annotations

from pathlib import Path
from typing import Tuple

from src.app.logger import get_logger
from src.app.storage import db
from src.app.models import FileRecord
from src.app.exceptions import ProcessingError, RecordNotFoundError, DecodeError

log = get_logger(__name__)


def _read_text_robust(path: Path) -> str:
    """
    Attempt to read text with a few sensible fallbacks.

    Order:
      1) utf-8
      2) utf-8-sig (handles BOM)
      3) latin-1
      4) utf-8 with errors='ignore' (last resort)

    Raises:
        DecodeError if the file cannot be decoded even after fallbacks.
    """
    # 1) utf-8
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        pass

    # 2) utf-8-sig
    try:
        return path.read_text(encoding="utf-8-sig")
    except UnicodeDecodeError:
        pass

    # 3) latin-1
    try:
        return path.read_text(encoding="latin-1")
    except UnicodeDecodeError:
        pass

    # 4) utf-8 ignore (do not raise here; explicitly last resort)
    try:
        return path.read_text(encoding="utf-8", errors="ignore")
    except Exception as exc:  # extremely rare
        raise DecodeError(f"Could not decode file: {path.name}") from exc


def _count_lines_words(text: str) -> Tuple[int, int]:
    """
    Count lines and words in a simple, deterministic way.

    - Lines: number of newline-separated lines (splitlines()).
    - Words: whitespace-separated tokens across all lines.
    """
    lines = text.splitlines()
    line_count = len(lines)
    word_count = 0
    for ln in lines:
        # split() without args splits on arbitrary whitespace and collapses repeats
        word_count += len(ln.split())
    return line_count, word_count


def process_file(record_id: str) -> FileRecord:
    """
    Process a stored file:
      - load DB record
      - read file text robustly
      - count lines & words
      - update record fields + status
      - log start/end
      - return the updated record

    Raises:
        RecordNotFoundError
        DecodeError
        ProcessingError
    """
    try:
        rec = db.get(record_id)
        if rec is None:
            raise RecordNotFoundError(f"Record not found: {record_id}")

        path: Path = rec.stored_path
        log.info("processing id='%s' file='%s'", rec.id, path.name)

        text = _read_text_robust(path)
        line_count, word_count = _count_lines_words(text)

        rec.line_count = line_count
        rec.word_count = word_count
        rec.status = "PROCESSED"

        db.save(rec)   # <--- persist the updated record

        log.info("processed '%s': lines=%d, words=%d", path.name, line_count, word_count)
        return rec

    except (RecordNotFoundError, DecodeError):
        # These are meaningful and already user-safe
        raise

    except Exception as exc:
        log.exception("unexpected error while processing '%s'", record_id)
        raise ProcessingError("Processing failed due to an unexpected error.") from exc
