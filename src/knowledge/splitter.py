"""Text splitter for document chunking."""

from typing import List, Optional, Union

from langchain_text_splitters import (
    RecursiveCharacterTextSplitter,
    MarkdownTextSplitter,
)
from langchain_core.documents import Document


class TextSplitter:
    """Configurable text splitter for various document types."""

    def __init__(
        self,
        chunk_size: int = 500,
        chunk_overlap: int = 50,
        separators: Optional[List[str]] = None,
    ):
        """Initialize text splitter.

        Args:
            chunk_size: Maximum size of each chunk
            chunk_overlap: Overlap between chunks
            separators: Custom separators (uses defaults if not provided)
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self._splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separators=separators,
            length_function=len,
        )

    def split_documents(
        self, documents: List[Document], add_chunk_id: bool = True
    ) -> List[Document]:
        """Split documents into chunks.

        Args:
            documents: List of documents to split
            add_chunk_id: Whether to add chunk ID to metadata

        Returns:
            List of chunked documents
        """
        splits = self._splitter.split_documents(documents)

        for i, doc in enumerate(splits):
            if add_chunk_id:
                doc.metadata["chunk_id"] = i
            if "chunk_id" not in doc.metadata:
                doc.metadata["chunk_id"] = i

        return splits

    def split_text(self, text: str) -> List[str]:
        """Split text into chunks.

        Args:
            text: Text to split

        Returns:
            List of text chunks
        """
        return self._splitter.split_text(text)


class MarkdownSplitter:
    """Specialized splitter for Markdown documents."""

    def __init__(
        self, chunk_size: int = 500, chunk_overlap: int = 50, **kwargs
    ):
        """Initialize Markdown splitter."""
        self._splitter = MarkdownTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
        )

    def split_documents(
        self, documents: List[Document]
    ) -> List[Document]:
        """Split Markdown documents."""
        splits = self._splitter.split_documents(documents)

        for i, doc in enumerate(splits):
            doc.metadata["chunk_id"] = i
            doc.metadata["file_type"] = "markdown"

        return splits


class CodeSplitter:
    """Specialized splitter for code documents."""

    SUPPORTED_LANGUAGES = {
        ".py": "python",
        ".js": "js",
        ".ts": "ts",
        ".jsx": "jsx",
        ".tsx": "tsx",
        ".java": "java",
        ".cpp": "cpp",
        ".c": "c",
        ".go": "go",
        ".rs": "rust",
        ".rb": "ruby",
        ".php": "php",
        ".cs": "csharp",
        ".swift": "swift",
        ".kt": "kotlin",
        ".scala": "scala",
        ".sql": "sql",
        ".sh": "bash",
        ".bash": "bash",
    }

    def __init__(
        self, chunk_size: int = 500, chunk_overlap: int = 50, **kwargs
    ):
        """Initialize code splitter."""
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        from langchain_text_splitters import PythonCodeTextSplitter
        self._splitter = PythonCodeTextSplitter()

    def split_documents(
        self, documents: List[Document]
    ) -> List[Document]:
        """Split code documents."""
        splits = self._splitter.split_documents(documents)

        for i, doc in enumerate(splits):
            doc.metadata["chunk_id"] = i
            doc.metadata["is_code"] = True

        return splits

    @classmethod
    def get_language(cls, file_path: str) -> Optional[str]:
        """Get programming language from file path."""
        import os

        _, ext = os.path.splitext(file_path)
        return cls.SUPPORTED_LANGUAGES.get(ext.lower())


class HSplitter:
    """Smart splitter that uses appropriate strategy based on document type."""

    def __init__(
        self, chunk_size: int = 500, chunk_overlap: int = 50, **kwargs
    ):
        """Initialize smart splitter."""
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def split_documents(
        self, documents: List[Document]
    ) -> List[Document]:
        """Split documents using appropriate strategy per document."""
        results = []

        for doc in documents:
            file_type = doc.metadata.get("file_type", "").lower()
            source = doc.metadata.get("source", "").lower()

            if file_type in (".md", ".markdown") or "markdown" in source:
                splitter = MarkdownSplitter(
                    self.chunk_size, self.chunk_overlap
                )
            elif CodeSplitter.get_language(source):
                splitter = CodeSplitter(self.chunk_size, self.chunk_overlap)
            else:
                splitter = TextSplitter(self.chunk_size, self.chunk_overlap)

            splits = splitter.split_documents([doc])
            results.extend(splits)

        return results


def get_splitter(
    splitter_type: str = "smart",
    **kwargs,
) -> Union[TextSplitter, MarkdownSplitter, CodeSplitter, HSplitter]:
    """Factory function to get appropriate splitter.

    Args:
        splitter_type: Type of splitter to create
        **kwargs: Additional arguments for splitter

    Returns:
        Appropriate splitter instance
    """
    splitters = {
        "recursive": TextSplitter,
        "markdown": MarkdownSplitter,
        "code": CodeSplitter,
        "smart": HSplitter,
    }

    splitter_class = splitters.get(splitter_type, HSplitter)
    return splitter_class(**kwargs)
