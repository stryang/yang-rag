"""FastAPI REST API for Yang RAG System."""

import os
import time
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional, Union

from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, File, HTTPException, UploadFile, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from src.core.config import reload_settings, settings
from src.knowledge.manager import get_kb_manager, reset_kb_manager
from src.generation.synthesizer import create_synthesizer
from src.retrieval.retriever import create_retriever
from src.retrieval.reranker import get_reranker


app = FastAPI(
    title="Yang RAG API",
    description="RAG System API with OpenAI-compatible endpoints",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def verify_api_key(x_api_key: str = Header(...)) -> str:
    """Verify API key."""
    if x_api_key != settings.api_key:
        raise HTTPException(status_code=401, detail="Invalid API key")
    return x_api_key


# ============== Request/Response Models ==============

class KnowledgeBaseCreate(BaseModel):
    """Request model for creating knowledge base."""

    name: str = Field(..., min_length=1, max_length=100)
    description: str = Field(default="", max_length=500)
    embedding_provider: Optional[str] = None
    embedding_model: Optional[str] = None


class KnowledgeBaseUpdate(BaseModel):
    """Request model for updating a knowledge base."""

    name: Optional[str] = Field(default=None, min_length=1, max_length=100)
    description: Optional[str] = Field(default=None, max_length=500)


class KnowledgeBaseResponse(BaseModel):
    """Response model for knowledge base."""

    id: str
    name: str
    description: str
    document_count: int
    chunk_count: int
    embedding_model: str
    created_at: str
    updated_at: str


class SearchRequest(BaseModel):
    """Request model for search."""

    query: str = Field(..., min_length=1, max_length=1000)
    top_k: int = Field(default=5, ge=1, le=20)
    retrieval_mode: Literal["vector", "hybrid"] = Field(default="vector")
    retrieval_top_k: Optional[int] = Field(default=None, ge=1, le=50)
    use_reranker: bool = Field(default=False)
    reranker_type: Literal["simple", "cross-encoder", "llm"] = Field(default="simple")
    rerank_top_k: Optional[int] = Field(default=None, ge=1, le=20)
    filter_dict: Optional[Dict[str, Any]] = None


class ChatMessage(BaseModel):
    """Chat message model."""

    role: Literal["system", "user", "assistant"]
    content: str


class ChatRequest(BaseModel):
    """Request model for chat/completions."""

    messages: List[ChatMessage]
    knowledge_base_id: Optional[str] = None
    temperature: float = Field(default=0.7, ge=0, le=2)
    max_tokens: int = Field(default=2000, ge=1, le=4000)
    stream: bool = Field(default=False)
    retrieval_mode: Literal["vector", "hybrid"] = Field(default="vector")
    retrieval_top_k: Optional[int] = Field(default=None, ge=1, le=50)
    use_reranker: bool = Field(default=True)
    reranker_type: Literal["simple", "cross-encoder", "llm"] = Field(default="simple")
    rerank_top_k: Optional[int] = Field(default=None, ge=1, le=20)


class ChatResponse(BaseModel):
    """Response model for chat."""

    answer: str
    sources: List[Dict[str, Any]]
    query: str


class UploadResponse(BaseModel):
    """Response model for file upload."""

    status: str
    file_name: str
    document_count: int
    chunk_count: int
    knowledge_base_id: str


class RuntimeReloadResponse(BaseModel):
    """Response model for runtime configuration reload."""

    status: str
    llm_provider: str
    llm_model: str
    embedding_provider: str
    embedding_model: str
    vector_store_type: str


# ============== Knowledge Base Endpoints ==============

@app.get("/api/v1/knowledge")
async def list_knowledge_bases() -> List[KnowledgeBaseResponse]:
    """List all knowledge bases."""
    manager = get_kb_manager()
    kbs = manager.list_knowledge_bases()
    return [
        KnowledgeBaseResponse(
            id=kb.id,
            name=kb.name,
            description=kb.description,
            document_count=kb.document_count,
            chunk_count=kb.chunk_count,
            embedding_model=kb.embedding_model,
            created_at=kb.created_at.isoformat(),
            updated_at=kb.updated_at.isoformat(),
        )
        for kb in kbs
    ]


@app.post("/api/v1/knowledge", response_model=KnowledgeBaseResponse)
async def create_knowledge_base(
    request: KnowledgeBaseCreate,
    _api_key: str = Depends(verify_api_key),
):
    """Create a new knowledge base."""
    manager = get_kb_manager()
    try:
        kb = manager.create_knowledge_base(
            name=request.name,
            description=request.description,
            embedding_provider=request.embedding_provider or settings.embedding_provider,
            embedding_model=request.embedding_model or settings.embedding_model,
        )
        return KnowledgeBaseResponse(
            id=kb.id,
            name=kb.name,
            description=kb.description,
            document_count=0,
            chunk_count=0,
            embedding_model=kb.embedding_model,
            created_at=kb.metadata.created_at.isoformat(),
            updated_at=kb.metadata.updated_at.isoformat(),
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/v1/knowledge/{kb_id}", response_model=KnowledgeBaseResponse)
async def get_knowledge_base(kb_id: str):
    """Get knowledge base by ID."""
    manager = get_kb_manager()
    try:
        kb = manager.get_knowledge_base(kb_id)
        stats = kb.get_stats()
        return KnowledgeBaseResponse(**stats)
    except KeyError:
        raise HTTPException(status_code=404, detail="Knowledge base not found")


@app.patch("/api/v1/knowledge/{kb_id}", response_model=KnowledgeBaseResponse)
async def update_knowledge_base(
    kb_id: str,
    request: KnowledgeBaseUpdate,
    _api_key: str = Depends(verify_api_key),
):
    """Update knowledge base name or description."""
    if request.name is None and request.description is None:
        raise HTTPException(status_code=400, detail="At least one field must be provided")

    manager = get_kb_manager()
    try:
        kb = manager.update_knowledge_base(
            kb_id=kb_id,
            name=request.name,
            description=request.description,
        )
        return KnowledgeBaseResponse(
            id=kb.id,
            name=kb.name,
            description=kb.description,
            document_count=kb.document_count,
            chunk_count=kb.chunk_count,
            embedding_model=kb.embedding_model,
            created_at=kb.metadata.created_at.isoformat(),
            updated_at=kb.metadata.updated_at.isoformat(),
        )
    except KeyError:
        raise HTTPException(status_code=404, detail="Knowledge base not found")


@app.delete("/api/v1/knowledge/{kb_id}")
async def delete_knowledge_base(
    kb_id: str,
    _api_key: str = Depends(verify_api_key),
):
    """Delete a knowledge base."""
    manager = get_kb_manager()
    try:
        manager.delete_knowledge_base(kb_id)
        return {"status": "deleted", "kb_id": kb_id}
    except KeyError:
        raise HTTPException(status_code=404, detail="Knowledge base not found")


# ============== Document Upload Endpoints ==============

@app.post("/api/v1/knowledge/{kb_id}/upload", response_model=UploadResponse)
async def upload_document(
    kb_id: str,
    file: UploadFile = File(...),
    _api_key: str = Depends(verify_api_key),
):
    """Upload and index a document."""
    manager = get_kb_manager()
    try:
        kb = manager.get_knowledge_base(kb_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="Knowledge base not found")

    suffix = Path(file.filename).suffix.lower()
    if suffix not in settings.supported_file_types:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type: {suffix}",
        )

    upload_dir = Path("./data/uploads")
    upload_dir.mkdir(parents=True, exist_ok=True)

    file_path = upload_dir / f"{kb_id}_{file.filename}"
    try:
        content = await file.read()
        with open(file_path, "wb") as f:
            f.write(content)

        result = kb.add_document(file_path)

        return UploadResponse(
            status="success",
            file_name=file.filename,
            document_count=result["document_count"],
            chunk_count=result["chunk_count"],
            knowledge_base_id=kb_id,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        try:
            file_path.unlink()
        except FileNotFoundError:
            pass


@app.post("/api/v1/runtime/reload", response_model=RuntimeReloadResponse)
async def reload_runtime_config(
    _api_key: str = Depends(verify_api_key),
):
    """Reload runtime configuration from .env without restarting the process."""
    reload_settings()
    reset_kb_manager()
    return RuntimeReloadResponse(
        status="reloaded",
        llm_provider=settings.llm_provider,
        llm_model=settings.llm_model,
        embedding_provider=settings.embedding_provider,
        embedding_model=settings.embedding_model,
        vector_store_type=settings.vector_store_type,
    )


# ============== Search Endpoints ==============

@app.post("/api/v1/knowledge/{kb_id}/search")
async def search_knowledge_base(
    kb_id: str,
    request: SearchRequest,
):
    """Search in a knowledge base."""
    manager = get_kb_manager()
    try:
        kb = manager.get_knowledge_base(kb_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="Knowledge base not found")

    retrieval_top_k = request.retrieval_top_k or max(request.top_k, settings.retrieval_top_k)

    if request.retrieval_mode == "hybrid":
        retriever = create_retriever(
            knowledge_base=kb,
            retriever_type="hybrid",
            top_k=retrieval_top_k,
        )
        results = retriever.search(query=request.query, top_k=retrieval_top_k)
    else:
        results = kb.search(
            query=request.query,
            top_k=retrieval_top_k,
            filter_dict=request.filter_dict,
        )

    if request.use_reranker and results:
        from langchain_core.documents import Document

        reranker = get_reranker(request.reranker_type)
        rerank_top_k = request.rerank_top_k or request.top_k
        docs = [
            Document(page_content=item.get("content", ""), metadata=item.get("metadata", {}))
            for item in results
        ]
        reranked = reranker.rerank(query=request.query, documents=docs, top_k=rerank_top_k)
        results = [
            {
                "content": item["content"],
                "metadata": item["metadata"],
                "score": item["score"],
            }
            for item in reranked
        ]

    results = results[:request.top_k]
    return {
        "query": request.query,
        "results": results,
        "total": len(results),
        "retrieval_mode": request.retrieval_mode,
        "reranked": request.use_reranker,
    }


# ============== Chat/Completion Endpoints ==============

@app.post("/v1/chat/completions")
async def chat_completions(
    request: ChatRequest,
    _api_key: str = Depends(verify_api_key),
):
    """OpenAI-compatible chat completions endpoint."""
    if not request.messages:
        raise HTTPException(status_code=400, detail="messages is required")

    last_message = request.messages[-1]
    if last_message.role != "user":
        raise HTTPException(status_code=400, detail="Last message must be from user")

    query = last_message.content
    conversation_history = [
        {"role": m.role, "content": m.content}
        for m in request.messages[:-1]
    ]

    if request.knowledge_base_id:
        manager = get_kb_manager()
        try:
            kb = manager.get_knowledge_base(request.knowledge_base_id)
        except KeyError:
            raise HTTPException(status_code=404, detail="Knowledge base not found")

        synthesizer = create_synthesizer(
            kb,
            synthesizer_type="streaming" if request.stream else "default",
            retrieval_mode=request.retrieval_mode,
            retrieval_top_k=request.retrieval_top_k or settings.retrieval_top_k,
            rerank_top_k=request.rerank_top_k or settings.rerank_top_k,
            use_reranker=request.use_reranker,
            reranker=request.reranker_type if request.use_reranker else None,
        )

        if request.stream:
            return StreamingResponse(
                stream_chat_response(synthesizer, query, conversation_history),
                media_type="text/event-stream",
            )

        result = synthesizer.invoke(query, conversation_history)
    else:
        from langchain_openai import ChatOpenAI
        llm = ChatOpenAI(
            model=settings.llm_model,
            api_key=settings.llm_api_key,
            base_url=settings.llm_base_url,
            temperature=request.temperature,
            max_tokens=request.max_tokens,
        )
        messages = [{"role": m.role, "content": m.content} for m in request.messages]
        response = llm.invoke(messages)
        result = {
            "answer": response.content,
            "sources": [],
            "query": query,
        }

    return {
        "id": "chatcmpl-" + os.urandom(12).hex(),
        "object": "chat.completion",
        "created": int(time.time()),
        "model": settings.llm_model,
        "choices": [
            {
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": result["answer"],
                },
                "finish_reason": "stop",
            }
        ],
        "usage": {
            "prompt_tokens": 0,
            "completion_tokens": len(result["answer"].split()),
            "total_tokens": len(result["answer"].split()) * 2,
        },
        "rag_sources": result.get("sources", []),
    }


async def stream_chat_response(
    synthesizer,
    query: str,
    conversation_history: List[Dict],
):
    """Stream chat response."""
    import json
    import asyncio

    results = synthesizer.invoke(query, conversation_history, return_sources=True)

    yield f"data: {json.dumps({'type': 'sources', 'data': results.get('sources', [])})}\n\n"

    for chunk in results.get("answer", ""):
        yield f"data: {json.dumps({'type': 'content', 'data': chunk})}\n\n"
        await asyncio.sleep(0.01)

    yield "data: [DONE]\n\n"


# ============== Health Check ==============

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "version": "1.0.0"}


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "name": "Yang RAG API",
        "version": "1.0.0",
        "docs": "/docs",
    }


def create_app() -> FastAPI:
    """Create and configure FastAPI app."""
    settings.ensure_directories()
    return app


if __name__ == "__main__":
    import uvicorn

    settings.ensure_directories()
    uvicorn.run(
        "src.api.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=True,
    )
