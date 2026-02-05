"""Search API router."""

from fastapi import APIRouter, Depends
from ..models.schemas import SearchRequest, SearchResponse, SearchResult
from ..services.search import search_hybrid
from ..middleware.auth import verify_api_key

router = APIRouter(dependencies=[Depends(verify_api_key)])


@router.post("/search", response_model=SearchResponse)
async def hybrid_search(request: SearchRequest):
    """
    Hybrid search (semantic + keyword with RRF fusion).

    Combines vector similarity and BM25 keyword matching.
    """
    results = search_hybrid(
        query=request.query,
        top_k=request.top_k,
        threshold=request.threshold
    )

    return SearchResponse(
        query=request.query,
        results=[SearchResult(**r) for r in results],
        count=len(results)
    )
