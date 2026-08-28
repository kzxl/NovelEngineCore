"""Base Abstract LLM Adapter."""

from abc import ABC, abstractmethod
from typing import Any, Callable, Dict, List, Optional, Type, TypeVar
from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)


class BaseLLMAdapter(ABC):
    def __init__(self, model_name: str, api_key: Optional[str] = None, base_url: Optional[str] = None):
        self.model_name = model_name
        self.api_key = api_key
        self.base_url = base_url

    @abstractmethod
    async def generate_text(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096
    ) -> str:
        """Generates raw text response."""
        pass

    @abstractmethod
    async def stream_text(
        self,
        prompt: str,
        on_chunk: Callable[[str], None],
        system_prompt: Optional[str] = None,
        temperature: float = 0.7
    ) -> str:
        """Streams text chunks in real time."""
        pass

    @abstractmethod
    async def generate_structured(
        self,
        prompt: str,
        response_model: Type[T],
        system_prompt: Optional[str] = None,
        temperature: float = 0.2
    ) -> T:
        """Generates structured output validated against a Pydantic model."""
        pass
