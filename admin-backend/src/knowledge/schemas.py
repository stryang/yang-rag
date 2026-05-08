"""Knowledge base schemas."""

from typing import Optional, List, Any, Dict, Literal

from pydantic import BaseModel, Field


class KnowledgeBaseCreate(BaseModel):
    """Schema for creating a knowledge base."""
    name: str = Field(..., min_length=1, max_length=100)
    description: str = Field(default="", max_length=500)


class KnowledgeBaseUpdate(BaseModel):
    """Schema for updating a knowledge base."""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)


class KnowledgeBaseResponse(BaseModel):
    """Schema for knowledge base response."""
    id: str
    name: str
    description: str
    document_count: int
    chunk_count: int
    embedding_model: str
    created_at: str
    updated_at: str


class KnowledgeBaseListResponse(BaseModel):
    """Schema for list of knowledge bases response."""
    knowledge_bases: List[KnowledgeBaseResponse]
    total: int


class SearchRequest(BaseModel):
    """Schema for search request."""

    query: str = Field(..., min_length=1, max_length=1000)
    top_k: int = Field(default=5, ge=1, le=20)
    retrieval_mode: Literal["vector", "hybrid"] = "vector"
    retrieval_top_k: Optional[int] = Field(default=None, ge=1, le=50)
    use_reranker: bool = False
    reranker_type: Literal["simple", "cross-encoder", "llm"] = "simple"
    rerank_top_k: Optional[int] = Field(default=None, ge=1, le=20)
    filter_dict: Optional[Dict[str, Any]] = None


class SearchResult(BaseModel):
    """Schema for a single search result."""
    content: str
    metadata: Dict[str, Any]
    score: float


class SearchResponse(BaseModel):
    """Schema for search response."""

    query: str
    results: List[SearchResult]
    total: int
    retrieval_mode: Literal["vector", "hybrid"] = "vector"
    reranked: bool = False


class UploadResponse(BaseModel):
    """Schema for upload response."""
    status: str
    file_name: str
    document_count: int
    chunk_count: int
    knowledge_base_id: str
