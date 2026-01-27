import bcrypt as bcrypt_lib
from jose import jwt, JWTError
import datetime
from datetime import UTC, timedelta
import secrets
import string
import hashlib

from app.core.config import settings

# Password Hashing (passlib with bcrypt)
def hash_password(password: str) -> str:
    password_bytes = password.encode('utf-8')
    salt = bcrypt_lib.gensalt(rounds=12)
    hashed = bcrypt_lib.hashpw(password_bytes, salt)
    return hashed.decode('utf-8')

def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt_lib.checkpw(plain.encode('utf-8'), hashed.encode('utf-8'))

# JWT Tokens (python-jose)
SECRET_KEY = settings.jwt_secret
ALGORITHM = settings.jwt_algorithm

def create_access_token(data: dict, expires_delta: timedelta = None) -> str:
    """
    Creates a JWT access token with an expiration time.
    """
    to_encode = data.copy()
    if expires_delta:
        # Use UTC for consistency and to avoid timezone issues.
        expire = datetime.datetime.now(UTC) + expires_delta
    else:
        # Default expiration (e.g., 15 minutes) if none specified.
        expire = datetime.datetime.now(UTC) + timedelta(minutes=15) 
    to_encode.update({"exp": expire}) # Add the expiration claim
    
    # The jwt.encode function handles the signing
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_access_token(token: str) -> dict:
    # Now validate and should be ok
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        raise ValueError("Invalid token")

# API Keys
def generate_api_key() -> str:
    random_part = ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(32))
    return f"dk_{random_part}"

def hash_api_key(key: str) -> str:
    return hashlib.sha256(key.encode()).hexdigest()