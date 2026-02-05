"""Hybrid search with RRF fusion."""

from typing import List, Dict, Any
from .embeddings import generate_embedding
from .storage import get_supabase_client


def search_hybrid(
    query: str,
    top_k: int = 5,
    threshold: float = 0.5,
    k_constant: int = 60
) -> List[Dict[str, Any]]:
    """
    Hybrid search with Reciprocal Rank Fusion (RRF).

    Combines semantic (vector) + keyword (BM25) search for better results.

    Args:
        query: Search query
        top_k: Max results
        threshold: Min semantic similarity
        k_constant: RRF constant (60 = balanced)

    Returns:
        Results with semantic_score, bm25_score, hybrid_score
    """
    supabase = get_supabase_client()

    # Generate query embedding
    query_embedding = generate_embedding(query, task_type="RETRIEVAL_QUERY")

    # Call hybrid search RPC
    response = supabase.rpc(
        "match_chunks_hybrid_rrf",
        {
            "query_embedding": query_embedding,
            "query_text": query,
            "match_threshold": threshold,
            "match_count": top_k,
            "k_constant": k_constant
        }
    ).execute()

    # Format results
    results = []
    for chunk in response.data:
        results.append({
            "chunk_id": chunk.get("chunk_id"),
            "title": chunk.get("document_title", "Unknown"),
            "section": chunk.get("section_title"),
            "content": chunk.get("content", ""),
            "source": chunk.get("source_path", ""),
            "image_type": chunk.get("image_type"),
            "semantic_score": chunk.get("semantic_score", 0.0),
            "bm25_score": chunk.get("bm25_score", 0.0),
            "hybrid_score": chunk.get("hybrid_score", 0.0),
            "score": chunk.get("hybrid_score", 0.0),
            "date": chunk.get("document_date")
        })

    return results
