"""Core module initialization."""

from .config import settings, get_settings, Settings
from .prompts import (
    RAG_SYSTEM_PROMPT,
    RAG_HUMAN_TEMPLATE,
    CODE_AGENT_SYSTEM_PROMPT,
    get_rag_prompt,
    get_code_agent_prompt,
    get_langchain_rag_prompt,
    format_context,
)

__all__ = [
    "settings",
    "get_settings",
    "Settings",
    "RAG_SYSTEM_PROMPT",
    "RAG_HUMAN_TEMPLATE",
    "CODE_AGENT_SYSTEM_PROMPT",
    "get_rag_prompt",
    "get_code_agent_prompt",
    "get_langchain_rag_prompt",
    "format_context",
]
