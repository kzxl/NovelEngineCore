"""LiteLLM Adapter supporting OpenAI, Anthropic, Gemini, DeepSeek, OpenRouter, and Ollama."""

import json
from typing import Callable, Optional, Type, TypeVar
from pydantic import BaseModel
from novel_engine.adapters.base import BaseLLMAdapter

T = TypeVar("T", bound=BaseModel)


class LiteLLMAdapter(BaseLLMAdapter):
    def __init__(self, model_name: str = "gpt-4o", api_key: Optional[str] = None, base_url: Optional[str] = None):
        super().__init__(model_name, api_key, base_url)
        # Import dynamically to allow optional litellm installation
        try:
            import litellm
            self.litellm = litellm
            if api_key:
                litellm.api_key = api_key
            if base_url:
                litellm.api_base = base_url
        except ImportError:
            self.litellm = None

    def _ensure_litellm(self):
        if self.litellm is None:
            raise ImportError("litellm is not installed. Please install via 'pip install litellm'.")

    async def generate_text(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096
    ) -> str:
        self._ensure_litellm()
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        response = await self.litellm.acompletion(
            model=self.model_name,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens
        )
        return response.choices[0].message.content

    async def stream_text(
        self,
        prompt: str,
        on_chunk: Callable[[str], None],
        system_prompt: Optional[str] = None,
        temperature: float = 0.7
    ) -> str:
        self._ensure_litellm()
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        response = await self.litellm.acompletion(
            model=self.model_name,
            messages=messages,
            temperature=temperature,
            stream=True
        )

        full_content = []
        async for chunk in response:
            delta = chunk.choices[0].delta.content or ""
            if delta:
                full_content.append(delta)
                on_chunk(delta)

        return "".join(full_content)

    async def generate_structured(
        self,
        prompt: str,
        response_model: Type[T],
        system_prompt: Optional[str] = None,
        temperature: float = 0.2
    ) -> T:
        self._ensure_litellm()
        schema_json = json.dumps(response_model.model_json_schema())
        system_directive = (
            (system_prompt + "\n\n" if system_prompt else "")
            + f"Output strictly valid JSON matching this schema:\n{schema_json}"
        )

        raw_output = await self.generate_text(
            prompt=prompt,
            system_prompt=system_directive,
            temperature=temperature
        )

        # Self-healing JSON extraction
        cleaned_json = self._extract_json(raw_output)
        return response_model.model_validate_json(cleaned_json)

    def _extract_json(self, text: str) -> str:
        text = text.strip()
        if text.startswith("```"):
            lines = text.splitlines()
            if lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].startswith("```"):
                lines = lines[:-1]
            text = "\n".join(lines).strip()
        first_brace = text.find("{")
        last_brace = text.rfind("}")
        if first_brace != -1 and last_brace != -1:
            return text[first_brace:last_brace + 1]
        return text
