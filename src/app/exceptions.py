"""
meaningful, user-safe exceptions for the upload flow.
"""

class UploadError(Exception):
    """Top-level upload failure (user-safe)."""


class InvalidFileTypeError(UploadError):
    """Raised when a file extension is not permitted."""


class FileAccessError(UploadError):
    """Raised when a file cannot be accessed (permissions, missing, etc.)."""