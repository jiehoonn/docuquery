# =============================================================================
# DocuQuery Dockerfile - Multi-Stage Build
#
# Stage 1 (builder): Install Python dependencies using Poetry
# Stage 2 (runtime): Copy only what's needed for a slim production image
#
# Usage:
#   docker build -t docuquery .
#   docker run -p 8000:8000 --env-file .env docuquery
# =============================================================================

# --------------- Stage 1: Builder ---------------
# Full Python image with build tools for compiling C extensions (bcrypt, etc.)
FROM python:3.11-slim AS builder

WORKDIR /app

# Install Poetry + export plugin (needed to generate requirements.txt)
RUN pip install --no-cache-dir poetry poetry-plugin-export

# Copy dependency files first (Docker layer caching optimization)
# If these files don't change, Docker skips reinstalling dependencies
COPY pyproject.toml poetry.lock ./

# Export Poetry deps to requirements.txt (so runtime stage doesn't need Poetry)
# --without dev: exclude test/lint tools from production image
RUN poetry export --without dev -f requirements.txt -o requirements.txt

# Install dependencies into the system Python
RUN pip install --no-cache-dir -r requirements.txt


# --------------- Stage 2: Runtime ---------------
# Slim image — no build tools, no Poetry, just Python + our code
FROM python:3.11-slim

WORKDIR /app

# Copy installed packages from builder stage
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application source code
COPY app/ ./app/

# Expose the port FastAPI runs on
EXPOSE 8000

# Run the FastAPI server with Uvicorn
# --host 0.0.0.0: Listen on all interfaces (required inside Docker)
# --port 8000: Match the EXPOSE above
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]