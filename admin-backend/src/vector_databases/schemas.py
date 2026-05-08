"""Pydantic schemas for vector database management."""

from datetime import datetime
from typing import Literal, Optional, List

from pydantic import BaseModel, Field, ConfigDict, model_validator


StoreType = Literal["chroma", "faiss", "milvus"]
StatusType = Literal["online", "warning", "offline", "unknown"]


class VectorDatabaseBase(BaseModel):
    """Base schema for managed vector database profiles."""

    name: str = Field(..., min_length=1, max_length=100)
    store_type: StoreType
    description: str = Field(default="", max_length=500)
    persist_path: Optional[str] = Field(default=None, max_length=255)
    host: Optional[str] = Field(default=None, max_length=255)
    port: Optional[int] = Field(default=None, ge=1, le=65535)
    collection_prefix: Optional[str] = Field(default=None, max_length=100)
    is_default: bool = False
    is_enabled: bool = True


class VectorDatabaseCreate(VectorDatabaseBase):
    """Schema for creating a managed vector database profile."""

    @model_validator(mode="after")
    def validate_target(self) -> "VectorDatabaseCreate":
        if self.store_type in {"chroma", "faiss"} and not self.persist_path:
            raise ValueError("persist_path is required for path-based vector stores")
        if self.store_type == "milvus":
            if not self.host:
                raise ValueError("host is required for Milvus")
            if self.port is None:
                raise ValueError("port is required for Milvus")
        return self


class VectorDatabaseUpdate(BaseModel):
    """Schema for updating a managed vector database profile."""

    name: Optional[str] = Field(default=None, min_length=1, max_length=100)
    store_type: Optional[StoreType] = None
    description: Optional[str] = Field(default=None, max_length=500)
    persist_path: Optional[str] = Field(default=None, max_length=255)
    host: Optional[str] = Field(default=None, max_length=255)
    port: Optional[int] = Field(default=None, ge=1, le=65535)
    collection_prefix: Optional[str] = Field(default=None, max_length=100)
    is_default: Optional[bool] = None
    is_enabled: Optional[bool] = None


class VectorDatabaseResponse(BaseModel):
    """Schema for vector database profile responses."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    store_type: StoreType
    description: str
    persist_path: Optional[str]
    host: Optional[str]
    port: Optional[int]
    collection_prefix: Optional[str]
    is_default: bool
    is_enabled: bool
    last_status: StatusType
    last_checked_at: Optional[datetime]
    last_error: Optional[str]
    created_at: datetime
    updated_at: datetime
    target: str


class VectorDatabaseListResponse(BaseModel):
    """Schema for vector database profile listing."""

    items: List[VectorDatabaseResponse]
    total: int


class VectorDatabaseTestResponse(BaseModel):
    """Schema for testing a vector database profile."""

    success: bool
    status: StatusType
    message: str
    checked_at: datetime
    resolved_target: str


class RuntimeCollectionSummary(BaseModel):
    """Summary of a knowledge-base-backed vector collection."""

    id: str
    name: str
    description: str
    document_count: int
    chunk_count: int
    embedding_model: str
    updated_at: str


class VectorDatabaseRuntimeResponse(BaseModel):
    """Schema for current runtime vector database overview."""

    store_type: StoreType
    status: StatusType
    target: str
    persist_path: Optional[str]
    host: Optional[str]
    port: Optional[int]
    message: str
    collection_count: int
    total_documents: int
    total_chunks: int
    storage_usage_bytes: int
    storage_usage_label: str
    managed_profiles: int
    collections: List[RuntimeCollectionSummary]
