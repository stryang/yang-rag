"""System overview router."""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.utils import get_current_user
from src.database import get_db
from src.models import User
from src.system.schemas import SystemOverviewResponse
from src.system.service import SystemOverviewService

router = APIRouter(prefix="/api/v1/system", tags=["System"])


@router.get("/overview", response_model=SystemOverviewResponse)
async def get_system_overview(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Return the admin dashboard overview payload."""
    service = SystemOverviewService(db)
    return await service.get_overview(include_user_total=current_user.role == "admin")
