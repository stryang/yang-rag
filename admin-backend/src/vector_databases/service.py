"""Service layer for vector database management."""

from __future__ import annotations

import json
import os
import socket
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models import VectorDatabase
from src.vector_databases.schemas import (
    RuntimeCollectionSummary,
    VectorDatabaseRuntimeResponse,
    VectorDatabaseTestResponse,
)


class VectorDatabaseService:
    """Service for managed vector database profiles and runtime inspection."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo_root = Path(__file__).resolve().parents[3]
        self._env_cache: Optional[Dict[str, str]] = None

    async def list_profiles(self) -> Tuple[List[VectorDatabase], int]:
        """List configured vector database profiles."""
        count_result = await self.db.execute(select(func.count(VectorDatabase.id)))
        total = count_result.scalar() or 0

        result = await self.db.execute(
            select(VectorDatabase)
            .order_by(VectorDatabase.is_default.desc(), VectorDatabase.updated_at.desc())
        )
        items = result.scalars().all()
        return list(items), total

    async def get_profile(self, profile_id: int) -> Optional[VectorDatabase]:
        """Get a single vector database profile."""
        result = await self.db.execute(
            select(VectorDatabase).where(VectorDatabase.id == profile_id)
        )
        return result.scalar_one_or_none()

    async def get_profile_by_name(self, name: str) -> Optional[VectorDatabase]:
        """Get a profile by unique name."""
        result = await self.db.execute(
            select(VectorDatabase).where(VectorDatabase.name == name)
        )
        return result.scalar_one_or_none()

    async def create_profile(
        self,
        *,
        name: str,
        store_type: str,
        description: str = "",
        persist_path: Optional[str] = None,
        host: Optional[str] = None,
        port: Optional[int] = None,
        collection_prefix: Optional[str] = None,
        is_default: bool = False,
        is_enabled: bool = True,
    ) -> VectorDatabase:
        """Create a new vector database profile."""
        profile = VectorDatabase(
            name=name,
            store_type=store_type,
            description=description,
            persist_path=persist_path,
            host=host,
            port=port,
            collection_prefix=collection_prefix,
            is_default=is_default,
            is_enabled=is_enabled,
        )

        if is_default or await self._count_profiles() == 0:
            await self._clear_default_flag()
            profile.is_default = True

        self.db.add(profile)
        await self.db.flush()
        await self._refresh_profile_status(profile)
        await self.db.commit()
        await self.db.refresh(profile)
        return profile

    async def update_profile(
        self,
        profile_id: int,
        *,
        name: Optional[str] = None,
        store_type: Optional[str] = None,
        description: Optional[str] = None,
        persist_path: Optional[str] = None,
        host: Optional[str] = None,
        port: Optional[int] = None,
        collection_prefix: Optional[str] = None,
        is_default: Optional[bool] = None,
        is_enabled: Optional[bool] = None,
    ) -> Optional[VectorDatabase]:
        """Update an existing vector database profile."""
        profile = await self.get_profile(profile_id)
        if not profile:
            return None

        if name is not None:
            profile.name = name
        if store_type is not None:
            profile.store_type = store_type
        if description is not None:
            profile.description = description
        if persist_path is not None:
            profile.persist_path = persist_path
        if host is not None:
            profile.host = host
        if port is not None:
            profile.port = port
        if collection_prefix is not None:
            profile.collection_prefix = collection_prefix
        if is_enabled is not None:
            profile.is_enabled = is_enabled

        if is_default:
            await self._clear_default_flag()
            profile.is_default = True
        elif is_default is False:
            profile.is_default = False

        await self._refresh_profile_status(profile)
        await self.db.commit()
        await self.db.refresh(profile)
        return profile

    async def delete_profile(self, profile_id: int) -> bool:
        """Delete a vector database profile."""
        profile = await self.get_profile(profile_id)
        if not profile:
            return False

        was_default = profile.is_default
        await self.db.delete(profile)
        await self.db.flush()

        if was_default:
            result = await self.db.execute(
                select(VectorDatabase).order_by(VectorDatabase.updated_at.desc())
            )
            fallback = result.scalars().first()
            if fallback:
                fallback.is_default = True

        await self.db.commit()
        return True

    async def set_default(self, profile_id: int) -> Optional[VectorDatabase]:
        """Set a profile as the default profile."""
        profile = await self.get_profile(profile_id)
        if not profile:
            return None

        await self._clear_default_flag()
        profile.is_default = True
        await self.db.commit()
        await self.db.refresh(profile)
        return profile

    async def test_profile(self, profile: VectorDatabase) -> VectorDatabaseTestResponse:
        """Test a configured vector database profile."""
        success, status, message, resolved_target = self._check_profile_target(profile)

        profile.last_status = status
        profile.last_checked_at = datetime.utcnow()
        profile.last_error = None if success else message
        await self.db.commit()
        await self.db.refresh(profile)

        return VectorDatabaseTestResponse(
            success=success,
            status=status,
            message=message,
            checked_at=profile.last_checked_at,
            resolved_target=resolved_target,
        )

    async def get_runtime_overview(self) -> VectorDatabaseRuntimeResponse:
        """Inspect the runtime vector database configuration used by the RAG service."""
        store_type = self._get_runtime_setting("VECTOR_STORE_TYPE", "chroma")
        persist_path = self._resolve_runtime_persist_path()
        host = self._get_runtime_setting("MILVUS_HOST", "localhost") if store_type == "milvus" else None
        port = int(self._get_runtime_setting("MILVUS_PORT", "19530")) if store_type == "milvus" else None

        collections = self._load_runtime_collections()
        storage_usage_bytes = self._directory_size(persist_path) if persist_path else 0
        managed_profiles = await self._count_profiles()

        if store_type == "milvus":
            reachable = self._can_connect_socket(host or "localhost", port or 19530)
            status = "online" if reachable else "warning"
            message = "Milvus 连接正常" if reachable else "Milvus 未连接，当前为配置视图"
            target = f"{host}:{port}"
        else:
            exists = persist_path.exists() if persist_path else False
            status = "online" if exists else "warning"
            message = "持久化目录可用" if exists else "持久化目录尚未生成，通常在首次写入后创建"
            target = str(persist_path) if persist_path else "-"

        return VectorDatabaseRuntimeResponse(
            store_type=store_type,  # type: ignore[arg-type]
            status=status,  # type: ignore[arg-type]
            target=target,
            persist_path=str(persist_path) if persist_path else None,
            host=host,
            port=port,
            message=message,
            collection_count=len(collections),
            total_documents=sum(item.document_count for item in collections),
            total_chunks=sum(item.chunk_count for item in collections),
            storage_usage_bytes=storage_usage_bytes,
            storage_usage_label=self._format_bytes(storage_usage_bytes),
            managed_profiles=managed_profiles,
            collections=collections,
        )

    async def _count_profiles(self) -> int:
        """Count configured vector database profiles."""
        result = await self.db.execute(select(func.count(VectorDatabase.id)))
        return result.scalar() or 0

    async def _clear_default_flag(self) -> None:
        """Clear the default marker from all profiles."""
        result = await self.db.execute(select(VectorDatabase))
        for profile in result.scalars().all():
            profile.is_default = False

    async def _refresh_profile_status(self, profile: VectorDatabase) -> None:
        """Refresh and persist last health state for a profile."""
        success, status, message, _ = self._check_profile_target(profile)
        profile.last_status = status
        profile.last_checked_at = datetime.utcnow()
        profile.last_error = None if success else message

    def _check_profile_target(self, profile: VectorDatabase) -> Tuple[bool, str, str, str]:
        """Run a lightweight availability check for a profile target."""
        if profile.store_type in {"chroma", "faiss"}:
            resolved_path = self._resolve_path(profile.persist_path or "")
            if resolved_path.exists() and resolved_path.is_dir():
                return True, "online", "路径存在且可访问", str(resolved_path)

            parent = resolved_path.parent
            if parent.exists() and os.access(parent, os.W_OK):
                return False, "warning", "目标目录尚不存在，但父目录可写", str(resolved_path)

            return False, "offline", "目标路径不可访问", str(resolved_path)

        target = f"{profile.host}:{profile.port}" if profile.host and profile.port else "-"
        if profile.host and profile.port and self._can_connect_socket(profile.host, profile.port):
            return True, "online", "网络连接成功", target
        return False, "warning", "无法连接到 Milvus 目标地址", target

    def _load_runtime_collections(self) -> List[RuntimeCollectionSummary]:
        """Load runtime collection summaries from knowledge base metadata."""
        metadata_dir = self.repo_root / "data" / "kb_metadata"
        if not metadata_dir.exists():
            return []

        collections: List[RuntimeCollectionSummary] = []
        for metadata_file in sorted(metadata_dir.glob("*.json")):
            try:
                payload = json.loads(metadata_file.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                continue

            collections.append(
                RuntimeCollectionSummary(
                    id=payload.get("id", metadata_file.stem),
                    name=payload.get("name", metadata_file.stem),
                    description=payload.get("description", ""),
                    document_count=int(payload.get("document_count", 0) or 0),
                    chunk_count=int(payload.get("chunk_count", 0) or 0),
                    embedding_model=payload.get("embedding_model", ""),
                    updated_at=str(payload.get("updated_at", "")),
                )
            )

        collections.sort(key=lambda item: item.updated_at, reverse=True)
        return collections

    def _get_runtime_setting(self, key: str, default: str) -> str:
        """Read a runtime setting from environment or repo .env."""
        if key in os.environ:
            return os.environ[key]

        env_values = self._load_repo_env()
        return env_values.get(key, default)

    def _resolve_runtime_persist_path(self) -> Path:
        """Resolve the runtime persist path relative to repository root."""
        raw_path = self._get_runtime_setting("VECTOR_STORE_PERSIST_DIR", "./data/vectorstore")
        return self._resolve_path(raw_path)

    def _resolve_path(self, raw_path: str) -> Path:
        """Resolve a potentially relative path against the repository root."""
        path = Path(raw_path)
        if path.is_absolute():
            return path
        return (self.repo_root / path).resolve()

    def _load_repo_env(self) -> Dict[str, str]:
        """Parse the repository .env file once."""
        if self._env_cache is not None:
            return self._env_cache

        env_path = self.repo_root / ".env"
        values: Dict[str, str] = {}
        if env_path.exists():
            for line in env_path.read_text(encoding="utf-8").splitlines():
                stripped = line.strip()
                if not stripped or stripped.startswith("#") or "=" not in stripped:
                    continue
                key, value = stripped.split("=", 1)
                values[key.strip()] = value.strip().strip('"').strip("'")

        self._env_cache = values
        return values

    def _directory_size(self, directory: Path) -> int:
        """Compute recursive directory size in bytes."""
        if not directory.exists():
            return 0

        total = 0
        for file_path in directory.rglob("*"):
            if file_path.is_file():
                try:
                    total += file_path.stat().st_size
                except OSError:
                    continue
        return total

    def _format_bytes(self, size: int) -> str:
        """Format a byte count for UI display."""
        if size <= 0:
            return "0 B"

        units = ["B", "KB", "MB", "GB", "TB"]
        value = float(size)
        for unit in units:
            if value < 1024 or unit == units[-1]:
                return f"{value:.1f} {unit}" if unit != "B" else f"{int(value)} {unit}"
            value /= 1024
        return f"{size} B"

    def _can_connect_socket(self, host: str, port: int) -> bool:
        """Check whether a TCP socket is reachable."""
        try:
            with socket.create_connection((host, port), timeout=1.0):
                return True
        except OSError:
            return False
