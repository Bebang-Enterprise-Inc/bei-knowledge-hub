-- 008_hybrid_search_rrf.sql
-- Hybrid search with Reciprocal Rank Fusion (RRF)

CREATE OR REPLACE FUNCTION match_chunks_hybrid_rrf(
    query_embedding vector(768),
    query_text TEXT,
    match_threshold FLOAT DEFAULT 0.5,
    match_count INT DEFAULT 5,
    k_constant INT DEFAULT 60  -- RRF constant (higher = more democratic)
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
        -- Semantic search (vector similarity)
        SELECT
            c.id,
            ROW_NUMBER() OVER (ORDER BY c.embedding <=> query_embedding) as rank
        FROM kb_chunks c
        JOIN kb_documents d ON c.document_id = d.id
        WHERE d.status = 'completed'
          AND c.quality_score >= 0.5
          AND 1 - (c.embedding <=> query_embedding) > match_threshold
        LIMIT match_count * 2  -- Get more candidates for fusion
    ),
    keyword_results AS (
        -- Keyword search (BM25 approximation via trigram)
        SELECT
            c.id,
            ROW_NUMBER() OVER (ORDER BY similarity(c.content, query_text) DESC) as rank
        FROM kb_chunks c
        JOIN kb_documents d ON c.document_id = d.id
        WHERE d.status = 'completed'
          AND c.quality_score >= 0.5
          AND c.content % query_text  -- Trigram similarity
        LIMIT match_count * 2
    ),
    rrf_scores AS (
        -- Reciprocal Rank Fusion
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
