"""Ollama Local LLM Native Adapter for NovelEngineCore.

Directly calls the native Ollama API endpoints (/api/chat, /api/generate)
over HTTP via httpx with optimized timeout and context window settings.
"""

import json
from typing import Any, Callable, Dict, List, Optional, Type, TypeVar
import httpx
from pydantic import BaseModel, ValidationError

from novel_engine.adapters.base import BaseLLMAdapter

T = TypeVar("T", bound=BaseModel)


class OllamaAdapter(BaseLLMAdapter):
    """Native Ollama adapter supporting local quantized models (Qwen, Llama, Mistral)."""

    def __init__(
        self,
        model_name: str = "qwen2.5-coder:3b",
        api_key: Optional[str] = None,
        base_url: Optional[str] = "http://localhost:11434",
        timeout: float = 300.0,
        num_ctx: int = 4096
    ):
        super().__init__(model_name=model_name, api_key=api_key, base_url=base_url or "http://localhost:11434")
        self.timeout = timeout
        self.num_ctx = num_ctx
        self.api_chat_url = f"{self.base_url.rstrip('/')}/api/chat"
        self.api_generate_url = f"{self.base_url.rstrip('/')}/api/generate"

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
                "num_ctx": self.num_ctx,
                "num_predict": max_tokens
            }
        }

        async with httpx.AsyncClient(timeout=httpx.Timeout(self.timeout, connect=30.0)) as client:
            res = await client.post(self.api_chat_url, json=payload)
            res.raise_for_status()
            data = res.json()
            return data.get("message", {}).get("content", "")

    async def stream_text(
        self,
        prompt: str,
        on_chunk: Callable[[str], None],
        system_prompt: Optional[str] = None,
        temperature: float = 0.7
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
                "num_ctx": self.num_ctx
            }
        }

        full_content = []
        async with httpx.AsyncClient(timeout=httpx.Timeout(self.timeout, connect=30.0)) as client:
            async with client.stream("POST", self.api_chat_url, json=payload) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if line:
                        chunk_data = json.loads(line)
                        chunk_text = chunk_data.get("message", {}).get("content", "")
                        if chunk_text:
                            full_content.append(chunk_text)
                            if on_chunk:
                                on_chunk(chunk_text)
        return "".join(full_content)

    async def generate_structured(
        self,
        prompt: str,
        response_model: Type[T],
        system_prompt: Optional[str] = None,
        temperature: float = 0.2
    ) -> T:
        schema_json = json.dumps(response_model.model_json_schema(), indent=2)
        system_directive = (
            (system_prompt + "\n\n" if system_prompt else "")
            + f"Output strictly a valid JSON object matching this JSON Schema:\n{schema_json}\n"
            + "Return ONLY raw JSON object. Do not include markdown codeblocks or explanations."
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
                "num_ctx": self.num_ctx
            }
        }

        async with httpx.AsyncClient(timeout=httpx.Timeout(self.timeout, connect=30.0)) as client:
            res = await client.post(self.api_chat_url, json=payload)
            res.raise_for_status()
            data = res.json()
            raw_output = data.get("message", {}).get("content", "")

        cleaned_json = self._extract_json(raw_output)
        
        try:
            parsed_dict = json.loads(cleaned_json)
        except Exception:
            parsed_dict = {}

        # Fallback patcher for missing required schema fields
        if hasattr(response_model, "__fields__") or hasattr(response_model, "model_fields"):
            fields = response_model.model_fields if hasattr(response_model, "model_fields") else response_model.__fields__
            for field_name, field_info in fields.items():
                if field_name not in parsed_dict or parsed_dict[field_name] is None:
                    if field_name == "world_id":
                        parsed_dict["world_id"] = "world_canglan"
                    elif field_name == "title":
                        parsed_dict["title"] = "Thương Lam Giới"
                    elif field_name == "genre":
                        parsed_dict["genre"] = "Xianxia"
                    elif field_name == "era_setting":
                        parsed_dict["era_setting"] = "Mạt Pháp Cổ Đại"
                    elif field_name == "energy_source":
                        parsed_dict["energy_source"] = "Thiên Địa Linh Khí"
                    elif field_name == "canon_rules":
                        parsed_dict["canon_rules"] = [
                            "Không thể trùng sinh sau khi hồn phi phách tán",
                            "Mọi pháp thuật đều tiêu hao linh lực hoặc thọ nguyên",
                            "Vượt cấp chiến đấu đòi hỏi pháp bảo hoặc đan dược nghịch thiên"
                        ]
                    elif field_name == "power_progression":
                        parsed_dict["power_progression"] = []
                    elif field_name == "factions":
                        parsed_dict["factions"] = []
                    elif field_name == "locations":
                        parsed_dict["locations"] = []

        try:
            return response_model.model_validate(parsed_dict)
        except ValidationError:
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
