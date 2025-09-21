"""
in-memory 'database' for FileRecord objects.
"""

from __future__ import annotations
from typing import Dict, Iterable, Optional
from .models import FileRecord


class InMemoryDB:
    def __init__(self) -> None:
        self._rows: Dict[str, FileRecord] = {}

    def save(self, record: FileRecord) -> None:
        self._rows[record.id] = record

    def get(self, record_id: str) -> Optional[FileRecord]:
        return self._rows.get(record_id)

    def all(self) -> Iterable[FileRecord]:
        # return a copy-like list to avoid accidental external mutation
        return list(self._rows.values())


# simple module-level singleton for convenience
db = InMemoryDB()