from typing import Optional


class Document:
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
    pass


class DocumentChunk:
    def __init__(self, page_number, chunk_index, text, word_count):
        self.page_number = page_number
        self.chunk_index = chunk_index
        self.text = text
        self.word_count = word_count


class SearchResult:
    def __init__(
        self,
        document: Document,
        matched_page: Optional[int] = None,
        snippet: Optional[str] = None,
    ):
        self.document = document
        self.matched_page = matched_page
        self.snippet = snippet
