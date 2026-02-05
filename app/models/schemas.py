"""Pydantic schemas for API requests and responses."""

from typing import List, Optional
from pydantic import BaseModel, Field


# Search schemas
class SearchRequest(BaseModel):
    query: str = Field(..., min_length=1)
    top_k: int = Field(5, ge=1, le=20)
    threshold: float = Field(0.5, ge=0.0, le=1.0)


class SearchResult(BaseModel):
    chunk_id: str
    title: str
    content: str
    source: str
    semantic_score: float
    bm25_score: Optional[float] = None
    hybrid_score: Optional[float] = None
    score: float
    image_type: Optional[str] = None


class SearchResponse(BaseModel):
    query: str
    results: List[SearchResult]
    count: int


# Document schemas
class DocumentMetadata(BaseModel):
    total_slides: Optional[int] = None
    total_pages: Optional[int] = None
    images_processed: int = 0


class DocumentResponse(BaseModel):
    id: str
    title: str
    source_type: str
    status: str
    created_at: str
    metadata: DocumentMetadata
