"""Service for reading and writing RAG runtime settings."""

from __future__ import annotations

from pathlib import Path
from typing import Dict, Iterable, Optional

from src.runtime_settings.schemas import RuntimeSettingsResponse, RuntimeSettingsUpdate


class RuntimeSettingsService:
    """Manage the shared RAG runtime settings stored in the repo .env file."""

    ENV_KEY_ORDER = (
        "API_ENDPOINT",
        "LLM_PROVIDER",
        "LLM_MODEL",
        "LLM_API_KEY",
        "LLM_BASE_URL",
        "LLM_TEMPERATURE",
        "LLM_MAX_TOKENS",
        "EMBEDDING_PROVIDER",
        "EMBEDDING_MODEL",
        "EMBEDDING_API_KEY",
        "EMBEDDING_BASE_URL",
        "EMBEDDING_DIMENSION",
        "VECTOR_STORE_TYPE",
        "VECTOR_STORE_PERSIST_DIR",
        "MILVUS_HOST",
        "MILVUS_PORT",
        "MILVUS_COLLECTION",
    )

    def __init__(self) -> None:
        self.repo_root = Path(__file__).resolve().parents[3]
        self.env_path = self.repo_root / ".env"

    def get_settings(self) -> RuntimeSettingsResponse:
        """Load runtime settings from the repository .env file."""
        env_values = self._load_repo_env()
        llm_api_key = self._normalize_secret(env_values.get("LLM_API_KEY", ""))
        embedding_api_key = self._normalize_secret(env_values.get("EMBEDDING_API_KEY", ""))

        return RuntimeSettingsResponse(
            llm_provider=env_values.get("LLM_PROVIDER", "openai"),  # type: ignore[arg-type]
            llm_model=env_values.get("LLM_MODEL", "gpt-4o-mini"),
            llm_api_key=llm_api_key,
            llm_base_url=self._normalize_optional(env_values.get("LLM_BASE_URL")),
            llm_temperature=float(env_values.get("LLM_TEMPERATURE", "0.7") or 0.7),
            llm_max_tokens=int(env_values.get("LLM_MAX_TOKENS", "2000") or 2000),
            embedding_provider=env_values.get("EMBEDDING_PROVIDER", "openai"),  # type: ignore[arg-type]
            embedding_model=env_values.get("EMBEDDING_MODEL", "text-embedding-3-small"),
            embedding_api_key=embedding_api_key,
            embedding_base_url=self._normalize_optional(env_values.get("EMBEDDING_BASE_URL")),
            embedding_dimension=int(env_values.get("EMBEDDING_DIMENSION", "1536") or 1536),
            vector_store_type=env_values.get("VECTOR_STORE_TYPE", "chroma"),  # type: ignore[arg-type]
            vector_store_persist_dir=env_values.get("VECTOR_STORE_PERSIST_DIR", "./data/vectorstore"),
            milvus_host=env_values.get("MILVUS_HOST", "localhost"),
            milvus_port=int(env_values.get("MILVUS_PORT", "19530") or 19530),
            milvus_collection=env_values.get("MILVUS_COLLECTION", "yang_rag"),
            api_endpoint=env_values.get("API_ENDPOINT", "http://localhost:8000"),
            uses_placeholder_llm_key=self._is_placeholder_secret(env_values.get("LLM_API_KEY")),
            uses_placeholder_embedding_key=self._is_placeholder_secret(env_values.get("EMBEDDING_API_KEY")),
        )

    def update_settings(self, payload: RuntimeSettingsUpdate) -> RuntimeSettingsResponse:
        """Persist runtime settings to the repository .env file."""
        updates = {
            "API_ENDPOINT": payload.api_endpoint.strip() or "http://localhost:8000",
            "LLM_PROVIDER": payload.llm_provider,
            "LLM_MODEL": payload.llm_model,
            "LLM_API_KEY": self._normalize_secret(payload.llm_api_key),
            "LLM_BASE_URL": self._normalize_optional(payload.llm_base_url) or "",
            "LLM_TEMPERATURE": str(payload.llm_temperature),
            "LLM_MAX_TOKENS": str(payload.llm_max_tokens),
            "EMBEDDING_PROVIDER": payload.embedding_provider,
            "EMBEDDING_MODEL": payload.embedding_model,
            "EMBEDDING_API_KEY": self._normalize_secret(payload.embedding_api_key),
            "EMBEDDING_BASE_URL": self._normalize_optional(payload.embedding_base_url) or "",
            "EMBEDDING_DIMENSION": str(payload.embedding_dimension),
            "VECTOR_STORE_TYPE": payload.vector_store_type,
            "VECTOR_STORE_PERSIST_DIR": payload.vector_store_persist_dir.strip() or "./data/vectorstore",
            "MILVUS_HOST": payload.milvus_host.strip() or "localhost",
            "MILVUS_PORT": str(payload.milvus_port),
            "MILVUS_COLLECTION": payload.milvus_collection.strip() or "yang_rag",
        }
        self._write_repo_env(updates)
        return self.get_settings()

    def _load_repo_env(self) -> Dict[str, str]:
        """Parse the repository .env file."""
        values: Dict[str, str] = {}
        if not self.env_path.exists():
            return values

        for line in self.env_path.read_text(encoding="utf-8").splitlines():
            stripped = line.strip()
            if not stripped or stripped.startswith("#") or "=" not in stripped:
                continue
            key, value = stripped.split("=", 1)
            values[key.strip()] = value.strip().strip('"').strip("'")
        return values

    def _write_repo_env(self, updates: Dict[str, str]) -> None:
        """Update the repository .env file while preserving unrelated lines."""
        existing_lines = []
        if self.env_path.exists():
            existing_lines = self.env_path.read_text(encoding="utf-8").splitlines()

        remaining = set(updates.keys())
        new_lines = []
        for line in existing_lines:
            stripped = line.strip()
            if not stripped or stripped.startswith("#") or "=" not in stripped:
                new_lines.append(line)
                continue

            key, _ = stripped.split("=", 1)
            normalized_key = key.strip()
            if normalized_key not in updates:
                new_lines.append(line)
                continue

            new_lines.append(f"{normalized_key}={self._serialize_env_value(updates[normalized_key])}")
            remaining.discard(normalized_key)

        for key in self._ordered_remaining_keys(remaining):
            if new_lines and new_lines[-1] != "":
                new_lines.append("")
            new_lines.append(f"{key}={self._serialize_env_value(updates[key])}")

        self.env_path.write_text("\n".join(new_lines).rstrip() + "\n", encoding="utf-8")

    def _ordered_remaining_keys(self, keys: Iterable[str]) -> Iterable[str]:
        """Yield remaining keys in a stable, human-readable order."""
        key_set = set(keys)
        for key in self.ENV_KEY_ORDER:
            if key in key_set:
                yield key
                key_set.remove(key)
        for key in sorted(key_set):
            yield key

    def _serialize_env_value(self, value: str) -> str:
        """Serialize a single environment value."""
        value = value.strip()
        if not value:
            return ""
        if any(char.isspace() for char in value):
            escaped = value.replace('"', '\\"')
            return f'"{escaped}"'
        return value

    def _normalize_optional(self, value: Optional[str]) -> Optional[str]:
        """Normalize optional string values."""
        if value is None:
            return None
        stripped = value.strip()
        return stripped or None

    def _normalize_secret(self, value: Optional[str]) -> str:
        """Clear known placeholder secrets so they do not persist as real credentials."""
        if self._is_placeholder_secret(value):
            return ""
        return (value or "").strip()

    def _is_placeholder_secret(self, value: Optional[str]) -> bool:
        """Return whether a secret still looks like a template placeholder."""
        normalized = (value or "").strip().lower()
        if not normalized:
            return False

        markers = (
            "sk-your-",
            "your-openai-api-key",
            "your-api-key",
            "sk-xxx",
            "your-siliconflow-key",
            "your-aliyun-key",
            "您的",
            "你的",
        )
        return any(marker in normalized for marker in markers)
