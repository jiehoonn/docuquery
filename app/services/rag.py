"""
app/services/rag.py - RAG (Retrieval-Augmented Generation) Orchestrator

This is the brain of the query system. It orchestrates the full RAG pipeline:
1. Check Redis cache for a previously answered identical query
2. Generate embedding for the user's question
3. Search Qdrant for semantically similar document chunks
4. Send chunks + question to the LLM for answer generation
5. Cache the result for future identical queries
6. Return the answer with source citations

Query flow (this file orchestrates all steps):

    User Question
         │
         ▼
    ┌─ Cache Hit? ──── YES ──→ Return cached answer (fast, free)
    │      │
    │     NO
    │      │
    │      ▼
    │   Embed Question (sentence-transformers)
    │      │
    │      ▼
    │   Search Qdrant (find similar chunks)
    │      │
    │      ▼
    │   Generate Answer (Gemini LLM)
    │      │
    │      ▼
    │   Cache Result (Redis, TTL: 1 hour)
    │      │
    └──────▼
       Return Response

Why separate this from the API endpoint?
    - The endpoint handles HTTP concerns (auth, validation, response format)
    - This service handles business logic (the RAG pipeline)
    - This makes it easier to test, reuse, and swap components
"""

from app.services.cache import cache_answer, get_cached_answer
from app.services.embeddings import generate_embedding
from app.services.llm import generate_answer
from app.services.qdrant import search_similar


async def query_documents(
    tenant_id: str, question: str, document_ids: list[str] | None = None
) -> dict:
    """
    Execute the full RAG query pipeline.

    This is the main entry point for answering user questions against
    their uploaded documents. It handles caching, retrieval, and generation.

    Args:
        tenant_id: The organization's UUID (for tenant isolation)
        question: The user's natural language question
        document_ids: Optional list of specific document UUIDs to search.
                     If None, searches all of the tenant's documents.

    Returns:
        dict with keys:
            - answer (str): The LLM-generated answer with citations
            - sources (list): Document chunks used, each containing:
                - score: Similarity score (0-1)
                - document_id: Which document the chunk is from
                - chunk_index: Position in the original document
                - text: The actual chunk text
            - cached (bool): Whether this answer came from cache

    Example:
        result = await query_documents("org-123", "What is the return policy?")
        # {
        #     "answer": "The return policy is 30 days [1]...",
        #     "sources": [{"document_id": "...", "chunk_index": 0, ...}],
        #     "cached": False
        # }
    """

    # Step 1: Check cache — if this exact question was asked before by this
    # tenant, return the cached answer immediately (saves LLM API cost)
    cached = await get_cached_answer(tenant_id, question)

    if cached:
        # Cache hit! Mark it as cached and return without touching Qdrant or Gemini
        cached["cached"] = True
        return cached
    else:
        # Cache miss — run the full RAG pipeline

        # Step 2: Convert question text into a 384-dimensional embedding vector
        # using the same model that embedded the document chunks (all-MiniLM-L6-v2)
        question_embedding = generate_embedding(question)

        # Step 3: Search Qdrant for the top 5 most semantically similar chunks
        # Results are filtered by tenant_id (and optionally by specific document_ids)
        results = search_similar(
            tenant_id, question_embedding, document_ids=document_ids
        )

        # Step 4: Extract just the text content from each search result
        chunks = [r["text"] for r in results]

        # Handle case where no relevant chunks were found
        # (e.g., tenant has no documents, or documents haven't been processed yet)
        if not chunks:
            return {
                "answer": "No relevant documents found. Please upload documents first.",
                "sources": [],
                "cached": False,
            }

        # Step 5: Send chunks + question to Gemini LLM for answer generation
        # The LLM reads the chunks as context and generates a grounded answer
        # Wrapped in try/except for graceful degradation if LLM is unavailable
        try:
            answer = await generate_answer(chunks, question)
        except Exception:
            # Graceful degradation: LLM is unavailable, return raw chunks instead
            # NOT cached — when the LLM recovers, the next query gets a real answer
            fallback_answer = "LLM unavailable. Here are the most relevant chunks:\n"
            for i in range(len(results)):
                fallback_answer += f"[{i + 1}] {results[i]['text']}\n"

            return {"answer": fallback_answer, "sources": results, "cached": False}

        # Step 6: Build the response with answer and source metadata
        response = {
            "answer": answer,
            "sources": results,  # Includes document_id, chunk_index, text, score
            "cached": False,
        }

        # Step 7: Cache the result in Redis (TTL: 1 hour)
        # Next identical query from this tenant will get an instant cache hit
        await cache_answer(tenant_id, question, response)

        return response
