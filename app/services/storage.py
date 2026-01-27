"""
app/services/storage.py - File Storage Services

Handles storing and retrieving uploaded documents.
Currently uses local filesystem; can be swapped for S3 later.

File Structure:
uploads/{tenant_id}/{document_id}/original.{extension}
"""

from pathlib import Path
import shutil
from fastapi import UploadFile

# Base directory for all uploads (relative to project root)
UPLOAD_DIR = Path("uploads")

def get_file_extension(filename: str) -> str:
    """Extract file extension from filename (e.g., 'report.pdf' -> 'pdf')"""
    return filename.rsplit(".", 1)[-1] if "." in filename else ""

def save_file(tenant_id: str, document_id: str, file: UploadFile) -> str:
    """
    Save an uploaded file to local storage.

    Args:
        tenant_id: The organization's UUID
        document_id: The document's UUID
        file: FastAPI UploadFile object
    
    Returns:
        The file path where the file was saved (relative path)
    """
    # Build directory path: uploads/{tenant_id}/{document_id}/
    file_dir = UPLOAD_DIR / tenant_id / document_id
    file_dir.mkdir(parents=True, exist_ok=True)

    # Build full file path: uploads/{tenant_id}/{document_id}/original.pdf
    extension = get_file_extension(file.filename)
    file_path = file_dir / f"original.{extension}"

    # Write the file contents
    with open(file_path, "wb") as f:
        # Read content from UploadFile and write to disk
        content = file.file.read()
        f.write(content)
    
    # Return relative path as string (for storing in database)
    return str(file_path)

def delete_file(file_path: str) -> bool:
    """
    Delete a file and its parent directory.

    Args:
        file_path: Path to the file
    
    Returns:
        True if deleted, False if not found
    """
    path = Path(file_path)
    if path.exists():
        # Delete the entire document directory
        shutil.rmtree(path.parent)
        return True
    return False