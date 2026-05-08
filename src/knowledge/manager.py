"""Knowledge base management."""

import hashlib
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Union

from pydantic import BaseModel, Field
from langchain_core.documents import Document

from src.knowledge.loader import get_loader
from src.knowledge.splitter import get_splitter
from src.knowledge.embedder import get_embedder
from src.knowledge.store import get_vector_store, BaseVectorStore
from src.core.config import settings


class KnowledgeBaseMetadata(BaseModel):
    """Metadata for a knowledge base."""

    id: str = Field(..., description="Unique identifier")
    name: str = Field(..., description="Knowledge base name")
    description: str = Field(default="", description="Description")
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    document_count: int = Field(default=0, description="Number of documents")
    chunk_count: int = Field(default=0, description="Number of chunks")
    file_types: List[str] = Field(default_factory=list)
    embedding_model: str = Field(default="", description="Embedding model used")
    metadata: Dict[str, Any] = Field(default_factory=dict)


class KnowledgeBase:
    """Knowledge base management class with lazy initialization."""

    def __init__(
        self,
        kb_id: str,
        name: str,
        description: str = "",
        embedding_provider: str = "openai",
        embedding_model: Optional[str] = None,
        chunk_size: Optional[int] = None,
        chunk_overlap: Optional[int] = None,
        metadata_update_callback: Optional[Callable[["KnowledgeBase"], None]] = None,
        lazy: bool = False,
    ):
        """Initialize knowledge base.

        Args:
            kb_id: Unique identifier
            name: Display name
            description: Description
            embedding_provider: Embedding provider
            embedding_model: Specific embedding model
            chunk_size: Text chunk size
            chunk_overlap: Chunk overlap
            lazy: If True, defer embedding initialization until needed
        """
        self.id = kb_id
        self.name = name
        self.description = description

        self.embedding_provider = embedding_provider
        self.embedding_model = embedding_model or settings.embedding_model
        self.chunk_size = chunk_size or settings.chunk_size
        self.chunk_overlap = chunk_overlap or settings.chunk_overlap
        self._metadata_update_callback = metadata_update_callback

        self._metadata = KnowledgeBaseMetadata(
            id=kb_id,
            name=name,
            description=description,
            embedding_model=self.embedding_model,
        )
        self._metadata.metadata.update({
            "embedding_provider": self.embedding_provider,
            "chunk_size": self.chunk_size,
            "chunk_overlap": self.chunk_overlap,
        })

        # Lazy initialization - only create when needed
        self._lazy = lazy
        self._embedder = None
        self._vector_store = None
        self._splitter = get_splitter(
            splitter_type="smart",
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
        )

    def _ensure_initialized(self) -> None:
        """Ensure embedder and vector store are initialized."""
        if self._embedder is None:
            self._embedder = get_embedder(
                provider=self.embedding_provider,
                model=self.embedding_model,
                dimension=settings.embedding_dimension,
                api_key=settings.embedding_api_key or None,
                base_url=settings.embedding_base_url,
            )
        if self._vector_store is None:
            self._vector_store = get_vector_store(
                collection_name=self.id,
                embedding_function=self._embedder,
            )

    def _sync_empty_kb_with_runtime_embedding(self) -> None:
        """Sync empty knowledge bases with current runtime embedding settings."""
        if self.document_count > 0 or self.chunk_count > 0:
            return

        runtime_provider = settings.embedding_provider
        runtime_model = settings.embedding_model
        if (
            self.embedding_provider == runtime_provider
            and self.embedding_model == runtime_model
        ):
            return

        self.embedding_provider = runtime_provider
        self.embedding_model = runtime_model
        self._metadata.embedding_model = runtime_model
        self._metadata.metadata.update({
            "embedding_provider": runtime_provider,
            "chunk_size": self.chunk_size,
            "chunk_overlap": self.chunk_overlap,
        })
        self._embedder = None
        self._vector_store = None
        self._metadata.updated_at = datetime.now()
        self._notify_metadata_updated()

    @property
    def metadata(self) -> KnowledgeBaseMetadata:
        """Get knowledge base metadata."""
        return self._metadata

    @property
    def document_count(self) -> int:
        """Get document count."""
        return self._metadata.document_count

    @property
    def chunk_count(self) -> int:
        """Get chunk count."""
        return self._metadata.chunk_count

    def add_document(
        self,
        file_path: Union[str, Path],
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Add a document to knowledge base.

        Args:
            file_path: Path to document file
            metadata: Additional metadata

        Returns:
            Result with document and chunk counts
        """
        self._sync_empty_kb_with_runtime_embedding()
        self._ensure_initialized()

        file_path = Path(file_path)

        loader = get_loader()
        documents = loader.load(file_path)

        for doc in documents:
            if metadata:
                doc.metadata.update(metadata)
            doc.metadata["kb_id"] = self.id
            doc.metadata["kb_name"] = self.name

        chunks = self._splitter.split_documents(documents)
        self._vector_store.add_documents(chunks)

        self._update_metadata(
            doc_count=len(documents),
            chunk_count=len(chunks),
            file_type=file_path.suffix.lower(),
        )

        return {
            "document_count": len(documents),
            "chunk_count": len(chunks),
            "file_name": file_path.name,
        }

    def add_documents(
        self,
        file_paths: List[Union[str, Path]],
        metadata: Optional[Dict[str, Any]] = None,
        show_progress: bool = True,
    ) -> List[Dict[str, Any]]:
        """Add multiple documents.

        Args:
            file_paths: List of file paths
            metadata: Additional metadata
            show_progress: Show progress indicator

        Returns:
            List of results for each document
        """
        self._sync_empty_kb_with_runtime_embedding()
        results = []

        for file_path in file_paths:
            try:
                result = self.add_document(file_path, metadata)
                results.append({"status": "success", **result})
            except Exception as e:
                results.append({
                    "status": "error",
                    "file_name": str(file_path),
                    "error": str(e),
                })

        return results

    def add_texts(
        self,
        texts: List[str],
        metadatas: Optional[List[Dict]] = None,
        ids: Optional[List[str]] = None,
    ) -> List[str]:
        """Add raw texts to knowledge base.

        Args:
            texts: List of text contents
            metadatas: List of metadata dicts
            ids: Optional IDs for each text

        Returns:
            List of document IDs
        """
        self._ensure_initialized()

        docs = []
        for i, text in enumerate(texts):
            metadata = (metadatas[i] if metadatas and i < len(metadatas) else {})
            metadata["kb_id"] = self.id
            metadata["kb_name"] = self.name
            docs.append(Document(page_content=text, metadata=metadata))

        chunks = self._splitter.split_documents(docs)
        stored_ids = self._vector_store.add_documents(chunks, ids=ids) if ids else self._vector_store.add_documents(chunks)
        self._update_metadata(doc_count=len(texts), chunk_count=len(chunks))
        return stored_ids

    def search(
        self,
        query: str,
        top_k: Optional[int] = None,
        filter_dict: Optional[Dict] = None,
    ) -> List[Dict[str, Any]]:
        """Search knowledge base.

        Args:
            query: Search query
            top_k: Number of results
            filter_dict: Metadata filter

        Returns:
            List of search results with content, metadata, and score
        """
        self._ensure_initialized()

        k = top_k or settings.retrieval_top_k

        results = self._vector_store.similarity_search_with_score(
            query=query,
            k=k,
            filter=filter_dict,
        )

        return [
            {
                "content": doc.page_content,
                "metadata": doc.metadata,
                "score": score,
            }
            for doc, score in results
        ]

    def get_stats(self) -> Dict[str, Any]:
        """Get knowledge base statistics."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "document_count": self._metadata.document_count,
            "chunk_count": self._metadata.chunk_count,
            "embedding_model": self.embedding_model,
            "chunk_size": self.chunk_size,
            "created_at": self._metadata.created_at.isoformat(),
            "updated_at": self._metadata.updated_at.isoformat(),
        }

    def delete(self, ids: Optional[List[str]] = None) -> None:
        """Delete documents from knowledge base.

        Args:
            ids: Document IDs to delete, None deletes all
        """
        self._ensure_initialized()
        self._vector_store.delete(ids)
        if ids is None:
            self._metadata.document_count = 0
            self._metadata.chunk_count = 0
            self._metadata.updated_at = datetime.now()
            self._notify_metadata_updated()

    def update_info(
        self,
        name: Optional[str] = None,
        description: Optional[str] = None,
    ) -> None:
        """Update mutable knowledge base info."""
        if name is not None:
            self.name = name
            self._metadata.name = name
        if description is not None:
            self.description = description
            self._metadata.description = description
        self._metadata.updated_at = datetime.now()
        self._notify_metadata_updated()

    def _update_metadata(
        self,
        doc_count: int,
        chunk_count: int,
        file_type: Optional[str] = None,
    ) -> None:
        """Update metadata after adding documents."""
        self._metadata.document_count += doc_count
        self._metadata.chunk_count += chunk_count
        if file_type and file_type not in self._metadata.file_types:
            self._metadata.file_types.append(file_type)
        self._metadata.updated_at = datetime.now()
        self._notify_metadata_updated()

    def _notify_metadata_updated(self) -> None:
        """Persist metadata when callback is configured."""
        if self._metadata_update_callback:
            self._metadata_update_callback(self)


class KnowledgeBaseManager:
    """Manager for multiple knowledge bases."""

    _instance = None

    def __init__(self, storage_path: Optional[Union[Path, str]] = None):
        """Initialize knowledge base manager."""
        self.storage_path = Path(storage_path or "./data/kb_metadata")
        self.storage_path.mkdir(parents=True, exist_ok=True)
        self._kb_store: Dict[str, KnowledgeBase] = {}
        self._has_loaded_all = False

    @classmethod
    def get_instance(cls, storage_path: Optional[Union[Path, str]] = None) -> "KnowledgeBaseManager":
        """Get singleton instance."""
        if cls._instance is None:
            cls._instance = cls(storage_path)
        return cls._instance

    def create_knowledge_base(
        self,
        name: str,
        description: str = "",
        kb_id: Optional[str] = None,
        **kwargs,
    ) -> KnowledgeBase:
        """Create a new knowledge base.

        Args:
            name: Knowledge base name
            description: Description
            kb_id: Optional custom ID (generated if not provided)
            **kwargs: Additional arguments

        Returns:
            Created KnowledgeBase instance
        """
        self._load_all_knowledge_bases()

        if kb_id is None:
            kb_id = self._generate_id(name)

        if kb_id in self._kb_store:
            raise ValueError(f"Knowledge base with ID {kb_id} already exists")

        kb = KnowledgeBase(
            kb_id=kb_id,
            name=name,
            description=description,
            metadata_update_callback=self._save_metadata,
            **kwargs,
        )

        self._kb_store[kb_id] = kb
        self._save_metadata(kb)

        return kb

    def get_knowledge_base(self, kb_id: str) -> KnowledgeBase:
        """Get knowledge base by ID.

        Args:
            kb_id: Knowledge base ID

        Returns:
            KnowledgeBase instance

        Raises:
            KeyError: If knowledge base not found
        """
        if kb_id not in self._kb_store:
            self._load_knowledge_base(kb_id)

        return self._kb_store[kb_id]

    def list_knowledge_bases(self) -> List[KnowledgeBaseMetadata]:
        """List all knowledge bases."""
        self._load_all_knowledge_bases()
        return sorted(
            [kb.metadata for kb in self._kb_store.values()],
            key=lambda metadata: metadata.updated_at,
            reverse=True,
        )

    def update_knowledge_base(
        self,
        kb_id: str,
        name: Optional[str] = None,
        description: Optional[str] = None,
    ) -> KnowledgeBase:
        """Update knowledge base name/description."""
        kb = self.get_knowledge_base(kb_id)
        kb.update_info(name=name, description=description)
        return kb

    def delete_knowledge_base(self, kb_id: str) -> None:
        """Delete a knowledge base.

        Args:
            kb_id: Knowledge base ID
        """
        kb = self.get_knowledge_base(kb_id)
        kb._ensure_initialized()  # Initialize before deleting
        kb.delete()
        del self._kb_store[kb_id]
        self._delete_metadata(kb_id)

    def _generate_id(self, name: str) -> str:
        """Generate unique ID for knowledge base."""
        hash_input = f"{name}_{datetime.now().isoformat()}"
        return hashlib.sha256(hash_input.encode()).hexdigest()[:16]

    def _save_metadata(self, kb: KnowledgeBase) -> None:
        """Save knowledge base metadata."""
        metadata_file = self.storage_path / f"{kb.id}.json"
        with open(metadata_file, "w", encoding="utf-8") as f:
            json.dump(kb.metadata.model_dump(), f, indent=2, default=str)

    def _load_knowledge_base(self, kb_id: str) -> None:
        """Load knowledge base from metadata."""
        metadata_file = self.storage_path / f"{kb_id}.json"

        if not metadata_file.exists():
            raise KeyError(f"Knowledge base {kb_id} not found")

        with open(metadata_file, encoding="utf-8") as f:
            metadata_dict = json.load(f)

        metadata = KnowledgeBaseMetadata.model_validate(metadata_dict)
        extra = metadata.metadata or {}
        kb = KnowledgeBase(
            kb_id=metadata.id,
            name=metadata.name,
            description=metadata.description,
            embedding_provider=extra.get("embedding_provider", settings.embedding_provider),
            embedding_model=metadata.embedding_model or settings.embedding_model,
            chunk_size=extra.get("chunk_size", settings.chunk_size),
            chunk_overlap=extra.get("chunk_overlap", settings.chunk_overlap),
            metadata_update_callback=self._save_metadata,
            lazy=True,
        )
        kb._metadata = metadata

        self._kb_store[kb_id] = kb

    def _load_all_knowledge_bases(self) -> None:
        """Load all metadata files once."""
        if self._has_loaded_all:
            return

        for metadata_file in self.storage_path.glob("*.json"):
            kb_id = metadata_file.stem
            if kb_id in self._kb_store:
                continue
            try:
                self._load_knowledge_base(kb_id)
            except Exception:
                continue

        self._has_loaded_all = True

    def _delete_metadata(self, kb_id: str) -> None:
        """Delete knowledge base metadata."""
        metadata_file = self.storage_path / f"{kb_id}.json"
        try:
            metadata_file.unlink()
        except FileNotFoundError:
            pass


def get_kb_manager(storage_path: Optional[Union[Path, str]] = None) -> KnowledgeBaseManager:
    """Get knowledge base manager instance."""
    return KnowledgeBaseManager.get_instance(storage_path)


def reset_kb_manager() -> None:
    """Reset the singleton knowledge base manager."""
    KnowledgeBaseManager._instance = None
