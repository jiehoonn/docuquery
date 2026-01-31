"""
app/services/cache.py - Query Cache Service

Caches RAG query results in Redis to avoid redundant LLM API calls.
This is a critical cost optimization - every cache hit saves one Gemini API call.

Cache key format: query:{tenant_id}:{sha256(query_text)[:16]}

Why this key format?
    - Prefixed with "query:" to namespace our keys in Redis
    - tenant_id ensures cache isolation between organizations
    - SHA-256 hash of the query text creates a fixed-length, unique identifier
    - We only use the first 16 hex chars (64 bits) to keep keys short
      while still having negligible collision probability

Cache behavior:
    - TTL (Time To Live): 1 hour (3600 seconds)
    - After TTL expires, Redis automatically deletes the entry
    - Next identical query will be a cache miss → full RAG pipeline runs
    - Result is cached again for another hour

TODO(cloud): In production, replace local Redis with AWS ElastiCache
    for high availability and automatic failover. Consider using a Redis
    cluster for larger deployments with multiple app instances.
"""

import hashlib
import json

import redis.asyncio as redis

from app.core.config import settings


def get_redis_client() -> redis.Redis:
    """
    Create an async Redis client connection.

    Returns:
        An async Redis client connected to the configured Redis URL

    Note:
        Creates a new client per call. In production, consider using
        a connection pool for better performance under high load.

    TODO(cloud): Use AWS ElastiCache endpoint URL instead of local Redis.
    """
    client = redis.from_url(settings.redis_url)
    return client


def get_cache_key(tenant_id: str, query_text: str) -> str:
    """
    Generate a unique cache key for a tenant's query.

    The key is deterministic - the same tenant + query always produces
    the same key, which is how cache lookups work.

    Args:
        tenant_id: The organization's UUID (ensures tenant isolation)
        query_text: The user's question

    Returns:
        Cache key string in format: query:{tenant_id}:{hash}

    Example:
        key = get_cache_key("org-123", "What is the return policy?")
        # Returns: "query:org-123:a1b2c3d4e5f6g7h8"
    """
    # 1. Hash the query text with SHA-256 (deterministic, fixed-length)
    query_hash = hashlib.sha256(query_text.encode()).hexdigest()

    # 2. Take first 16 characters (enough to be unique, keeps keys short)
    short_hash = query_hash[:16]

    # 3. Combine into cache key with tenant isolation
    return f"query:{tenant_id}:{short_hash}"


async def get_cached_answer(tenant_id: str, query_text: str) -> dict | None:
    """
    Look up a cached answer for a query.

    Args:
        tenant_id: The organization's UUID
        query_text: The user's question

    Returns:
        The cached response dict if found, None if cache miss

    Example:
        cached = await get_cached_answer("org-123", "What is the return policy?")
        if cached:
            return cached  # Skip the entire RAG pipeline!
    """
    # 1. Generate the deterministic cache key
    key = get_cache_key(tenant_id, query_text)

    # 2. Connect to Redis
    client = get_redis_client()

    # 3. Attempt to retrieve the cached value
    value = await client.get(key)

    # 4. If found, deserialize from JSON string back to Python dict
    if value:
        return json.loads(value)
    return None


async def cache_answer(
    tenant_id: str, query_text: str, answer: dict, ttl: int = 3600
) -> None:
    """
    Store a query result in the cache.

    Args:
        tenant_id: The organization's UUID
        query_text: The user's question (used to generate cache key)
        answer: The full response dict (answer, sources, cached flag)
        ttl: Time-to-live in seconds (default: 3600 = 1 hour)

    Note:
        The TTL ensures stale results are eventually cleared.
        If a document is updated, cached answers based on old content
        will naturally expire. For immediate invalidation, you'd need
        to delete cache entries when documents change.

    TODO(cloud): Consider cache invalidation strategy when documents
        are re-processed or deleted. Could use Redis pub/sub or
        delete keys matching a pattern for the affected tenant.
    """
    # 1. Generate the deterministic cache key
    key = get_cache_key(tenant_id, query_text)

    # 2. Connect to Redis
    client = get_redis_client()

    # 3. Serialize the answer dict to JSON and store with TTL
    # ex=ttl sets the expiration time in seconds
    await client.set(key, json.dumps(answer), ex=ttl)
