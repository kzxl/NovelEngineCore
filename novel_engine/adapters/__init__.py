"""LLM Adapter package."""
from novel_engine.adapters.base import BaseLLMAdapter
from novel_engine.adapters.mock_adapter import MockLLMAdapter

__all__ = ["BaseLLMAdapter", "MockLLMAdapter"]
