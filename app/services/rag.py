from app.services.cache import get_cached_answer, cache_answer
from app.services.embeddings import generate_embedding
from app.services.qdrant import search_similar
from app.services.llm import generate_answer

async def query_documents(
    tenant_id: str,
    question: str,
    document_ids: list[str] | None = None
) -> dict:
    """
    Main RAG query function.
    
    Returns:
        {
            "answer": "The return policy is 30 days [1]...",
            "sources": [{"document_id": "...", "chunk_index": 0, "text": "..."}],
            "cached": True/False
        }
    """

    # 1. Check cache with get_cached_answer()
    cached = await get_cached_answer(tenant_id, question)
    # 2. If hit, return it with cached: True
    if cached:
        cached["cached"] = True
        return cached
    else:
    # 3. If miss:
    #   - Generate embedding for the question
        question_embedding = generate_embedding(question)
    #   - Search Qdrant for similar chunks
        results = search_similar(tenant_id, question_embedding, document_ids=document_ids)
    #   - Extract just the text from each result
        chunks = [r["text"] for r in results]
        if not chunks:
            return {
                "answer": "No relevant documents found. Please upload documents first.",
                "sources": [],
                "cached": False
            }
    #   - Call LLM with chunks and question
        answer = await generate_answer(chunks, question)
    #   - Build response with answer + sources
        response = {
            "answer": answer,
            "sources": results,  # includes document_id, chunks_index, text
            "cached": False
        }
    #   - Cache the result
        await cache_answer(tenant_id, question, response)
    #   - Return with cached: False
        return response