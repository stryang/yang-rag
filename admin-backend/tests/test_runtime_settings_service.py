"""Tests for admin runtime settings persistence."""

from src.runtime_settings.schemas import RuntimeSettingsUpdate
from src.runtime_settings.service import RuntimeSettingsService


def test_runtime_settings_service_persists_api_endpoint(tmp_path):
    """The shared API endpoint should round-trip through the repo .env file."""
    service = RuntimeSettingsService()
    service.env_path = tmp_path / ".env"

    payload = RuntimeSettingsUpdate(
        llm_provider="openai",
        llm_model="gpt-4o-mini",
        llm_api_key="",
        llm_base_url=None,
        llm_temperature=0.7,
        llm_max_tokens=2000,
        embedding_provider="openai",
        embedding_model="text-embedding-3-small",
        embedding_api_key="",
        embedding_base_url=None,
        embedding_dimension=1536,
        vector_store_type="chroma",
        vector_store_persist_dir="./data/vectorstore",
        milvus_host="localhost",
        milvus_port=19530,
        milvus_collection="yang_rag",
        api_endpoint="http://127.0.0.1:9000",
    )

    updated = service.update_settings(payload)

    assert updated.api_endpoint == "http://127.0.0.1:9000"
    assert "API_ENDPOINT=http://127.0.0.1:9000" in service.env_path.read_text(encoding="utf-8")
