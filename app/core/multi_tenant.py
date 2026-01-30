"""
app/core/multi_tenant.py - Multi-Tenant Utilities

Provides utilities for enforcing tenant isolation, rate limiting,
and usage quotas across the application.

Rate Limiting Strategy:
    Uses Redis counters with hourly windows to enforce per-tenant rate limits.

    Key format: ratelimit:{tenant_id}:{hour_timestamp}
    - Atomic INCR ensures accuracy under concurrent requests
    - TTL of 3600 seconds auto-expires old counters (no cleanup needed)
    - Each hour gets a fresh counter (simple, effective)

    Example:
        Tenant makes 100 requests between 2:00-3:00 PM → counter hits 100
        At 3:00 PM, a new key is created → counter resets to 0
        Old key expires automatically after 1 hour

Usage Quotas (PRD requirements):
    - Rate limit: 100 requests/hour per tenant
    - Storage limit: 100 MB per tenant (free tier)
    - Query tracking: queries_this_month on Organization model
"""

from datetime import datetime
from app.services.cache import get_redis_client

# ============ Configuration ============

# Maximum API requests per tenant per hour
RATE_LIMIT_PER_HOUR = 100

# Maximum storage per tenant in MB (free tier)
STORAGE_LIMIT_MB = 100


# ============ Rate Limiting ============

async def check_rate_limit(tenant_id: str) -> dict:
    """
    Check and increment the rate limit counter for a tenant.

    This function is called on every authenticated request. It:
    1. Generates a key based on tenant_id + current hour
    2. Atomically increments the counter (INCR is atomic in Redis)
    3. Sets TTL on first request of the hour (auto-cleanup)
    4. Returns the current count and limit status

    Args:
        tenant_id: The organization's UUID

    Returns:
        dict with:
            - allowed (bool): Whether the request should proceed
            - current (int): Number of requests made this hour
            - limit (int): Maximum allowed requests per hour
            - remaining (int): Requests remaining this hour

    Example:
        result = await check_rate_limit("org-123")
        if not result["allowed"]:
            raise HTTPException(status_code=429, detail="Rate limit exceeded")
    """
    client = get_redis_client()

    # Generate key using current hour (resets every hour automatically)
    # e.g., "ratelimit:org-123:2026012920" (YYYYMMDDHH format)
    current_hour = datetime.utcnow().strftime("%Y%m%d%H")
    key = f"ratelimit:{tenant_id}:{current_hour}"

    # Atomically increment the counter
    # INCR creates the key with value 1 if it doesn't exist
    current_count = await client.incr(key)

    # Set TTL only on the first request (when count is 1)
    # This ensures the key auto-expires after 1 hour
    if current_count == 1:
        await client.expire(key, 3600)

    # Calculate remaining requests
    remaining = max(0, RATE_LIMIT_PER_HOUR - current_count)
    allowed = current_count <= RATE_LIMIT_PER_HOUR

    return {
        "allowed": allowed,
        "current": current_count,
        "limit": RATE_LIMIT_PER_HOUR,
        "remaining": remaining,
    }


async def get_rate_limit_status(tenant_id: str) -> dict:
    """
    Get the current rate limit status WITHOUT incrementing the counter.

    Used by the /usage endpoint to show rate limit info.

    Args:
        tenant_id: The organization's UUID

    Returns:
        dict with current count, limit, and remaining requests
    """
    client = get_redis_client()

    current_hour = datetime.utcnow().strftime("%Y%m%d%H")
    key = f"ratelimit:{tenant_id}:{current_hour}"

    # GET doesn't increment — just reads the current value
    current_count = await client.get(key)
    current_count = int(current_count) if current_count else 0

    return {
        "current_requests_this_hour": current_count,
        "limit_per_hour": RATE_LIMIT_PER_HOUR,
        "remaining": max(0, RATE_LIMIT_PER_HOUR - current_count),
    }
