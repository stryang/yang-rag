"""Pydantic schemas for runtime settings management."""

from typing import Literal, Optional

from pydantic import BaseModel, Field


EmbeddingProvider = Literal["openai", "ollama", "siliconflow", "local", "huggingface"]
LLMProvider = Literal["openai", "ollama", "siliconflow", "qwen"]
VectorStoreType = Literal["chroma", "faiss", "milvus"]


class RuntimeSettingsBase(BaseModel):
    """Shared runtime settings payload."""

    llm_provider: LLMProvider = "openai"
    llm_model: str = Field(default="gpt-4o-mini", min_length=1, max_length=200)
    llm_api_key: str = ""
    llm_base_url: Optional[str] = None
    llm_temperature: float = Field(default=0.7, ge=0, le=2)
    llm_max_tokens: int = Field(default=2000, ge=1, le=16000)

    embedding_provider: EmbeddingProvider = "openai"
    embedding_model: str = Field(default="text-embedding-3-small", min_length=1, max_length=200)
    embedding_api_key: str = ""
    embedding_base_url: Optional[str] = None
    embedding_dimension: int = Field(default=1536, ge=1, le=16384)

    vector_store_type: VectorStoreType = "chroma"
    vector_store_persist_dir: str = "./data/vectorstore"
    milvus_host: str = "localhost"
    milvus_port: int = Field(default=19530, ge=1, le=65535)
    milvus_collection: str = Field(default="yang_rag", min_length=1, max_length=200)

    api_endpoint: str = "http://localhost:8000"


class RuntimeSettingsResponse(RuntimeSettingsBase):
    """Runtime settings response."""

    uses_placeholder_llm_key: bool = False
    uses_placeholder_embedding_key: bool = False


class RuntimeSettingsUpdate(RuntimeSettingsBase):
    """Runtime settings update payload."""


class RuntimeReloadResponse(BaseModel):
    """Response after triggering a RAG runtime reload."""

    status: str
    llm_provider: str
    llm_model: str
    embedding_provider: str
    embedding_model: str
    vector_store_type: str
