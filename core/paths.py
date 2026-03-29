"""Shared filesystem paths used by the document manager."""

from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = BASE_DIR / "data"
STORAGE_DIR = BASE_DIR / "storage"
PDF_STORAGE_DIR = STORAGE_DIR / "pdfs"
THUMBNAIL_DIR = STORAGE_DIR / "thumbnails"
DB_PATH = DATA_DIR / "documents.db"


def ensure_directory(path: Path) -> Path:
    """Create a directory when missing and return the same path."""
    path.mkdir(parents=True, exist_ok=True)
    return path
