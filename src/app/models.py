"""
models.py — simple data model(s) for uploaded file records.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional


@dataclass(slots=True)
class FileRecord:
    """
    Represents an uploaded file.

    Attributes:
        id: Unique id (we use the generated stored filename).
        original_name: Original basename provided by the user.
        stored_path: Absolute path where the file is stored locally.
        size_bytes: File size in bytes.
        uploaded_at: UTC timestamp of record creation.
        status: 'UPLOADED' | 'PROCESSED' (processing in next step).
        line_count: Optional number of lines.
        word_count: Optional number of words.
    """
    id: str
    original_name: str
    stored_path: Path
    size_bytes: int
    uploaded_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    status: str = "UPLOADED"
    line_count: Optional[int] = None
    word_count: Optional[int] = None