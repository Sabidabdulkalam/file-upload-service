"""
file validation + "upload" (copy) + record creation.

This simulates a file upload in a CLI context by copying a local file
into the app's `uploads/` directory with a unique, safe name.
"""

from __future__ import annotations
import shutil
import uuid
from pathlib import Path

from src.app import config
from src.app.exceptions import InvalidFileTypeError, FileAccessError, UploadError
from src.app.logger import get_logger
from src.app.models import FileRecord
from src.app.storage import db


log = get_logger(__name__)


def is_allowed_file(path: Path) -> bool:
    """
    Return True if the file has an allowed extension (.txt, .csv).
    Case-insensitive.
    """
    return path.suffix.lower() in config.ALLOWED_EXTENSIONS


def upload_file(src_path: Path) -> FileRecord:
    """
    Validate and copy a file into the local uploads folder.

    Steps:
      - ensure file exists and is a regular file
      - validate file extension
      - ensure uploads/ exists
      - copy to a unique filename (preserve extension)
      - create & save FileRecord to in-memory DB
      - log everything with user-safe error handling

    Raises:
        InvalidFileTypeError
        FileAccessError
        UploadError  (generic, user-safe wrapper)
    """
    try:
        if not src_path.exists() or not src_path.is_file():
            raise FileAccessError(f"File not found or not a regular file: {src_path}")

        if not is_allowed_file(src_path):
            raise InvalidFileTypeError(
                f"Extension '{src_path.suffix}' is not allowed. "
                f"Allowed: {sorted(config.ALLOWED_EXTENSIONS)}"
            )

        # ensure uploads dir exists
        config.UPLOADS_DIR.mkdir(parents=True, exist_ok=True)

        # unique target name keeps extension; use uuid4 hex
        target_name = f"{uuid.uuid4().hex}{src_path.suffix.lower()}"
        dest_path = config.UPLOADS_DIR / target_name

        # copy with metadata (copy2)
        shutil.copy2(src_path, dest_path)

        size_bytes = dest_path.stat().st_size
        record = FileRecord(
            id=target_name,               # simple id = stored filename
            original_name=src_path.name,
            stored_path=dest_path,
            size_bytes=size_bytes,
        )

        db.save(record)
        log.info("uploaded file '%s' as '%s' (%d bytes)",
                 src_path.name, dest_path.name, size_bytes)
        return record

    except InvalidFileTypeError:
        log.warning("blocked upload for disallowed file type: %s", src_path)
        raise

    except FileAccessError:
        log.error("cannot access file: %s", src_path)
        raise

    except Exception as exc:
        # keep internal details in logs; expose a safe message to user
        log.exception("unexpected error while uploading '%s'", src_path)
        raise UploadError("Upload failed due to an unexpected error.") from exc
