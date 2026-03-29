Project Description

DocManager is a Streamlit-based PDF document manager for locally stored learning content. It helps users upload PDFs, store document metadata in SQLite, search by tags, lecture date, and full text, read documents page by page inside the app, and monitor basic usage analytics and reading progress.

Problem We Are Solving

When learning material is stored only as files on local folders, it becomes hard to:

- remember where a document is saved
- organize documents consistently
- find a PDF by tags or lecture date
- search inside PDF content for a keyword
- work with scanned PDFs that do not already contain a text layer
- understand how documents are being used inside the app

Current App Scope

The current codebase supports:

- uploading PDF documents only
- saving uploaded files locally
- saving document metadata in SQLite
- generating thumbnails for uploaded PDFs
- converting PDF pages into images for in-app reading
- full-text search inside PDF content
- OCR fallback for scanned or image-based PDFs
- searching by tags
- searching by lecture date
- reader-mode page navigation
- reading-progress tracking by unique pages viewed
- analytics for key app actions such as upload, search, open document, next page, previous page, and close reader
- resetting analytics data
- admin reset controls protected by `ADMIN_PASSWORD` in `.env`

Technology Stack

- Language: Python
- UI Framework: Streamlit
- Database: SQLite
- PDF Processing: PyMuPDF
- OCR Engine: Tesseract OCR
- Analytics Table Handling: Pandas
- Environment Configuration: python-dotenv
- Local Storage: filesystem-based storage under `storage/` and `data/`

Complete System Design

The application follows a local-first design. The Streamlit app runs as the presentation layer, uploaded PDFs and generated assets are stored on disk, and structured data is stored in SQLite.

System Overview

```text
User
  |
  v
Streamlit UI (app/main.py)
  |
  v
DocumentService / AnalyticsService
  |
  +--> FileManager ------> storage/pdfs/
  +--> ThumbnailGenerator -> storage/thumbnails/
  +--> PDFReader ---------> page images folder per PDF
  +--> DocumentIndexer ---> extracted text chunks
  |
  v
DocumentRepository / SQLite
  |
  +--> documents
  +--> document_chunks
  +--> document_chunks_fts
  +--> page_visits
  +--> app_visits
```

Core Components

- `app/main.py`: Streamlit entry point, session-state management, upload flow, search flow, reader mode, analytics UI, and admin reset controls
- `core/services.py`: orchestration layer for document upload, indexing, search, and reindexing
- `core/analytics.py`: analytics event recording and progress retrieval
- `core/file_manager.py`: PDF file saving
- `core/thumbnail.py`: thumbnail generation and page counting
- `core/reader.py`: PDF-to-image conversion for reader mode
- `core/indexer.py`: text extraction, OCR fallback, text normalization, and chunk creation
- `core/models.py`: shared models for documents, chunks, and search results
- `core/paths.py`: central path and directory helpers
- `db/database.py`: SQLite schema initialization and FTS setup
- `db/repository.py`: persistence and search queries

Storage Design

- PDF files are stored in `storage/pdfs/`
- generated thumbnails are stored in `storage/thumbnails/`
- page images for reader mode are stored in a folder derived from the PDF filename
- SQLite database is stored under `data/`

Database Design

The schema is separated by responsibility:

- `documents`: one row per uploaded PDF with metadata and file paths
- `document_chunks`: many rows per document containing extracted searchable text
- `document_chunks_fts`: SQLite FTS5 virtual table for full-text search
- `page_visits`: page-level reading activity used for progress tracking
- `app_visits`: app-level event tracking such as upload, search, open document, next page, previous page, and close reader

Main Runtime Flows

Upload Flow

1. User uploads a PDF from the Streamlit UI.
2. `DocumentService` saves the file through `FileManager`.
3. The app generates a thumbnail and reads total pages.
4. The PDF is converted into page images for reader mode.
5. `DocumentIndexer` extracts page text.
6. If direct extraction returns no text, OCR fallback is attempted.
7. Text is normalized and split into overlapping chunks.
8. Document metadata is written to `documents`.
9. Text chunks are written to `document_chunks`.

Search Flow

1. User searches by tag, lecture date, or full text.
2. Metadata-only search reads from `documents`.
3. Full-text search reads from `document_chunks_fts`.
4. If FTS is unavailable, the repository falls back to `LIKE` search on `document_chunks`.
5. Results return the document, matched page, and snippet.
6. Reader mode opens at the matched page for content-based search results.

Reader And Analytics Flow

1. User opens a document from search results.
2. The app loads page images from local storage.
3. Reader navigation updates Streamlit session state.
4. Each viewed page is written to `page_visits`.
5. App actions are written to `app_visits`.
6. The Analytics tab aggregates this data into usage charts and per-document progress.

Admin Reset Flow

1. `.env` is loaded at app startup.
2. If `ADMIN_PASSWORD` exists, admin reset controls are shown.
3. On successful password confirmation, the app deletes the SQLite database and generated storage folders.
4. Required directories are recreated and the database schema is initialized again.

Architecture

The project uses a layered architecture:

- Presentation layer: `app/main.py`
- Application layer: `core/services.py`, `core/analytics.py`
- Domain/model layer: `core/models.py`
- Infrastructure layer: `core/file_manager.py`, `core/thumbnail.py`, `core/reader.py`, `core/indexer.py`, `core/paths.py`
- Persistence layer: `db/database.py`, `db/repository.py`

Architecture Principles Used

- separation of concerns between UI, orchestration, infrastructure, and persistence
- local-first design with no external backend dependency
- repository pattern for database access
- chunk-based indexing so the same structure can later support semantic search
- session-state-driven UI flow in Streamlit
- environment-based protection for destructive admin actions

Current Limitations

- The app only supports PDFs.
- OCR quality depends on scan quality and handwriting clarity.
- Handwritten PDFs can still produce noisy text extraction results.
- Full-text search is implemented, but semantic search is not yet implemented.
- Analytics are basic product-usage and progress metrics, not AI analytics.

Future Work

- semantic search over indexed document chunks
- better search ranking and result grouping
- improved OCR quality handling for difficult handwritten PDFs
- richer analytics on reading behavior and document usage

How To Run

Prerequisites

- a Python virtual environment for the project
- project dependencies installed
- Tesseract OCR installed if you want searchable text from scanned or image-based PDFs

Install Dependencies

```bash
uv add -r requirements.txt
```

If you are using `uv`, you can also run:

```bash
uv sync
```

Optional Environment Setup

To enable the admin reset controls, create a `.env` file in the project root:

```env
ADMIN_PASSWORD=changeme
```

You can use `.env.example` as the starting point.

Windows OCR Setup

If you want OCR support for scanned PDFs, install Tesseract OCR on Windows. A common install path is:

`C:\Program Files\Tesseract-OCR`

If the `tesseract` command is not available in your terminal, set:

```powershell
$env:PATH = "C:\Program Files\Tesseract-OCR;" + $env:PATH
$env:TESSDATA_PREFIX = "C:\Program Files\Tesseract-OCR\tessdata"
```

Run The App

On Windows:

```powershell
.venv\Scripts\activate
streamlit run app/main.py
```

Notes

- printed or digital PDFs usually work better for full-text search than handwritten PDFs
- if OCR is not available, scanned PDFs can still be uploaded, but searchable text may not be extracted
- the Analytics tab becomes more useful after you upload, search, open documents, and navigate pages in reader mode
