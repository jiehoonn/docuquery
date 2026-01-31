"""
app/db/models.py - Database Models (Tables)

This module defines the database schema using SQLAlchemy ORM.
Each class represents a table in PostgreSQL.

Key concepts:
- Mapped[] - Type hint that tells SQLAlchemy this is a database column
- mapped_column() - Configures the column (type, constraints, defaults)
- ForeignKey - Creates a relationship between tables
- Index - Speeds up queries on specific columns

Multi-tenancy pattern:
    Every query for tenant-scoped data (documents, queries) MUST filter
    by tenant_id to ensure organizations can't see each other's data.
"""

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, Index, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


class User(Base):
    """
    Represents a user account in the system.

    Users belong to an Organization and authenticate via email/password.
    Each user can access only their organization's documents.

    Table: users
    """

    __tablename__ = "users"

    # Primary key: UUID is better than auto-increment for distributed systems
    # default=uuid.uuid4 generates a new UUID automatically
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)

    # Email: unique constraint prevents duplicate accounts
    # index=True speeds up login queries (WHERE email = ?)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)

    # Password hash: NEVER store plain passwords!
    # This stores the bcrypt hash from security.hash_password()
    password_hash: Mapped[str] = mapped_column(String(255))

    # Foreign key linking user to their organization
    # ForeignKey enforces referential integrity (org must exist)
    organization_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("organizations.id"))

    # Timestamp for when the account was created
    # default=datetime.utcnow is called when a new user is created
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class Organization(Base):
    """
    Represents a tenant (organization/company) in the multi-tenant system.

    Each organization:
    - Has its own set of documents
    - Has its own Qdrant collection for vectors
    - Has usage quotas (storage, queries)
    - Has an API key for programmatic access

    Table: organizations
    """

    __tablename__ = "organizations"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)

    # Organization name (e.g., "Acme Corp")
    name: Mapped[str] = mapped_column(String(255), unique=True, index=True)

    # Hashed API key for programmatic access
    # unique=True ensures no collision (extremely unlikely anyway)
    api_key_hash: Mapped[str] = mapped_column(String(255), unique=True, index=True)

    # Usage tracking for quotas
    storage_used_mb: Mapped[int] = mapped_column(Integer, default=0)
    queries_this_month: Mapped[int] = mapped_column(Integer, default=0)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class Document(Base):
    """
    Represents a document uploaded to the system.

    Document lifecycle:
    1. User uploads file → status='queued', stored in S3
    2. Worker picks it up → status='processing'
    3. Text extracted, chunked, embedded → status='ready'
    4. If error occurs → status='failed', error_message set

    Table: documents

    CRITICAL: All queries MUST filter by tenant_id for security!
    """

    __tablename__ = "documents"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)

    # CRITICAL: tenant_id links document to an organization
    # Every query for documents MUST include: WHERE tenant_id = ?
    tenant_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("organizations.id"))

    # Document metadata
    title: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # S3 path: {tenant_id}/{document_id}/original.pdf
    file_path: Mapped[str] = mapped_column(String(1024))

    file_size_bytes: Mapped[int] = mapped_column(Integer)

    # Processing status: queued → processing → ready OR failed
    status: Mapped[str] = mapped_column(String(50), default="queued")

    # Number of text chunks created (set after processing)
    chunks_count: Mapped[int] = mapped_column(Integer, default=0)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # When processing completed (null if still processing)
    processed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Error message if processing failed
    error_message: Mapped[Optional[str]] = mapped_column(String(1024), nullable=True)

    # Composite index for efficient tenant-scoped queries
    # This makes "SELECT * FROM documents WHERE tenant_id = ?" fast
    __table_args__ = (Index("idx_document_tenant", "tenant_id", "id"),)
