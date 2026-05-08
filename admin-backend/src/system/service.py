"""Service layer for the admin dashboard overview."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.knowledge.schemas import KnowledgeBaseResponse
from src.knowledge.service import KnowledgeService, RagServiceError
from src.models import User
from src.system.schemas import (
    SystemOverviewResponse,
    SystemOverviewStats,
    SystemServiceItem,
)
from src.vector_databases.service import VectorDatabaseService


class SystemOverviewService:
    """Aggregate runtime signals across admin and RAG services."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.knowledge_service = KnowledgeService()

    async def get_overview(self, *, include_user_total: bool) -> SystemOverviewResponse:
        """Build the dashboard overview payload."""
        vector_runtime = await VectorDatabaseService(self.db).get_runtime_overview()

        rag_status = "online"
        rag_detail = "RAG 服务运行正常"
        recent_knowledge_bases: list[KnowledgeBaseResponse] = []
        total_knowledge_bases = 0
        total_documents = 0
        total_chunks = 0

        try:
            await self.knowledge_service.get_health()
            kb_payloads = await self.knowledge_service.list_knowledge_bases()
            recent_knowledge_bases = [
                KnowledgeBaseResponse.model_validate(item)
                for item in kb_payloads[:5]
            ]
            total_knowledge_bases = len(kb_payloads)
            total_documents = sum(item.document_count for item in recent_knowledge_bases)
            total_chunks = sum(item.chunk_count for item in recent_knowledge_bases)

            if len(kb_payloads) > len(recent_knowledge_bases):
                for item in kb_payloads[len(recent_knowledge_bases):]:
                    total_documents += int(item.get("document_count", 0) or 0)
                    total_chunks += int(item.get("chunk_count", 0) or 0)
        except RagServiceError as exc:
            rag_status = "offline"
            rag_detail = exc.detail

        total_users = await self._count_users() if include_user_total else 0
        vector_service_status = (
            "online" if vector_runtime.status == "online" else "warning"
        )

        return SystemOverviewResponse(
            generated_at=datetime.utcnow(),
            stats=SystemOverviewStats(
                total_users=total_users,
                total_knowledge_bases=total_knowledge_bases,
                total_documents=total_documents,
                total_chunks=total_chunks,
                vector_profiles=vector_runtime.managed_profiles,
            ),
            services=[
                SystemServiceItem(
                    key="admin",
                    name="管理后端",
                    status="online",
                    detail="认证、配置与管理接口可用",
                ),
                SystemServiceItem(
                    key="rag",
                    name="RAG 服务",
                    status=rag_status,  # type: ignore[arg-type]
                    detail=rag_detail,
                ),
                SystemServiceItem(
                    key="vector",
                    name="向量存储",
                    status=vector_service_status,  # type: ignore[arg-type]
                    detail=vector_runtime.message,
                ),
            ],
            recent_knowledge_bases=recent_knowledge_bases,
            vector_runtime=vector_runtime,
        )

    async def _count_users(self) -> int:
        """Count current users."""
        result = await self.db.execute(select(func.count(User.id)))
        return result.scalar() or 0
