-- 007_create_analytics_tables.sql
-- Query analytics and user feedback tables

-- Query log for observability
CREATE TABLE IF NOT EXISTS kb_query_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    query TEXT NOT NULL,
    user_id TEXT,
    results_count INT,
    response_time_ms INT,
    search_type TEXT DEFAULT 'semantic',  -- 'semantic', 'hybrid', 'enhanced'
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
