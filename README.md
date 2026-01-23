# DocuQuery 🔍

> Multi-tenant document Q&A platform powered by RAG (Retrieval-Augmented Generation)

**Portfolio Project** | [Architecture](#architecture) | [Demo](#demo) | [API Docs](http://localhost:8000/docs)

## Overview

DocuQuery is a production-ready SaaS platform that enables organizations to upload their internal documents and query them using natural language. Built with Python, FastAPI, and AWS, it demonstrates distributed systems, multi-tenancy, and modern MLOps practices.

### Key Features

- 🔐 **Multi-tenant Architecture** - Complete data isolation per organization
- 📄 **Document Processing** - Async pipeline with SQS + Lambda
- 🤖 **RAG Pipeline** - Vector search + LLM for accurate Q&A
- ⚡ **High Performance** - Redis caching, 40%+ cache hit rate
- 📊 **Observability** - Prometheus metrics, Grafana dashboards, distributed tracing
- ☁️ **Cloud Native** - Deployed on AWS (ECS, RDS, S3, SQS)

## Tech Stack

**Backend**: Python 3.11, FastAPI, SQLAlchemy  
**Databases**: PostgreSQL (metadata), Qdrant (vectors), Redis (cache)  
**ML/AI**: Sentence Transformers, OpenAI GPT-3.5  
**AWS**: ECS, RDS, S3, SQS, Lambda  
**Monitoring**: Prometheus, Grafana, OpenTelemetry  
**Frontend**: React + TypeScript (minimal)

## Quick Start

[To be filled in during development]

## Architecture

[Architecture diagram to be added]

## Performance

[Load test results to be added]

## Development

See [Sprint Planning](docs/sprint_planning.md) for detailed task breakdown.

## License

MIT License - see LICENSE file