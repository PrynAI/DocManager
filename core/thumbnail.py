from pathlib import Path

import pymupdf

from core.paths import THUMBNAIL_DIR, ensure_directory

class ThumbnailGenerator:

    def generate_thumbnail(self, pdf_path):
        doc = pymupdf.open(str(pdf_path))
        page = doc.load_page(0)
        pix = page.get_pixmap() # low resolution

        base_name = Path(pdf_path).with_suffix(".png").name
        # c://hello/user/a/a.pdf
        # a.pdf
        # a.png
        thumb_path = ensure_directory(THUMBNAIL_DIR) / base_name

        pix.save(str(thumb_path))

        doc.close()

        return str(thumb_path)
    
    def get_total_pages(self, pdf_path):
        doc = pymupdf.open(str(pdf_path))
        total = len(doc)
        doc.close()
        return total
