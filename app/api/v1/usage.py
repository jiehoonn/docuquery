"""
app/api/v1/usage.py - Usage Statistics Endpoint

Provides an endpoint for tenants to view their current usage stats,
including storage consumption, query count, and rate limit status.

Endpoint:
    GET /api/v1/usage - Returns current usage statistics for the tenant

This endpoint helps organizations:
    - Monitor how much storage they've consumed (quota: 100 MB)
    - Track how many queries they've made this month
    - See their current rate limit status (100 requests/hour)
"""

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.auth import get_current_user
from app.core.multi_tenant import STORAGE_LIMIT_MB, get_rate_limit_status
from app.db.models import Document, Organization, User
from app.db.session import get_db

# Create router - all routes will be prefixed with /usage
router = APIRouter(prefix="/usage", tags=["usage"])


# ============ Response Schemas ============


class UsageResponse(BaseModel):
    """
    Response schema for the usage endpoint.

    Provides a complete picture of the tenant's current resource consumption
    and quota limits.
    """

    # Storage usage
    storage_used_mb: int
    storage_limit_mb: int

    # Query usage
    queries_this_month: int

    # Document counts
    total_documents: int
    documents_ready: int
    documents_processing: int
    documents_failed: int

    # Rate limit status (current hour)
    rate_limit: dict


# ============ Endpoints ============


@router.get("", response_model=UsageResponse)
async def get_usage(
    current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    """
    Get usage statistics for the current user's organization.

    Returns storage usage, query count, document counts, and rate limit status.
    Useful for monitoring consumption against quotas.

    Returns:
        UsageResponse with all usage metrics

    Example response:
        {
            "storage_used_mb": 42,
            "storage_limit_mb": 100,
            "queries_this_month": 156,
            "total_documents": 12,
            "documents_ready": 10,
            "documents_processing": 1,
            "documents_failed": 1,
            "rate_limit": {
                "current_requests_this_hour": 23,
                "limit_per_hour": 100,
                "remaining": 77
            }
        }
    """
    tenant_id = current_user.organization_id

    # 1. Fetch organization for storage and query stats
    result = await db.execute(select(Organization).where(Organization.id == tenant_id))
    org = result.scalar_one_or_none()

    if not org:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Organization not found"
        )

    # 2. Count documents by status (single query with conditional aggregation)
    # CRITICAL: Filter by tenant_id for multi-tenant isolation
    result = await db.execute(
        select(
            func.count().label("total"),
            func.count().filter(Document.status == "ready").label("ready"),
            func.count().filter(Document.status == "processing").label("processing"),
            func.count().filter(Document.status == "failed").label("failed"),
        ).where(Document.tenant_id == tenant_id)
    )
    doc_stats = result.one()

    # 3. Get current rate limit status (reads from Redis, doesn't increment)
    rate_limit = await get_rate_limit_status(str(tenant_id))

    return UsageResponse(
        storage_used_mb=org.storage_used_mb,
        storage_limit_mb=STORAGE_LIMIT_MB,
        queries_this_month=org.queries_this_month,
        total_documents=doc_stats.total,
        documents_ready=doc_stats.ready,
        documents_processing=doc_stats.processing,
        documents_failed=doc_stats.failed,
        rate_limit=rate_limit,
    )
