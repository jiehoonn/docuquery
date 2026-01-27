from fastapi import FastAPI
from app.api.v1.auth import router as auth_router

app = FastAPI()

app.include_router(auth_router, prefix="/api/v1")

# Root endpoint
@app.get("/")
def read_root():
    return {
        "Hello": "World"
        }

# Health check endpoint
@app.get("/health")
def health_check():
    return {
        "status": "healthy"
        }