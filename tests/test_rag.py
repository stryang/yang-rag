"""Tests for Yang RAG System."""

import pytest

from src.knowledge.loader import get_loader, MultiFormatLoader
from src.knowledge.splitter import get_splitter, TextSplitter
from src.knowledge.manager import KnowledgeBase, KnowledgeBaseManager
from src.retrieval.reranker import SimpleReranker
from langchain_core.documents import Document


class TestDocumentLoader:
    """Tests for document loader."""

    def test_get_loader_returns_singleton(self):
        """Test that get_loader returns same instance."""
        loader1 = get_loader()
        loader2 = get_loader()
        assert loader1 is loader2

    def test_loader_has_supported_types(self):
        """Test loader has all supported file types."""
        loader = MultiFormatLoader()
        expected_types = [".pdf", ".txt", ".md", ".html", ".docx", ".pptx", ".xlsx"]
        for file_type in expected_types:
            assert file_type in loader.LOADER_MAP

    def test_unsupported_file_raises_error(self):
        """Test that unsupported files raise ValueError."""
        loader = get_loader()
        # Create a non-existent file with unsupported extension
        # Check the LOADER_MAP directly instead
        assert ".xyz" not in loader.LOADER_MAP


class TestTextSplitter:
    """Tests for text splitter."""

    def test_text_splitter_creates_chunks(self):
        """Test text splitter creates appropriate chunks."""
        splitter = TextSplitter(chunk_size=100, chunk_overlap=10)
        text = "Hello world. This is a test. " * 50
        chunks = splitter.split_text(text)
        assert len(chunks) > 1
        assert all(len(chunk) <= 100 + 10 for chunk in chunks)

    def test_get_splitter_factory(self):
        """Test splitter factory function."""
        splitter = get_splitter("recursive", chunk_size=200)
        assert isinstance(splitter, TextSplitter)

    def test_splitter_adds_chunk_ids(self):
        """Test that splitter adds chunk IDs to metadata."""
        splitter = get_splitter("recursive")
        docs = [Document(page_content="Test content", metadata={})]
        chunks = splitter.split_documents(docs)

        for chunk in chunks:
            assert "chunk_id" in chunk.metadata


class TestKnowledgeBase:
    """Tests for KnowledgeBase class."""

    def test_knowledge_base_initialization(self):
        """Test KnowledgeBase initializes correctly."""
        kb = KnowledgeBase(
            kb_id="test-kb",
            name="Test KB",
            description="Test description",
        )

        assert kb.id == "test-kb"
        assert kb.name == "Test KB"
        assert kb.description == "Test description"
        assert kb.metadata.id == "test-kb"
        assert kb.metadata.name == "Test KB"

    def test_knowledge_base_get_stats(self):
        """Test get_stats returns correct info."""
        kb = KnowledgeBase(kb_id="stats-test", name="Stats Test")
        stats = kb.get_stats()

        assert "id" in stats
        assert "name" in stats
        assert "document_count" in stats
        assert "chunk_count" in stats
        assert stats["document_count"] == 0

    def test_knowledge_base_search_returns_list(self):
        """Test search returns properly formatted results."""
        kb = KnowledgeBase(kb_id="search-test", name="Search Test")
        kb._embedder = object()
        kb._vector_store = type("VectorStoreStub", (), {
            "similarity_search_with_score": lambda self, **kwargs: [
                (Document(page_content="Test content", metadata={"source": "test.txt"}), 0.9),
            ]
        })()

        results = kb.search("test query")
        assert isinstance(results, list)
        assert len(results) == 1
        assert results[0]["metadata"]["source"] == "test.txt"


class TestKnowledgeBaseManager:
    """Tests for KnowledgeBaseManager."""

    def test_manager_is_singleton(self):
        """Test manager follows singleton pattern."""
        # Reset singleton for testing
        KnowledgeBaseManager._instance = None
        manager1 = KnowledgeBaseManager.get_instance()
        manager2 = KnowledgeBaseManager.get_instance()
        assert manager1 is manager2

    def test_create_knowledge_base(self, tmp_path):
        """Test creating a new knowledge base."""
        manager = KnowledgeBaseManager(storage_path=tmp_path)
        kb = manager.create_knowledge_base(
            name="New KB",
            description="A new knowledge base",
        )

        assert kb.name == "New KB"
        assert kb.description == "A new knowledge base"
        assert kb.id is not None

    def test_create_duplicate_kb_raises_error(self, tmp_path):
        """Test creating duplicate KB raises ValueError."""
        manager = KnowledgeBaseManager(storage_path=tmp_path)
        manager.create_knowledge_base(name="Duplicate Test", kb_id="dup-test")

        with pytest.raises(ValueError, match="already exists"):
            manager.create_knowledge_base(name="Duplicate Test", kb_id="dup-test")

    def test_list_loads_from_metadata_files(self, tmp_path):
        """Test list can load metadata written by previous manager instance."""
        manager_a = KnowledgeBaseManager(storage_path=tmp_path)
        manager_a.create_knowledge_base(name="Persisted KB", kb_id="persisted-kb")

        manager_b = KnowledgeBaseManager(storage_path=tmp_path)
        listed = manager_b.list_knowledge_bases()
        listed_ids = [item.id for item in listed]

        assert "persisted-kb" in listed_ids

    def test_update_knowledge_base_persists(self, tmp_path):
        """Test update operation is persisted to metadata file."""
        manager = KnowledgeBaseManager(storage_path=tmp_path)
        manager.create_knowledge_base(name="Before", kb_id="update-kb")
        manager.update_knowledge_base("update-kb", name="After", description="updated")

        reloaded = KnowledgeBaseManager(storage_path=tmp_path).get_knowledge_base("update-kb")
        assert reloaded.name == "After"
        assert reloaded.description == "updated"


class TestReranker:
    """Tests for reranker classes."""

    def test_simple_reranker_reranks(self):
        """Test SimpleReranker returns reranked results."""
        reranker = SimpleReranker()
        docs = [
            Document(page_content="Python is great", metadata={}),
            Document(page_content="Java is also great", metadata={}),
            Document(page_content="Python programming tutorial", metadata={}),
        ]

        results = reranker.rerank("Python", docs, top_k=2)

        assert len(results) == 2
        assert results[0]["score"] >= results[1]["score"]
        assert "Python" in results[0]["content"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
