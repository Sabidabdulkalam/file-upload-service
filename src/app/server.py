"""
stdlib HTTP server for uploading and processing files.

- No external frameworks (http.server + cgi only).
- POST /upload (multipart/form-data, field name 'file'):
    * validates extension (.txt, .csv)
    * stores a copy via uploader
    * processes it (count lines + words)
    * persists to data/db.json
    * returns JSON { id, original_name, size_bytes, status, line_count, word_count }

- GET /records:
    * returns JSON array of all records

- GET /:
    * serves a minimal HTML page with a file input and results panel

This is intentionally basic for a pre-test; production apps would use
a real framework and stronger security hardening.
"""

from __future__ import annotations

import io
import json
import os
from http.server import HTTPServer, BaseHTTPRequestHandler
import cgi
from pathlib import Path
from typing import Tuple

from src.app.logger import get_logger
from src.app import config
from src.app.uploader import upload_file
from src.app.processor import process_file
from src.app.storage import db
from src.app.exceptions import (
    InvalidFileTypeError, FileAccessError, UploadError,
    RecordNotFoundError, DecodeError, ProcessingError
)

log = get_logger(__name__)


def _json_bytes(payload: dict | list, status: int = 200) -> Tuple[int, bytes, str]:
    data = json.dumps(payload, indent=2).encode("utf-8")
    return status, data, "application/json; charset=utf-8"


def _html_bytes(html: str, status: int = 200) -> Tuple[int, bytes, str]:
    return status, html.encode("utf-8"), "text/html; charset=utf-8"


INDEX_HTML = """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8"/>
  <title>File Upload & Processing (Minimal)</title>
  <meta name="viewport" content="width=device-width, initial-scale=1"/>
  <style>
    body { font-family: system-ui, sans-serif; max-width: 820px; margin: 40px auto; padding: 0 16px; }
    header { margin-bottom: 16px; }
    .card { border: 1px solid #ddd; border-radius: 12px; padding: 16px; margin-bottom: 16px; }
    button { padding: 8px 14px; border-radius: 8px; border: 1px solid #ccc; cursor: pointer; }
    table { width: 100%; border-collapse: collapse; }
    th, td { padding: 8px; border-bottom: 1px solid #eee; text-align: left; }
    .muted { color: #666; }
    .ok { color: #2563eb; }
    .err { color: #b91c1c; }
  </style>
</head>
<body>
  <header>
    <h1>File Upload & Processing</h1>
    <p class="muted">Allowed: <code>.txt</code>, <code>.csv</code>. Counts lines & words; stores results in memory (with JSON persistence).</p>
  </header>

  <section class="card">
    <h2>Upload a file</h2>
    <input id="file" type="file" />
    <button id="btn">Upload</button>
    <div id="msg" class="muted" style="margin-top:8px;"></div>
  </section>

  <section class="card">
    <h2>Records</h2>
    <button id="refresh">Refresh</button>
    <div id="table"></div>
  </section>

<script>
async function refresh() {
  const r = await fetch('/records');
  const data = await r.json();
  if (!Array.isArray(data) || data.length === 0) {
    document.getElementById('table').innerHTML = '<p class="muted">(no records yet)</p>';
    return;
  }
  const rows = data.map(x => `
    <tr>
      <td><code>${x.id}</code></td>
      <td>${x.original_name}</td>
      <td>${x.size_bytes}</td>
      <td>${x.status}</td>
      <td>${x.line_count ?? '-'}</td>
      <td>${x.word_count ?? '-'}</td>
    </tr>`).join('');
  document.getElementById('table').innerHTML = `
    <table>
      <thead><tr><th>ID</th><th>Original</th><th>Size</th><th>Status</th><th>Lines</th><th>Words</th></tr></thead>
      <tbody>${rows}</tbody>
    </table>`;
}

async function upload() {
  const fileInput = document.getElementById('file');
  const msg = document.getElementById('msg');
  if (!fileInput.files || fileInput.files.length === 0) {
    msg.textContent = 'Please choose a file.';
    msg.className = 'err';
    return;
  }
  const form = new FormData();
  form.append('file', fileInput.files[0]);
  msg.textContent = 'Uploading...';
  msg.className = 'muted';
  try {
    const r = await fetch('/upload', { method: 'POST', body: form });
    const data = await r.json();
    if (!r.ok) {
      msg.textContent = data.error || 'Upload failed';
      msg.className = 'err';
    } else {
      msg.textContent = `OK: id=${data.id}, lines=${data.line_count}, words=${data.word_count}`;
      msg.className = 'ok';
      await refresh();
      fileInput.value = '';
    }
  } catch (e) {
    msg.textContent = 'Network error';
    msg.className = 'err';
  }
}

document.getElementById('btn').addEventListener('click', upload);
document.getElementById('refresh').addEventListener('click', refresh);
window.addEventListener('load', refresh);
</script>
</body>
</html>
"""


class Handler(BaseHTTPRequestHandler):
    server_version = "MiniUpload/0.1"

    def _send(self, status: int, body: bytes, content_type: str):
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        # Simple CORS for local dev if you open the file directly
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self):
        # minimal CORS preflight support if needed
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET,POST,OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self):
        if self.path == "/":
            status, body, ctype = _html_bytes(INDEX_HTML)
            return self._send(status, body, ctype)

        if self.path == "/records":
            payload = []
            for r in db.all():
                payload.append({
                    "id": r.id,
                    "original_name": r.original_name,
                    "stored_path": str(r.stored_path),
                    "size_bytes": r.size_bytes,
                    "uploaded_at": r.uploaded_at.isoformat(),
                    "status": r.status,
                    "line_count": r.line_count,
                    "word_count": r.word_count,
                })
            status, body, ctype = _json_bytes(payload)
            return self._send(status, body, ctype)

        status, body, ctype = _json_bytes({"error": "Not found"}, 404)
        return self._send(status, body, ctype)

    def do_POST(self):
        if self.path != "/upload":
            status, body, ctype = _json_bytes({"error": "Not found"}, 404)
            return self._send(status, body, ctype)

        # Parse multipart form
        ctype, pdict = cgi.parse_header(self.headers.get("Content-Type", ""))
        if ctype != "multipart/form-data":
            status, body, ctype2 = _json_bytes({"error": "Use multipart/form-data"}, 400)
            return self._send(status, body, ctype2)

        form = cgi.FieldStorage(
            fp=self.rfile,
            headers=self.headers,
            environ={
                "REQUEST_METHOD": "POST",
                "CONTENT_TYPE": self.headers.get("Content-Type"),
            }
        )

        file_item = form["file"] if "file" in form else None
        if file_item is None or not file_item.filename:
            status, body, ctype2 = _json_bytes({"error": "Missing file"}, 400)
            return self._send(status, body, ctype2)

        # Save the uploaded stream to a temporary file first
        tmp_dir = config.UPLOADS_DIR / "_incoming"
        tmp_dir.mkdir(parents=True, exist_ok=True)
        tmp_path = tmp_dir / Path(file_item.filename).name
        try:
            with open(tmp_path, "wb") as f:
                f.write(file_item.file.read())

            # Use our existing uploader + processor
            rec = upload_file(tmp_path)
            rec = process_file(rec.id)  # updates counts + status, persists

            payload = {
                "id": rec.id,
                "original_name": rec.original_name,
                "size_bytes": rec.size_bytes,
                "status": rec.status,
                "line_count": rec.line_count,
                "word_count": rec.word_count,
            }
            status, body, ctype2 = _json_bytes(payload, 200)
            self._send(status, body, ctype2)

        except (InvalidFileTypeError, FileAccessError) as e:
            status, body, ctype2 = _json_bytes({"error": str(e)}, 400)
            self._send(status, body, ctype2)
        except (UploadError, RecordNotFoundError, DecodeError, ProcessingError) as e:
            status, body, ctype2 = _json_bytes({"error": str(e)}, 500)
            self._send(status, body, ctype2)
        except Exception:
            log.exception("unexpected failure in /upload")
            status, body, ctype2 = _json_bytes({"error": "Unexpected server error"}, 500)
            self._send(status, body, ctype2)
        finally:
            # best-effort cleanup of the temporary file
            try:
                if tmp_path.exists():
                    tmp_path.unlink()
            except Exception:
                pass


def run(host: str = "127.0.0.1", port: int = 8000) -> None:
    server = HTTPServer((host, port), Handler)
    log.info("serving on http://%s:%d", host, port)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        log.info("shutting down…")
    finally:
        server.server_close()


if __name__ == "__main__":
    run()
