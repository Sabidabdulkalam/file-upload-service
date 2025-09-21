"""
small command-line interface for the module.

Commands:
  upload <path>         : validate + copy file into uploads/, create DB record
  list                  : list in-memory records
  process <record_id>   : count lines & words, update record
"""

from __future__ import annotations

import argparse
from pathlib import Path

from src.app.logger import get_logger
from src.app.uploader import upload_file, InvalidFileTypeError, FileAccessError, UploadError
from src.app.storage import db
from src.app.processor import process_file
from src.app.exceptions import RecordNotFoundError, DecodeError, ProcessingError

log = get_logger(__name__)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="file-upload-service",
        description="Upload and process files (.txt, .csv) locally."
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # upload
    p_up = sub.add_parser("upload", help="Upload a file (local path).")
    p_up.add_argument("path", type=str, help="Path to the file to upload (.txt or .csv).")

    # list
    sub.add_parser("list", help="List uploaded records (from in-memory DB).")

    # process
    p_proc = sub.add_parser("process", help="Process a file by record id (count lines & words).")
    p_proc.add_argument("record_id", type=str, help="Record id to process (use the id shown in 'list').")

    args = parser.parse_args(argv)

    if args.command == "upload":
        try:
            rec = upload_file(Path(args.path))
            print(f"OK: uploaded '{rec.original_name}' -> id={rec.id} size={rec.size_bytes}B")
            return 0
        except InvalidFileTypeError as e:
            print(f"ERROR: {e}")
            return 2
        except FileAccessError as e:
            print(f"ERROR: {e}")
            return 3
        except UploadError as e:
            print(f"ERROR: {e}")
            return 4

    if args.command == "list":
        rows = list(db.all())
        if not rows:
            print("(no records yet)")
            return 0
        for r in rows:
            # include counts if processed
            counts = ""
            if r.line_count is not None and r.word_count is not None:
                counts = f" | lines={r.line_count} words={r.word_count}"
            print(f"{r.id} | {r.original_name} | {r.size_bytes}B | {r.status}{counts}")
        return 0

    if args.command == "process":
        try:
            rec = process_file(args.record_id)
            print(f"OK: processed id={rec.id} -> lines={rec.line_count} words={rec.word_count}")
            return 0
        except RecordNotFoundError as e:
            print(f"ERROR: {e}")
            return 5
        except DecodeError as e:
            print(f"ERROR: {e}")
            return 6
        except ProcessingError as e:
            print(f"ERROR: {e}")
            return 7

    parser.print_help()
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
