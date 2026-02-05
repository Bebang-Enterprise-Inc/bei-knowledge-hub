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
