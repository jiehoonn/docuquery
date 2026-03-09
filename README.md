# DocuQuery

> Multi-tenant document Q&A platform powered by RAG (Retrieval-Augmented Generation)

Upload documents. Ask questions. Get cited answers.

## Demo

**[Watch the product walkthrough on YouTube →](https://youtu.be/pc5CzUN9_Og)**

---

## What It Does

Organizations upload internal documents (PDF, DOCX, TXT) and query them with natural language. The system chunks documents, generates embeddings, performs vector search, and returns LLM-generated answers with source citations — each answer is grounded in the actual document content, not the model's general knowledge.

**Example:** A law firm uploads case filings and asks *"What constitutional amendments were cited in the Dobbs opinion?"* — DocuQuery returns the answer with `[1]`, `[2]` citations pointing to the exact source chunks.

---

## Architecture

```
Browser ──→ Next.js (3000) ──→ FastAPI (8000) ──→ PostgreSQL
                                    │
                                    ├──→ Qdrant (vector search)
                                    ├──→ Redis (query cache)
                                    └──→ Gemini (LLM)
```

**RAG Pipeline:**

```
User Question
     │
     ▼
┌─ Cache Hit? ──── YES ──→ Return cached answer (fast, free)
│      │
│     NO
│      ▼
│   Embed Question  (all-MiniLM-L6-v2, 384 dimensions)
│      │
│      ▼
│   Vector Search   (Qdrant, top 5 chunks, cosine similarity)
│      │
│      ▼
│   Generate Answer (Gemini 2.0 Flash, grounded prompt)
│      │
│      ▼
│   Cache Result    (Redis, TTL: 1 hour)
│      │
└──────▼
   Return Response  (answer + citations + sources)
```

---

## Tech Stack

| Layer | Technology |
|---|---|
| **Frontend** | Next.js 16, React 19, TypeScript, Tailwind CSS 4, shadcn/ui |
| **Backend** | Python 3.11, FastAPI, SQLAlchemy 2.0, Pydantic |
| **Databases** | PostgreSQL 15, Qdrant (vectors), Redis 7 (cache) |
| **AI/ML** | sentence-transformers (embeddings), Google Gemini 2.0 Flash (LLM) |
| **Infrastructure** | Docker Compose, Terraform (AWS: ECS, RDS, S3, SQS, Lambda) |
| **Testing** | pytest (48 unit tests), GitHub Actions CI |

---

## Key Features

- **Multi-Tenant Isolation** — Every PostgreSQL query filters by `tenant_id`. Each organization gets a dedicated Qdrant collection. File paths are namespaced by tenant. Cross-tenant data access is structurally impossible.
- **Dual Authentication** — JWT tokens (60-minute expiry) for the web UI; API keys (`X-API-Key: dk_...`) for programmatic access. A single `get_current_user` dependency handles both transparently.
- **Redis Query Cache** — Queries are hashed with SHA-256 and cached with a 1-hour TTL. Identical queries skip the entire RAG pipeline — no embedding, no vector search, no LLM call.
- **Graceful Degradation** — If Gemini is unavailable, the system returns the raw retrieved document chunks rather than returning an error.
- **Usage Tracking** — Per-tenant storage quotas (100MB), rate limiting (100 req/hour via atomic Redis counters), and monthly query counters.
- **Full Document Lifecycle** — Upload → chunk → embed → store → query → delete. Deletion cleans up storage, Qdrant vectors, and the PostgreSQL record atomically.

---

## Project Structure

```
docuquery/
├── app/                        # FastAPI backend
│   ├── api/v1/                 #   REST endpoints (auth, documents, query, usage)
│   ├── core/                   #   Config, security, multi-tenancy, rate limiting
│   ├── db/                     #   SQLAlchemy models, Alembic migrations
│   └── services/               #   RAG engine, embeddings, cache, Qdrant, storage
├── frontend/                   # Next.js web UI
│   └── src/
│       ├── app/                #   Pages (login, dashboard, documents, query, usage)
│       ├── components/ui/      #   shadcn/ui component library
│       └── lib/                #   API client, auth helpers
├── infrastructure/terraform/   # AWS IaC (VPC, ECS, RDS, S3, SQS, Lambda)
├── tests/unit/                 # 48 unit tests
├── docker-compose.yml          # 5-service local environment
└── Dockerfile                  # Multi-stage production build
```

---

## Quick Start

**Prerequisites:** Docker Desktop, a free [Gemini API key](https://aistudio.google.com/apikeys)

```bash
# 1. Clone the repository
git clone https://github.com/jiehoonn/docuquery.git
cd docuquery

# 2. Configure environment
cp .env.example .env
# Open .env and add your Gemini API key:
# GEMINI_API_KEY=your_key_here

# 3. Start all services
docker compose up --build

# 4. Open the app
# Frontend:  http://localhost:3000
# API Docs:  http://localhost:8000/docs
```

This starts 5 containers: FastAPI backend, Next.js frontend, PostgreSQL, Qdrant, and Redis.

---

## API Endpoints

All endpoints accept either `Authorization: Bearer <jwt>` or `X-API-Key: dk_...`

```
POST   /api/v1/auth/register       # Create account → returns JWT + API key
POST   /api/v1/auth/login          # Authenticate → returns JWT token

POST   /api/v1/documents/upload    # Upload document (PDF/DOCX/TXT, max 10MB)
GET    /api/v1/documents           # List documents for current organization
DELETE /api/v1/documents/{id}      # Delete document + vectors + file

POST   /api/v1/query               # Ask a question (full RAG pipeline)
GET    /api/v1/usage               # Storage, rate limits, query count
```

Full interactive documentation is available at `http://localhost:8000/docs` when running locally.

---

## Design Decisions

### 1. Multi-Layer Tenant Isolation

Tenant isolation is not a single API-level check — it is enforced at every layer of the stack:

- **PostgreSQL:** All queries filter by `tenant_id`. The `documents` table has a composite index on `(tenant_id, id)` for efficient scoped lookups.
- **Qdrant:** Each organization gets its own collection (`tenant_{tenant_id}`). Vector search is scoped to that collection — a misconfigured query cannot reach another tenant's vectors.
- **File Storage:** Paths follow `uploads/{tenant_id}/{document_id}/original.{ext}`. No shared namespace.

### 2. Dual Authentication with a Single Dependency

Two authentication methods are supported — JWT tokens and API keys — but endpoints don't need to know which was used. A single FastAPI dependency (`get_current_user`) handles both:

- **JWT tokens** are appropriate for the web UI (short-lived, 60-minute expiry).
- **API keys** are appropriate for scripts and integrations (long-lived, regeneratable).

Password hashing uses **bcrypt** (intentionally slow, 12 rounds — resistant to brute force). API key hashing uses **SHA-256** (fast). The asymmetry is intentional: API keys are checked on every request, making bcrypt's slowness a per-request bottleneck. SHA-256 is appropriate because API keys are already 32 cryptographically random characters.

### 3. Redis Cache with SHA-256 Query Hashing

Cache keys follow the format `query:{tenant_id}:{sha256(query_text)[:16]}`:

- The `tenant_id` prefix ensures cache isolation between organizations.
- SHA-256 produces a deterministic, fixed-length identifier for any query string.
- The first 16 hex characters (64 bits) keep keys short while maintaining negligible collision probability.
- TTL of 1 hour means stale answers naturally expire without manual invalidation.

### 4. Grounded LLM Prompting

The RAG prompt explicitly instructs Gemini to answer only from the provided context chunks and cite sources with `[1]`, `[2]` notation. This prevents hallucination — the model cannot reach outside what the system provides. If no relevant chunks are found, the system returns a clear "no documents found" message rather than generating an unsupported answer.

### 5. Frontend: One-Time API Key Modal

After registration, the API key is displayed exactly once in a modal dialog that cannot be accidentally dismissed. The key is rendered in a monospace, selectable format with a one-click copy button. The backend never stores the plaintext key — only a SHA-256 hash — so this is the user's only opportunity to save it.

### 6. Frontend: Usage Color Threshold System

The usage dashboard uses a single `getUsageLevel(current, limit)` utility that computes green / yellow / red status from a percentage threshold (< 50% healthy, 50–80% warning, > 80% critical). The same function drives both the storage card and the rate limit card, ensuring consistent visual feedback across all metrics from a single source of truth.

---

## Tradeoffs & Known Limitations

**Synchronous document processing:** Processing currently runs inline during the upload request, which blocks the HTTP response for large files. The fix is already mapped in the codebase: replace inline processing with an SQS queue and a Lambda/ECS consumer so uploads return immediately with `status: queued` and clients poll for completion.

**Cache invalidation gap:** If a document is deleted or re-uploaded, cached query answers based on old content persist until their TTL expires (up to 1 hour). A production fix would scan and delete affected cache keys on document deletion.

**Embedding model per instance:** The `all-MiniLM-L6-v2` model loads into every app instance at startup. At scale, this should move to a dedicated embedding service (SageMaker endpoint or separate container) so API servers and embedding compute scale independently.

**Local infrastructure:** Redis and file storage are local for development. Production replacements are: AWS ElastiCache (Redis with automatic failover) and S3 with server-side encryption (file storage). Both are abstracted behind service modules, making the swap straightforward.

---

## Testing

```bash
# Run unit tests
pytest tests/unit/ -v

# Lint
black --check .
isort --check-only .
```

48 tests covering: text chunking, Redis caching, JWT/API key security, LLM prompt construction, and the full RAG pipeline including graceful degradation.

---

## License

MIT
