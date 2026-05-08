"""Service layer for knowledge-base management via the RAG API."""

from __future__ import annotations

import asyncio
import json
import mimetypes
import os
import uuid
from pathlib import Path
from typing import Any, Dict, Optional
from urllib import error, request


class RagServiceError(Exception):
    """Raised when the upstream RAG service returns an actionable error."""

    def __init__(self, status_code: int, detail: str):
        super().__init__(detail)
        self.status_code = status_code
        self.detail = detail


class KnowledgeService:
    """Proxy knowledge-base operations to the standalone RAG service."""

    def __init__(self) -> None:
        self.repo_root = Path(__file__).resolve().parents[3]
        self.env_path = self.repo_root / ".env"
        self._env_cache: Optional[Dict[str, str]] = None

    async def get_health(self) -> Dict[str, Any]:
        """Return the upstream RAG health payload."""
        payload = await self._request("GET", "/health", include_api_key=False)
        return payload if isinstance(payload, dict) else {}

    async def list_knowledge_bases(self) -> list[Dict[str, Any]]:
        """List knowledge bases from the RAG service."""
        payload = await self._request("GET", "/api/v1/knowledge", include_api_key=False)
        return payload if isinstance(payload, list) else []

    async def get_knowledge_base(self, kb_id: str) -> Dict[str, Any]:
        """Fetch a knowledge base."""
        payload = await self._request("GET", f"/api/v1/knowledge/{kb_id}", include_api_key=False)
        return payload if isinstance(payload, dict) else {}

    async def create_knowledge_base(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Create a knowledge base."""
        result = await self._request("POST", "/api/v1/knowledge", json_body=payload)
        return result if isinstance(result, dict) else {}

    async def update_knowledge_base(self, kb_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Update a knowledge base."""
        result = await self._request("PATCH", f"/api/v1/knowledge/{kb_id}", json_body=payload)
        return result if isinstance(result, dict) else {}

    async def delete_knowledge_base(self, kb_id: str) -> None:
        """Delete a knowledge base."""
        await self._request("DELETE", f"/api/v1/knowledge/{kb_id}")

    async def upload_document(
        self,
        kb_id: str,
        *,
        file_name: str,
        file_bytes: bytes,
        content_type: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Upload a document into a knowledge base."""
        result = await self._request(
            "POST",
            f"/api/v1/knowledge/{kb_id}/upload",
            files={
                "file": (
                    file_name,
                    file_bytes,
                    content_type or mimetypes.guess_type(file_name)[0] or "application/octet-stream",
                )
            },
            timeout=120.0,
        )
        return result if isinstance(result, dict) else {}

    async def search_knowledge_base(self, kb_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Search a knowledge base."""
        result = await self._request(
            "POST",
            f"/api/v1/knowledge/{kb_id}/search",
            json_body=payload,
            include_api_key=False,
        )
        return result if isinstance(result, dict) else {}

    async def reload_runtime(self) -> Dict[str, Any]:
        """Trigger a hot reload on the RAG runtime."""
        result = await self._request("POST", "/api/v1/runtime/reload")
        return result if isinstance(result, dict) else {}

    async def _request(
        self,
        method: str,
        path: str,
        *,
        json_body: Optional[Dict[str, Any]] = None,
        files: Optional[Dict[str, Any]] = None,
        include_api_key: bool = True,
        timeout: float = 30.0,
    ) -> Any:
        """Send a request to the upstream RAG service and normalize failures."""
        headers: Dict[str, str] = {}
        if include_api_key:
            headers["X-API-Key"] = self._get_setting("API_KEY", "rag-secret-key")

        body: Optional[bytes] = None
        if json_body is not None:
            body = json.dumps(json_body).encode("utf-8")
            headers["Content-Type"] = "application/json"
        elif files is not None:
            body, content_type = self._encode_multipart(files)
            headers["Content-Type"] = content_type

        target = self._get_setting("API_ENDPOINT", "http://localhost:8000").rstrip("/") + path
        req = request.Request(target, data=body, headers=headers, method=method)

        def do_request() -> Any:
            try:
                with request.urlopen(req, timeout=timeout) as response:
                    raw = response.read().decode("utf-8")
                    if not raw:
                        return None
                    try:
                        return json.loads(raw)
                    except json.JSONDecodeError:
                        return raw
            except error.HTTPError as exc:
                raw = exc.read().decode("utf-8", errors="ignore")
                raise RagServiceError(exc.code, self._extract_error_detail(raw) or exc.reason) from exc
            except error.URLError as exc:
                raise RagServiceError(503, f"RAG 服务不可用：{exc.reason}") from exc

        return await self._run_blocking(do_request)

    def _load_repo_env(self) -> Dict[str, str]:
        """Parse the shared repository .env file once."""
        if self._env_cache is not None:
            return self._env_cache

        values: Dict[str, str] = {}
        if self.env_path.exists():
            for line in self.env_path.read_text(encoding="utf-8").splitlines():
                stripped = line.strip()
                if not stripped or stripped.startswith("#") or "=" not in stripped:
                    continue
                key, value = stripped.split("=", 1)
                values[key.strip()] = value.strip().strip('"').strip("'")

        self._env_cache = values
        return values

    def _get_setting(self, key: str, default: str) -> str:
        """Read a setting from environment or the repo .env file."""
        return os.environ.get(key) or self._load_repo_env().get(key, default)

    def _extract_error_detail(self, payload: str) -> str:
        """Extract the most useful error message from an upstream response."""
        try:
            data = json.loads(payload)
        except json.JSONDecodeError:
            return payload

        detail = data.get("detail")
        return detail if isinstance(detail, str) else payload

    def _encode_multipart(self, files: Dict[str, Any]) -> tuple[bytes, str]:
        """Encode a small multipart/form-data payload using only the stdlib."""
        boundary = f"----YangRagBoundary{uuid.uuid4().hex}"
        body = bytearray()

        for field_name, file_info in files.items():
            file_name, file_bytes, content_type = file_info
            body.extend(f"--{boundary}\r\n".encode("utf-8"))
            body.extend(
                f'Content-Disposition: form-data; name="{field_name}"; filename="{file_name}"\r\n'.encode("utf-8")
            )
            body.extend(f"Content-Type: {content_type}\r\n\r\n".encode("utf-8"))
            body.extend(file_bytes)
            body.extend(b"\r\n")

        body.extend(f"--{boundary}--\r\n".encode("utf-8"))
        return bytes(body), f"multipart/form-data; boundary={boundary}"

    async def _run_blocking(self, func):
        """Run a blocking stdlib HTTP request in a Python 3.8-compatible way."""
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, func)
