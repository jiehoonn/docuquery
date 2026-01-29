"""
app/services/qdrant.py - Vector Database Service

Handles storing and searching document embeddings in Qdrant.
This is the fourth step in the document processing pipeline.

Pipeline: Extract Text → Chunk → Embed → Store in Qdrant
                                         ^^^^^^^^^^^^^^^^
                                           (this file)

What is Qdrant?
    Qdrant is a vector database optimized for similarity search.
    It stores vectors (embeddings) with metadata and can quickly
    find the most similar vectors to a query.

Multi-tenancy approach:
    Each tenant (organization) gets their own collection.
    Collection naming: tenant_{tenant_id}

    This ensures complete data isolation - one tenant can never
    accidentally (or maliciously) access another tenant's data.

Typical usage:
    1. Document uploaded → chunks embedded → store_embeddings()
    2. User asks question → embed question → search_similar()
    3. Document deleted → delete_document_vectors()
"""

from qdrant_client import QdrantClient
from qdrant_client.models import (
    VectorParams,
    Distance,
    PointStruct,
    Filter,
    FieldCondition,
    MatchValue,
)
import uuid

from app.core.config import settings


# ============ Client Connection ============

def get_client() -> QdrantClient:
    """
    Get a Qdrant client connection.

    Returns:
        QdrantClient connected to the configured Qdrant instance

    Note:
        In production, you might want to use connection pooling
        or a singleton pattern. For simplicity, we create a new
        client for each operation.
    """
    return QdrantClient(
        host=settings.qdrant_host,
        port=settings.qdrant_port,
    )


def get_collection_name(tenant_id: str) -> str:
    """
    Generate the collection name for a tenant.

    Args:
        tenant_id: The organization's UUID

    Returns:
        Collection name in format: tenant_{tenant_id}
    """
    return f"tenant_{tenant_id}"


# ============ Collection Management ============

def ensure_collection(tenant_id: str) -> None:
    """
    Create a collection for a tenant if it doesn't exist.

    Collections are like tables in a traditional database.
    Each tenant gets their own collection for data isolation.

    Args:
        tenant_id: The organization's UUID

    Note:
        Vector size is 384 to match the all-MiniLM-L6-v2 model.
        We use cosine distance for similarity (most common for text).
    """
    client = get_client()
    collection_name = get_collection_name(tenant_id)

    # Check if collection already exists
    collections = client.get_collections().collections
    collection_names = [c.name for c in collections]

    if collection_name not in collection_names:
        # Create new collection
        client.create_collection(
            collection_name=collection_name,
            vectors_config=VectorParams(
                size=384,  # all-MiniLM-L6-v2 produces 384-dimensional vectors
                distance=Distance.COSINE,  # Cosine similarity for text
            ),
        )


def delete_collection(tenant_id: str) -> None:
    """
    Delete a tenant's entire collection.

    Use with caution - this deletes ALL vectors for a tenant.

    Args:
        tenant_id: The organization's UUID
    """
    client = get_client()
    collection_name = get_collection_name(tenant_id)

    try:
        client.delete_collection(collection_name=collection_name)
    except Exception:
        # Collection might not exist, that's okay
        pass


# ============ Vector Operations ============

def store_embeddings(
    tenant_id: str,
    document_id: str,
    chunks: list[str],
    embeddings: list[list[float]],
) -> None:
    """
    Store chunk embeddings for a document.

    Each chunk becomes a "point" in Qdrant with:
    - A unique ID
    - The embedding vector
    - Metadata (payload) for filtering and retrieval

    Args:
        tenant_id: The organization's UUID
        document_id: The document's UUID
        chunks: List of text chunks
        embeddings: List of embedding vectors (same length as chunks)

    Example:
        store_embeddings(
            tenant_id="org-123",
            document_id="doc-456",
            chunks=["First chunk text", "Second chunk text"],
            embeddings=[[0.1, 0.2, ...], [0.3, 0.4, ...]]
        )
    """
    # Ensure collection exists
    ensure_collection(tenant_id)

    client = get_client()
    collection_name = get_collection_name(tenant_id)

    # Create points (vector + metadata) for each chunk
    points = []
    for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
        point = PointStruct(
            id=str(uuid.uuid4()),  # Unique ID for this point
            vector=embedding,
            payload={
                "document_id": document_id,
                "chunk_index": i,
                "text": chunk,  # Store the original text for retrieval
            },
        )
        points.append(point)

    # Batch upsert all points
    client.upsert(
        collection_name=collection_name,
        points=points,
    )


def search_similar(
    tenant_id: str,
    query_embedding: list[float],
    top_k: int = 5,
    document_ids: list[str] | None = None,
) -> list[dict]:
    """
    Find the most similar chunks to a query.

    This is the core of the RAG search - given a query embedding,
    find the chunks that are most semantically similar.

    Args:
        tenant_id: The organization's UUID
        query_embedding: The embedded query vector (384 dimensions)
        top_k: Number of results to return (default: 5)
        document_ids: Optional list of document IDs to filter by

    Returns:
        List of results, each containing:
        - score: Similarity score (0-1, higher is more similar)
        - document_id: Which document this chunk is from
        - chunk_index: Position of chunk in the document
        - text: The actual chunk text

    Example:
        results = search_similar(
            tenant_id="org-123",
            query_embedding=[0.1, 0.2, ...],
            top_k=5
        )
        for r in results:
            print(f"Score: {r['score']}, Text: {r['text'][:100]}...")
    """
    client = get_client()
    collection_name = get_collection_name(tenant_id)

    # Check if collection exists
    collections = client.get_collections().collections
    collection_names = [c.name for c in collections]

    if collection_name not in collection_names:
        # No documents uploaded yet for this tenant
        return []

    # Build filter if document_ids specified
    query_filter = None
    if document_ids:
        query_filter = Filter(
            must=[
                FieldCondition(
                    key="document_id",
                    match=MatchValue(value=doc_id),
                )
                for doc_id in document_ids
            ]
        )

    # Search for similar vectors
    # Note: qdrant-client v1.12+ renamed search() to query_points()
    results = client.query_points(
        collection_name=collection_name,
        query=query_embedding,
        limit=top_k,
        query_filter=query_filter,
        with_payload=True,  # Include metadata in results
    )

    # Format results (query_points returns a QueryResponse with .points list)
    return [
        {
            "score": hit.score,
            "document_id": hit.payload["document_id"],
            "chunk_index": hit.payload["chunk_index"],
            "text": hit.payload["text"],
        }
        for hit in results.points
    ]


def delete_document_vectors(tenant_id: str, document_id: str) -> None:
    """
    Delete all vectors for a specific document.

    Called when a document is deleted to clean up its vectors.

    Args:
        tenant_id: The organization's UUID
        document_id: The document's UUID
    """
    client = get_client()
    collection_name = get_collection_name(tenant_id)

    # Check if collection exists
    collections = client.get_collections().collections
    collection_names = [c.name for c in collections]

    if collection_name not in collection_names:
        return  # Nothing to delete

    # Delete points where document_id matches
    client.delete(
        collection_name=collection_name,
        points_selector=Filter(
            must=[
                FieldCondition(
                    key="document_id",
                    match=MatchValue(value=document_id),
                )
            ]
        ),
    )
