"""
app/api/v1/query.py - Query Endpoint

Provides the main query endpoint for asking questions about uploaded documents.
This is the user-facing interface to the RAG pipeline.

Endpoint:
    POST /api/v1/query - Submit a question and receive an AI-generated answer

Flow:
    1. User sends question (+ optional document_ids filter)
    2. Endpoint validates input (question length ≤ 500 chars)
    3. Calls the RAG orchestrator (app/services/rag.py)
    4. Returns answer with source citations and cache status

Authentication:
    Requires JWT token in Authorization header.
    The tenant_id is extracted from the authenticated user's organization,
    ensuring users can only query their own organization's documents.
"""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from app.api.v1.auth import get_current_user
from app.core.multi_tenant import check_rate_limit
from app.db.models import User
from app.services.rag import query_documents

# Create router - all routes will be prefixed with /query
# tags=["query"] groups this endpoint in the API docs
router = APIRouter(prefix="/query", tags=["query"])


# ============ Request/Response Schemas ============


class QueryRequest(BaseModel):
    """
    Request body for the query endpoint.

    Attributes:
        question: The natural language question to ask (max 500 characters)
        document_ids: Optional list of specific document UUIDs to search.
                     If omitted, searches all documents in the organization.
    """

    question: str
    document_ids: Optional[List[str]] = None


class QueryResponse(BaseModel):
    """
    Response from the query endpoint.

    Attributes:
        answer: The AI-generated answer with citation references [1], [2], etc.
        sources: List of document chunks used to generate the answer, each containing
                 score, document_id, chunk_index, and text
        cached: Whether this response was served from Redis cache
    """

    answer: str
    sources: list
    cached: bool


# ============ Endpoints ============


@router.post("", response_model=QueryResponse)
async def query(request: QueryRequest, current_user: User = Depends(get_current_user)):
    """
    Query documents using natural language.

    Submits a question to the RAG pipeline which:
    1. Checks Redis cache for a previous identical query
    2. Embeds the question using sentence-transformers
    3. Searches Qdrant for semantically similar document chunks
    4. Sends chunks + question to Gemini LLM for answer generation
    5. Caches the result and returns with source citations

    Args:
        request: QueryRequest with question and optional document_ids

    Returns:
        QueryResponse with answer, source chunks, and cache status

    Raises:
        400: If question exceeds 500 characters
        401: If not authenticated

    Example request:
        POST /api/v1/query
        {"question": "What is the return policy?"}

    Example response:
        {
            "answer": "The return policy is 30 days [1].",
            "sources": [{"score": 0.85, "document_id": "...", "text": "..."}],
            "cached": false
        }
    """
    # 1. Validate question length (max 500 chars per PRD security constraints)
    if len(request.question) > 500:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Question must be 500 characters or less",
        )

    # 2. Check rate limit before running the (expensive) RAG pipeline
    # Call check_rate_limit with the tenant_id, and if not allowed, raise 429
    rate = await check_rate_limit(str(current_user.organization_id))
    if not rate["allowed"]:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Rate limit exceeded. {rate['remaining']} requests remaining. Limit: {rate['limit']}/hour",
        )

    # 3. Call RAG orchestrator with tenant_id from the authenticated user
    # CRITICAL: tenant_id comes from the JWT, not from user input,
    # ensuring users can only query their own organization's documents
    result = await query_documents(
        tenant_id=str(current_user.organization_id),
        question=request.question,
        document_ids=request.document_ids,
    )

    # 3. Return the result (FastAPI auto-serializes to QueryResponse)
    return result
