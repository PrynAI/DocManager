import pymupdf
from pathlib import Path

class PDFReader:
    def convert_pdf_to_images(self, pdf_path):
        pdf_path = Path(pdf_path)
        doc = pymupdf.open(str(pdf_path))

        # c://hello/user/a/a.pdf
        # a.pdf
        # .pdf --> '' -> a
        output_dir = pdf_path.with_suffix("")
        output_dir.mkdir(parents=True, exist_ok=True)

        image_paths = []

        for i in range(len(doc)):
            page = doc.load_page(i)
            matrix = pymupdf.Matrix(2,2)
            pix = page.get_pixmap(matrix=matrix)

            img_path = output_dir / f"page_{i:04d}.png"

            pix.save(str(img_path))

            image_paths.append(str(img_path))

        doc.close()

        return image_paths
