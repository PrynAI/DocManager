from datetime import datetime
from pathlib import Path

from core.paths import PDF_STORAGE_DIR, ensure_directory

class FileManager:

    def save_file(self, uploaded_file):
        storage_dir = ensure_directory(PDF_STORAGE_DIR)

        # Generate unique filename
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        original_name = Path(uploaded_file.name).name
        filename = f"{timestamp}_{original_name}"

        file_path = storage_dir / filename

        # Save file
        with file_path.open("wb") as f:
            f.write(uploaded_file.getbuffer())

        return str(file_path)
