"""
app/services/storage.py - File Storage Service

Handles storing and retrieving uploaded documents.
Currently uses local filesystem for development.

File structure (mirrors planned S3 layout):
    uploads/{tenant_id}/{document_id}/original.{extension}

This tenant-namespaced path structure ensures:
    - Complete file isolation between organizations
    - Easy migration to S3 (same path becomes the S3 key)
    - Simple cleanup when deleting a document

TODO(cloud): Replace local filesystem with AWS S3.
    - Use boto3 S3 client for upload/download/delete
    - S3 bucket: docuquery-documents (or per-environment)
    - S3 key format: {tenant_id}/{document_id}/original.{ext}
    - Enable server-side encryption (SSE-S3)
    - Set lifecycle rules for cost optimization (e.g., move to
      S3 Infrequent Access after 90 days)
    - The text_extractor.py will need updating to read from S3
      instead of local filesystem (download to /tmp first)
"""

import shutil
from pathlib import Path

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
