"""Answer synthesizer using LLM for RAG."""

from typing import Any, Dict, List, Literal, Optional, Union

from langchain.callbacks.streaming_stdout import StreamingStdOutCallbackHandler
from langchain_core.output_parsers import StrOutputParser
from langchain_core.language_models import BaseChatModel

from src.core.config import is_placeholder_secret, settings
from src.core.prompts import (
    RAG_SYSTEM_PROMPT,
    RAG_HUMAN_TEMPLATE,
    format_context,
)
from src.knowledge.manager import KnowledgeBase
from src.retrieval.reranker import get_reranker, BaseReranker
from src.retrieval.retriever import create_retriever


def create_llm(
    provider: Optional[str] = None,
    model: Optional[str] = None,
    api_key: Optional[str] = None,
    base_url: Optional[str] = None,
    temperature: float = 0.7,
    streaming: bool = True,
) -> BaseChatModel:
    """Create LLM instance based on provider configuration.

    Args:
        provider: LLM provider (openai, ollama, siliconflow, qwen)
        model: Model name
        api_key: API key
        base_url: Base URL for API
        temperature: Sampling temperature
        streaming: Enable streaming

    Returns:
        LLM instance
    """
    from langchain_openai import ChatOpenAI
    from langchain_community.chat_models import ChatOllama

    provider = provider or settings.llm_provider
    model = model or settings.llm_model
    api_key = api_key or settings.llm_api_key or None
    base_url = base_url or settings.llm_base_url

    callbacks = [StreamingStdOutCallbackHandler()] if streaming else []

    if provider == "openai":
        if is_placeholder_secret(api_key):
            raise ValueError("OpenAI LLM API Key 未配置，请先在系统设置中保存有效的 LLM_API_KEY。")
        return ChatOpenAI(
            model=model,
            api_key=api_key,
            base_url=base_url,
            streaming=streaming,
            temperature=temperature,
            callbacks=callbacks,
        )
    elif provider == "ollama":
        return ChatOllama(
            model=model,
            base_url=base_url or "http://localhost:11434",
            temperature=temperature,
            callbacks=callbacks,
        )
    elif provider == "siliconflow":
        if is_placeholder_secret(api_key):
            raise ValueError("硅基流动 LLM API Key 未配置，请先在系统设置中保存有效的 LLM_API_KEY。")
        return ChatOpenAI(
            model=model,
            api_key=api_key,
            base_url="https://api.siliconflow.cn/v1",
            streaming=streaming,
            temperature=temperature,
            callbacks=callbacks,
        )
    elif provider == "qwen":
        if is_placeholder_secret(api_key):
            raise ValueError("阿里云百炼 LLM API Key 未配置，请先在系统设置中保存有效的 LLM_API_KEY。")
        return ChatOpenAI(
            model=model,
            api_key=api_key,
            base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
            streaming=streaming,
            temperature=temperature,
            callbacks=callbacks,
        )
    else:
        raise ValueError(f"Unknown LLM provider: {provider}")


class RAGSynthesizer:
    """RAG answer synthesizer combining retrieval and generation."""

    def __init__(
            self,
            knowledge_base: KnowledgeBase,
            llm: Optional[BaseChatModel] = None,
            reranker: Optional[BaseReranker] = None,
            retrieval_top_k: int = 5,
            rerank_top_k: int = 3,
            retrieval_mode: Literal["vector", "hybrid"] = "vector",
            use_reranker: bool = True,
            streaming: bool = True,
    ):
        """Initialize RAG synthesizer.

        Args:
            knowledge_base: Knowledge base to query
            llm: LLM for answer generation
            reranker: Reranker for improving results
            retrieval_top_k: Number of initial retrieval results
            rerank_top_k: Number of results after reranking
            retrieval_mode: Retrieval mode (vector or hybrid)
            use_reranker: Whether to use reranking
            streaming: Whether to enable streaming responses
        """
        self.knowledge_base = knowledge_base
        self.retrieval_top_k = retrieval_top_k
        self.rerank_top_k = rerank_top_k
        self.retrieval_mode = retrieval_mode
        self.use_reranker = use_reranker

        self.llm = llm or create_llm(
            streaming=streaming,
            temperature=settings.llm_temperature,
        )

        if isinstance(reranker, str):
            reranker = get_reranker(reranker)
        if use_reranker and reranker is None:
            reranker = get_reranker("simple")
        self.reranker = reranker

    @property
    def provider_info(self) -> Dict[str, str]:
        """Get current LLM provider information."""
        return {
            "provider": settings.llm_provider,
            "model": settings.llm_model,
        }

    def _retrieve(self, query: str) -> List[dict]:
        """Retrieve documents for query."""
        if self.retrieval_mode == "hybrid":
            retriever = create_retriever(
                knowledge_base=self.knowledge_base,
                retriever_type="hybrid",
                top_k=self.retrieval_top_k,
            )
            return retriever.search(query=query, top_k=self.retrieval_top_k)

        return self.knowledge_base.search(
            query=query,
            top_k=self.retrieval_top_k,
        )

    def _rerank(
            self,
            query: str,
            documents: List[dict],
    ) -> List[dict]:
        """Rerank retrieved documents."""
        if not self.use_reranker or not self.reranker:
            return documents[:self.rerank_top_k]

        from langchain_core.documents import Document

        docs_for_rerank = [
            Document(page_content=d["content"], metadata=d["metadata"])
            for d in documents
        ]

        reranked = self.reranker.rerank(
            query=query,
            documents=docs_for_rerank,
            top_k=self.rerank_top_k,
        )

        return [
            {
                "content": r["content"],
                "metadata": r["metadata"],
                "score": r["score"],
            }
            for r in reranked
        ]

    def _format_context(self, results: List[dict]) -> str:
        """Format retrieval results as context."""
        return format_context(results, max_length=3000)

    def _generate(
            self,
            query: str,
            context: str,
            conversation_history: Optional[List[dict]] = None,
    ) -> str:
        """Generate answer using LLM."""
        from langchain_core.prompts import ChatPromptTemplate

        prompt = ChatPromptTemplate.from_messages([
            ("system", RAG_SYSTEM_PROMPT),
            ("human", RAG_HUMAN_TEMPLATE),
        ])

        chain = prompt | self.llm | StrOutputParser()

        response = chain.invoke({
            "question": query,
            "context": context,
        })

        return response

    def invoke(
            self,
            query: str,
            conversation_history: Optional[List[dict]] = None,
            return_sources: bool = True,
    ) -> Dict[str, Any]:
        """Process a query and generate answer.

        Args:
            query: User query
            conversation_history: Optional conversation history
            return_sources: Whether to return source documents

        Returns:
            Dict with answer and optionally sources
        """
        results = self._retrieve(query)

        if not results:
            return {
                "answer": "抱歉，我在知识库中没有找到与您问题相关的内容。",
                "sources": [],
                "query": query,
            }

        reranked_results = self._rerank(query, results)
        context = self._format_context(reranked_results)

        answer = self._generate(query, context, conversation_history)

        result = {
            "answer": answer,
            "query": query,
        }

        if return_sources:
            result["sources"] = [
                {
                    "content": r["content"][:200] + "..." if len(r["content"]) > 200 else r["content"],
                    "source": r["metadata"].get("source", "Unknown"),
                    "score": r.get("score", 0),
                }
                for r in reranked_results
            ]

        return result

    async def ainvoke(
            self,
            query: str,
            conversation_history: Optional[List[dict]] = None,
            return_sources: bool = True,
    ) -> Dict[str, Any]:
        """Async version of invoke."""
        import asyncio
        return await asyncio.to_thread(
            self.invoke,
            query,
            conversation_history,
            return_sources,
        )


class StreamingRAGSynthesizer(RAGSynthesizer):
    """RAG synthesizer with streaming support."""

    def __init__(self, *args, **kwargs):
        """Initialize with streaming enabled."""
        super().__init__(*args, streaming=True, **kwargs)

    def _generate_streaming(
            self,
            query: str,
            context: str,
    ):
        """Generate streaming response."""
        from langchain_core.prompts import ChatPromptTemplate

        prompt = ChatPromptTemplate.from_messages([
            ("system", RAG_SYSTEM_PROMPT),
            ("human", RAG_HUMAN_TEMPLATE),
        ])

        chain = prompt | self.llm

        return chain.stream({
            "question": query,
            "context": context,
        })

    def invoke_streaming(
            self,
            query: str,
            return_sources: bool = True,
    ):
        """Process query with streaming response.

        Yields:
            Chunks of the response
        """
        results = self._retrieve(query)

        reranked_results = self._rerank(query, results)
        context = self._format_context(reranked_results)

        if return_sources:
            yield {"type": "sources", "data": reranked_results}

        for chunk in self._generate_streaming(query, context):
            yield {"type": "content", "data": chunk}


class CodeAgentRAGSynthesizer(RAGSynthesizer):
    """RAG synthesizer optimized for code assistance."""

    CODE_AGENT_PROMPT = """你是一个专业的代码助手。当回答涉及代码的问题时：

1. 优先从知识库中检索相关的代码示例和文档
2. 提供清晰、可运行的代码示例
3. 解释代码的工作原理和最佳实践
4. 如果涉及特定框架或库，引用知识库中的相关文档

## 上下文
{context}

## 用户问题
{question}

## 回答：
"""

    def __init__(self, *args, **kwargs):
        """Initialize code agent RAG synthesizer."""
        super().__init__(*args, **kwargs)

    def _generate(
            self,
            query: str,
            context: str,
            conversation_history: Optional[List[dict]] = None,
    ) -> str:
        """Generate answer with code-focused prompt."""
        prompt = self.CODE_AGENT_PROMPT.format(
            context=context,
            question=query,
        )

        messages = [
            {"role": "system", "content": RAG_SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ]

        if conversation_history:
            for msg in conversation_history[-5:]:
                messages.append({
                    "role": msg.get("role", "user"),
                    "content": msg.get("content", ""),
                })

        return self.llm.invoke(messages).content


def create_synthesizer(
        knowledge_base: KnowledgeBase,
        synthesizer_type: Literal["default", "streaming", "code-agent"] = "default",
        **kwargs,
) -> Union[RAGSynthesizer, StreamingRAGSynthesizer, CodeAgentRAGSynthesizer]:
    """Create synthesizer instance.

    Args:
        knowledge_base: Knowledge base to query
        synthesizer_type: Type of synthesizer
        **kwargs: Additional arguments

    Returns:
        Synthesizer instance
    """
    reranker = kwargs.pop("reranker", None)
    if reranker and isinstance(reranker, str):
        reranker = get_reranker(reranker)

    if synthesizer_type == "streaming":
        return StreamingRAGSynthesizer(
            knowledge_base=knowledge_base,
            reranker=reranker,
            **kwargs,
        )
    elif synthesizer_type == "code-agent":
        return CodeAgentRAGSynthesizer(
            knowledge_base=knowledge_base,
            reranker=reranker,
            **kwargs,
        )
    else:
        return RAGSynthesizer(
            knowledge_base=knowledge_base,
            reranker=reranker,
            **kwargs,
        )
