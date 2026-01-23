# Product Requirements Document (PRD)
## DocuQuery - Multi-Tenant Document Q&A Platform

**Version**: 1.0  
**Author**: Jiehoon Lee  
**Date**: January 22, 2026  
**Status**: Planning

---

## 1. Executive Summary

**Project Name**: DocuQuery  
**Project Type**: Portfolio Project / Technical Showcase  
**Timeline**: 2-3 weeks (14-21 days)  

### Problem Statement
Organizations struggle to extract insights from their internal documents (contracts, reports, policies, manuals). Existing solutions are either too expensive for small teams or require significant technical setup. There's a need for an accessible, multi-tenant platform that allows teams to upload documents and query them using natural language.

### Solution
DocuQuery is a multi-tenant SaaS platform that enables organizations to:
- Upload and manage internal documents securely
- Query documents using natural language
- Get AI-generated answers with source citations
- Maintain data isolation between organizations
- Monitor usage and stay within quotas

### Success Criteria (Portfolio Perspective)
1. **Demonstrates technical depth**: Showcases distributed systems, cloud infrastructure, and scalability patterns
2. **Production-ready architecture**: Not over-engineered, but includes essential production patterns (monitoring, error handling, testing)
3. **Completable in timeline**: MVP in 7-10 days, full showcase in 14-21 days
4. **Conversation starter**: Each architectural decision has a defensible rationale
5. **Cost-effective**: Runs on <$50/month, can be torn down between interviews

---

## 2. Goals & Objectives

### Primary Objectives
1. Build a functional multi-tenant RAG (Retrieval-Augmented Generation) platform
2. Demonstrate proficiency with Python backend, Docker, AWS, and distributed systems
3. Implement production-grade observability and monitoring
4. Document architectural decisions and trade-offs professionally

### Secondary Objectives
1. Practice basic frontend development (React/Next.js)
2. Implement CI/CD pipeline with GitHub Actions
3. Write comprehensive technical documentation
4. Create demo video and architecture diagrams

### Non-Goals (Out of Scope for Portfolio)
- Production-level security hardening (OAuth 2.0, SOC 2 compliance)
- Payment processing / billing system
- Advanced admin dashboard with analytics
- Mobile applications
- Support for 100+ document formats
- Multi-region deployment
- High availability (99.99% uptime)

---

## 3. User Personas

### Primary Persona: Small Business Owner (Tenant Admin)
- **Name**: Sarah, Restaurant Owner
- **Goals**: Access internal SOPs, training materials, and policies quickly
- **Pain Points**: Information scattered across Google Docs, doesn't want to read 50-page PDFs
- **Technical Skill**: Low, needs simple interface

### Secondary Persona: Team Member (Tenant User)
- **Name**: Mike, Restaurant Manager
- **Goals**: Find answers to operational questions during busy hours
- **Pain Points**: Can't remember all procedures, owner is too busy to answer
- **Technical Skill**: Low to medium

### Tertiary Persona: Hiring Manager/Recruiter
- **Name**: Alex, Senior Backend Engineer
- **Goals**: Evaluate candidate's architecture, coding, and infrastructure skills
- **Pain Points**: Sees too many over-engineered or under-documented portfolio projects
- **Technical Skill**: Expert
- **What they look for**: 
  - Clear architectural decisions
  - Production patterns (not just "works on my machine")
  - Understanding of trade-offs and scalability
  - Clean, readable code
  - Comprehensive documentation

---

## 4. User Stories & Use Cases

### Epic 1: Tenant Management
**As a** business owner,  
**I want to** create an organization account,  
**So that** I can start uploading and querying my documents securely.

- US-1.1: User registration with email/password
- US-1.2: Organization creation during signup
- US-1.3: API key generation for programmatic access
- US-1.4: View organization quotas (storage, queries)
- US-1.5: Invite team members to organization (future)

**Acceptance Criteria**:
- User can register with valid email/password
- Each organization gets unique tenant ID and API key
- Tenant data is isolated from other tenants
- Quotas are enforced (100MB storage, 1000 queries/month for free tier)

### Epic 2: Document Management
**As a** team member,  
**I want to** upload documents to the platform,  
**So that** I can query them later using natural language.

- US-2.1: Upload single document (PDF, DOCX, TXT)
- US-2.2: View list of uploaded documents
- US-2.3: See document processing status (queued, processing, ready, failed)
- US-2.4: Delete documents
- US-2.5: Add metadata to documents (title, category, tags)
- US-2.6: View storage usage

**Acceptance Criteria**:
- Supports PDF, DOCX, TXT formats
- Max file size: 10MB per document
- Processing completes within 5 minutes for typical document
- User receives feedback on processing status
- Documents are chunked and embedded automatically

### Epic 3: Document Querying (RAG)
**As a** team member,  
**I want to** ask questions about my documents in natural language,  
**So that** I can quickly find information without manual searching.

- US-3.1: Submit natural language query
- US-3.2: Receive AI-generated answer with source citations
- US-3.3: View source chunks that were used for the answer
- US-3.4: Filter queries by specific documents or categories
- US-3.5: See query history (optional)

**Acceptance Criteria**:
- Query returns answer within 3 seconds (p95)
- Answer includes citation numbers linking to source chunks
- User can click on citations to see full source text
- Cache reduces cost for repeated queries by 40%+
- Gracefully handles queries with no relevant information

### Epic 4: API Access
**As a** developer in an organization,  
**I want to** access DocuQuery via REST API,  
**So that** I can integrate it into my own applications.

- US-4.1: Authenticate using API key
- US-4.2: Upload documents via API
- US-4.3: Query documents via API
- US-4.4: List documents via API
- US-4.5: Rate limiting per API key

**Acceptance Criteria**:
- API is RESTful with clear endpoints
- API returns consistent JSON responses
- Rate limits enforced (100 requests/hour per tenant)
- Auto-generated API documentation (Swagger/OpenAPI)

### Epic 5: Monitoring & Observability
**As a** platform operator (developer),  
**I want to** monitor system health and performance,  
**So that** I can identify bottlenecks and demonstrate operational maturity.

- US-5.1: Prometheus metrics for all critical paths
- US-5.2: Grafana dashboards for visualization
- US-5.3: Distributed tracing with OpenTelemetry
- US-5.4: Structured logging with request IDs
- US-5.5: Cost tracking (LLM tokens used per tenant)

**Acceptance Criteria**:
- Key metrics tracked: request latency, cache hit rate, queue depth, error rate
- Dashboards show real-time and historical data
- Traces show end-to-end request flow across services
- Logs are searchable and include context (tenant_id, request_id)

---

## 5. Functional Requirements

### FR-1: Authentication & Authorization
- FR-1.1: Support email/password registration and login
- FR-1.2: Generate secure API keys (format: `dk_` + 32 random characters)
- FR-1.3: Validate API keys on every request
- FR-1.4: Support both JWT tokens (web) and API keys (programmatic)

### FR-2: Document Upload & Processing
- FR-2.1: Accept PDF, DOCX, TXT files up to 10MB
- FR-2.2: Store original files in S3 with tenant namespacing
- FR-2.3: Extract text from documents (PyPDF2, python-docx)
- FR-2.4: Chunk text into 512-character segments with 50-char overlap
- FR-2.5: Generate embeddings using sentence-transformers (all-MiniLM-L6-v2)
- FR-2.6: Store embeddings in Qdrant with metadata (tenant_id, document_id, chunk_index)
- FR-2.7: Process documents asynchronously using SQS + Lambda/ECS
- FR-2.8: Update document status in real-time

### FR-3: Document Querying
- FR-3.1: Accept natural language queries up to 500 characters
- FR-3.2: Generate query embeddings using same model as documents
- FR-3.3: Perform vector similarity search in Qdrant (top 5 results)
- FR-3.4: Construct prompt with retrieved chunks + user query
- FR-3.5: Call LLM API (OpenAI GPT-3.5 or Claude Haiku)
- FR-3.6: Parse response and add citation numbers
- FR-3.7: Cache query results for 1 hour

### FR-4: Multi-Tenancy
- FR-4.1: Isolate tenant data using separate Qdrant collections
- FR-4.2: Filter all database queries by tenant_id
- FR-4.3: Enforce per-tenant rate limits (100 req/hour)
- FR-4.4: Enforce storage quotas (100MB free tier)
- FR-4.5: Track per-tenant usage metrics

### FR-5: API Endpoints
```
POST   /api/v1/auth/register          - Create account
POST   /api/v1/auth/login             - Get JWT token
GET    /api/v1/auth/apikey            - Get API key

POST   /api/v1/documents/upload       - Upload document
GET    /api/v1/documents              - List documents
GET    /api/v1/documents/{id}         - Get document details
DELETE /api/v1/documents/{id}         - Delete document

POST   /api/v1/query                  - Query documents
GET    /api/v1/query/history          - Get query history (optional)

GET    /api/v1/usage                  - Get usage stats
GET    /health                        - Health check
GET    /metrics                       - Prometheus metrics
```

---

## 6. Non-Functional Requirements

### NFR-1: Performance
- Query latency (p95): <3 seconds
- Document upload: <5 seconds for 1MB file
- Document processing: <5 minutes for 10-page PDF
- API availability: 99% (portfolio acceptable)
- Cache hit rate: >40% under normal usage

### NFR-2: Scalability
- Support 10+ concurrent tenants
- Handle 100+ documents per tenant
- Process 10 documents simultaneously
- Support 50+ concurrent queries
- Demonstrate understanding of scaling to 100x

### NFR-3: Reliability
- Graceful degradation when LLM API is down
- Automatic retry on transient failures (3 attempts)
- Dead letter queue for failed document processing
- Transaction rollback on partial failures
- Comprehensive error messages in API responses

### NFR-4: Security
- Passwords hashed with bcrypt (cost factor: 12)
- API keys stored hashed in database
- HTTPS only in production
- Tenant data isolation (cannot access other tenant's data)
- Input validation on all endpoints
- SQL injection prevention (use ORM)

### NFR-5: Observability
- 100% of critical paths instrumented with metrics
- All errors logged with stack traces
- Request tracing across all services
- Cost tracking (LLM tokens, storage, compute)
- Dashboards for key SLIs (latency, error rate, saturation)

### NFR-6: Maintainability
- Code coverage: >70% (unit + integration tests)
- Type hints on all Python functions
- Docstrings for all public functions
- README with architecture diagram
- API documentation auto-generated
- Clear commit messages (Conventional Commits)

### NFR-7: Cost Efficiency
- Development: <$10/month
- Production demo: <$100/month
- Use AWS Free Tier where possible
- Cache to reduce LLM API costs by 40%+
- Self-hosted embeddings (free vs paid API)

---

## 7. Technical Requirements

### TR-1: Technology Stack
**Backend**: Python 3.11+, FastAPI, SQLAlchemy, Pydantic  
**Database**: PostgreSQL 15 (metadata), Qdrant 1.7+ (vectors)  
**Cache**: Redis 7+  
**Queue**: AWS SQS  
**Storage**: AWS S3  
**Compute**: AWS Lambda (processing), AWS ECS/EC2 (API)  
**Monitoring**: Prometheus, Grafana, OpenTelemetry  
**Frontend**: React 18+ with TypeScript (minimal, basic UI only)  
**IaC**: Terraform or AWS CDK (optional but impressive)  
**CI/CD**: GitHub Actions

### TR-2: Development Environment
- Docker Compose for local development
- Poetry or pip + requirements.txt for dependencies
- Pre-commit hooks for linting (black, isort, mypy)
- Unit tests with pytest
- Integration tests with pytest + testcontainers

### TR-3: Deployment
- Containerized application (Dockerfile)
- Deploy API to AWS ECS Fargate or EC2
- Deploy Qdrant to EC2 (self-hosted)
- Use AWS managed services (RDS, ElastiCache, S3, SQS)
- Infrastructure as Code (Terraform or CDK)
- Blue-green deployment capability (demo in README)

### TR-4: Data Models

**User**:
```python
id: UUID
email: str
password_hash: str
created_at: datetime
```

**Organization (Tenant)**:
```python
id: UUID
name: str
api_key_hash: str
storage_used_mb: int
queries_this_month: int
created_at: datetime
```

**Document**:
```python
id: UUID
tenant_id: UUID
title: str
file_path: str (S3)
file_size_bytes: int
status: enum (queued, processing, ready, failed)
chunks_count: int
created_at: datetime
processed_at: datetime
error_message: str (nullable)
```

**Query** (optional, for history):
```python
id: UUID
tenant_id: UUID
query_text: str
answer: str
sources: JSON
cache_hit: bool
latency_ms: int
created_at: datetime
```

---

## 8. Success Metrics

### For Portfolio (Hiring Manager Perspective)
1. **Demonstrates technical depth**: ✅ Distributed systems, async processing, multi-tenancy
2. **Production patterns**: ✅ Monitoring, caching, error handling, rate limiting
3. **Defensible architecture**: ✅ Every decision has rationale documented
4. **Clean code**: ✅ Typed, tested, linted
5. **Documentation quality**: ✅ README, architecture diagram, API docs, blog post

### For Platform (User Perspective)
1. Query accuracy: Answers are relevant >80% of the time
2. Query speed: p95 latency <3 seconds
3. Upload reliability: 99%+ success rate
4. Cost efficiency: <$0.01 per query (with caching)

### Key Performance Indicators (KPIs)
- Average query latency (target: <2 seconds p95)
- Cache hit rate (target: >40%)
- Document processing success rate (target: >95%)
- Cost per 1000 queries (target: <$2.50)
- Code coverage (target: >70%)

---

## 9. Timeline & Milestones

### Phase 1: MVP (Week 1) - Days 1-7
**Goal**: Single-tenant RAG that works end-to-end locally

Milestones:
- ✅ Project setup complete (Docker Compose, FastAPI skeleton)
- ✅ Document upload works (stores in local filesystem)
- ✅ Document processing works (chunking, embeddings, Qdrant)
- ✅ Query endpoint works (embedding → search → LLM → response)
- ✅ Basic error handling and validation

### Phase 2: Production Patterns (Week 2) - Days 8-14
**Goal**: Multi-tenant with AWS infrastructure

Milestones:
- ✅ Multi-tenant isolation (collections, rate limiting, quotas)
- ✅ AWS integration (S3, SQS, Lambda/ECS)
- ✅ Caching layer (Redis)
- ✅ Authentication (API keys, JWT)
- ✅ Deployed to AWS (ECS/EC2)

### Phase 3: Polish & Documentation (Week 3) - Days 15-21
**Goal**: Interview-ready showcase

Milestones:
- ✅ Monitoring stack (Prometheus, Grafana, OpenTelemetry)
- ✅ Load testing with results
- ✅ Comprehensive README with architecture diagram
- ✅ API documentation (Swagger)
- ✅ Demo video or screenshots
- ✅ Blog post explaining design decisions

---

## 10. Risks & Mitigation

### Risk 1: Scope Creep
**Probability**: High  
**Impact**: High (won't finish on time)  
**Mitigation**: 
- Strictly follow MVP → Production → Polish phases
- Mark features as "future work" if not essential
- Timebox each feature (2 hours max before re-evaluating)

### Risk 2: AWS Costs
**Probability**: Medium  
**Impact**: Medium ($100+ monthly bill)  
**Mitigation**:
- Use AWS Free Tier religiously
- Set billing alerts at $20, $50, $100
- Tear down after demo/interviews
- Document infrastructure to rebuild easily

### Risk 3: LLM API Availability/Cost
**Probability**: Low  
**Impact**: Medium  
**Mitigation**:
- Implement aggressive caching (40%+ hit rate)
- Use cheapest models (GPT-3.5/Haiku)
- Mock LLM responses in tests
- Have fallback: "LLM unavailable, here are relevant chunks"

### Risk 4: Technical Blockers
**Probability**: Medium  
**Impact**: High (delays entire project)  
**Mitigation**:
- Spike risky components early (Qdrant, SQS, embeddings)
- Have simple fallback implementations
- Budget 3-4 days for unexpected issues

### Risk 5: Over-Engineering
**Probability**: Medium  
**Impact**: Medium (looks bad to recruiters)  
**Mitigation**:
- Document WHY each complexity is needed
- Ask: "Is this solving a real problem or just impressive?"
- Get feedback from engineer friends

---

## 11. Future Enhancements (Out of Scope)

These are explicitly **not** included in the portfolio version but should be documented in README as "Future Work" to show you're thinking ahead:

1. **Team collaboration**: Invite users, role-based access control
2. **Advanced RAG**: Re-ranking, hybrid search (BM25 + vector), query expansion
3. **Document formats**: Excel, PowerPoint, images (OCR)
4. **Multi-modal**: Image search, audio transcription
5. **Analytics dashboard**: Query trends, most-asked questions, document usage
6. **Billing system**: Stripe integration, usage-based pricing
7. **Fine-tuned embeddings**: Train custom embedding model on domain data
8. **Multi-region**: Deploy to multiple AWS regions for latency
9. **Webhooks**: Notify on document processing completion
10. **Integrations**: Slack bot, Chrome extension, API SDKs

---

## 12. Appendix

### A. Reference Architecture Diagram
[To be created in draw.io or Excalidraw - see planning document]

### B. API Example Requests
[To be documented in OpenAPI/Swagger]

### C. Glossary
- **RAG**: Retrieval-Augmented Generation - AI technique that retrieves relevant context before generating answers
- **Embedding**: Vector representation of text (typically 384-1536 dimensions)
- **Vector Database**: Database optimized for similarity search on embeddings
- **Chunking**: Breaking documents into smaller segments for embedding
- **Multi-tenancy**: Single system serving multiple isolated customers
- **SQS**: Simple Queue Service - AWS managed message queue
- **ECS**: Elastic Container Service - AWS container orchestration

### D. Related Resources
- OpenAI Embeddings Guide: https://platform.openai.com/docs/guides/embeddings
- Qdrant Documentation: https://qdrant.tech/documentation/
- LangChain RAG Tutorial: https://python.langchain.com/docs/use_cases/question_answering/
- FastAPI Best Practices: https://fastapi.tiangolo.com/tutorial/

---

**Document Owner**: Jiehoon Lee  
**Last Updated**: January 22, 2026  
**Next Review**: Upon Phase 1 completion