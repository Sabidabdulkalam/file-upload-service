"""
user-safe exceptions
for upload, processing, and persistence.
"""

# ---- Upload errors ----
class UploadError(Exception):
    """Top-level upload failure (user-safe)."""

class InvalidFileTypeError(UploadError):
    """Raised when a file extension is not permitted."""

class FileAccessError(UploadError):
    """Raised when a file cannot be accessed (missing, permissions, etc.)."""


# ---- Processing errors ----
class ProcessingError(Exception):
    """Top-level processing failure (user-safe)."""

class RecordNotFoundError(ProcessingError):
    """Raised when a FileRecord id does not exist in the in-memory DB."""

class DecodeError(ProcessingError):
    """Raised when decoding the file to text fails."""


# ---- Persistence errors (optional, future-proofing) ----
class PersistenceError(Exception):
    """Raised when saving/loading records to disk fails."""
