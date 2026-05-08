"""Runtime settings router."""

from fastapi import APIRouter, Depends, HTTPException

from src.auth.utils import get_admin_user
from src.models import User
from src.knowledge.service import KnowledgeService, RagServiceError
from src.runtime_settings.schemas import (
    RuntimeReloadResponse,
    RuntimeSettingsResponse,
    RuntimeSettingsUpdate,
)
from src.runtime_settings.service import RuntimeSettingsService

router = APIRouter(prefix="/api/v1/runtime-settings", tags=["Runtime Settings"])


@router.get("", response_model=RuntimeSettingsResponse)
async def get_runtime_settings(
    current_user: User = Depends(get_admin_user),
):
    """Get the current RAG runtime settings from the shared .env file."""
    return RuntimeSettingsService().get_settings()


@router.put("", response_model=RuntimeSettingsResponse)
async def update_runtime_settings(
    payload: RuntimeSettingsUpdate,
    current_user: User = Depends(get_admin_user),
):
    """Update the shared RAG runtime settings in the repository .env file."""
    return RuntimeSettingsService().update_settings(payload)


@router.post("/reload", response_model=RuntimeReloadResponse)
async def reload_runtime_settings(
    current_user: User = Depends(get_admin_user),
):
    """Hot reload the running RAG service after config changes."""
    del current_user
    try:
        payload = await KnowledgeService().reload_runtime()
    except RagServiceError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.detail) from exc
    return RuntimeReloadResponse.model_validate(payload)
