"""Reranker for improving retrieval results."""

from typing import Any, Dict, List, Optional, Union

from langchain_core.documents import Document


class BaseReranker:
    """Base class for rerankers."""

    def rerank(
        self,
        query: str,
        documents: Union[List[Document], List[Dict]],
        top_k: int = 3,
    ) -> List[Dict]:
        """Rerank documents.

        Args:
            query: Search query
            documents: List of documents to rerank
            top_k: Number of top results to return

        Returns:
            List of reranked results with scores
        """
        raise NotImplementedError


class SimpleReranker(BaseReranker):
    """Simple reranker based on keyword overlap and position."""

    def rerank(
        self,
        query: str,
        documents: Union[List[Document], List[Dict]],
        top_k: int = 3,
    ) -> List[Dict]:
        """Rerank using simple scoring.

        Args:
            query: Search query
            documents: Documents to rerank
            top_k: Number of results

        Returns:
            Reranked results
        """
        query_terms = set(query.lower().split())

        results: List[Dict] = []

        for i, doc in enumerate(documents):
            if isinstance(doc, Document):
                content = doc.page_content
                metadata = doc.metadata
            else:
                content = doc.get("content", "")
                metadata = doc.get("metadata", {})

            content_lower = content.lower()
            content_terms = set(content_lower.split())

            term_overlap = len(query_terms & content_terms)

            position_score = 1.0 - (i / len(documents))

            exact_match_bonus = 0.0
            for term in query_terms:
                if term in content_lower:
                    exact_match_bonus += 0.1

            final_score = (
                0.5 * (term_overlap / max(len(query_terms), 1)) +
                0.3 * position_score +
                0.2 * exact_match_bonus
            )

            results.append({
                "content": content,
                "metadata": metadata,
                "score": final_score,
                "original_index": i,
            })

        results.sort(key=lambda x: x["score"], reverse=True)

        return results[:top_k]


class CrossEncoderReranker(BaseReranker):
    """Cross-encoder based reranker using sentence-transformers."""

    def __init__(
        self,
        model_name: str = "cross-encoder/ms-marco-MiniLM-L-6-v2",
        device: str = "cpu",
        top_k: int = 10,
    ):
        """Initialize cross-encoder reranker.

        Args:
            model_name: Cross-encoder model name
            device: Device (cpu/cuda)
            top_k: Default top k
        """
        self.model_name = model_name
        self.device = device
        self.top_k = top_k
        self._model = None

    def _load_model(self):
        """Lazy load the model."""
        if self._model is None:
            from sentence_transformers import CrossEncoder
            self._model = CrossEncoder(self.model_name, device=self.device)

    def rerank(
        self,
        query: str,
        documents: Union[List[Document], List[Dict]],
        top_k: Optional[int] = None,
    ) -> List[Dict]:
        """Rerank using cross-encoder.

        Args:
            query: Search query
            documents: Documents to rerank
            top_k: Number of results

        Returns:
            Reranked results
        """
        self._load_model()
        top_k = top_k or self.top_k

        pairs: List[List[str]] = []
        for doc in documents:
            content = doc.page_content if isinstance(doc, Document) else doc.get("content", "")
            pairs.append([query, content])

        scores = self._model.predict(pairs)

        results: List[Dict] = []
        for i, (doc, score) in enumerate(zip(documents, scores)):
            content = doc.page_content if isinstance(doc, Document) else doc.get("content", "")
            metadata = doc.metadata if isinstance(doc, Document) else doc.get("metadata", {})

            results.append({
                "content": content,
                "metadata": metadata,
                "score": float(score),
                "original_index": i,
            })

        results.sort(key=lambda x: x["score"], reverse=True)

        return results[:top_k]


class LLMReranker(BaseReranker):
    """LLM-based reranker using relevance scoring."""

    def __init__(
        self,
        llm: Any = None,
        top_k: int = 5,
    ):
        """Initialize LLM reranker.

        Args:
            llm: LLM instance for scoring
            top_k: Default top k
        """
        self.llm = llm
        self.top_k = top_k

    def rerank(
        self,
        query: str,
        documents: Union[List[Document], List[Dict]],
        top_k: Optional[int] = None,
    ) -> List[Dict]:
        """Rerank using LLM relevance scoring.

        Args:
            query: Search query
            documents: Documents to rerank
            top_k: Number of results

        Returns:
            Reranked results
        """
        if self.llm is None:
            from langchain_openai import ChatOpenAI
            from src.core.config import settings
            self.llm = ChatOpenAI(
                model=settings.llm_model,
                api_key=settings.llm_api_key,
                base_url=settings.llm_base_url,
            )

        top_k = top_k or self.top_k

        from langchain_core.prompts import ChatPromptTemplate

        prompt = ChatPromptTemplate.from_messages([
            ("system", "你是一个文档相关性评分专家。"),
            ("human", """评估以下文档与查询的相关性。

查询: {query}

文档内容:
{doc_content}

请给出0-10的相关性分数，只需要输出数字。
"""),
        ])

        results: List[Dict] = []

        for i, doc in enumerate(documents):
            content = doc.page_content if isinstance(doc, Document) else doc.get("content", "")

            chain = prompt | self.llm
            score_text = chain.invoke({
                "query": query,
                "doc_content": content[:500],
            }).content

            try:
                score = float(score_text.strip()) / 10.0
            except ValueError:
                score = 0.5

            results.append({
                "content": content,
                "metadata": doc.metadata if isinstance(doc, Document) else doc.get("metadata", {}),
                "score": score,
                "original_index": i,
            })

        results.sort(key=lambda x: x["score"], reverse=True)

        return results[:top_k]


def get_reranker(
    reranker_type: str = "simple",
    **kwargs,
) -> BaseReranker:
    """Get reranker instance.

    Args:
        reranker_type: Type of reranker
        **kwargs: Additional arguments

    Returns:
        Reranker instance
    """
    rerankers = {
        "simple": SimpleReranker,
        "cross-encoder": CrossEncoderReranker,
        "llm": LLMReranker,
    }

    if reranker_type not in rerankers:
        raise ValueError(f"Unknown reranker type: {reranker_type}")

    return rerankers[reranker_type](**kwargs)
