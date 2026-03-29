"""Thumbnail generation helpers for uploaded PDFs."""

from pathlib import Path

import pymupdf

from core.paths import THUMBNAIL_DIR, ensure_directory

class ThumbnailGenerator:
    """Create preview thumbnails and read PDF page counts."""

    def generate_thumbnail(self, pdf_path):
        """Render the first page of a PDF into a PNG thumbnail."""
        doc = pymupdf.open(str(pdf_path))
        page = doc.load_page(0)
        # Default resolution is enough for a small preview and keeps
        # thumbnail generation fast during upload.
        pix = page.get_pixmap()

        base_name = Path(pdf_path).with_suffix(".png").name
        thumb_path = ensure_directory(THUMBNAIL_DIR) / base_name

        pix.save(str(thumb_path))

        doc.close()

        return str(thumb_path)
    
    def get_total_pages(self, pdf_path):
        """Return the total number of pages in the PDF."""
        doc = pymupdf.open(str(pdf_path))
        total = len(doc)
        doc.close()
        return total
