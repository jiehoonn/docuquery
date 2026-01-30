"""
app/api/v1/auth.py - Authentication Endpoints

This module provides all authentication-related API endpoints:
- POST /register - Create a new user and organization
- POST /login - Authenticate and receive a JWT token
- GET /apikey - Generate a new API key (requires authentication)

Authentication flow:
1. User registers → gets JWT token + API key
2. User includes token in requests: Authorization: Bearer <token>
3. Protected endpoints use get_current_user to validate the token

Two authentication methods are supported:
- JWT tokens (for web UI, expire after 60 minutes)
- API keys (for scripts/integrations, don't expire)
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials, APIKeyHeader
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel, EmailStr

from app.db.session import get_db
from app.db.models import User, Organization
from app.core.security import (
    hash_password,
    verify_password,
    create_access_token,
    verify_access_token,
    generate_api_key,
    hash_api_key
)

# Create a router with a prefix - all routes here will start with /auth
# tags=["auth"] groups these endpoints together in the API docs
router = APIRouter(prefix="/auth", tags=["auth"])

# HTTPBearer extracts the token from "Authorization: Bearer <token>" header
# auto_error=False makes it return None instead of 401 when header is missing,
# allowing us to fall through to API key auth
security = HTTPBearer(auto_error=False)

# APIKeyHeader extracts the value from the "X-API-Key" header
# auto_error=False means it returns None if the header isn't present
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


# ============ Request/Response Schemas ============
# Pydantic models define the shape of request bodies and responses.
# They provide automatic validation and generate API documentation.

class RegisterRequest(BaseModel):
    """Data required to register a new account."""
    email: EmailStr  # EmailStr validates proper email format
    password: str
    organization_name: str


class LoginRequest(BaseModel):
    """Data required to log in."""
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    """Response containing a JWT token (for login)."""
    access_token: str
    token_type: str = "bearer"  # Always "bearer" for JWT


class RegisterResponse(BaseModel):
    """Response for registration (includes API key shown only once)."""
    access_token: str
    token_type: str = "bearer"
    api_key: str  # Only returned once - user must save it!


class ApiKeyResponse(BaseModel):
    """Response when generating a new API key."""
    api_key: str
    message: str = "Save this key - it cannot be retrieved again"


# ============ Dependencies ============
# Dependencies are reusable functions that FastAPI injects into endpoints.
# get_current_user validates the JWT and returns the authenticated user.

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    api_key: str = Depends(api_key_header),
    db: AsyncSession = Depends(get_db)
) -> User:
    """
    Dependency that authenticates a user via API key OR JWT token.

    Supports two authentication methods (checked in this order):
        1. API Key: X-API-Key header → hash key → find org → find user in org
        2. JWT Token: Authorization: Bearer <token> → decode → find user by ID

    If neither is provided, returns 401 Unauthorized.

    Usage in an endpoint:
        @router.get("/protected")
        async def protected_route(current_user: User = Depends(get_current_user)):
            # current_user is guaranteed to be a valid, authenticated user
            # Works with EITHER auth method - endpoint doesn't need to know which

    Raises:
        HTTPException 401: If credentials are missing, invalid, or user not found
    """

    # ── Method 1: API Key Authentication ──
    # Check X-API-Key header first (preferred for programmatic access)
    if api_key:
        # 1. Hash the api_key using hash_api_key() (already imported)
        hashed_key = hash_api_key(api_key)
        # 2. Look up the Organization where api_key_hash matches
        result = await db.execute(select(Organization).where(Organization.api_key_hash == hashed_key))
        org = result.scalar_one_or_none()
        # 3. If no org found, raise 401 "Invalid API key"
        if not org:   
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid Organization API Key"
            )
        # 4. Find a User that belongs to this organization
        else:
            result = await db.execute(select(User).where(User.organization_id == org.id))
            user = result.scalar_one_or_none()
         # 5. If no user found, raise 401 "No user found for this API key"
            if not user:   
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="No user found for this API key"
                )
        # 6. Return the user
        return user

    # ── Method 2: JWT Token Authentication ──
    # Fall back to Bearer token (used by web UI)
    if credentials:
        # Extract the token string from the Authorization header
        token = credentials.credentials

        try:
            # Verify token signature and decode the payload
            payload = verify_access_token(token)

            # "sub" (subject) claim contains the user ID
            user_id: str = payload.get("sub")

            if not user_id:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token"
                )
        except ValueError:
            # verify_access_token raises ValueError for invalid tokens
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )

        # Fetch the user from the database
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()

        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found"
            )

        return user

    # ── No credentials provided ──
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Authentication required. Provide either X-API-Key header or Authorization: Bearer <token>"
    )


# ============ Endpoints ============

@router.post("/register", response_model=RegisterResponse)
async def register(request: RegisterRequest, db: AsyncSession = Depends(get_db)):
    """
    Register a new user and organization.

    This endpoint:
    1. Checks if email is already taken
    2. Creates a new organization with an API key
    3. Creates a new user linked to that organization
    4. Returns a JWT token and the API key (shown only once!)

    Request body:
        {
            "email": "user@example.com",
            "password": "secretpassword",
            "organization_name": "My Company"
        }

    Returns:
        {
            "access_token": "eyJhbG...",
            "token_type": "bearer",
            "api_key": "dk_Abc123..."  <- Save this! Can't be retrieved later
        }
    """
    # 1. Check if user already exists
    result = await db.execute(select(User).where(User.email == request.email))
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    # 2. Create Organization
    # Generate API key BEFORE hashing so we can return it to the user
    api_key = generate_api_key()
    organization = Organization(
        name=request.organization_name,
        api_key_hash=hash_api_key(api_key),  # Store only the hash!
    )
    db.add(organization)

    # flush() sends the INSERT to the database but doesn't commit
    # This gives us the organization.id to use in the user
    await db.flush()

    # 3. Create User
    user = User(
        email=request.email,
        password_hash=hash_password(request.password),  # Never store plain password!
        organization_id=organization.id,  # Link user to organization
    )
    db.add(user)

    # commit() saves all changes permanently
    await db.commit()

    # 4. Create JWT Token and return response
    # "sub" is a standard JWT claim meaning "subject" (the user ID)
    token = create_access_token({"sub": str(user.id)})
    return RegisterResponse(access_token=token, api_key=api_key)


@router.post("/login", response_model=TokenResponse)
async def login(request: LoginRequest, db: AsyncSession = Depends(get_db)):
    """
    Authenticate a user and return a JWT token.

    Request body:
        {
            "email": "user@example.com",
            "password": "secretpassword"
        }

    Returns:
        {
            "access_token": "eyJhbG...",
            "token_type": "bearer"
        }

    Security note:
        We return the same error message for "user not found" and
        "wrong password" to prevent email enumeration attacks.
    """
    # 1. Fetch user by email
    result = await db.execute(select(User).where(User.email == request.email))
    user = result.scalar_one_or_none()

    if not user:
        # Don't reveal that the email doesn't exist
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )

    # 2. Verify password
    if not verify_password(request.password, user.password_hash):
        # Same error message as above (security best practice)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )

    # 3. Create and return token
    token = create_access_token({"sub": str(user.id)})
    return TokenResponse(access_token=token)


@router.get("/apikey", response_model=ApiKeyResponse)
async def regenerate_api_key(
    current_user: User = Depends(get_current_user),  # Requires authentication!
    db: AsyncSession = Depends(get_db)
):
    """
    Generate a new API key for the current user's organization.

    IMPORTANT: This invalidates the previous API key!

    Requires: JWT token in Authorization header

    Returns:
        {
            "api_key": "dk_NewKey123...",
            "message": "Save this key - it cannot be retrieved again"
        }

    Note: The old API key immediately stops working.
    """
    # Fetch the user's organization
    result = await db.execute(
        select(Organization).where(Organization.id == current_user.organization_id)
    )
    org = result.scalar_one_or_none()

    if not org:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found"
        )

    # Generate new API key and update the hash
    # The old key immediately becomes invalid
    new_api_key = generate_api_key()
    org.api_key_hash = hash_api_key(new_api_key)

    await db.commit()

    return ApiKeyResponse(api_key=new_api_key)
