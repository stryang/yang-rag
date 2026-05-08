"""Retriever for knowledge base search."""

from typing import Any, Dict, List, Literal, Optional, Tuple, Union

from langchain_core.documents import Document
from langchain_core.retrievers import BaseRetriever

from src.knowledge.manager import KnowledgeBase


class KnowledgeBaseRetriever(BaseRetriever):
    """Retriever for knowledge base search."""

    def __init__(
        self,
        knowledge_base: KnowledgeBase,
        top_k: int = 5,
        score_threshold: Optional[float] = None,
        filter_dict: Optional[Dict] = None,
    ):
        """Initialize retriever.

        Args:
            knowledge_base: Knowledge base to search
            top_k: Number of results to return
            score_threshold: Minimum similarity score threshold
            filter_dict: Metadata filter
        """
        self.knowledge_base = knowledge_base
        self.top_k = top_k
        self.score_threshold = score_threshold
        self.filter_dict = filter_dict

    def _get_relevant_documents(
        self, query: str, **kwargs
    ) -> List[Document]:
        """Get relevant documents for query."""
        results = self.knowledge_base.search(
            query=query,
            top_k=self.top_k,
            filter_dict=self.filter_dict,
        )

        docs = []
        for result in results:
            score = result.get("score", 0.0)

            if self.score_threshold and score < self.score_threshold:
                continue

            docs.append(
                Document(
                    page_content=result["content"],
                    metadata={
                        **result["metadata"],
                        "search_score": score,
                    },
                )
            )

        return docs

    async def _aget_relevant_documents(self, query: str, **kwargs) -> List[Document]:
        """Async get relevant documents."""
        return self._get_relevant_documents(query, **kwargs)


class HybridRetriever:
    """Hybrid retriever combining vector and keyword search."""

    def __init__(
        self,
        knowledge_base: KnowledgeBase,
        vector_weight: float = 0.7,
        keyword_weight: float = 0.3,
        top_k: int = 5,
    ):
        """Initialize hybrid retriever.

        Args:
            knowledge_base: Knowledge base to search
            vector_weight: Weight for vector search scores
            keyword_weight: Weight for keyword search scores
            top_k: Number of results to return
        """
        self.knowledge_base = knowledge_base
        self.vector_weight = vector_weight
        self.keyword_weight = keyword_weight
        self.top_k = top_k

    def search(
        self,
        query: str,
        top_k: Optional[int] = None,
    ) -> List[Dict]:
        """Hybrid search combining vector and keyword matching.

        Args:
            query: Search query
            top_k: Number of results

        Returns:
            List of search results
        """
        k = top_k or self.top_k

        vector_results = self.knowledge_base.search(query, top_k=k * 2)

        keyword_scores = self._keyword_search(query, vector_results)

        combined_results = []
        for vr in vector_results:
            content = vr["content"].lower()
            query_terms = query.lower().split()

            keyword_score = sum(1 for term in query_terms if term in content) / len(query_terms)

            combined_score = (
                self.vector_weight * (1 - vr["score"]) +
                self.keyword_weight * keyword_score
            )

            combined_results.append({
                **vr,
                "keyword_score": keyword_score,
                "combined_score": combined_score,
            })

        combined_results.sort(key=lambda x: x["combined_score"], reverse=True)

        return combined_results[:k]

    def _keyword_search(
        self,
        query: str,
        candidates: List[Dict],
    ) -> Dict[str, float]:
        """Calculate keyword matching scores."""
        scores = {}
        query_terms = set(query.lower().split())

        for candidate in candidates:
            content_terms = set(candidate["content"].lower().split())
            intersection = query_terms & content_terms

            scores[candidate["metadata"].get("chunk_id", "")] = (
                len(intersection) / len(query_terms) if query_terms else 0
            )

        return scores


class EnsembleRetriever:
    """Ensemble retriever combining multiple retrieval strategies."""

    def __init__(
        self,
        retrievers: List[BaseRetriever],
        weights: Optional[List[float]] = None,
    ):
        """Initialize ensemble retriever.

        Args:
            retrievers: List of retriever instances
            weights: Optional weights for each retriever
        """
        self.retrievers = retrievers
        self.weights = weights or [1.0 / len(retrievers)] * len(retrievers)

        if len(self.weights) != len(self.retrievers):
            raise ValueError("Number of weights must match number of retrievers")

    def search(
        self,
        query: str,
        top_k: int = 5,
    ) -> List[Document]:
        """Search using ensemble of retrievers.

        Args:
            query: Search query
            top_k: Number of results

        Returns:
            List of documents with combined scores
        """
        all_results: Dict[str, Dict] = {}

        for retriever, weight in zip(self.retrievers, self.weights):
            docs = retriever.invoke(query)

            for doc in docs:
                doc_id = doc.metadata.get("chunk_id", doc.page_content[:100])

                if doc_id not in all_results:
                    all_results[doc_id] = {
                        "document": doc,
                        "combined_score": 0.0,
                    }

                score = 1 - doc.metadata.get("search_score", 0.5)
                all_results[doc_id]["combined_score"] += weight * score

        sorted_results = sorted(
            all_results.values(),
            key=lambda x: x["combined_score"],
            reverse=True,
        )

        return [r["document"] for r in sorted_results[:top_k]]


def create_retriever(
    knowledge_base: KnowledgeBase,
    retriever_type: Literal["vector", "hybrid", "ensemble"] = "vector",
    **kwargs,
) -> Union[BaseRetriever, HybridRetriever, EnsembleRetriever]:
    """Create retriever instance.

    Args:
        knowledge_base: Knowledge base to search
        retriever_type: Type of retriever
        **kwargs: Additional arguments

    Returns:
        Retriever instance
    """
    if retriever_type == "vector":
        return KnowledgeBaseRetriever(knowledge_base=knowledge_base, **kwargs)
    elif retriever_type == "hybrid":
        return HybridRetriever(knowledge_base=knowledge_base, **kwargs)
    else:
        raise ValueError(f"Unknown retriever type: {retriever_type}")
