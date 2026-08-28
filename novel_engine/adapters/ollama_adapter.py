"""Native Ollama Adapter for local LLM inference."""

import json
from typing import Callable, Optional, Type, TypeVar
import httpx
from pydantic import BaseModel
from novel_engine.adapters.base import BaseLLMAdapter

T = TypeVar("T", bound=BaseModel)


class OllamaAdapter(BaseLLMAdapter):
    """Direct, high-performance HTTP adapter for local Ollama server."""

    def __init__(
        self,
        model_name: str = "qwen2.5-coder:3b",
        base_url: str = "http://localhost:11434"
    ):
        super().__init__(model_name=model_name, base_url=base_url)
        self.api_chat_url = f"{base_url.rstrip('/')}/api/chat"

    async def generate_text(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096
    ) -> str:
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": self.model_name,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
                "num_ctx": 4096
            }
        }

        async with httpx.AsyncClient(timeout=httpx.Timeout(300.0, connect=30.0)) as client:
            res = await client.post(self.api_chat_url, json=payload)
            res.raise_for_status()
            data = res.json()
            return data.get("message", {}).get("content", "")

    async def stream_text(
        self,
        prompt: str,
        on_chunk: Callable[[str], None],
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096
    ) -> str:
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": self.model_name,
            "messages": messages,
            "stream": True,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
                "num_ctx": 4096
            }
        }

        full_text = []
        async with httpx.AsyncClient(timeout=120.0) as client:
            async with client.stream("POST", self.api_chat_url, json=payload) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if line:
                        chunk = json.loads(line)
                        content = chunk.get("message", {}).get("content", "")
                        if content:
                            full_text.append(content)
                            on_chunk(content)

        return "".join(full_text)

    async def generate_structured(
        self,
        prompt: str,
        response_model: Type[T],
        system_prompt: Optional[str] = None,
        temperature: float = 0.2
    ) -> T:
        schema_json = json.dumps(response_model.model_json_schema())
        system_directive = (
            (system_prompt + "\n\n" if system_prompt else "")
            + f"Output strictly a single JSON object matching this JSON schema:\n{schema_json}\nDo not include any explanation or extra text."
        )

        messages = [
            {"role": "system", "content": system_directive},
            {"role": "user", "content": prompt}
        ]

        payload = {
            "model": self.model_name,
            "messages": messages,
            "stream": False,
            "format": "json",
            "options": {
                "temperature": temperature,
                "num_ctx": 4096
            }
        }

        async with httpx.AsyncClient(timeout=httpx.Timeout(300.0, connect=30.0)) as client:
            res = await client.post(self.api_chat_url, json=payload)
            res.raise_for_status()
            data = res.json()
            raw_output = data.get("message", {}).get("content", "")

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
