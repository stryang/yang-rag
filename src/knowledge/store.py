"""Vector store management for document storage and retrieval."""

import logging
import sqlite3
import sys
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings

logger = logging.getLogger(__name__)
MIN_CHROMA_SQLITE_VERSION = (3, 35, 0)


def _parse_version(version: str) -> Tuple[int, ...]:
    """Parse a version string into a comparable tuple."""
    parts = []
    for part in version.split("."):
        digits = "".join(ch for ch in part if ch.isdigit())
        if not digits:
            break
        parts.append(int(digits))
    return tuple(parts)


def _sqlite_supports_chroma() -> bool:
    """Check whether the active sqlite runtime satisfies Chroma's minimum."""
    return _parse_version(sqlite3.sqlite_version) >= MIN_CHROMA_SQLITE_VERSION


def _prepare_chroma_runtime() -> bool:
    """Prepare sqlite runtime for Chroma, swapping in pysqlite3 when available."""
    if _sqlite_supports_chroma():
        return True

    try:
        import pysqlite3  # type: ignore
    except ImportError:
        return False

    sys.modules["sqlite3"] = pysqlite3
    return _parse_version(pysqlite3.sqlite_version) >= MIN_CHROMA_SQLITE_VERSION


def _should_fallback_to_faiss(store_type: str) -> bool:
    """Return whether the configured store should transparently fall back to FAISS."""
    if store_type != "chroma":
        return False

    if _prepare_chroma_runtime():
        return False

    logger.warning(
        "Chroma is unavailable because sqlite3 %s is below %s; falling back to FAISS.",
        sqlite3.sqlite_version,
        ".".join(str(part) for part in MIN_CHROMA_SQLITE_VERSION),
    )
    return True


class BaseVectorStore(ABC):
    """Base class for vector stores."""

    @abstractmethod
    def add_documents(
        self, documents: List[Document], **kwargs
    ) -> List[str]:
        """Add documents to vector store."""
        pass

    @abstractmethod
    def similarity_search(
        self, query: str, k: int = 4, **kwargs
    ) -> List[Document]:
        """Search for similar documents."""
        pass

    @abstractmethod
    def similarity_search_with_score(
        self, query: str, k: int = 4, **kwargs
    ) -> List[Tuple[Document, float]]:
        """Search with similarity scores."""
        pass

    @abstractmethod
    def delete(self, ids: Optional[List[str]] = None, **kwargs) -> None:
        """Delete documents by IDs."""
        pass

    @abstractmethod
    def persist(self) -> None:
        """Persist vector store to disk."""
        pass


class ChromaVectorStore(BaseVectorStore):
    """ChromaDB vector store implementation."""

    def __init__(
        self,
        collection_name: str,
        embedding_function: Embeddings,
        persist_directory: Optional[Union[Path, str]] = None,
        metadata_filter: Optional[Dict] = None,
    ):
        """Initialize ChromaDB vector store."""
        from src.core.config import settings

        self.collection_name = collection_name
        self.embedding_function = embedding_function
        self.persist_directory = persist_directory or settings.vector_store_persist_dir
        self.metadata_filter = metadata_filter

        self._client = None
        self._vectorstore = None

    def _build_faiss_client(self):
        """Create a FAISS client as a transparent fallback for Chroma failures."""
        fallback_store = FAISSVectorStore(
            collection_name=self.collection_name,
            embedding_function=self.embedding_function,
            persist_directory=self.persist_directory,
        )
        return fallback_store._get_client()

    def _get_client(self):
        """Get or create ChromaDB client."""
        if self._vectorstore is None:
            if _should_fallback_to_faiss("chroma"):
                self._vectorstore = self._build_faiss_client()
                return self._vectorstore

            from langchain_community.vectorstores import Chroma

            try:
                self._vectorstore = Chroma(
                    client=self._client,
                    collection_name=self.collection_name,
                    embedding_function=self.embedding_function,
                    persist_directory=str(self.persist_directory),
                )
            except RuntimeError as exc:
                if "unsupported version of sqlite3" not in str(exc):
                    raise
                logger.warning(
                    "Chroma client initialization failed for collection %s; "
                    "falling back to FAISS.",
                    self.collection_name,
                )
                self._vectorstore = self._build_faiss_client()
        return self._vectorstore

    def add_documents(
        self, documents: List[Document], **kwargs
    ) -> List[str]:
        """Add documents to vector store."""
        vs = self._get_client()
        return vs.add_documents(documents, **kwargs)

    def add_texts(
        self,
        texts: List[str],
        metadatas: Optional[List[Dict]] = None,
        ids: Optional[List[str]] = None,
        **kwargs,
    ) -> List[str]:
        """Add texts to vector store."""
        vs = self._get_client()
        return vs.add_texts(texts, metadatas, ids, **kwargs)

    def similarity_search(
        self, query: str, k: int = 4, filter: Optional[Dict] = None, **kwargs
    ) -> List[Document]:
        """Search for similar documents."""
        vs = self._get_client()
        return vs.similarity_search(
            query, k=k, filter=filter or self.metadata_filter, **kwargs
        )

    def similarity_search_with_score(
        self, query: str, k: int = 4, filter: Optional[Dict] = None, **kwargs
    ) -> List[Tuple[Document, float]]:
        """Search with similarity scores."""
        vs = self._get_client()
        return vs.similarity_search_with_score(
            query, k=k, filter=filter or self.metadata_filter, **kwargs
        )

    def delete(self, ids: Optional[List[str]] = None, **kwargs) -> None:
        """Delete documents."""
        vs = self._get_client()
        vs.delete(ids, **kwargs)

    def persist(self) -> None:
        """Persist vector store (ChromaDB auto-persists)."""
        pass

    def get_collection(self) -> Any:
        """Get underlying ChromaDB collection."""
        vs = self._get_client()
        return vs._collection

    @classmethod
    def from_documents(
        cls,
        documents: List[Document],
        embedding_function: Embeddings,
        collection_name: str,
        persist_directory: Optional[Union[Path, str]] = None,
    ) -> "ChromaVectorStore":
        """Create vector store from documents."""
        from src.core.config import settings

        persist_dir = persist_directory or settings.vector_store_persist_dir
        Path(persist_dir).mkdir(parents=True, exist_ok=True)

        if _should_fallback_to_faiss("chroma"):
            return FAISSVectorStore.from_documents(
                documents=documents,
                embedding_function=embedding_function,
                collection_name=collection_name,
                persist_directory=persist_dir,
            )

        from langchain_community.vectorstores import Chroma

        try:
            vectorstore = Chroma.from_documents(
                documents=documents,
                embedding=embedding_function,
                collection_name=collection_name,
                persist_directory=str(persist_dir),
            )
        except RuntimeError as exc:
            if "unsupported version of sqlite3" not in str(exc):
                raise
            logger.warning(
                "Chroma from_documents failed for collection %s; falling back to FAISS.",
                collection_name,
            )
            return FAISSVectorStore.from_documents(
                documents=documents,
                embedding_function=embedding_function,
                collection_name=collection_name,
                persist_directory=persist_dir,
            )

        store = cls(
            collection_name=collection_name,
            embedding_function=embedding_function,
            persist_directory=persist_dir,
        )
        store._vectorstore = vectorstore
        return store


class FAISSVectorStore(BaseVectorStore):
    """FAISS vector store implementation."""

    def __init__(
        self,
        embedding_function: Embeddings,
        collection_name: Optional[str] = None,
        index_name: Optional[str] = None,
        persist_directory: Optional[Union[Path, str]] = None,
    ):
        """Initialize FAISS vector store."""
        self.embedding_function = embedding_function
        self.index_name = index_name or collection_name or "index"
        self.persist_directory = Path(persist_directory) if persist_directory else None
        self._vectorstore = None

    def _has_persisted_index(self) -> bool:
        """Check whether a persisted FAISS index exists."""
        if not self.persist_directory:
            return False
        return (
            (self.persist_directory / "{}.faiss".format(self.index_name)).exists()
            and (self.persist_directory / "{}.pkl".format(self.index_name)).exists()
        )

    def _create_empty_store(self):
        """Create an empty FAISS vector store."""
        import faiss
        from langchain_community.docstore.in_memory import InMemoryDocstore
        from langchain_community.vectorstores import FAISS

        dimension = getattr(self.embedding_function, "dimension", None)
        if not isinstance(dimension, int) or dimension <= 0:
            dimension = len(self.embedding_function.embed_query("dimension probe"))
        index = faiss.IndexFlatL2(dimension)
        return FAISS(
            embedding_function=self.embedding_function,
            index=index,
            docstore=InMemoryDocstore({}),
            index_to_docstore_id={},
        )

    def _get_client(self):
        """Get or create FAISS index."""
        if self._vectorstore is None:
            from langchain_community.vectorstores import FAISS

            if self._has_persisted_index():
                self._vectorstore = FAISS.load_local(
                    str(self.persist_directory),
                    embeddings=self.embedding_function,
                    index_name=self.index_name,
                    allow_dangerous_deserialization=True,
                )
            else:
                self._vectorstore = self._create_empty_store()
        return self._vectorstore

    def add_documents(
        self, documents: List[Document], **kwargs
    ) -> List[str]:
        """Add documents."""
        vs = self._get_client()
        return vs.add_documents(documents, **kwargs)

    def similarity_search(
        self, query: str, k: int = 4, **kwargs
    ) -> List[Document]:
        """Search for similar documents."""
        if self._vectorstore is None and not self._has_persisted_index():
            return []
        vs = self._get_client()
        return vs.similarity_search(query, k=k, **kwargs)

    def similarity_search_with_score(
        self, query: str, k: int = 4, **kwargs
    ) -> List[Tuple[Document, float]]:
        """Search with scores."""
        if self._vectorstore is None and not self._has_persisted_index():
            return []
        vs = self._get_client()
        return vs.similarity_search_with_score(query, k=k, **kwargs)

    def delete(self, ids: Optional[List[str]] = None, **kwargs) -> None:
        """Delete documents."""
        if self._vectorstore is None and not self._has_persisted_index():
            return
        vs = self._get_client()
        vs.delete(ids=ids, **kwargs)

    def persist(self) -> None:
        """Persist FAISS index."""
        if self._vectorstore and self.persist_directory:
            self.persist_directory.mkdir(parents=True, exist_ok=True)
            self._vectorstore.save_local(str(self.persist_directory), index_name=self.index_name)

    @classmethod
    def from_documents(
        cls,
        documents: List[Document],
        embedding_function: Embeddings,
        collection_name: Optional[str] = None,
        persist_directory: Optional[Union[Path, str]] = None,
    ) -> "FAISSVectorStore":
        """Create from documents."""
        from langchain_community.vectorstores import FAISS

        store = cls(
            collection_name=collection_name,
            embedding_function=embedding_function,
            persist_directory=persist_directory,
        )
        store._vectorstore = FAISS.from_documents(
            documents=documents,
            embedding=embedding_function,
        )
        return store


class MilvusVectorStore(BaseVectorStore):
    """Milvus vector store implementation."""

    def __init__(
        self,
        collection_name: str,
        embedding_function: Embeddings,
        connection_args: Optional[Dict[str, Any]] = None,
        consistency_level: str = "Session",
        index_params: Optional[Dict[str, Any]] = None,
        search_params: Optional[Dict[str, Any]] = None,
        **kwargs,
    ):
        """Initialize Milvus vector store."""
        from src.core.config import settings

        host = kwargs.pop("host", settings.milvus_host)
        port = kwargs.pop("port", settings.milvus_port)

        self.collection_name = collection_name or settings.milvus_collection
        self.embedding_function = embedding_function
        self.connection_args = connection_args or {
            "host": host,
            "port": str(port),
        }
        self.consistency_level = consistency_level
        self.index_params = index_params
        self.search_params = search_params
        self._vectorstore = None

    def _get_client(self):
        """Get or create Milvus collection."""
        if self._vectorstore is None:
            try:
                from langchain_community.vectorstores import Milvus
            except ImportError as exc:
                raise RuntimeError(
                    "Milvus support requires the optional pymilvus dependency"
                ) from exc

            self._vectorstore = Milvus(
                embedding_function=self.embedding_function,
                collection_name=self.collection_name,
                connection_args=self.connection_args,
                consistency_level=self.consistency_level,
                index_params=self.index_params,
                search_params=self.search_params,
            )
        return self._vectorstore

    def add_documents(
        self, documents: List[Document], **kwargs
    ) -> List[str]:
        """Add documents to Milvus."""
        vs = self._get_client()
        return vs.add_documents(documents, **kwargs)

    def similarity_search(
        self, query: str, k: int = 4, **kwargs
    ) -> List[Document]:
        """Search for similar documents."""
        vs = self._get_client()
        return vs.similarity_search(query, k=k, **kwargs)

    def similarity_search_with_score(
        self, query: str, k: int = 4, **kwargs
    ) -> List[Tuple[Document, float]]:
        """Search with similarity scores."""
        vs = self._get_client()
        return vs.similarity_search_with_score(query, k=k, **kwargs)

    def delete(self, ids: Optional[List[str]] = None, **kwargs) -> None:
        """Delete documents."""
        vs = self._get_client()
        vs.delete(ids=ids, **kwargs)

    def persist(self) -> None:
        """Milvus persists data remotely."""
        return None

    @classmethod
    def from_documents(
        cls,
        documents: List[Document],
        embedding_function: Embeddings,
        collection_name: str,
        **kwargs,
    ) -> "MilvusVectorStore":
        """Create a Milvus vector store from documents."""
        try:
            from langchain_community.vectorstores import Milvus
        except ImportError as exc:
            raise RuntimeError(
                "Milvus support requires the optional pymilvus dependency"
            ) from exc

        vectorstore = Milvus.from_documents(
            documents=documents,
            embedding=embedding_function,
            collection_name=collection_name,
            **kwargs,
        )

        store = cls(
            collection_name=collection_name,
            embedding_function=embedding_function,
            connection_args=kwargs.get("connection_args"),
            consistency_level=kwargs.get("consistency_level", "Session"),
            index_params=kwargs.get("index_params"),
            search_params=kwargs.get("search_params"),
        )
        store._vectorstore = vectorstore
        return store


class VectorStoreFactory:
    """Factory for creating vector store instances."""

    @staticmethod
    def create(
        store_type: str = "chroma",
        collection_name: str = "default",
        embedding_function: Optional[Embeddings] = None,
        persist_directory: Optional[Union[Path, str]] = None,
        **kwargs,
    ) -> BaseVectorStore:
        """Create vector store instance."""
        stores = {
            "chroma": ChromaVectorStore,
            "faiss": FAISSVectorStore,
            "milvus": MilvusVectorStore,
        }

        if store_type not in stores:
            raise ValueError("Unknown store type: {}".format(store_type))

        store_class = stores[store_type]
        return store_class(
            collection_name=collection_name,
            embedding_function=embedding_function,
            persist_directory=persist_directory,
            **kwargs,
        )


def get_vector_store(
    collection_name: str,
    embedding_function: Embeddings,
    store_type: Optional[str] = None,
    **kwargs,
) -> BaseVectorStore:
    """Get configured vector store."""
    from src.core.config import settings

    store_type = store_type or settings.vector_store_type
    persist_dir = kwargs.pop("persist_directory", settings.vector_store_persist_dir)
    effective_store_type = "faiss" if _should_fallback_to_faiss(store_type) else store_type

    return VectorStoreFactory.create(
        store_type=effective_store_type,
        collection_name=collection_name,
        embedding_function=embedding_function,
        persist_directory=persist_dir,
        **kwargs,
    )
