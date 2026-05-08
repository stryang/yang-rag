"""Core configuration module for Yang RAG System."""

import os
from pathlib import Path
from typing import List, Literal, Optional

from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class LLMConfig(BaseModel):
    """LLM provider configuration."""
    provider: Literal["openai", "ollama", "siliconflow", "qwen"] = "openai"
    model: str = "gpt-4o-mini"
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    temperature: float = 0.7
    max_tokens: int = 2000


class EmbeddingConfig(BaseModel):
    """Embedding provider configuration."""
    provider: Literal["openai", "ollama", "siliconflow", "local", "huggingface"] = "openai"
    model: str = "text-embedding-3-small"
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    dimension: int = 1536


class Settings(BaseSettings):
    """Application settings with environment variable support."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ============== LLM Configuration ==============
    # Provider: openai, ollama, siliconflow, qwen
    llm_provider: Literal["openai", "ollama", "siliconflow", "qwen"] = Field(
        default="openai", alias="LLM_PROVIDER"
    )
    llm_model: str = Field(default="gpt-4o-mini", alias="LLM_MODEL")
    llm_api_key: str = Field(default="", alias="LLM_API_KEY")
    llm_base_url: Optional[str] = Field(default=None, alias="LLM_BASE_URL")
    llm_temperature: float = Field(default=0.7, alias="LLM_TEMPERATURE")
    llm_max_tokens: int = Field(default=2000, alias="LLM_MAX_TOKENS")

    # ============== Embedding Configuration ==============
    # Provider: openai, ollama, siliconflow, local, huggingface
    embedding_provider: Literal["openai", "ollama", "siliconflow", "local", "huggingface"] = Field(
        default="openai", alias="EMBEDDING_PROVIDER"
    )
    embedding_model: str = Field(default="text-embedding-3-small", alias="EMBEDDING_MODEL")
    embedding_api_key: str = Field(default="", alias="EMBEDDING_API_KEY")
    embedding_base_url: Optional[str] = Field(default=None, alias="EMBEDDING_BASE_URL")
    embedding_dimension: int = Field(default=1536, alias="EMBEDDING_DIMENSION")

    # ============== Vector Store ==============
    vector_store_type: Literal["chroma", "faiss", "milvus"] = Field(
        default="chroma", alias="VECTOR_STORE_TYPE"
    )
    vector_store_persist_dir: Path = Field(
        default=Path("./data/vectorstore"), alias="VECTOR_STORE_PERSIST_DIR"
    )

    # ChromaDB
    chroma_tenant: str = Field(default="default_tenant", alias="CHROMA_TENANT")
    chroma_database: str = Field(default="default_database", alias="CHROMA_DATABASE")

    # Milvus (optional)
    milvus_host: str = Field(default="localhost", alias="MILVUS_HOST")
    milvus_port: int = Field(default=19530, alias="MILVUS_PORT")
    milvus_collection: str = Field(default="yang_rag", alias="MILVUS_COLLECTION")

    # ============== API Configuration ==============
    api_host: str = Field(default="0.0.0.0", alias="API_HOST")
    api_port: int = Field(default=8000, alias="API_PORT")
    api_key: str = Field(default="rag-secret-key", alias="API_KEY")

    # MCP Server
    mcp_server_host: str = Field(default="0.0.0.0", alias="MCP_SERVER_HOST")
    mcp_server_port: int = Field(default=8001, alias="MCP_SERVER_PORT")

    # ============== Retrieval Settings ==============
    retrieval_top_k: int = Field(default=5, alias="RETRIEVAL_TOP_K")
    rerank_top_k: int = Field(default=3, alias="RERANK_TOP_K")
    chunk_size: int = Field(default=500, alias="CHUNK_SIZE")
    chunk_overlap: int = Field(default=50, alias="CHUNK_OVERLAP")

    # ============== Supported File Types ==============
    supported_file_types: List[str] = Field(
        default=[".pdf", ".docx", ".doc", ".txt", ".md", ".html", ".pptx", ".xlsx"],
        alias="SUPPORTED_FILE_TYPES",
    )

    # ============== CORS ==============
    cors_origins: List[str] = Field(
        default=["http://localhost:3000", "http://localhost:5173"],
        alias="CORS_ORIGINS",
    )

    @property
    def is_production(self) -> bool:
        """Check if running in production."""
        return os.getenv("ENVIRONMENT", "development") == "production"

    @property
    def llm_config(self) -> LLMConfig:
        """Get LLM configuration."""
        return LLMConfig(
            provider=self.llm_provider,
            model=self.llm_model,
            api_key=self.llm_api_key or None,
            base_url=self.llm_base_url,
            temperature=self.llm_temperature,
            max_tokens=self.llm_max_tokens,
        )

    @property
    def embedding_config(self) -> EmbeddingConfig:
        """Get embedding configuration."""
        return EmbeddingConfig(
            provider=self.embedding_provider,
            model=self.embedding_model,
            api_key=self.embedding_api_key or None,
            base_url=self.embedding_base_url,
            dimension=self.embedding_dimension,
        )

    def ensure_directories(self) -> None:
        """Ensure required directories exist."""
        self.vector_store_persist_dir.mkdir(parents=True, exist_ok=True)


def get_settings() -> Settings:
    """Get singleton settings instance."""
    return Settings()


def is_placeholder_secret(value: Optional[str]) -> bool:
    """Return whether a configured secret still looks like a template placeholder."""
    if value is None:
        return True

    normalized = value.strip().lower()
    if not normalized:
        return True

    markers = (
        "sk-your-",
        "your-openai-api-key",
        "your-api-key",
        "sk-xxx",
        "your-siliconflow-key",
        "your-aliyun-key",
        "您的",
        "你的",
    )
    return any(marker in normalized for marker in markers)


def reload_settings() -> Settings:
    """Reload settings from the current runtime environment and .env file."""
    refreshed = Settings()
    for field_name in Settings.model_fields:
        setattr(settings, field_name, getattr(refreshed, field_name))
    settings.ensure_directories()
    return settings


# Global settings instance
settings = get_settings()
