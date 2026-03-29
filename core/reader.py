"""Convert PDFs into page images for the in-app reader."""

from pathlib import Path

import pymupdf

class PDFReader:
    """Generate per-page PNG files that Streamlit can render easily."""

    def convert_pdf_to_images(self, pdf_path):
        """Render each PDF page to an image and return the generated paths."""
        pdf_path = Path(pdf_path)
        doc = pymupdf.open(str(pdf_path))

        # The image folder sits next to the PDF and reuses the same base name.
        # Example: storage/pdfs/file.pdf -> storage/pdfs/file/page_0000.png
        output_dir = pdf_path.with_suffix("")
        output_dir.mkdir(parents=True, exist_ok=True)

        image_paths = []

        for i in range(len(doc)):
            page = doc.load_page(i)
            # Scale pages up so the reader images stay readable in the UI.
            matrix = pymupdf.Matrix(2, 2)
            pix = page.get_pixmap(matrix=matrix)

            img_path = output_dir / f"page_{i:04d}.png"

            pix.save(str(img_path))

            image_paths.append(str(img_path))

        doc.close()

        return image_paths
