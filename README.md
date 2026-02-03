# DocuQuery

> Multi-tenant document Q&A platform powered by RAG (Retrieval-Augmented Generation)

Upload documents. Ask questions. Get cited answers.

## Demo

<!-- TODO: Add demo video -->
> *Demo video coming soon*

## What It Does

Organizations upload internal documents (PDF, DOCX, TXT) and query them with natural language. The system chunks documents, generates embeddings, performs vector search, and returns LLM-generated answers with source citations.

**Example:** A law firm uploads case filings and asks *"What constitutional amendments were cited in the Dobbs opinion?"* — DocuQuery returns the answer with `[1]`, `[2]` citations pointing to the exact source chunks.

## Architecture

```
Browser ──→ Next.js (3000) ──→ FastAPI (8000) ──→ PostgreSQL
                                    │
                                    ├──→ Qdrant (vector search)
                                    ├──→ Redis (query cache)
                                    └──→ Gemini (LLM)
```

**RAG Pipeline:** Question → Embed → Vector Search (top 5 chunks) → Build Prompt → LLM → Cached Response

## Tech Stack

| Layer | Technology |
|---|---|
| **Frontend** | Next.js 16, React 19, TypeScript, Tailwind CSS 4, shadcn/ui |
| **Backend** | Python 3.11, FastAPI, SQLAlchemy 2.0, Pydantic |
| **Databases** | PostgreSQL 15, Qdrant (vectors), Redis 7 (cache) |
| **AI/ML** | sentence-transformers (embeddings), Google Gemini (LLM) |
| **Infrastructure** | Docker Compose, Terraform (AWS: ECS, RDS, S3, SQS, Lambda) |
| **Testing** | pytest (48 unit tests), GitHub Actions CI |

## Key Features

- **Multi-Tenant Isolation** — Every query filters by `tenant_id`. Separate Qdrant collections per org. S3 paths namespaced by tenant.
- **Dual Authentication** — JWT tokens for the web UI, API keys (`X-API-Key`) for programmatic access.
- **Caching Layer** — Redis cache with SHA-256 query hashing. Target >40% hit rate to reduce LLM costs.
- **Graceful Degradation** — If the LLM is down, returns relevant document chunks instead of failing.
- **Usage Tracking** — Storage quotas (100MB), rate limiting (100 req/hour), monthly query counters.
- **Full Document Lifecycle** — Upload → chunk → embed → store → query → delete (cleans up S3 + Qdrant + PostgreSQL).

## Project Structure

```
docuquery/
├── app/                        # FastAPI backend
│   ├── api/v1/                 #   REST endpoints (auth, documents, query, usage)
│   ├── core/                   #   Config, security, multi-tenancy
│   ├── db/                     #   SQLAlchemy models, migrations
│   └── services/               #   RAG engine, embeddings, cache, Qdrant, S3
├── frontend/                   # Next.js web UI
│   └── src/
│       ├── app/                #   Pages (login, dashboard, query, usage)
│       ├── components/ui/      #   shadcn/ui components
│       └── lib/                #   API client, auth helpers
├── infrastructure/terraform/   # AWS IaC (VPC, ECS, RDS, S3, SQS)
├── tests/unit/                 # 48 unit tests (chunker, cache, security, RAG)
├── docker-compose.yml          # 5-service local environment
└── Dockerfile                  # Multi-stage production build
```

## Quick Start

```bash
# 1. Clone
git clone https://github.com/your-username/docuquery.git
cd docuquery

# 2. Configure
cp .env.example .env
# Add your Gemini API key (free at https://aistudio.google.com/apikeys)

# 3. Run
docker compose up --build

# 4. Open
# Frontend: http://localhost:3000
# API Docs: http://localhost:8000/docs
```

## API Endpoints

```
POST   /api/v1/auth/register       # Create account (returns API key)
POST   /api/v1/auth/login          # Get JWT token

POST   /api/v1/documents/upload    # Upload document (PDF/DOCX/TXT)
GET    /api/v1/documents           # List documents
DELETE /api/v1/documents/{id}      # Delete document + vectors + file

POST   /api/v1/query               # Ask a question (RAG pipeline)
GET    /api/v1/usage               # Storage, rate limits, query count
```

All endpoints accept either `Authorization: Bearer <jwt>` or `X-API-Key: dk_...`

## Testing

```bash
# Run unit tests
pytest tests/unit/ -v

# Lint
black --check .
isort --check-only .
```

48 tests covering: text chunking, Redis caching, JWT/API key security, LLM prompt construction, and the full RAG pipeline with graceful degradation.

## License

MIT