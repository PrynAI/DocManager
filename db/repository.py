"""Repository layer for document storage and search queries."""

import re
import sqlite3

from db.database import get_connection
from core.models import Document, DocumentRecord, SearchResult

class DocumentRepository:
    """Encapsulate all direct SQLite reads and writes for documents."""
    
    def add_document(self, doc: Document):
        """Insert one document metadata row and return its database id."""
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("""
        INSERT INTO documents (
            name, path, thumbnail_path, tags, description,
            upload_date, lecture_date, total_pages
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            doc.name,
            doc.path,
            doc.thumbnail_path,
            doc.tags,
            doc.description,
            doc.upload_date,
            doc.lecture_date,
            doc.total_pages
        ))

        conn.commit()
        document_id = cursor.lastrowid
        conn.close()
        return document_id

    def add_document_chunks(self, document_id, chunks):
        """Insert all searchable text chunks belonging to one document."""
        if not chunks:
            return

        conn = get_connection()
        cursor = conn.cursor()

        cursor.executemany("""
        INSERT INTO document_chunks (
            document_id, page_number, chunk_index, chunk_text, word_count
        )
        VALUES (?, ?, ?, ?, ?)
        """, [
            (
                document_id,
                chunk.page_number,
                chunk.chunk_index,
                chunk.text,
                chunk.word_count,
            )
            for chunk in chunks
        ])

        conn.commit()
        conn.close()

    def replace_document_chunks(self, document_id, chunks):
        """Replace all saved chunks for a document during reindexing."""
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM document_chunks WHERE document_id = ?", (document_id,))

        if chunks:
            cursor.executemany("""
            INSERT INTO document_chunks (
                document_id, page_number, chunk_index, chunk_text, word_count
            )
            VALUES (?, ?, ?, ?, ?)
            """, [
                (
                    document_id,
                    chunk.page_number,
                    chunk.chunk_index,
                    chunk.text,
                    chunk.word_count,
                )
                for chunk in chunks
            ])

        conn.commit()
        conn.close()

    def get_documents_missing_chunks(self):
        """Return documents that exist in metadata storage but are not indexed."""
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("""
        SELECT d.*
        FROM documents d
        LEFT JOIN document_chunks c ON c.document_id = d.id
        WHERE c.id IS NULL
        ORDER BY d.id
        """)

        rows = cursor.fetchall()
        conn.close()

        return [DocumentRecord(*row) for row in rows]

    def get_all_documents(self):
        """Return every stored document ordered by most recent upload."""
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM documents ORDER BY upload_date DESC, id DESC")
        rows = cursor.fetchall()
        conn.close()

        return [Document(*row) for row in rows]

    def search_documents(self, tag=None, date=None, content_query=None):
        """Route to metadata search or content search depending on inputs."""
        if content_query:
            return self._search_document_content(tag=tag, date=date, content_query=content_query)

        return self._search_document_metadata(tag=tag, date=date)

    def _search_document_metadata(self, tag=None, date=None):
        """Search only the document table using tag/date filters."""
        conn = get_connection()
        cursor = conn.cursor()

        query = "SELECT * FROM documents"
        conditions = []
        params = []

        if tag:
            conditions.append("tags LIKE ?")
            params.append(f"%{tag}%")

        if date:
            conditions.append("lecture_date = ?")
            params.append(date)
        
        if conditions:
            # Metadata search keeps the current UI behavior: if both filters are
            # provided, a match on either tag or date is returned.
            query += " WHERE " + " OR ".join(conditions)
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()

        return [SearchResult(document=Document(*row)) for row in rows]

    def _search_document_content(self, tag=None, date=None, content_query=None):
        """Search indexed chunk text, falling back when FTS5 is unavailable."""
        fts_query = self._build_fts_query(content_query)

        if not fts_query:
            return self._search_document_metadata(tag=tag, date=date)

        try:
            return self._search_with_fts(tag=tag, date=date, fts_query=fts_query)
        except sqlite3.OperationalError:
            return self._search_with_like(tag=tag, date=date, content_query=content_query)

    def _search_with_fts(self, tag=None, date=None, fts_query=None):
        """Use SQLite FTS5 to return ranked content matches."""
        conn = get_connection()
        cursor = conn.cursor()

        conditions = ["document_chunks_fts MATCH ?"]
        params = [fts_query]

        if tag:
            conditions.append("d.tags LIKE ?")
            params.append(f"%{tag}%")

        if date:
            conditions.append("d.lecture_date = ?")
            params.append(date)

        query = """
        SELECT
            d.id,
            d.name,
            d.path,
            d.thumbnail_path,
            d.tags,
            d.description,
            d.upload_date,
            d.lecture_date,
            d.total_pages,
            c.page_number,
            snippet(document_chunks_fts, 0, '[', ']', '...', 18) AS snippet_text
        FROM document_chunks_fts
        JOIN document_chunks c ON c.id = document_chunks_fts.rowid
        JOIN documents d ON d.id = c.document_id
        WHERE
        """ + " AND ".join(conditions) + """
        ORDER BY bm25(document_chunks_fts), d.id, c.page_number, c.chunk_index
        LIMIT 50
        """

        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()

        return [self._build_search_result(row) for row in rows]

    def _search_with_like(self, tag=None, date=None, content_query=None):
        """Fallback content search for SQLite builds without FTS5 support."""
        conn = get_connection()
        cursor = conn.cursor()

        conditions = ["c.chunk_text LIKE ?"]
        params = [f"%{content_query}%"]

        if tag:
            conditions.append("d.tags LIKE ?")
            params.append(f"%{tag}%")

        if date:
            conditions.append("d.lecture_date = ?")
            params.append(date)

        query = """
        SELECT
            d.id,
            d.name,
            d.path,
            d.thumbnail_path,
            d.tags,
            d.description,
            d.upload_date,
            d.lecture_date,
            d.total_pages,
            c.page_number,
            c.chunk_text
        FROM document_chunks c
        JOIN documents d ON d.id = c.document_id
        WHERE
        """ + " AND ".join(conditions) + """
        ORDER BY d.id, c.page_number, c.chunk_index
        LIMIT 50
        """

        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()

        return [
            self._build_search_result(
                row[:-1] + (self._build_snippet(row[-1], content_query),)
            )
            for row in rows
        ]

    def _build_search_result(self, row):
        """Convert a mixed SQL row into the UI-facing SearchResult model."""
        document = Document(*row[:9])
        return SearchResult(
            document=document,
            matched_page=row[9],
            snippet=row[10],
        )

    def _build_fts_query(self, content_query):
        """Normalize free text into a simple FTS token query."""
        terms = re.findall(r"\w+", content_query.lower())
        return " ".join(terms)

    def _build_snippet(self, text, content_query, radius=120):
        """Return a short excerpt around the matched text for display."""
        normalized_text = " ".join(text.split())
        lower_text = normalized_text.lower()
        lower_query = content_query.lower()
        match_index = lower_text.find(lower_query)

        if match_index == -1:
            snippet = normalized_text[: radius * 2]
            return snippet + ("..." if len(normalized_text) > len(snippet) else "")

        start = max(0, match_index - radius)
        end = min(len(normalized_text), match_index + len(content_query) + radius)

        prefix = "..." if start > 0 else ""
        suffix = "..." if end < len(normalized_text) else ""

        return prefix + normalized_text[start:end] + suffix

        
