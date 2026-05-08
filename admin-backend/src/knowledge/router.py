"""Knowledge-base management router."""

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile

from src.auth.utils import get_current_user
from src.knowledge.schemas import (
    KnowledgeBaseCreate,
    KnowledgeBaseListResponse,
    KnowledgeBaseResponse,
    KnowledgeBaseUpdate,
    SearchRequest,
    SearchResponse,
    UploadResponse,
)
from src.knowledge.service import KnowledgeService, RagServiceError
from src.models import User

router = APIRouter(prefix="/api/v1/knowledge", tags=["Knowledge Bases"])


def _handle_rag_error(exc: RagServiceError) -> HTTPException:
    """Convert upstream service failures into FastAPI HTTP exceptions."""
    return HTTPException(status_code=exc.status_code, detail=exc.detail)


@router.get("", response_model=KnowledgeBaseListResponse)
async def list_knowledge_bases(
    current_user: User = Depends(get_current_user),
):
    """List knowledge bases from the RAG service."""
    del current_user
    service = KnowledgeService()
    try:
        items = await service.list_knowledge_bases()
    except RagServiceError as exc:
        raise _handle_rag_error(exc) from exc

    return KnowledgeBaseListResponse(
        knowledge_bases=[KnowledgeBaseResponse.model_validate(item) for item in items],
        total=len(items),
    )


@router.get("/{kb_id}", response_model=KnowledgeBaseResponse)
async def get_knowledge_base(
    kb_id: str,
    current_user: User = Depends(get_current_user),
):
    """Get a single knowledge base."""
    del current_user
    service = KnowledgeService()
    try:
        payload = await service.get_knowledge_base(kb_id)
    except RagServiceError as exc:
        raise _handle_rag_error(exc) from exc
    return KnowledgeBaseResponse.model_validate(payload)


@router.post("", response_model=KnowledgeBaseResponse)
async def create_knowledge_base(
    payload: KnowledgeBaseCreate,
    current_user: User = Depends(get_current_user),
):
    """Create a knowledge base."""
    del current_user
    service = KnowledgeService()
    try:
        created = await service.create_knowledge_base(payload.model_dump())
    except RagServiceError as exc:
        raise _handle_rag_error(exc) from exc
    return KnowledgeBaseResponse.model_validate(created)


@router.patch("/{kb_id}", response_model=KnowledgeBaseResponse)
async def update_knowledge_base(
    kb_id: str,
    payload: KnowledgeBaseUpdate,
    current_user: User = Depends(get_current_user),
):
    """Update a knowledge base."""
    del current_user
    service = KnowledgeService()
    try:
        updated = await service.update_knowledge_base(
            kb_id,
            payload.model_dump(exclude_none=True),
        )
    except RagServiceError as exc:
        raise _handle_rag_error(exc) from exc
    return KnowledgeBaseResponse.model_validate(updated)


@router.delete("/{kb_id}", status_code=204)
async def delete_knowledge_base(
    kb_id: str,
    current_user: User = Depends(get_current_user),
):
    """Delete a knowledge base."""
    del current_user
    service = KnowledgeService()
    try:
        await service.delete_knowledge_base(kb_id)
    except RagServiceError as exc:
        raise _handle_rag_error(exc) from exc


@router.post("/{kb_id}/upload", response_model=UploadResponse)
async def upload_document(
    kb_id: str,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
):
    """Upload a document to the RAG service."""
    del current_user
    service = KnowledgeService()
    try:
        payload = await service.upload_document(
            kb_id,
            file_name=file.filename or "upload.bin",
            file_bytes=await file.read(),
            content_type=file.content_type,
        )
    except RagServiceError as exc:
        raise _handle_rag_error(exc) from exc
    return UploadResponse.model_validate(payload)


@router.post("/{kb_id}/search", response_model=SearchResponse)
async def search_knowledge_base(
    kb_id: str,
    payload: SearchRequest,
    current_user: User = Depends(get_current_user),
):
    """Search a knowledge base."""
    del current_user
    service = KnowledgeService()
    try:
        result = await service.search_knowledge_base(kb_id, payload.model_dump(exclude_none=True))
    except RagServiceError as exc:
        raise _handle_rag_error(exc) from exc
    return SearchResponse.model_validate(result)
