"""Vector database management router."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.utils import get_admin_user
from src.database import get_db
from src.models import User
from src.vector_databases.schemas import (
    VectorDatabaseCreate,
    VectorDatabaseListResponse,
    VectorDatabaseResponse,
    VectorDatabaseRuntimeResponse,
    VectorDatabaseTestResponse,
    VectorDatabaseUpdate,
)
from src.vector_databases.service import VectorDatabaseService

router = APIRouter(prefix="/api/v1/vector-databases", tags=["Vector Databases"])


def _serialize_profile(profile) -> VectorDatabaseResponse:
    """Serialize a SQLAlchemy profile model into the API response shape."""
    target = (
        profile.persist_path
        if profile.store_type in {"chroma", "faiss"}
        else f"{profile.host}:{profile.port}" if profile.host and profile.port else "-"
    )

    return VectorDatabaseResponse(
        id=profile.id,
        name=profile.name,
        store_type=profile.store_type,
        description=profile.description,
        persist_path=profile.persist_path,
        host=profile.host,
        port=profile.port,
        collection_prefix=profile.collection_prefix,
        is_default=profile.is_default,
        is_enabled=profile.is_enabled,
        last_status=profile.last_status,
        last_checked_at=profile.last_checked_at,
        last_error=profile.last_error,
        created_at=profile.created_at,
        updated_at=profile.updated_at,
        target=target,
    )


@router.get("/runtime", response_model=VectorDatabaseRuntimeResponse)
async def get_runtime_overview(
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """Get the vector database runtime overview used by the RAG service."""
    service = VectorDatabaseService(db)
    return await service.get_runtime_overview()


@router.get("", response_model=VectorDatabaseListResponse)
async def list_vector_databases(
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """List managed vector database profiles."""
    service = VectorDatabaseService(db)
    items, total = await service.list_profiles()
    return VectorDatabaseListResponse(
        items=[_serialize_profile(item) for item in items],
        total=total,
    )


@router.get("/{profile_id}", response_model=VectorDatabaseResponse)
async def get_vector_database(
    profile_id: int,
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """Get a managed vector database profile."""
    service = VectorDatabaseService(db)
    profile = await service.get_profile(profile_id)
    if not profile:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vector database profile not found")
    return _serialize_profile(profile)


@router.post("", response_model=VectorDatabaseResponse, status_code=status.HTTP_201_CREATED)
async def create_vector_database(
    payload: VectorDatabaseCreate,
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new managed vector database profile."""
    service = VectorDatabaseService(db)
    existing = await service.get_profile_by_name(payload.name)
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Profile name already exists")

    profile = await service.create_profile(**payload.model_dump())
    return _serialize_profile(profile)


@router.put("/{profile_id}", response_model=VectorDatabaseResponse)
async def update_vector_database(
    profile_id: int,
    payload: VectorDatabaseUpdate,
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """Update a managed vector database profile."""
    service = VectorDatabaseService(db)
    profile = await service.get_profile(profile_id)
    if not profile:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vector database profile not found")

    if payload.name and payload.name != profile.name:
        existing = await service.get_profile_by_name(payload.name)
        if existing:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Profile name already exists")

    updated = await service.update_profile(profile_id, **payload.model_dump(exclude_unset=True))
    if not updated:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vector database profile not found")
    return _serialize_profile(updated)


@router.post("/{profile_id}/test", response_model=VectorDatabaseTestResponse)
async def test_vector_database(
    profile_id: int,
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """Test a managed vector database profile."""
    service = VectorDatabaseService(db)
    profile = await service.get_profile(profile_id)
    if not profile:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vector database profile not found")
    return await service.test_profile(profile)


@router.post("/{profile_id}/default", response_model=VectorDatabaseResponse)
async def set_default_vector_database(
    profile_id: int,
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """Set a managed vector database profile as default."""
    service = VectorDatabaseService(db)
    profile = await service.set_default(profile_id)
    if not profile:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vector database profile not found")
    return _serialize_profile(profile)


@router.delete("/{profile_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_vector_database(
    profile_id: int,
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete a managed vector database profile."""
    service = VectorDatabaseService(db)
    deleted = await service.delete_profile(profile_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vector database profile not found")
