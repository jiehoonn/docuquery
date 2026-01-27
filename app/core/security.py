"""
app/core/security.py - Security Utilities

This module contains all security-related functions for the application:
- Password hashing and verification (using bcrypt)
- JWT token creation and verification
- API key generation and hashing

Security principles followed:
1. Passwords are hashed with bcrypt (slow by design, resistant to brute force)
2. JWT tokens are signed and have expiration times
3. API keys are hashed with SHA-256 before storage (can't be reversed)
"""

import bcrypt as bcrypt_lib  # For password hashing
from jose import jwt, JWTError  # For JWT token handling
import datetime
from datetime import UTC, timedelta
import secrets  # Cryptographically secure random number generation
import string
import hashlib  # For SHA-256 hashing of API keys

from app.core.config import settings


# ============ Password Hashing ============
# We use bcrypt because it's designed to be slow, making brute-force
# attacks impractical. The "rounds" parameter controls how slow it is.

def hash_password(password: str) -> str:
    """
    Hash a plain-text password using bcrypt.

    Args:
        password: The plain-text password from user input

    Returns:
        A hashed password string safe to store in the database

    Example:
        hashed = hash_password("mysecretpassword")
        # Returns something like: "$2b$12$LQv3c1yqBw..."
    """
    # Convert string to bytes (bcrypt works with bytes)
    password_bytes = password.encode('utf-8')

    # Generate a random salt with 12 rounds (2^12 = 4096 iterations)
    # Higher rounds = more secure but slower
    salt = bcrypt_lib.gensalt(rounds=12)

    # Hash the password with the salt
    hashed = bcrypt_lib.hashpw(password_bytes, salt)

    # Convert bytes back to string for database storage
    return hashed.decode('utf-8')


def verify_password(plain: str, hashed: str) -> bool:
    """
    Verify a plain-text password against a hashed password.

    Args:
        plain: The plain-text password from user input (login attempt)
        hashed: The hashed password from the database

    Returns:
        True if the password matches, False otherwise

    Example:
        if verify_password("mysecretpassword", user.password_hash):
            print("Password correct!")
    """
    # bcrypt.checkpw handles extracting the salt from the hash
    # and comparing securely (constant-time comparison)
    return bcrypt_lib.checkpw(plain.encode('utf-8'), hashed.encode('utf-8'))


# ============ JWT Tokens ============
# JWT (JSON Web Token) is used for stateless authentication.
# The token contains the user ID and is signed with our secret key.

# Load settings once at module level for efficiency
SECRET_KEY = settings.jwt_secret
ALGORITHM = settings.jwt_algorithm


def create_access_token(data: dict, expires_delta: timedelta = None) -> str:
    """
    Create a JWT access token.

    Args:
        data: Dictionary of claims to include in the token.
              Typically includes "sub" (subject) with the user ID.
        expires_delta: Optional custom expiration time.
                      Defaults to 15 minutes if not specified.

    Returns:
        A signed JWT token string

    Example:
        token = create_access_token({"sub": "user-uuid-here"})
        # Returns: "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."

    How JWT works:
        1. The data (payload) is base64 encoded
        2. A signature is created using our SECRET_KEY
        3. Both are combined into a single string
        4. Anyone can READ the payload, but only we can VERIFY the signature
    """
    # Create a copy so we don't modify the original dict
    to_encode = data.copy()

    # Set expiration time
    if expires_delta:
        expire = datetime.datetime.now(UTC) + expires_delta
    else:
        # Default: 15 minutes from now
        expire = datetime.datetime.now(UTC) + timedelta(minutes=15)

    # Add expiration claim - JWT standard uses "exp"
    to_encode.update({"exp": expire})

    # Create and sign the token
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def verify_access_token(token: str) -> dict:
    """
    Verify and decode a JWT access token.

    Args:
        token: The JWT token string from the request header

    Returns:
        The decoded payload (claims) if valid

    Raises:
        ValueError: If the token is invalid, expired, or tampered with

    Example:
        try:
            payload = verify_access_token(token)
            user_id = payload["sub"]
        except ValueError:
            print("Invalid token!")
    """
    try:
        # jwt.decode verifies the signature and checks expiration
        # If anything is wrong, it raises JWTError
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        # Convert to a more generic error
        raise ValueError("Invalid token")


# ============ API Keys ============
# API keys are used for programmatic access (scripts, integrations).
# Unlike JWT tokens, they don't expire but can be regenerated.

def generate_api_key() -> str:
    """
    Generate a cryptographically secure API key.

    Returns:
        A new API key in the format "dk_" followed by 32 random characters.
        The "dk_" prefix makes it easy to identify DocuQuery API keys.

    Example:
        api_key = generate_api_key()
        # Returns: "dk_Abc123XyzRandomCharacters123456"

    Security note:
        Uses secrets.choice() which is cryptographically secure,
        unlike random.choice() which is predictable.
    """
    # Characters allowed in the API key (letters and digits)
    alphabet = string.ascii_letters + string.digits

    # Generate 32 random characters
    random_part = ''.join(secrets.choice(alphabet) for _ in range(32))

    # Prefix with "dk_" (DocuQuery key)
    return f"dk_{random_part}"


def hash_api_key(key: str) -> str:
    """
    Hash an API key using SHA-256 for secure storage.

    Args:
        key: The plain-text API key

    Returns:
        A SHA-256 hash of the key (64 hexadecimal characters)

    Why SHA-256 instead of bcrypt?
        - API keys are checked on EVERY request
        - bcrypt is intentionally slow (good for passwords, bad for frequent checks)
        - SHA-256 is fast and still secure for random 32-char keys

    Example:
        hashed = hash_api_key("dk_Abc123...")
        # Store 'hashed' in database, never store plain key
    """
    return hashlib.sha256(key.encode()).hexdigest()
