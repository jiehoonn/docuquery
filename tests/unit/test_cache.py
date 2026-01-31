"""
tests/unit/test_cache.py - Cache Service Tests

Tests for the cache key generation (pure function, no mocks needed)
and the cache get/set operations (mocked Redis).
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.cache import cache_answer, get_cache_key, get_cached_answer


class TestCacheKey:
    """Tests for the deterministic cache key generator (pure function)."""

    def test_format(self):
        """Key should follow format: query:{tenant_id}:{hash}"""
        key = get_cache_key("tenant-abc", "What is the policy?")
        parts = key.split(":")
        assert parts[0] == "query"
        assert parts[1] == "tenant-abc"
        assert len(parts[2]) == 16  # SHA-256 truncated to 16 hex chars

    def test_deterministic(self):
        """Same inputs should always produce the same key."""
        key1 = get_cache_key("t-1", "Hello world")
        key2 = get_cache_key("t-1", "Hello world")
        assert key1 == key2

    def test_tenant_isolation(self):
        """Same query from different tenants should produce different keys."""
        key1 = get_cache_key("tenant-A", "Same question")
        key2 = get_cache_key("tenant-B", "Same question")
        assert key1 != key2

    def test_different_queries(self):
        """Different queries from same tenant should produce different keys."""
        key1 = get_cache_key("t-1", "Question one")
        key2 = get_cache_key("t-1", "Question two")
        assert key1 != key2


class TestCacheOperations:
    """Tests for Redis cache get/set (mocked Redis)."""

    @patch("app.services.cache.get_redis_client")
    async def test_cache_miss_returns_none(self, mock_get_client):
        """get_cached_answer should return None on cache miss."""
        mock_redis = AsyncMock()
        mock_redis.get.return_value = None
        mock_get_client.return_value = mock_redis

        result = await get_cached_answer("tenant-1", "Unknown question")
        assert result is None

    @patch("app.services.cache.get_redis_client")
    async def test_cache_hit_returns_dict(self, mock_get_client):
        """get_cached_answer should deserialize JSON from Redis."""
        mock_redis = AsyncMock()
        mock_redis.get.return_value = '{"answer": "cached answer", "sources": []}'
        mock_get_client.return_value = mock_redis

        result = await get_cached_answer("tenant-1", "Cached question")
        assert result == {"answer": "cached answer", "sources": []}

    @patch("app.services.cache.get_redis_client")
    async def test_cache_set_stores_with_ttl(self, mock_get_client):
        """cache_answer should call Redis SET with the correct TTL."""
        mock_redis = AsyncMock()
        mock_get_client.return_value = mock_redis

        answer = {"answer": "test", "sources": []}
        await cache_answer("tenant-1", "Some question", answer, ttl=3600)

        # Verify Redis SET was called with expiration
        mock_redis.set.assert_called_once()
        call_kwargs = mock_redis.set.call_args
        assert call_kwargs.kwargs.get("ex") == 3600 or call_kwargs[1].get("ex") == 3600
