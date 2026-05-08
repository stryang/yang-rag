"""Embedding model for document vectorization."""

from typing import Any, Dict, List, Optional

from langchain_core.embeddings import Embeddings

from src.core.config import is_placeholder_secret


class BaseEmbedder(Embeddings):
    """Base class for embedding models."""

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Embed a list of documents."""
        raise NotImplementedError()

    def embed_query(self, text: str) -> List[float]:
        """Embed a single query."""
        raise NotImplementedError()


class OpenAIEmbedder(BaseEmbedder):
    """OpenAI embedding model wrapper."""

    def __init__(
        self,
        model: str = "text-embedding-3-small",
        dimension: int = 1536,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        **kwargs,
    ):
        """Initialize OpenAI embedder."""
        if is_placeholder_secret(api_key):
            raise ValueError("OpenAI Embedding API Key 未配置，请先在系统设置中保存有效的 EMBEDDING_API_KEY。")
        self.model = model
        self.dimension = dimension
        from langchain_openai import OpenAIEmbeddings
        self._embeddings = OpenAIEmbeddings(
            model=model,
            dimensions=dimension,
            api_key=api_key,
            base_url=base_url,
            check_embedding_ctx_length=False,
            **kwargs,
        )

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Embed documents."""
        return self._embeddings.embed_documents(texts)

    def embed_query(self, text: str) -> List[float]:
        """Embed query."""
        return self._embeddings.embed_query(text)


class HuggingFaceEmbedder(BaseEmbedder):
    """HuggingFace embedding model wrapper (free, local)."""

    DEFAULT_MODELS = {
        "bge-small": "BAAI/bge-small-en-v1.5",
        "bge-base": "BAAI/bge-base-en-v1.5",
        "bge-large": "BAAI/bge-large-en-v1.5",
        "bge-small-zh": "BAAI/bge-small-zh-v1.5",
        "bge-base-zh": "BAAI/bge-base-zh-v1.5",
        "bge-large-zh": "BAAI/bge-large-zh-v1.5",
    }

    def __init__(
        self,
        model_name: str = "bge-small-zh",
        device: str = "cpu",
        encode_kwargs: Optional[Dict[str, Any]] = None,
        query_instruction: Optional[str] = None,
        **kwargs,
    ):
        """Initialize HuggingFace embedder."""
        if model_name in self.DEFAULT_MODELS:
            model_name = self.DEFAULT_MODELS[model_name]

        from langchain_community.embeddings import HuggingFaceBgeEmbeddings

        # Use Chinese instruction for Chinese models
        if "zh" in model_name.lower():
            query_instruction = query_instruction or "为这个句子生成向量以用于检索："
        else:
            query_instruction = query_instruction or "Represent this sentence for searching: "

        self._embeddings = HuggingFaceBgeEmbeddings(
            model_name=model_name,
            model_kwargs={"device": device},
            encode_kwargs=encode_kwargs or {"normalize_embeddings": True},
            query_instruction=query_instruction,
        )

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Embed documents."""
        return self._embeddings.embed_documents(texts)

    def embed_query(self, text: str) -> List[float]:
        """Embed query."""
        return self._embeddings.embed_query(text)


class OllamaEmbedder(BaseEmbedder):
    """Ollama embedding model wrapper (free, local)."""

    def __init__(
        self,
        base_url: str = "http://localhost:11434",
        model: str = "nomic-embed-text",
        **kwargs,
    ):
        """Initialize Ollama embedder."""
        from langchain_community.embeddings import OllamaEmbeddings
        self._embeddings = OllamaEmbeddings(
            base_url=base_url,
            model=model,
            **kwargs,
        )

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Embed documents."""
        return self._embeddings.embed_documents(texts)

    def embed_query(self, text: str) -> List[float]:
        """Embed query."""
        return self._embeddings.embed_query(text)


class SiliconFlowEmbedder(BaseEmbedder):
    """SiliconFlow embedding model wrapper (free tier available)."""

    def __init__(
        self,
        model: str = "BAAI/bge-large-zh-v1.5",
        api_key: Optional[str] = None,
        dimension: int = 1024,
        **kwargs,
    ):
        """Initialize SiliconFlow embedder."""
        if is_placeholder_secret(api_key):
            raise ValueError("硅基流动 Embedding API Key 未配置，请先在系统设置中保存有效的 EMBEDDING_API_KEY。")
        self.model = model
        self.dimension = dimension
        self.api_key = api_key
        self.base_url = "https://api.siliconflow.cn/v1"

    def _embed(self, texts: List[str], task: str = " retrieval") -> List[List[float]]:
        """Call SiliconFlow API for embeddings."""
        import requests

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        embeddings = []
        # Process in batches of 8 (SiliconFlow limit)
        batch_size = 8
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            payload = {
                "model": self.model,
                "input": batch,
                "encoding_format": "float",
            }

            response = requests.post(
                f"{self.base_url}/embeddings",
                headers=headers,
                json=payload,
            )
            response.raise_for_status()
            data = response.json()

            for item in data["data"]:
                embeddings.append(item["embedding"])

        return embeddings

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Embed documents."""
        return self._embed(texts, task=" retrieval")

    def embed_query(self, text: str) -> List[float]:
        """Embed query."""
        return self._embed([text], task=" retrieval")[0]


def get_embedder(
    provider: str = "openai",
    model: Optional[str] = None,
    dimension: int = 1536,
    api_key: Optional[str] = None,
    base_url: Optional[str] = None,
    **kwargs,
) -> BaseEmbedder:
    """Get configured embedder instance.

    Args:
        provider: Embedding provider (openai, huggingface, ollama, siliconflow)
        model: Model name (provider-specific)
        dimension: Embedding dimension
        api_key: API key for cloud providers
        base_url: Base URL for custom endpoints
        **kwargs: Additional arguments

    Returns:
        Embedder instance
    """
    # Set defaults based on provider
    if provider == "openai":
        return OpenAIEmbedder(
            model=model or "text-embedding-3-small",
            dimension=dimension,
            api_key=api_key,
            base_url=base_url,
            **kwargs,
        )
    elif provider == "huggingface" or provider == "local":
        model_name = model or "bge-small-zh"
        return HuggingFaceEmbedder(
            model_name=model_name,
            **kwargs,
        )
    elif provider == "ollama":
        return OllamaEmbedder(
            model=model or "nomic-embed-text",
            base_url=base_url or "http://localhost:11434",
            **kwargs,
        )
    elif provider == "siliconflow":
        return SiliconFlowEmbedder(
            model=model or "BAAI/bge-large-zh-v1.5",
            api_key=api_key,
            dimension=dimension,
            **kwargs,
        )
    else:
        raise ValueError(f"Unknown embedding provider: {provider}")
