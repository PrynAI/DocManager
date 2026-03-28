# upload document
# --> uploaded_file, tags, document, date
# --> uploaded_file --> test.pdf
# --> uploaded_file --> test.pdf --> thumbnail
# --> uploaded_file --> folder with the same name as pdf file --> test --> extract all images -> 0.jpg, 1.jpg
# --> uploaded_file -> total pages
# upload_date -> time, datetime

from datetime import datetime

from db.repository import DocumentRepository
from core.file_manager import FileManager
from core.indexer import DocumentIndexer
from core.thumbnail import ThumbnailGenerator
from core.reader import PDFReader
from core.models import Document

class DocumentService:
    def __init__(self):
        self.repo =DocumentRepository()
        self.file_manager = FileManager()
        self.indexer = DocumentIndexer()
        self.thumbnail_generator = ThumbnailGenerator()
        self.reader = PDFReader()

    def upload_document(self, uploaded_file, tags, description, lecture_date=None):

        # 1. Save file
        file_path = self.file_manager.save_file(uploaded_file)
        
        # 2. Generate thumbnail
        thumbnail_path = self.thumbnail_generator.generate_thumbnail(file_path)
        
        # 3. Get total pages
        total_pages = self.thumbnail_generator.get_total_pages(file_path)
        
        # 4. Convert to images
        self.reader.convert_pdf_to_images(file_path)
        # 5. create required variables : upload date

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

        # 6. Save to db
        document_id = self.repo.add_document(doc)
        self.repo.add_document_chunks(document_id, chunks)
        return len(chunks)
    
    def search_documents(self, tag=None, date=None, content_query=None):
        return self.repo.search_documents(tag, date, content_query)

    def reindex_unindexed_documents(self):
        reindexed_count = 0

        for document in self.repo.get_documents_missing_chunks():
            chunks = self.indexer.extract_chunks(document.path)

            if not chunks:
                continue

            self.repo.replace_document_chunks(document.id, chunks)
            reindexed_count += 1

        return reindexed_count
