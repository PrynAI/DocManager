import sqlite3

from core.paths import DATA_DIR, DB_PATH, ensure_directory

def get_connection():
    ensure_directory(DATA_DIR)
    return sqlite3.connect(str(DB_PATH))

def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    # Document table - Schema
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

    try:
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
    print("DB operation successfull.")
    conn.close()
