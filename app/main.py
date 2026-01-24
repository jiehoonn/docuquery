from fastapi import FastAPI

app = FastAPI()

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