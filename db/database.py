"""SQLite schema creation and connection helpers."""

import sqlite3

from core.paths import DATA_DIR, DB_PATH, ensure_directory

def get_connection():
    """Return a connection to the app database, creating the data dir first."""
    ensure_directory(DATA_DIR)
    return sqlite3.connect(str(DB_PATH))

def init_db():
    """Create application tables, indexes, and FTS helpers when missing."""
    conn = get_connection()
    cursor = conn.cursor()

    # Core document metadata.
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS documents (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        path TEXT,
        thumbnail_path TEXT,
        tags TEXT,
        description TEXT,
        upload_date TEXT,
        lecture_date TEXT,
        total_pages INTEGER
        )
    """
    )

    # Searchable text chunks extracted from document pages.
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS document_chunks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        document_id INTEGER NOT NULL,
        page_number INTEGER NOT NULL,
        chunk_index INTEGER NOT NULL,
        chunk_text TEXT NOT NULL,
        word_count INTEGER NOT NULL,
        FOREIGN KEY (document_id) REFERENCES documents(id)
        )
    """
    )

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_document_chunks_document_id
        ON document_chunks(document_id)
    """
    )

    cursor.execute("""
        CREATE UNIQUE INDEX IF NOT EXISTS idx_document_chunks_unique_chunk
        ON document_chunks(document_id, page_number, chunk_index)
    """
    )

    # Reader progress analytics.
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS page_visits (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        document_id INTEGER NOT NULL,
        page_number INTEGER NOT NULL,
        timestamp TEXT NOT NULL,
        FOREIGN KEY (document_id) REFERENCES documents(id)
        )
    """
    )

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_page_visits_document_page
        ON page_visits(document_id, page_number)
    """
    )

    # App-level clickstream style events.
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS app_visits (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        event_type TEXT NOT NULL,
        timestamp TEXT NOT NULL
        )
    """
    )

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_app_visits_event_type
        ON app_visits(event_type)
    """
    )

    try:
        # FTS5 accelerates keyword search over extracted chunk text.
        cursor.execute("""
            CREATE VIRTUAL TABLE IF NOT EXISTS document_chunks_fts
            USING fts5(chunk_text, content='document_chunks', content_rowid='id')
        """
        )

        cursor.execute("""
            CREATE TRIGGER IF NOT EXISTS document_chunks_ai AFTER INSERT ON document_chunks
            BEGIN
                INSERT INTO document_chunks_fts(rowid, chunk_text)
                VALUES (new.id, new.chunk_text);
            END;
        """
        )

        cursor.execute("""
            CREATE TRIGGER IF NOT EXISTS document_chunks_ad AFTER DELETE ON document_chunks
            BEGIN
                INSERT INTO document_chunks_fts(document_chunks_fts, rowid, chunk_text)
                VALUES ('delete', old.id, old.chunk_text);
            END;
        """
        )

        cursor.execute("""
            CREATE TRIGGER IF NOT EXISTS document_chunks_au AFTER UPDATE ON document_chunks
            BEGIN
                INSERT INTO document_chunks_fts(document_chunks_fts, rowid, chunk_text)
                VALUES ('delete', old.id, old.chunk_text);
                INSERT INTO document_chunks_fts(rowid, chunk_text)
                VALUES (new.id, new.chunk_text);
            END;
        """
        )

        cursor.execute("""
            INSERT INTO document_chunks_fts(document_chunks_fts)
            VALUES ('rebuild')
        """
        )
    except sqlite3.OperationalError:
        # Fallback search logic in the repository uses LIKE when FTS5
        # is unavailable in the local SQLite build.
        pass

    conn.commit()
    conn.close()
