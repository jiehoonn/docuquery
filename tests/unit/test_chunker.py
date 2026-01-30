"""
tests/unit/test_chunker.py - Text Chunking Tests

Tests for the sliding-window chunking algorithm.
chunk_text() is a pure function with zero dependencies — ideal for unit testing.
"""

import pytest
from app.services.chunker import chunk_text


class TestChunkTextBasics:
    """Basic behavior tests for the chunker."""

    def test_empty_string_returns_empty_list(self):
        """Empty input should return no chunks."""
        assert chunk_text("") == []

    def test_whitespace_only_returns_empty_list(self):
        """Whitespace-only input should return no chunks."""
        assert chunk_text("   \n\t  ") == []

    def test_short_text_returns_single_chunk(self):
        """Text shorter than chunk_size should return one chunk (the full text)."""
        text = "Hello world"
        chunks = chunk_text(text, chunk_size=512)
        assert len(chunks) == 1
        assert chunks[0] == text

    def test_chunks_have_correct_size(self):
        """Each chunk (except last) should be exactly chunk_size characters."""
        text = "A" * 1000
        chunks = chunk_text(text, chunk_size=100, overlap=10)
        # All chunks except the last should be exactly 100 chars
        for chunk in chunks[:-1]:
            assert len(chunk) == 100

    def test_overlap_creates_shared_text(self):
        """Consecutive chunks should share 'overlap' characters."""
        text = "ABCDEFGHIJKLMNOPQRSTUVWXYZ" * 10  # 260 chars
        chunks = chunk_text(text, chunk_size=50, overlap=10)
        # The last 10 chars of chunk[0] should appear at the start of chunk[1]
        if len(chunks) >= 2:
            end_of_first = chunks[0][-10:]
            start_of_second = chunks[1][:10]
            assert end_of_first == start_of_second

    def test_all_text_covered(self):
        """Joining all chunks (accounting for overlap) should reconstruct full text."""
        text = "The quick brown fox jumps over the lazy dog. " * 30
        chunks = chunk_text(text, chunk_size=100, overlap=20)
        # The full text should start with the first chunk and end with the last chunk
        assert text.startswith(chunks[0])
        assert text.endswith(chunks[-1])


class TestChunkTextEdgeCases:
    """Edge case tests — boundary conditions that could break the algorithm."""

    # What if the text is exactly chunk_size characters? (1 chunk? 2?)
    def test_exact_chunk_size_chars(self):
        """Text size of exactly chunk_size should be 1 chunk."""
        text = "ABCDEFGHIJ" * 5
        chunks = chunk_text(text, chunk_size=50, overlap=10)
        assert len(chunks) == 1

    # What if overlap is 0? (no overlap - chunks should tile perfectly)
    def test_no_overlap(self):
        """Chunks with no overlap should tile perfectly"""
        text = "ABCDEFGHIJ" * 2
        chunks = chunk_text(text, chunk_size=10, overlap=0)
        assert "".join(chunks) == text

    # What if chunk_size equals overlap? (would the window ever advance?)
    def test_chunk_size_equals_overlap(self):
        """overlap >= chunk_size would infinite loop, so it should raise ValueError."""
        with pytest.raises(ValueError, match="overlap"):
            chunk_text("some text", chunk_size=10, overlap=10)