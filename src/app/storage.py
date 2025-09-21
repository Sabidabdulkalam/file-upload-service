"""
in-memory 'database' with lightweight JSON persistence.

keep a dict of FileRecord objects in memory, but also mirror them to
data/db.json so that CLI commands in *separate processes* can see past uploads.

- On import: load from data/db.json if it exists.
- On save(): write db.json.
- Also register an atexit flush in case of pending changes.
"""

from __future__ import annotations

import json
import atexit
from datetime import datetime
from pathlib import Path
from typing import Dict, Iterable, Optional

from src.app.models import FileRecord
from src.app import config


_DB_PATH: Path = config.DATA_DIR / "db.json"


class InMemoryDB:
    def __init__(self) -> None:
        self._rows: Dict[str, FileRecord] = {}
        self._dirty: bool = False
        self._load()
        atexit.register(self._flush_if_dirty)

    # ---------- public API ----------

    def save(self, record: FileRecord) -> None:
        self._rows[record.id] = record
        self._dirty = True
        self._flush()  # persist immediately for CLI friendliness

    def get(self, record_id: str) -> Optional[FileRecord]:
        return self._rows.get(record_id)

    def all(self) -> Iterable[FileRecord]:
        # return a copy-like list to avoid accidental external mutation
        return list(self._rows.values())

    # ---------- persistence helpers ----------

    def _flush_if_dirty(self) -> None:
        if self._dirty:
            self._flush()

    def _flush(self) -> None:
        config.DATA_DIR.mkdir(parents=True, exist_ok=True)
        data = [self._to_dict(fr) for fr in self._rows.values()]
        _DB_PATH.write_text(json.dumps(data, indent=2), encoding="utf-8")
        self._dirty = False

    def _load(self) -> None:
        if not _DB_PATH.exists():
            return
        try:
            items = json.loads(_DB_PATH.read_text(encoding="utf-8"))
            self._rows = {d["id"]: self._from_dict(d) for d in items}
        except Exception:
            # If the file is corrupted, start fresh (could also log; kept simple here).
            self._rows = {}

    @staticmethod
    def _to_dict(fr: FileRecord) -> dict:
        return {
            "id": fr.id,
            "original_name": fr.original_name,
            "stored_path": str(fr.stored_path),
            "size_bytes": fr.size_bytes,
            "uploaded_at": fr.uploaded_at.isoformat(),
            "status": fr.status,
            "line_count": fr.line_count,
            "word_count": fr.word_count,
        }

    @staticmethod
    def _from_dict(d: dict) -> FileRecord:
        return FileRecord(
            id=d["id"],
            original_name=d["original_name"],
            stored_path=Path(d["stored_path"]),
            size_bytes=int(d["size_bytes"]),
            uploaded_at=datetime.fromisoformat(d["uploaded_at"]),
            status=d.get("status", "UPLOADED"),
            line_count=d.get("line_count"),
            word_count=d.get("word_count"),
        )


# module-level singleton
db = InMemoryDB()
