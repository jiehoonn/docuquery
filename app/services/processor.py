"""
app/services/processor.py - Document Processing Orchestrator

Coordinates the entire document processing pipeline:
1. Extract text from document
2. Chunk text into smaller pieces
3. Generate embeddings for each chunk
4. Store embeddings in Qdrant
5. Update document status

Pipeline: Extract Text → Chunk → Embed → Store in Qdrant
          ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
                        (this file orchestrates all)

This processor is designed to be called:
- Synchronously for testing/simple cases
- By a background worker (SQS + Lambda) in production

Document status flow:
    queued → processing → ready (success)
                       → failed (error)
"""

from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.models import Document
from app.services.text_extractor import extract_text
from app.services.chunker import chunk_text
from app.services.embeddings import generate_embeddings
from app.services.qdrant import store_embeddings, delete_document_vectors


async def process_document(document_id: str, db: AsyncSession) -> bool:
    """
    Process a single document through the RAG pipeline.

    This function:
    1. Fetches the document from the database
    2. Extracts text from the file
    3. Chunks the text
    4. Generates embeddings
    5. Stores embeddings in Qdrant
    6. Updates document status to 'ready' or 'failed'

    Args:
        document_id: UUID of the document to process
        db: Database session

    Returns:
        True if processing succeeded, False otherwise

    Example:
        async with async_session() as db:
            success = await process_document("doc-uuid-here", db)
    """
    # 1. Fetch document from database
    result = await db.execute(
        select(Document).where(Document.id == document_id)
    )
    document = result.scalar_one_or_none()

    if not document:
        print(f"Document {document_id} not found")
        return False

    # Update status to processing
    document.status = "processing"
    await db.commit()

    try:
        # 2. Extract text from file
        print(f"Extracting text from {document.file_path}...")
        text = extract_text(document.file_path)

        if not text or not text.strip():
            raise ValueError("No text could be extracted from document")

        print(f"Extracted {len(text)} characters")

        # 3. Chunk the text
        print("Chunking text...")
        chunks = chunk_text(text, chunk_size=512, overlap=50)

        if not chunks:
            raise ValueError("No chunks generated from text")

        print(f"Created {len(chunks)} chunks")

        # 4. Generate embeddings
        print("Generating embeddings...")
        embeddings = generate_embeddings(chunks)
        print(f"Generated {len(embeddings)} embeddings")

        # 5. Store in Qdrant
        print("Storing in Qdrant...")
        store_embeddings(
            tenant_id=str(document.tenant_id),
            document_id=str(document.id),
            chunks=chunks,
            embeddings=embeddings,
        )
        print("Stored in Qdrant successfully")

        # 6. Update document status to ready
        document.status = "ready"
        document.chunks_count = len(chunks)
        document.processed_at = datetime.utcnow()
        document.error_message = None
        await db.commit()

        print(f"Document {document_id} processed successfully!")
        return True

    except Exception as e:
        # Processing failed - update status and store error
        print(f"Error processing document {document_id}: {str(e)}")

        document.status = "failed"
        document.error_message = str(e)[:1000]  # Truncate long errors
        document.processed_at = datetime.utcnow()
        await db.commit()

        return False


async def reprocess_document(document_id: str, db: AsyncSession) -> bool:
    """
    Reprocess a document (e.g., after a failed attempt or to update embeddings).

    This will:
    1. Delete existing vectors from Qdrant
    2. Process the document again

    Args:
        document_id: UUID of the document to reprocess
        db: Database session

    Returns:
        True if reprocessing succeeded, False otherwise
    """
    # Fetch document to get tenant_id
    result = await db.execute(
        select(Document).where(Document.id == document_id)
    )
    document = result.scalar_one_or_none()

    if not document:
        print(f"Document {document_id} not found")
        return False

    # Delete existing vectors
    print(f"Deleting existing vectors for document {document_id}...")
    delete_document_vectors(
        tenant_id=str(document.tenant_id),
        document_id=str(document.id),
    )

    # Reset document status
    document.status = "queued"
    document.chunks_count = 0
    document.processed_at = None
    document.error_message = None
    await db.commit()

    # Process again
    return await process_document(document_id, db)


async def process_all_queued(db: AsyncSession) -> dict:
    """
    Process all documents with status 'queued'.

    Useful for:
    - Batch processing
    - Recovery after system restart
    - Development/testing

    Args:
        db: Database session

    Returns:
        Dict with counts: {"processed": N, "failed": M, "total": N+M}
    """
    # Find all queued documents
    result = await db.execute(
        select(Document).where(Document.status == "queued")
    )
    documents = result.scalars().all()

    processed = 0
    failed = 0

    for doc in documents:
        success = await process_document(str(doc.id), db)
        if success:
            processed += 1
        else:
            failed += 1

    return {
        "processed": processed,
        "failed": failed,
        "total": processed + failed,
    }
