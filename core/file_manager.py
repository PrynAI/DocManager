"""Helpers for persisting uploaded PDF files to local storage."""

from datetime import datetime
from pathlib import Path

from core.paths import PDF_STORAGE_DIR, ensure_directory

class FileManager:
    """Save uploaded files under the repository's PDF storage folder."""

    def save_file(self, uploaded_file):
        """Persist a Streamlit uploaded file and return the saved path."""
        storage_dir = ensure_directory(PDF_STORAGE_DIR)

        # Prefixing the original name with a timestamp avoids collisions when
        # different uploads reuse the same filename, such as "notes.pdf".
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        original_name = Path(uploaded_file.name).name
        filename = f"{timestamp}_{original_name}"

        file_path = storage_dir / filename

        with file_path.open("wb") as f:
            f.write(uploaded_file.getbuffer())

        return str(file_path)
