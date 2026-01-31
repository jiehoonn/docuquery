"""
tests/unit/test_rag.py - RAG Pipeline Tests (with mocks)

Tests the query_documents() orchestrator by mocking all external dependencies:
    - cache (Redis)
    - embeddings (sentence-transformers model)
    - qdrant (vector database)
    - llm (Gemini API)

This lets us test the pipeline logic (caching, fallback, response format)
without needing any running services.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.rag import query_documents

# Fake data that our mocks will return
FAKE_EMBEDDING = [0.1] * 384  # 384-dimensional vector (matches all-MiniLM-L6-v2)
FAKE_SEARCH_RESULTS = [
    {
        "score": 0.95,
        "document_id": "doc-1",
        "chunk_index": 0,
        "text": "Mars is the fourth planet.",
    },
    {
        "score": 0.87,
        "document_id": "doc-1",
        "chunk_index": 1,
        "text": "Mars has two moons.",
    },
]


class TestRAGCacheHit:
    """Test behavior when the answer is already cached."""

    @patch("app.services.rag.get_cached_answer")
    async def test_cache_hit_returns_cached_response(self, mock_cache):
        """When cache hits, return cached data without touching Qdrant or Gemini."""
        cached_response = {
            "answer": "Mars is the fourth planet [1].",
            "sources": FAKE_SEARCH_RESULTS,
        }
        mock_cache.return_value = cached_response

        result = await query_documents("tenant-123", "What is Mars?")

        assert result["cached"] is True
        assert result["answer"] == "Mars is the fourth planet [1]."
        mock_cache.assert_called_once_with("tenant-123", "What is Mars?")

    @patch("app.services.rag.get_cached_answer")
    @patch("app.services.rag.generate_embedding")
    async def test_cache_hit_skips_embedding(self, mock_embed, mock_cache):
        """A cache hit should never call the embedding model."""
        mock_cache.return_value = {"answer": "cached", "sources": []}

        await query_documents("tenant-123", "Any question?")

        mock_embed.assert_not_called()


class TestRAGCacheMiss:
    """Test the full pipeline when cache misses."""

    @patch("app.services.rag.cache_answer", new_callable=AsyncMock)
    @patch("app.services.rag.generate_answer", new_callable=AsyncMock)
    @patch("app.services.rag.search_similar")
    @patch("app.services.rag.generate_embedding")
    @patch("app.services.rag.get_cached_answer")
    async def test_full_pipeline_on_cache_miss(
        self, mock_cache_get, mock_embed, mock_search, mock_llm, mock_cache_set
    ):
        """Cache miss should run: embed → search → LLM → cache → return."""
        mock_cache_get.return_value = None
        mock_embed.return_value = FAKE_EMBEDDING
        mock_search.return_value = FAKE_SEARCH_RESULTS
        mock_llm.return_value = "Mars is the fourth planet from the Sun [1]."

        result = await query_documents("tenant-123", "What is Mars?")

        assert result["cached"] is False
        assert result["answer"] == "Mars is the fourth planet from the Sun [1]."
        assert result["sources"] == FAKE_SEARCH_RESULTS
        # Verify the result was cached
        mock_cache_set.assert_called_once()

    @patch("app.services.rag.cache_answer", new_callable=AsyncMock)
    @patch("app.services.rag.generate_answer", new_callable=AsyncMock)
    @patch("app.services.rag.search_similar")
    @patch("app.services.rag.generate_embedding")
    @patch("app.services.rag.get_cached_answer")
    async def test_no_chunks_found(
        self, mock_cache_get, mock_embed, mock_search, mock_llm, mock_cache_set
    ):
        """If Qdrant returns no results, return a helpful message without calling LLM."""
        mock_cache_get.return_value = None
        mock_embed.return_value = FAKE_EMBEDDING
        mock_search.return_value = []  # No matching chunks

        result = await query_documents("tenant-123", "Random question")

        assert "No relevant documents found" in result["answer"]
        assert result["sources"] == []
        assert result["cached"] is False
        # LLM should NOT be called when there are no chunks
        mock_llm.assert_not_called()


class TestRAGGracefulDegradation:
    """Test fallback behavior when the LLM is unavailable."""

    @patch("app.services.rag.cache_answer", new_callable=AsyncMock)
    @patch("app.services.rag.generate_answer", new_callable=AsyncMock)
    @patch("app.services.rag.search_similar")
    @patch("app.services.rag.generate_embedding")
    @patch("app.services.rag.get_cached_answer")
    async def test_llm_failure_returns_chunks(
        self, mock_cache_get, mock_embed, mock_search, mock_llm, mock_cache_set
    ):
        """When LLM fails, return raw chunks instead of crashing."""
        mock_cache_get.return_value = None
        mock_embed.return_value = FAKE_EMBEDDING
        mock_search.return_value = FAKE_SEARCH_RESULTS
        mock_llm.side_effect = Exception("Gemini API is down")

        result = await query_documents("tenant-123", "What is Mars?")

        assert "LLM unavailable" in result["answer"]
        assert "[1]" in result["answer"]
        assert "[2]" in result["answer"]
        assert result["sources"] == FAKE_SEARCH_RESULTS
        assert result["cached"] is False

    @patch("app.services.rag.cache_answer", new_callable=AsyncMock)
    @patch("app.services.rag.generate_answer", new_callable=AsyncMock)
    @patch("app.services.rag.search_similar")
    @patch("app.services.rag.generate_embedding")
    @patch("app.services.rag.get_cached_answer")
    async def test_llm_failure_not_cached(
        self, mock_cache_get, mock_embed, mock_search, mock_llm, mock_cache_set
    ):
        """Degraded responses should NOT be cached (LLM might recover)."""
        mock_cache_get.return_value = None
        mock_embed.return_value = FAKE_EMBEDDING
        mock_search.return_value = FAKE_SEARCH_RESULTS
        mock_llm.side_effect = Exception("Gemini API is down")

        await query_documents("tenant-123", "What is Mars?")

        # cache_answer should NOT be called for degraded responses
        mock_cache_set.assert_not_called()
