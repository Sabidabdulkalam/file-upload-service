"""
small command-line interface for the module.

Commands:
  upload <path>   : validate + copy file into uploads/, create DB record
  list            : list in-memory records
"""

from __future__ import annotations

import argparse
from pathlib import Path

from src.app.logger import get_logger        # absolute import for IntelliJ run convenience
from src.app.uploader import upload_file, InvalidFileTypeError, FileAccessError, UploadError
from src.app.storage import db

log = get_logger(__name__)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="file-upload-service",
        description="Upload files (.txt, .csv) into a local uploads directory."
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_up = sub.add_parser("upload", help="Upload a file (local path).")
    p_up.add_argument("path", type=str, help="Path to the file to upload (.txt or .csv).")

    sub.add_parser("list", help="List uploaded records (from in-memory DB).")

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
            print(f"{r.id} | {r.original_name} | {r.size_bytes}B | {r.status}")
        return 0

    parser.print_help()
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
