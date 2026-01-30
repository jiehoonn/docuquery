"""
tests/conftest.py - Shared Test Fixtures

This file is automatically loaded by pytest. Any fixture defined here
is available to ALL test files without importing.

Fixture hierarchy:
    conftest.py (this file) → shared across all tests
    tests/unit/conftest.py → shared across unit tests only
    tests/integration/conftest.py → shared across integration tests only
"""

import pytest


@pytest.fixture
def sample_text():
    """A short sample text for testing chunking and embeddings."""
    return "The quick brown fox jumps over the lazy dog. " * 20


@pytest.fixture
def sample_chunks():
    """Pre-built chunks for testing LLM prompt building and RAG."""
    return [
        "Mars is the fourth planet from the Sun.",
        "Olympus Mons on Mars is the tallest volcano in the solar system.",
        "Mars has two moons: Phobos and Deimos.",
    ]