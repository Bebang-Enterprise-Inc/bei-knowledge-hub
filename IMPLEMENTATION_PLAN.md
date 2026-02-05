# Knowledge Hub v3: Implementation Plan (Separate Repo)

> **Repository**: bei-knowledge-hub (standalone FastAPI microservice)
> **Adapted from**: BEI-ERP docs/plans/2026-02-05-knowledge-hub-v3-vision-api.md

**Goal:** Build vision-powered RAG system with Gemini 2.0 Flash, hybrid search, and production observability as a standalone FastAPI service.

**Architecture:** Separate microservice deployed alongside BEI-ERP in AWS Swarm, with isolated deployment pipeline.

**Tech Stack:** FastAPI, Gemini 2.0 Flash, python-pptx, PyPDF2, python-docx, Pillow, Supabase pgvector, OpenTelemetry, Langfuse

**Deployment Isolation:** GitHub Actions with deployment guards prevent cross-contamination with BEI-ERP or bei-tasks.

---

## Phase 1: Schema Migration & Database Setup

### Task 1: Add Vision Processing Fields to Schema

**Files:**
- Create: `migrations/006_add_vision_fields.sql`

**Steps:**
1. Create migration file (see below)
2. Load Supabase MCP tool
3. Execute migration via `mcp__supabase__execute_sql`
4. Verify columns exist
5. Commit

**Migration SQL:**
```sql
-- 006_add_vision_fields.sql
-- Add vision processing and hybrid search fields

-- Document-level version tracking
ALTER TABLE kb_documents ADD COLUMN IF NOT EXISTS version INT DEFAULT 1;
ALTER TABLE kb_documents ADD COLUMN IF NOT EXISTS previous_version_id UUID REFERENCES kb_documents(id);
ALTER TABLE kb_documents ADD COLUMN IF NOT EXISTS is_latest BOOLEAN DEFAULT true;
ALTER TABLE kb_documents ADD COLUMN IF NOT EXISTS source_url TEXT;
ALTER TABLE kb_documents ADD COLUMN IF NOT EXISTS last_modified_at TIMESTAMPTZ;
ALTER TABLE kb_documents ADD COLUMN IF NOT EXISTS content_checksum TEXT;
ALTER TABLE kb_documents ADD COLUMN IF NOT EXISTS view_count INT DEFAULT 0;
ALTER TABLE kb_documents ADD COLUMN IF NOT EXISTS last_accessed TIMESTAMPTZ;

-- Chunk-level vision and hybrid search
ALTER TABLE kb_chunks ADD COLUMN IF NOT EXISTS image_source TEXT;
ALTER TABLE kb_chunks ADD COLUMN IF NOT EXISTS image_type TEXT;
ALTER TABLE kb_chunks ADD COLUMN IF NOT EXISTS bm25_score FLOAT;
ALTER TABLE kb_chunks ADD COLUMN IF NOT EXISTS hybrid_score FLOAT;
ALTER TABLE kb_chunks ADD COLUMN IF NOT EXISTS helpful_count INT DEFAULT 0;
ALTER TABLE kb_chunks ADD COLUMN IF NOT EXISTS unhelpful_count INT DEFAULT 0;

-- Indexes for hybrid search
CREATE INDEX IF NOT EXISTS idx_kb_chunks_image_type ON kb_chunks(image_type);
CREATE INDEX IF NOT EXISTS idx_kb_documents_version ON kb_documents(version, is_latest);
CREATE INDEX IF NOT EXISTS idx_kb_documents_checksum ON kb_documents(content_checksum);

-- Full-text search support (BM25)
CREATE EXTENSION IF NOT EXISTS pg_trgm;
CREATE INDEX IF NOT EXISTS idx_kb_chunks_content_trgm ON kb_chunks USING gin(content gin_trgm_ops);
```

**Verification:**
```bash
doppler run -- python -c "from app.services.storage import get_supabase_client; s = get_supabase_client(); r = s.table('kb_chunks').select('id, image_source, image_type').limit(1).execute(); print('✅ Schema updated')"
```

---

### Task 2: Create Analytics Tables

**Files:**
- Create: `migrations/007_create_analytics_tables.sql`

**Migration SQL:**
```sql
-- 007_create_analytics_tables.sql
-- Query analytics and user feedback tables

-- Query log for observability
CREATE TABLE IF NOT EXISTS kb_query_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    query TEXT NOT NULL,
    user_id TEXT,
    results_count INT,
    response_time_ms INT,
    search_type TEXT DEFAULT 'semantic',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- User feedback for quality improvement
CREATE TABLE IF NOT EXISTS kb_feedback (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    query_id UUID REFERENCES kb_query_log(id) ON DELETE CASCADE,
    chunk_id UUID REFERENCES kb_chunks(id) ON DELETE CASCADE,
    rating INT CHECK (rating BETWEEN 1 AND 5),
    helpful BOOLEAN,
    comment TEXT,
    user_id TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for analytics queries
CREATE INDEX IF NOT EXISTS idx_query_log_created ON kb_query_log(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_query_log_user ON kb_query_log(user_id);
CREATE INDEX IF NOT EXISTS idx_feedback_chunk ON kb_feedback(chunk_id);
CREATE INDEX IF NOT EXISTS idx_feedback_helpful ON kb_feedback(helpful);
```

---

### Task 3: Create Hybrid Search RPC Function

**Files:**
- Create: `migrations/008_hybrid_search_rrf.sql`

**Migration SQL:**
```sql
-- 008_hybrid_search_rrf.sql
-- Hybrid search with Reciprocal Rank Fusion (RRF)

CREATE OR REPLACE FUNCTION match_chunks_hybrid_rrf(
    query_embedding vector(768),
    query_text TEXT,
    match_threshold FLOAT DEFAULT 0.5,
    match_count INT DEFAULT 5,
    k_constant INT DEFAULT 60
)
RETURNS TABLE (
    chunk_id UUID,
    document_id UUID,
    document_title TEXT,
    section_title TEXT,
    content TEXT,
    source_path TEXT,
    image_type TEXT,
    semantic_score FLOAT,
    bm25_score FLOAT,
    hybrid_score FLOAT,
    document_date TIMESTAMPTZ
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    WITH semantic_results AS (
        SELECT
            c.id,
            ROW_NUMBER() OVER (ORDER BY c.embedding <=> query_embedding) as rank
        FROM kb_chunks c
        JOIN kb_documents d ON c.document_id = d.id
        WHERE d.status = 'completed'
          AND c.quality_score >= 0.5
          AND 1 - (c.embedding <=> query_embedding) > match_threshold
        LIMIT match_count * 2
    ),
    keyword_results AS (
        SELECT
            c.id,
            ROW_NUMBER() OVER (ORDER BY similarity(c.content, query_text) DESC) as rank
        FROM kb_chunks c
        JOIN kb_documents d ON c.document_id = d.id
        WHERE d.status = 'completed'
          AND c.quality_score >= 0.5
          AND c.content % query_text
        LIMIT match_count * 2
    ),
    rrf_scores AS (
        SELECT
            COALESCE(s.id, k.id) as chunk_id,
            (1.0 / (k_constant + COALESCE(s.rank, 999999)))::FLOAT +
            (1.0 / (k_constant + COALESCE(k.rank, 999999)))::FLOAT as rrf_score,
            s.rank as semantic_rank,
            k.rank as keyword_rank
        FROM semantic_results s
        FULL OUTER JOIN keyword_results k ON s.id = k.id
    )
    SELECT
        c.id,
        c.document_id,
        d.title,
        c.section_title,
        c.content,
        d.source_path,
        c.image_type,
        (1 - (c.embedding <=> query_embedding))::FLOAT as semantic_score,
        similarity(c.content, query_text)::FLOAT as bm25_score,
        r.rrf_score as hybrid_score,
        d.created_at
    FROM rrf_scores r
    JOIN kb_chunks c ON r.chunk_id = c.id
    JOIN kb_documents d ON c.document_id = d.id
    ORDER BY r.rrf_score DESC
    LIMIT match_count;
END;
$$;
```

---

## Phase 2: Vision Processing Module

### Task 4: Create Vision Service with Gemini 2.0 Flash

**Files:**
- Create: `app/services/vision.py`
- Create: `tests/test_vision.py`

**TDD Approach:**
1. Write failing test
2. Run test (verify fails)
3. Write minimal implementation
4. Run test (verify passes)
5. Commit

**Test:** See original plan for full test code
**Implementation:** See original plan for full vision.py code

**Key Functions:**
- `classify_image()` - Returns chart|table|diagram|photo|decorative
- `extract_image_content()` - Extracts text from images
- `get_quality_score_for_type()` - Returns 0.0-1.0 score
- `process_image()` - Full pipeline

---

## Phase 3: Document Extractors

### Task 5: Update PPTX Extractor with Vision

**Files:**
- Create: `app/extractors/pptx.py`
- Modify: `tests/test_extractors.py`

### Task 6: Create PDF Extractor

**Files:**
- Create: `app/extractors/pdf.py`
- Modify: `tests/test_extractors.py`

### Task 7: Create DOCX Extractor

**Files:**
- Create: `app/extractors/docx.py`
- Modify: `tests/test_extractors.py`

---

## Phase 4: Search & Versioning

### Task 8: Hybrid Search Module

**Files:**
- Create: `app/services/search.py`
- Create: `tests/test_search.py`

### Task 9: Versioning Module

**Files:**
- Create: `app/services/versioning.py`
- Create: `tests/test_versioning.py`

---

## Phase 5: FastAPI Routes

### Task 10: Application Structure

**Files:**
- Update: `app/main.py`
- Create: `app/models/schemas.py`

### Task 11: Authentication Middleware

**Files:**
- Create: `app/middleware/auth.py`

### Task 12: Ingest Router

**Files:**
- Create: `app/api/ingest.py`
- Create: `tests/test_api_ingest.py`

### Task 13: Search Router

**Files:**
- Create: `app/api/search.py`
- Create: `tests/test_api_search.py`

---

## Phase 6: Observability

### Task 14: OpenTelemetry

**Files:**
- Create: `app/middleware/observability.py`
- Update: `app/main.py`

### Task 15: Analytics Router

**Files:**
- Create: `app/api/analytics.py`

---

## Phase 7: Deployment

### Task 16: Docker Optimization

**Files:**
- Update: `Dockerfile` (already exists, optimize)

### Task 17: Local Development

**Files:**
- Update: `docker-compose.yml` (already exists, enhance)

### Task 18: AWS Swarm Integration

**Files:**
- Create: `aws-swarm-stack.yml`

**Content:**
```yaml
version: '3.8'

services:
  knowledge-hub:
    image: ghcr.io/bebang-enterprise-inc/bei-knowledge-hub:latest
    deploy:
      replicas: 2
      update_config:
        parallelism: 1
        delay: 10s
      restart_policy:
        condition: on-failure
    environment:
      # Secrets via AWS Secrets Manager or Doppler
      - GEMINI_API_KEY=${GEMINI_API_KEY}
      - SUPABASE_URL=${SUPABASE_URL}
      - SUPABASE_SERVICE_ROLE_KEY=${SUPABASE_SERVICE_ROLE_KEY}
    ports:
      - "8000:8000"
    networks:
      - swarm-network
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

networks:
  swarm-network:
    external: true
```

---

## Phase 8: Testing & Documentation

### Task 19: Integration Tests

**Files:**
- Create: `tests/test_integration.py`

### Task 20: Update Documentation

**Files:**
- Update: `README.md` (already done)
- Create: `docs/API.md`
- Create: `docs/DEPLOYMENT.md`

---

## Execution Notes

**Repository Isolation:**
- ✅ Separate GitHub repo prevents accidental deployments to BEI-ERP
- ✅ Deployment guard in `.github/workflows/deploy.yml` verifies repo name
- ✅ AWS Swarm service name: `knowledge-hub` (not `frappe` or `bei-tasks`)

**Dependencies:**
- Gemini API key must be in Doppler: `GEMINI_API_KEY`
- Supabase credentials: `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY`

**Development Workflow:**
1. Create feature branch
2. Implement task with TDD
3. Run tests locally
4. Commit with descriptive message
5. Push to GitHub
6. Create PR to `main`
7. Merge triggers automatic deployment to AWS Swarm

**Deployment Flow:**
```
Push to main → GitHub Actions → Build Docker Image → AWS Swarm (knowledge-hub only)
```

**No Cross-Contamination:**
- BEI-ERP has its own GitHub Actions (`.github/workflows/build-and-deploy.yml`)
- bei-tasks has its own Vercel deployment
- bei-knowledge-hub has isolated deployment with guards
