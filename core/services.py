"""Service layer that orchestrates document upload, search, and reindexing."""

from datetime import datetime

from db.repository import DocumentRepository
from core.file_manager import FileManager
from core.indexer import DocumentIndexer
from core.thumbnail import ThumbnailGenerator
from core.reader import PDFReader
from core.models import Document

class DocumentService:
    """Coordinate file, indexing, reader, and repository operations."""

    def __init__(self):
        self.repo = DocumentRepository()
        self.file_manager = FileManager()
        self.indexer = DocumentIndexer()
        self.thumbnail_generator = ThumbnailGenerator()
        self.reader = PDFReader()

    def upload_document(self, uploaded_file, tags, description, lecture_date=None):
        """Run the full upload pipeline and return the number of saved chunks."""

        file_path = self.file_manager.save_file(uploaded_file)
        thumbnail_path = self.thumbnail_generator.generate_thumbnail(file_path)
        total_pages = self.thumbnail_generator.get_total_pages(file_path)
        self.reader.convert_pdf_to_images(file_path)

        # Chunk extraction happens after the PDF is on disk so both direct text
        # extraction and OCR can open the saved file path.
        chunks = self.indexer.extract_chunks(file_path)
        upload_date = datetime.now().strftime("%Y-%m-%d")

        doc = Document(
            id=None,
            name=uploaded_file.name,
            path=file_path,
            thumbnail_path=thumbnail_path,
            tags=tags,
            description=description,
            upload_date=upload_date,
            lecture_date=lecture_date,
            total_pages=total_pages
        )

        document_id = self.repo.add_document(doc)
        self.repo.add_document_chunks(document_id, chunks)
        return len(chunks)
    
    def search_documents(self, tag=None, date=None, content_query=None):
        """Search documents by metadata or indexed content."""
        return self.repo.search_documents(tag, date, content_query)

    def reindex_unindexed_documents(self):
        """Backfill chunk records for documents that predate indexing."""
        reindexed_count = 0

        for document in self.repo.get_documents_missing_chunks():
            chunks = self.indexer.extract_chunks(document.path)

            if not chunks:
                continue

            self.repo.replace_document_chunks(document.id, chunks)
            reindexed_count += 1

        return reindexed_count

    def get_all_documents(self):
        """Return every stored document for analytics and UI summaries."""
        return self.repo.get_all_documents()
