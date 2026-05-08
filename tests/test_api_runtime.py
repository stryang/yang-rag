"""API runtime regression tests."""

import pytest

from src.api import main as api_main


@pytest.mark.asyncio
async def test_chat_completions_uses_runtime_llm_settings(monkeypatch):
    """Plain chat completions should honor the unified runtime LLM settings."""
    captured = {}

    class FakeChatOpenAI:
        def __init__(self, **kwargs):
            captured.update(kwargs)

        def invoke(self, messages):
            class Response:
                content = "unit-test-answer"

            captured["messages"] = messages
            return Response()

    monkeypatch.setattr("langchain_openai.ChatOpenAI", FakeChatOpenAI)
    monkeypatch.setattr(api_main.settings, "llm_model", "test-llm-model")
    monkeypatch.setattr(api_main.settings, "llm_api_key", "test-llm-key")
    monkeypatch.setattr(api_main.settings, "llm_base_url", "https://example.test/v1")

    response = await api_main.chat_completions(
        api_main.ChatRequest(
            messages=[api_main.ChatMessage(role="user", content="你好")],
            stream=False,
        ),
        _api_key=api_main.settings.api_key,
    )

    assert captured["model"] == "test-llm-model"
    assert captured["api_key"] == "test-llm-key"
    assert captured["base_url"] == "https://example.test/v1"
    assert response["model"] == "test-llm-model"
    assert response["choices"][0]["message"]["content"] == "unit-test-answer"
