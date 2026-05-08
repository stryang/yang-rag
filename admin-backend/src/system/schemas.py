"""Schemas for admin dashboard system overview."""

from datetime import datetime
from typing import List, Literal

from pydantic import BaseModel

from src.knowledge.schemas import KnowledgeBaseResponse
from src.vector_databases.schemas import VectorDatabaseRuntimeResponse


ServiceStatus = Literal["online", "warning", "offline"]


class SystemServiceItem(BaseModel):
    """Health summary for a service shown in the dashboard."""

    key: str
    name: str
    status: ServiceStatus
    detail: str


class SystemOverviewStats(BaseModel):
    """Top-level counters for the dashboard."""

    total_users: int
    total_knowledge_bases: int
    total_documents: int
    total_chunks: int
    vector_profiles: int


class SystemOverviewResponse(BaseModel):
    """Payload consumed by the dashboard overview page."""

    generated_at: datetime
    stats: SystemOverviewStats
    services: List[SystemServiceItem]
    recent_knowledge_bases: List[KnowledgeBaseResponse]
    vector_runtime: VectorDatabaseRuntimeResponse
