"""
app/main.py - FastAPI Application Entry Point

This is the main entry point for the DocuQuery API. It creates the FastAPI
application instance and configures all the routes (endpoints) that the API
will respond to.

To run this application:
    poetry run uvicorn app.main:app --reload

The app will be available at http://localhost:8000
API documentation is auto-generated at http://localhost:8000/docs
"""

from fastapi import FastAPI

# Import the auth router which contains all authentication-related endpoints
# We rename it to 'auth_router' for clarity when registering it below
from app.api.v1.auth import router as auth_router

# Import document router which contains document management endpoints (upload, list, get, delete)
from app.api.v1.documents import router as documents_router

# Import RAG router
from app.api.v1.query import router as query_router

# Import usage router which provides usage statistics (storage, queries, rate limits)
from app.api.v1.usage import router as usage_router

# Create the FastAPI application instance
# This is the main object that handles all incoming HTTP requests
app = FastAPI(
    title="DocuQuery API",
    description="Multi-tenant document Q&A platform powered by RAG",
    version="0.1.0"
)

# Register the auth router with a URL prefix
# This means all routes in auth_router will be prefixed with "/api/v1"
# For example, "/auth/login" becomes "/api/v1/auth/login"
app.include_router(auth_router, prefix="/api/v1")

# Register the documents router
# Routes: /api/v1/documents/upload, /api/v1/documents, etc.
app.include_router(documents_router, prefix="/api/v1")

# Register the RAG router
app.include_router(query_router, prefix="/api/v1")

# Register the usage router
# Routes: /api/v1/usage
app.include_router(usage_router, prefix="/api/v1")


@app.get("/")
def read_root():
    """
    Root endpoint - returns a simple welcome message.
    Useful for quickly checking if the API is running.

    Returns:
        dict: A simple JSON response
    """
    return {"Hello": "World"}


@app.get("/health")
def health_check():
    """
    Health check endpoint - used by monitoring systems and load balancers
    to verify the application is running and responsive.

    In production, this might also check database connectivity,
    Redis availability, etc.

    Returns:
        dict: Status information about the application
    """
    return {"status": "healthy"}
