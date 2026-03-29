"""Text extraction and chunking helpers for full-text search."""

import os
import re
from pathlib import Path
from typing import List

import pymupdf

from core.models import DocumentChunk


class DocumentIndexer:
    """Extract normalized text chunks from PDFs, with OCR as fallback."""

    # Small overlapping chunks work well for FTS now and can be reused later
    # when embedding-based semantic search is added.
    CHUNK_SIZE_WORDS = 160
    CHUNK_OVERLAP_WORDS = 40

    def extract_chunks(self, pdf_path: str) -> List[DocumentChunk]:
        """Extract searchable chunks from every page of a PDF."""
        doc = pymupdf.open(str(pdf_path))
        chunks: List[DocumentChunk] = []

        try:
            for page_number in range(len(doc)):
                page = doc.load_page(page_number)
                page_text = self._extract_page_text(page)

                if not page_text:
                    continue

                page_chunks = self._chunk_page_text(
                    page_text=page_text,
                    page_number=page_number + 1,
                )
                chunks.extend(page_chunks)
        finally:
            doc.close()

        return chunks

    def _extract_page_text(self, page: pymupdf.Page) -> str:
        """Read page text directly, then fall back to OCR when needed."""
        page_text = self._normalize_text(page.get_text("text"))

        if page_text:
            return page_text

        try:
            self._ensure_ocr_environment()
            # OCR is only attempted when the page has no embedded text layer.
            text_page = page.get_textpage_ocr(language="eng", dpi=300, full=True)
            return self._normalize_text(page.get_text("text", textpage=text_page))
        except RuntimeError:
            return ""

    def _chunk_page_text(self, page_text: str, page_number: int) -> List[DocumentChunk]:
        """Split page text into overlapping windows for better retrieval."""
        words = page_text.split()

        if not words:
            return []

        chunk_size = self.CHUNK_SIZE_WORDS
        overlap = self.CHUNK_OVERLAP_WORDS
        step = max(1, chunk_size - overlap)

        chunks: List[DocumentChunk] = []
        chunk_index = 0

        for start in range(0, len(words), step):
            chunk_words = words[start:start + chunk_size]

            if not chunk_words:
                continue

            chunk_text = " ".join(chunk_words).strip()

            if not chunk_text:
                continue

            chunks.append(
                DocumentChunk(
                    page_number=page_number,
                    chunk_index=chunk_index,
                    text=chunk_text,
                    word_count=len(chunk_words),
                )
            )
            chunk_index += 1

            if start + chunk_size >= len(words):
                break

        return chunks

    def _normalize_text(self, text: str) -> str:
        """Collapse noisy whitespace and remove null characters."""
        text = text.replace("\x00", " ")
        text = re.sub(r"\s+", " ", text)
        return text.strip()

    def _ensure_ocr_environment(self) -> None:
        """Populate OCR-related environment variables when possible."""
        if os.environ.get("TESSDATA_PREFIX"):
            return

        candidate_dirs = [
            Path("/usr/share/tesseract-ocr/5/tessdata"),
            Path("/usr/share/tesseract-ocr/4.00/tessdata"),
            Path("/usr/share/tessdata"),
            Path(r"C:\Program Files\Tesseract-OCR\tessdata"),
            Path(r"C:\Program Files (x86)\Tesseract-OCR\tessdata"),
        ]

        for tessdata_dir in candidate_dirs:
            if tessdata_dir.exists():
                os.environ["TESSDATA_PREFIX"] = str(tessdata_dir)

                # PyMuPDF's OCR support relies on the Tesseract binary being
                # reachable from PATH in addition to the tessdata folder.
                tesseract_bin = tessdata_dir.parent
                path_entries = os.environ.get("PATH", "").split(os.pathsep)
                if str(tesseract_bin) not in path_entries:
                    os.environ["PATH"] = str(tesseract_bin) + os.pathsep + os.environ.get("PATH", "")
                return
