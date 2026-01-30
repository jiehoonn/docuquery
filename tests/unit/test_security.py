"""
tests/unit/test_security.py - Security Utility Tests

Tests for password hashing, JWT tokens, and API key functions.
These are all pure functions with no external dependencies (no DB, no Redis).
"""

import pytest
from datetime import timedelta

from app.core.security import (
    hash_password,
    verify_password,
    create_access_token,
    verify_access_token,
    generate_api_key,
    hash_api_key,
)


# ============ Password Hashing Tests ============

class TestPasswordHashing:
    """Tests for bcrypt password hashing and verification."""

    def test_hash_returns_string(self):
        """hash_password should return a string (bcrypt hash)."""
        result = hash_password("testpassword")
        assert isinstance(result, str)

    def test_hash_not_plaintext(self):
        """The hash must NOT be the original password."""
        password = "mysecretpassword"
        hashed = hash_password(password)
        assert hashed != password

    def test_hash_is_salted(self):
        """Two hashes of the same password should differ (random salt)."""
        password = "samepassword"
        hash1 = hash_password(password)
        hash2 = hash_password(password)
        assert hash1 != hash2

    def test_verify_correct_password(self):
        """verify_password should return True for the correct password."""
        password = "correcthorsebatterystaple"
        hashed = hash_password(password)
        assert verify_password(password, hashed) is True

    def test_verify_wrong_password(self):
        """verify_password should return False for the wrong password."""
        hashed = hash_password("rightpassword")
        assert verify_password("wrongpassword", hashed) is False


# ============ JWT Token Tests ============

class TestJWTTokens:
    """Tests for JWT creation and verification."""

    def test_create_token_returns_string(self):
        """create_access_token should return a JWT string."""
        token = create_access_token({"sub": "user-123"})
        assert isinstance(token, str)
        # JWT tokens have 3 parts separated by dots
        assert token.count(".") == 2

    def test_roundtrip_token(self):
        """Creating then verifying a token should return the original claims."""
        data = {"sub": "user-456"}
        token = create_access_token(data)
        payload = verify_access_token(token)
        assert payload["sub"] == "user-456"

    def test_token_with_custom_expiration(self):
        """Token with custom expiration should still verify."""
        token = create_access_token(
            {"sub": "user-789"},
            expires_delta=timedelta(hours=2)
        )
        payload = verify_access_token(token)
        assert payload["sub"] == "user-789"

    def test_verify_invalid_token_raises(self):
        """verify_access_token should raise ValueError for garbage input."""
        with pytest.raises(ValueError, match="Invalid token"):
            verify_access_token("this.is.garbage")

    def test_verify_tampered_token_raises(self):
        """Modifying a token should invalidate it."""
        token = create_access_token({"sub": "user-123"})
        # Flip a character in the signature (last segment)
        tampered = token[:-1] + ("A" if token[-1] != "A" else "B")
        with pytest.raises(ValueError, match="Invalid token"):
            verify_access_token(tampered)


# ============ API Key Tests ============

class TestAPIKeys:
    """Tests for API key generation and hashing."""

    def test_api_key_format(self):
        """API key should start with 'dk_' and be 35 chars total."""
        key = generate_api_key()
        assert key.startswith("dk_")
        assert len(key) == 35  # "dk_" (3) + 32 random chars

    def test_api_key_unique(self):
        """Two generated API keys should never be the same."""
        key1 = generate_api_key()
        key2 = generate_api_key()
        assert key1 != key2

    def test_hash_api_key_deterministic(self):
        """Hashing the same key twice should produce the same hash."""
        key = "dk_testkey12345"
        assert hash_api_key(key) == hash_api_key(key)

    def test_hash_api_key_different_keys(self):
        """Different keys should produce different hashes."""
        hash1 = hash_api_key("dk_key1")
        hash2 = hash_api_key("dk_key2")
        assert hash1 != hash2

    def test_hash_api_key_length(self):
        """SHA-256 hash should be 64 hex characters."""
        hashed = hash_api_key("dk_anykey")
        assert len(hashed) == 64