"""Main module initialization."""

# 只导出配置，延迟加载其他模块
from .core.config import settings, get_settings

__all__ = [
    "settings",
    "get_settings",
]
