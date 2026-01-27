from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
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

router = APIRouter(prefix="/auth", tags=["auth"])
security = HTTPBearer()

# =============== Schemas ===============

class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    organization_name: str

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"

class RegisterResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    api_key: str

class ApiKeyResponse(BaseModel):
    api_key: str
    message: str = "Save this key - it cannot be retrieved again"

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> User:
    token = credentials.credentials
    try:
        payload = verify_access_token(token)
        user_id: str = payload.get("sub")
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )
    return user

# =============== Endpoints ===============
@router.post("/register", response_model=RegisterResponse)
async def register(request: RegisterRequest, db: AsyncSession = Depends(get_db)):
    # 1. Check if user already exists
    result = await db.execute(select(User).where(User.email == request.email))
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    # 2. Create Organization
    api_key = generate_api_key()
    organization = Organization(
        name=request.organization_name,
        api_key_hash=hash_api_key(api_key),
    )
    db.add(organization)
    await db.flush() # Get the organization.id without committing

    # 3. Create User
    user = User(
        email=request.email,
        password_hash=hash_password(request.password),
        organization_id=organization.id,
    )
    db.add(user)
    await db.commit()

    # 4. Create JWT Token
    token = create_access_token({"sub": str(user.id)})
    return RegisterResponse(access_token=token, api_key=api_key)

@router.post("/login", response_model=TokenResponse)
async def login(request: LoginRequest, db: AsyncSession = Depends(get_db)):
    # 1. Fetch user by email
    result = await db.execute(select(User).where(User.email == request.email))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )

    # 2. Verify password (raise 401 if wrong)
    if not verify_password(request.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )

    # 3. Create and return token
    token = create_access_token({"sub": str(user.id)})
    return TokenResponse(access_token=token)

@router.get("/apikey", response_model=ApiKeyResponse)
async def regenerate_api_key(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(Organization).where(Organization.id == current_user.organization_id)
    )
    org = result.scalar_one_or_none()

    if not org:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Organization not found")
    
    new_api_key = generate_api_key()
    org.api_key_hash = hash_api_key(new_api_key)
    await db.commit()

    return ApiKeyResponse(api_key=new_api_key)
    