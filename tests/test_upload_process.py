"""
Stdlib unittest (no external deps).

Sandbox by redirecting config paths to a temp directory for each test,
and reloading the storage module so its singleton DB points at the temp data dir.
"""

import importlib
import tempfile
import unittest
from pathlib import Path

from src.app import config
from src.app.uploader import upload_file, is_allowed_file
from src.app.exceptions import InvalidFileTypeError, FileAccessError
from src.app.processor import process_file
import src.app.storage as storage  # we will reload this module after changing config paths


class UploadProcessTests(unittest.TestCase):
    def setUp(self) -> None:
        # Create a temp workspace and repoint config paths into it
        self.tmpdir = tempfile.TemporaryDirectory()
        base = Path(self.tmpdir.name)

        config.UPLOADS_DIR = base / "uploads"
        config.LOGS_DIR = base / "logs"
        config.DATA_DIR = base / "data"

        config.UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
        config.LOGS_DIR.mkdir(parents=True, exist_ok=True)
        config.DATA_DIR.mkdir(parents=True, exist_ok=True)

        # IMPORTANT: reload storage so its module-level singleton `db` uses the new DATA_DIR
        importlib.reload(storage)

        # Build sample files inside the temp folder
        self.sample_txt = base / "sample.txt"
        self.sample_txt.write_text(
            "Hello there!\nThis is a tiny sample text file.\nIt has three lines.",
            encoding="utf-8"
        )

        self.sample_csv = base / "sample.csv"
        self.sample_csv.write_text(
            "name,age\nAlice,30\nBob,22\nCharlie,27\n",
            encoding="utf-8"
        )

        self.bad_pdf = base / "report.pdf"
        self.bad_pdf.write_bytes(b"%PDF-1.4 pretend-binary")

    def tearDown(self) -> None:
        self.tmpdir.cleanup()

    # ---------- validation ----------

    def test_is_allowed_file(self):
        self.assertTrue(is_allowed_file(self.sample_txt))
        self.assertTrue(is_allowed_file(self.sample_csv))
        self.assertFalse(is_allowed_file(self.bad_pdf))

    def test_upload_disallowed_extension_raises(self):
        with self.assertRaises(InvalidFileTypeError):
            upload_file(self.bad_pdf)

    def test_upload_missing_file_raises(self):
        missing = Path(self.tmpdir.name) / "nope.txt"
        with self.assertRaises(FileAccessError):
            upload_file(missing)

    # ---------- upload + process happy paths ----------

    def test_upload_txt_creates_record_and_copy(self):
        rec = upload_file(self.sample_txt)
        self.assertTrue(rec.id.endswith(".txt"))
        self.assertEqual(rec.original_name, "sample.txt")
        self.assertTrue(rec.stored_path.exists())
        self.assertEqual(rec.status, "UPLOADED")

    def test_process_counts_and_status(self):
        rec = upload_file(self.sample_txt)
        rec2 = process_file(rec.id)
        self.assertEqual(rec2.status, "PROCESSED")
        self.assertEqual(rec2.line_count, 3)
        self.assertEqual(rec2.word_count, 13)

    def test_process_csv_counts_lines_and_words(self):
        rec = upload_file(self.sample_csv)
        rec2 = process_file(rec.id)
        # 4 lines including header
        self.assertEqual(rec2.line_count, 4)
        # Our word counting is whitespace-based; each CSV line is a single token.
        self.assertEqual(rec2.word_count, 4)

    # ---------- persistence across processes simulation ----------

    def test_persistence_after_reload(self):
        rec = upload_file(self.sample_txt)  # save() flushes to data/db.json
        # Simulate a fresh process by reloading storage
        importlib.reload(storage)
        db2 = storage.db
        found = db2.get(rec.id)
        self.assertIsNotNone(found)
        self.assertEqual(found.original_name, "sample.txt")


if __name__ == "__main__":
    unittest.main(verbosity=2)
