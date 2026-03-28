Project Description

This project solves a practical problem: learning PDFs such as notes, books, resumes, and study material are often scattered across local folders, which makes them difficult to organize and search later.

The current MVP is a Streamlit-based PDF document manager that lets users upload PDF files, store metadata, generate thumbnails, open page images in a reader view, and search documents in multiple ways.

Problem We Are Solving

When learning content is stored only as files on local storage, it becomes hard to:

- remember where a document is saved
- find documents by tag or lecture date
- search inside PDF content for a keyword
- work with scanned PDFs that do not already contain a text layer

Current MVP Scope

The code currently supports:

- uploading PDF documents only
- saving document metadata in SQLite
- searching by tags
- searching by lecture date
- full-text search inside PDF content
- OCR-based text extraction fallback for scanned or image-based PDFs
- thumbnail generation for uploaded PDFs
- page-by-page reading view inside the app

What The App Does Today

1. Upload a PDF.
2. Save the file locally.
3. Generate a thumbnail.
4. Convert PDF pages into images for reader mode.
5. Extract searchable text from the PDF.
6. If direct text extraction fails, try OCR for scanned PDFs.
7. Store document metadata and text chunks in SQLite.
8. Let the user search and open matching documents.

Current Limitations

- The app only supports PDFs.
- OCR quality depends on scan quality and handwriting clarity.
- Full-text search is implemented, but semantic search is not yet implemented.
- The Analytics tab is reserved for future work and is not implemented yet.

Future Work

- semantic search over indexed document chunks
- AI-based analytics on uploaded learning documents
- better grouping and ranking of search results
- improved OCR quality handling for difficult handwritten PDFs

How To Run

Prerequisites

- Python virtual environment for the project
- project dependencies installed
- Tesseract OCR installed if you want searchable text from scanned or image-based PDFs

Install Dependencies

```bash
pip install -r requirements.txt
```

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

- Printed or digital PDFs usually work better for full-text search than handwritten PDFs.
- If OCR is not available, scanned PDFs can still be uploaded, but searchable text may not be extracted.
