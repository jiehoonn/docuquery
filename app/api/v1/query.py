from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import List, Optional

from app.db.models import User
from app.api.v1.auth import get_current_user
from app.services.rag import query_documents

router = APIRouter(prefix="/query", tags=["query"])

class QueryRequest(BaseModel):
    question: str   # Max 500 chars per PRD
    document_ids: Optional[List[str]] = None    # Filter by specific docs

class QueryResponse(BaseModel):
    answer: str
    sources: list
    cached: bool

@router.post("", response_model=QueryResponse)
async def query(
    request: QueryRequest,
    current_user: User = Depends(get_current_user)
):
    # 1. Validate question length (max 500 chars)
    if len(request.question) > 500:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Question must be 500 characters or less"
        )
    # 2. Call query_documents with tenant_id from current_user
    result = await query_documents(
        tenant_id=str(current_user.organization_id),
        question=request.question,
        document_ids=request.document_ids
    )
    # 3. Return the result
    return result