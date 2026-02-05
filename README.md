# BEI Knowledge Hub v3

Vision-powered RAG system with Gemini 2.0 Flash for document understanding.

## Architecture

**FastAPI microservice** for ingesting PPTX/PDF/DOCX documents with vision processing:
- Gemini 2.0 Flash for chart/table/diagram extraction
- Hybrid search (semantic + BM25 via RRF fusion)
- Document versioning with incremental updates
- OpenTelemetry + Langfuse observability
- Supabase pgvector storage

## Tech Stack

- **Framework**: FastAPI
- **Vision**: Gemini 2.0 Flash (google-genai SDK)
- **Search**: Supabase pgvector + hybrid search
- **Extractors**: python-pptx, pypdf, python-docx
- **Observability**: OpenTelemetry, Langfuse
- **Deployment**: Docker + AWS Swarm

## Project Structure

```
bei-knowledge-hub/
├── app/
│   ├── api/            # FastAPI routers
│   ├── services/       # Business logic
│   ├── extractors/     # Document parsers
│   ├── models/         # Pydantic schemas
│   ├── config.py       # Configuration
│   └── main.py         # FastAPI app
├── tests/              # Pytest tests
├── migrations/         # Supabase migrations
├── .github/workflows/  # CI/CD
├── Dockerfile
├── docker-compose.yml
└── requirements.txt
```

## Development Setup

### Prerequisites

- Python 3.11+
- Docker
- Doppler CLI (for secrets)

### Install Dependencies

```bash
pip install -r requirements.txt
```

### Configure Secrets

```bash
# Set up Doppler (all secrets managed there)
doppler login
doppler setup --project bei-knowledge-hub --config dev
```

Required secrets:
- `GEMINI_API_KEY` - Google AI API key
- `SUPABASE_URL` - Supabase project URL
- `SUPABASE_SERVICE_ROLE_KEY` - Supabase admin key
- `LANGFUSE_PUBLIC_KEY` - Observability
- `LANGFUSE_SECRET_KEY` - Observability

### Run Locally

```bash
# With Doppler (recommended)
doppler run -- uvicorn app.main:app --reload

# Or with .env file
cp .env.example .env
# Edit .env with your secrets
uvicorn app.main:app --reload
```

API available at: http://localhost:8000

## Testing

```bash
# Run all tests
pytest

# With coverage
pytest --cov=app tests/

# Specific test file
pytest tests/test_vision.py -v
```

## Deployment

**Target**: AWS Docker Swarm (separate service from Frappe ERP)

### Deployment Guards

- **Repository check**: Only deploys `bei-knowledge-hub`
- **Branch protection**: Only `main` branch deploys to production
- **No cross-contamination**: Cannot deploy to BEI-ERP or bei-tasks stacks

### CI/CD Pipeline

```bash
# Push triggers GitHub Actions
git push origin main

# Workflow:
# 1. Run tests
# 2. Build Docker image
# 3. Push to registry
# 4. Deploy to AWS Swarm (knowledge-hub service only)
```

## API Endpoints

### Ingest
- `POST /api/ingest` - Upload and process document
- `GET /api/documents` - List documents
- `GET /api/documents/{id}` - Get document details

### Search
- `POST /api/search` - Hybrid search (semantic + keyword)
- `POST /api/search/semantic` - Pure vector search
- `POST /api/search/enhanced` - Enriched with Frappe data

### Analytics
- `GET /api/analytics/queries` - Query logs
- `POST /api/feedback` - Submit feedback
- `GET /api/analytics/quality` - Content quality metrics

### Health
- `GET /health` - Service health check
- `GET /metrics` - Prometheus metrics

## Integration

### With Frappe ERP (Optional)

Knowledge Hub can enrich search results with live Frappe data:

```python
# Example: Enrich employee search with HR data
result = await search_enhanced(
    query="John Doe performance review",
    enrich_source="frappe",
    doctype="Employee"
)
```

### Authentication

Supports dual authentication:
1. **API Key** (header: `X-API-Key`)
2. **Frappe Session** (cookie: `sid`)

## Observability

- **Traces**: OpenTelemetry → Langfuse
- **Metrics**: Prometheus format at `/metrics`
- **Logs**: Structured JSON to stdout

## License

Proprietary - Bebang Enterprise Inc.
