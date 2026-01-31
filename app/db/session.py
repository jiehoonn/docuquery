"""
app/db/session.py - Database Connection Setup

This module configures the database connection using SQLAlchemy with
async support. It creates:
1. An async engine - the connection pool to PostgreSQL
2. A session factory - creates sessions for each request
3. A base class - all database models inherit from this
4. A dependency - FastAPI uses this to inject database sessions

How async database access works:
    - Traditional (sync): Code waits while database query runs
    - Async: Code can handle other requests while waiting for database
    - Result: Better performance under high load
"""

from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.core.config import settings

# ============ Database Engine ============
# The engine manages the connection pool to the database.
# It doesn't connect immediately - connections are made when needed.
#
# TODO(cloud): In production with AWS RDS:
#   - Use RDS PostgreSQL endpoint as DATABASE_URL
#   - Set echo=False to disable SQL logging (use structured logging instead)
#   - Consider using RDS Proxy for connection pooling and IAM auth
#   - Add pool_size and max_overflow parameters for production load

engine = create_async_engine(
    settings.database_url,  # e.g., "postgresql+asyncpg://user:pass@localhost/db"
    echo=True,  # Log all SQL statements (helpful for debugging, disable in production)
)


# ============ Session Factory ============
# Sessions are the "workspace" for database operations.
# Each request gets its own session to prevent data conflicts.

async_session = async_sessionmaker(
    engine, expire_on_commit=False  # Objects remain usable after commit
)


# ============ Base Class for Models ============
# All database models (User, Organization, Document) inherit from this.
# It provides the foundation for SQLAlchemy's ORM magic.


class Base(DeclarativeBase):
    """
    Base class for all database models.

    Models that inherit from this will:
    - Automatically be mapped to database tables
    - Have access to SQLAlchemy's query capabilities
    - Be tracked for migrations by Alembic
    """

    pass


# ============ Dependency for FastAPI ============
# This is a "dependency injection" pattern used throughout FastAPI.
# Endpoints declare they need a database session, and FastAPI provides one.


async def get_db():
    """
    Dependency that provides a database session to endpoints.

    Usage in an endpoint:
        @router.get("/items")
        async def get_items(db: AsyncSession = Depends(get_db)):
            result = await db.execute(select(Item))
            return result.scalars().all()

    How it works:
        1. When a request comes in, FastAPI calls this function
        2. We create a new session with 'async with'
        3. 'yield' gives the session to the endpoint
        4. After the endpoint finishes, cleanup happens automatically
        5. The session is closed (but not committed - endpoints must commit)

    The 'async with' ensures the session is properly closed even if
    an error occurs in the endpoint.
    """
    async with async_session() as session:
        yield session
