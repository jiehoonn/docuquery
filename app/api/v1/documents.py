"""
app/api/v1/documents.py - Document Management Endpoints

This module provides endpoints for managing documents:
- POST /upload - Upload a new document
- GET / - List all documents for the current user's organization
- GET /{id} - Get details of a specific document
- DELETE /{id} - Delete a document

All endpoints require authentication and enforce tenant isolation -
users can only access documents belonging to their organization.
"""

import uuid
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.auth import get_current_user
from app.db.models import Document, User
from app.db.session import get_db
from app.services.processor import process_document
from app.services.qdrant import delete_document_vectors
from app.services.storage import delete_file, get_file_extension, save_file

# Create router - all routes will be prefixed with /documents
router = APIRouter(prefix="/documents", tags=["documents"])

# ============ Configuration ============

# Allowed file extensions for upload
ALLOWED_EXTENSIONS = {"pdf", "docx", "txt"}

# Maximum file size in bytes (10MB)
MAX_FILE_SIZE = 10 * 1024 * 1024


# ============ Schemas ============


class DocumentResponse(BaseModel):
    """Response schema for document data."""

    id: uuid.UUID
    title: Optional[str]
    file_path: str
    file_size_bytes: int
    status: str
    chunks_count: int
    created_at: datetime
    processed_at: Optional[datetime]
    error_message: Optional[str]

    class Config:
        # Allows Pydantic to read data from SQLAlchemy models
        from_attributes = True


class DocumentListResponse(BaseModel):
    """Response schema for listing documents."""

    documents: List[DocumentResponse]
    total: int


# ============ Helper Functions ============


def validate_file(file: UploadFile) -> None:
    """
    Validate uploaded file type and size.

    Args:
        file: The uploaded file

    Raises:
        HTTPException: If file type or size is invalid
    """
    # Check file extension
    extension = get_file_extension(file.filename).lower()
    if extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File type '{extension}' not allowed. Allowed types: {', '.join(ALLOWED_EXTENSIONS)}",
        )

    # Check file size (read content to get size, then reset)
    file.file.seek(0, 2)  # Seek to end
    size = file.file.tell()  # Get position (= file size)
    file.file.seek(0)  # Reset to beginning

    if size > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File too large. Maximum size is {MAX_FILE_SIZE // (1024 * 1024)}MB",
        )


# ============ Endpoints ============


@router.post("/upload", response_model=DocumentResponse)
async def upload_document(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Upload a new document.

    The document will be:
    1. Validated (file type and size)
    2. Saved to storage
    3. Recorded in the database with status 'queued'

    Later, a background worker will process the document
    (extract text, create chunks, generate embeddings).

    Args:
        file: The uploaded file (multipart/form-data)

    Returns:
        The created document record

    Allowed file types: pdf, docx, txt
    Maximum file size: 10MB
    """
    # 1. Validate file
    validate_file(file)

    # 2. Generate document ID
    document_id = uuid.uuid4()

    # 3. Get file size
    file.file.seek(0, 2)
    file_size = file.file.tell()
    file.file.seek(0)

    # 4. Save file to storage
    # Path will be: uploads/{tenant_id}/{document_id}/original.{ext}
    file_path = save_file(
        tenant_id=str(current_user.organization_id),
        document_id=str(document_id),
        file=file,
    )

    # 5. Create document record in database
    document = Document(
        id=document_id,
        tenant_id=current_user.organization_id,  # CRITICAL: tenant isolation
        title=file.filename,  # Use original filename as title
        file_path=file_path,
        file_size_bytes=file_size,
        status="queued",  # Will be processed by background worker
    )
    db.add(document)
    await db.commit()
    await db.refresh(document)  # Refresh to get any default values

    # 6. Process the document inline (extract text, chunk, embed, store in Qdrant)
    # TODO(cloud): Replace inline processing with async SQS + Lambda/ECS worker.
    #   - After creating the document record, send a message to SQS queue
    #     with the document_id and tenant_id
    #   - A Lambda function or ECS task picks up the message and runs
    #     process_document() asynchronously
    #   - The upload endpoint returns immediately with status="queued"
    #   - Client polls GET /documents/{id} to check processing status
    #   - Failed processing goes to a Dead Letter Queue (DLQ) for inspection
    await process_document(str(document.id), db)
    await db.refresh(document)

    return document


@router.get("", response_model=DocumentListResponse)
async def list_documents(
    current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    """
    List all documents for the current user's organization.

    Returns documents ordered by creation date (newest first).
    Only returns documents belonging to the user's organization
    (tenant isolation enforced).

    Returns:
        List of documents and total count
    """
    # CRITICAL: Always filter by tenant_id for multi-tenancy security
    result = await db.execute(
        select(Document)
        .where(Document.tenant_id == current_user.organization_id)
        .order_by(Document.created_at.desc())
    )
    documents = result.scalars().all()

    return DocumentListResponse(documents=documents, total=len(documents))


@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document(
    document_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get details of a specific document.

    Args:
        document_id: The UUID of the document

    Returns:
        The document details

    Raises:
        404: If document not found or belongs to different organization
    """
    # CRITICAL: Filter by both document_id AND tenant_id
    result = await db.execute(
        select(Document).where(
            Document.id == document_id,
            Document.tenant_id == current_user.organization_id,  # Tenant isolation
        )
    )
    document = result.scalar_one_or_none()

    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Document not found"
        )

    return document


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
    document_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Delete a document.

    This will:
    1. Delete vectors from Qdrant
    2. Delete the file from storage
    3. Delete the database record

    Args:
        document_id: The UUID of the document to delete

    Returns:
        204 No Content on success

    Raises:
        404: If document not found or belongs to different organization
    """
    # CRITICAL: Filter by both document_id AND tenant_id
    result = await db.execute(
        select(Document).where(
            Document.id == document_id,
            Document.tenant_id == current_user.organization_id,  # Tenant isolation
        )
    )
    document = result.scalar_one_or_none()

    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Document not found"
        )

    # Delete vectors from Qdrant (must happen before DB delete so we still have tenant_id)
    delete_document_vectors(
        tenant_id=str(document.tenant_id),
        document_id=str(document.id),
    )

    # Delete file from storage
    delete_file(document.file_path)

    # Delete from database
    await db.delete(document)
    await db.commit()

    # Return 204 No Content (no response body)
    return None
