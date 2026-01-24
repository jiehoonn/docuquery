# app/db/session.py: Database connection setup

from app.core.config import settings
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase

# Create the async engine using the database URL from settings
engine = create_async_engine(settings.database_url, echo=True)

# Create the async session maker
async_session = async_sessionmaker(engine, expire_on_commit=False)

# Base class for models
class Base(DeclarativeBase):
    pass

# Dependency function for FastAPI to get a session per request:
async def get_db():
    async with async_session() as session:
        yield session