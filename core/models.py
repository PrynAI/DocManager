"""Simple models shared across services, repositories, and the UI."""

from typing import Optional


class Document:
    """Represents one uploaded PDF and its stored metadata."""

    def __init__(
        self,
        id,
        name,
        path,
        thumbnail_path,
        tags,
        description,
        upload_date,
        lecture_date,
        total_pages
    ):
        self.id = id
        self.name = name
        self.path = path
        self.thumbnail_path = thumbnail_path
        self.tags = tags
        self.description = description
        self.upload_date = upload_date
        self.lecture_date = lecture_date
        self.total_pages = total_pages


class DocumentRecord(Document):
    """Concrete database row type kept separate for future specialization."""
    pass


class DocumentChunk:
    """One searchable chunk of text extracted from a PDF page."""

    def __init__(self, page_number, chunk_index, text, word_count):
        self.page_number = page_number
        self.chunk_index = chunk_index
        self.text = text
        self.word_count = word_count


class SearchResult:
    """Search output containing the document plus match-specific context."""

    def __init__(
        self,
        document: Document,
        matched_page: Optional[int] = None,
        snippet: Optional[str] = None,
    ):
        self.document = document
        self.matched_page = matched_page
        self.snippet = snippet
