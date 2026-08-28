"""Ollama Local LLM Native Adapter for NovelEngineCore.

Directly calls the native Ollama API endpoints (/api/chat, /api/generate)
over HTTP via httpx with resilient JSON parsing, schema sanitization, and fallback patchers.
"""

import json
import re
from typing import Any, Callable, Dict, List, Optional, Type, TypeVar
import httpx
from pydantic import BaseModel, ValidationError

from novel_engine.adapters.base import BaseLLMAdapter
from novel_engine.core.state import (
    WorldBible,
    PowerTier,
    Faction,
    Location,
    CharacterDossier,
    CharacterRole,
    PersonalityTraits,
    SpeechStyle,
    CharacterStatus,
    InventoryItem,
    GeneratedCharacterList,
    WorldExpansionResult,
    UnifiedSceneResponse
)
from novel_engine.core.plot_events import PlotEvent, GeneratedEventList, EventSeverity

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
        temperature: float = 0.3
    ) -> T:
        compact_schema = self._get_compact_schema_instruction(response_model)
        system_directive = (
            (system_prompt + "\n\n" if system_prompt else "")
            + f"Output strictly a valid JSON object matching this structure:\n{compact_schema}\n"
            + "Return ONLY the raw JSON object. Do not include markdown codeblocks or explanations."
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

        parsed_json = self._parse_json_lenient(raw_output)

        # Apply Model-Specific Resilient Sanitizers
        if response_model == GeneratedCharacterList:
            return self._sanitize_characters(parsed_json)  # type: ignore
        elif response_model == GeneratedEventList:
            return self._sanitize_events(parsed_json)  # type: ignore
        elif response_model == WorldBible:
            return self._sanitize_world_bible(parsed_json)  # type: ignore
        elif response_model == WorldExpansionResult:
            return self._sanitize_world_expansion(parsed_json)  # type: ignore
        elif response_model == UnifiedSceneResponse:
            return self._sanitize_unified_scene(parsed_json, raw_output)  # type: ignore

        # General Pydantic validation
        try:
            return response_model.model_validate(parsed_json)
        except Exception:
            return response_model.model_validate({})

    def _get_compact_schema_instruction(self, model: Type[Any]) -> str:
        if model == UnifiedSceneResponse:
            return '{\n  "scene_title": "Tên hồi/phân cảnh",\n  "prose_content": "Toàn bộ bài văn xuôi của chương truyện...",\n  "key_events": ["Sự kiện 1", "Sự kiện 2"],\n  "discovered_items": ["Vân Hà Ngọc Bội"],\n  "discovered_locations": ["Hội Nghị Đường"],\n  "discovered_secrets": ["Bí mật chiếc nhẫn"],\n  "hp_change": 0,\n  "reputation_change": 10,\n  "luck_change": 5,\n  "ending_cliffhanger": "Nút thắt kết cảnh",\n  "next_fate_choices": [\n    {"title": "Hướng 1: Liều mạng phá vây", "description": "Tấn công bất ngờ để mở đường máu"},\n    {"title": "Hướng 2: Nhẫn nhịn hoãn binh", "description": "Giao nộp linh thạch tìm cơ hội khác"},\n    {"title": "Hướng 3: Chạy vào cấm địa", "description": "Tìm kiếm cơ duyên thượng cổ"}\n  ]\n}'
        elif model == GeneratedCharacterList:
            return '{\n  "characters": [\n    {\n      "character_id": "char_id",\n      "name": "Tên",\n      "role": "Protagonist/Antagonist/Mentor/Sidekick",\n      "visual_tags": ["tag1", "tag2"],\n      "personality": {\n        "core_motivation": "Động cơ",\n        "fatal_flaw": "Điểm yếu",\n        "moral_boundary": "Ranh giới đạo đức",\n        "hidden_secret": "Bí mật"\n      },\n      "status": {\n        "power_tier": "Luyện Khí Tầng 1",\n        "health_condition": "Khỏe mạnh",\n        "mental_state": "Bình tĩnh"\n      }\n    }\n  ]\n}'
        elif model == GeneratedEventList:
            return '{\n  "events": [\n    {\n      "event_id": "evt_1",\n      "title": "Tên biến cố",\n      "severity": "Tiểu Biến Cố / Đại Sự Kiện / Thiên Địa Dị Biến",\n      "category": "Tông Môn Tranh Đấu",\n      "trigger_cause": "Nguyên nhân",\n      "involved_characters": ["char_1"],\n      "location": "Địa danh",\n      "impact_summary": "Tác động",\n      "suggested_scene_goal": "Mục tiêu cảnh",\n      "suggested_conflict": "Xung đột chính",\n      "suggested_cliffhanger": "Nút thắt kết cảnh"\n    }\n  ]\n}'
        elif model == WorldBible:
            return '{\n  "world_id": "world_1",\n  "title": "Tên thế giới",\n  "genre": "Xianxia",\n  "era_setting": "Mạt Pháp Cổ Đại",\n  "energy_source": "Thiên Địa Linh Khí",\n  "canon_rules": ["Luật 1", "Luật 2"],\n  "factions": [{"name": "Phái A", "alignment": "Chính Đạo", "core_doctrine": "Tu tâm"}],\n  "locations": [{"name": "Địa Danh A", "climate_and_vibe": "U ám", "key_hazards": "Yêu thú"}]\n}'
        elif model == WorldExpansionResult:
            return '{\n  "new_factions": [{"name": "Tông Môn Mới", "alignment": "Trung Lập", "core_doctrine": "Bảo vệ cấm địa"}],\n  "new_locations": [{"name": "Cấm Địa Mới", "climate_and_vibe": "Sương mù", "key_hazards": "Cạm bẫy cổ xưa"}],\n  "new_canon_rules": ["Luật bổ sung"]\n}'
        return "{}"

    def _parse_json_lenient(self, text: str) -> Any:
        text = text.strip()
        if text.startswith("```"):
            lines = text.splitlines()
            if lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].startswith("```"):
                lines = lines[:-1]
            text = "\n".join(lines).strip()

        # Find object or array boundaries
        obj_start = text.find("{")
        obj_end = text.rfind("}")
        arr_start = text.find("[")
        arr_end = text.rfind("]")

        clean_str = text
        if obj_start != -1 and obj_end != -1 and (arr_start == -1 or obj_start < arr_start):
            clean_str = text[obj_start:obj_end + 1]
        elif arr_start != -1 and arr_end != -1:
            clean_str = text[arr_start:arr_end + 1]

        # Fix python-style constants
        clean_str = clean_str.replace(": True", ": true").replace(": False", ": false").replace(": None", ": null")
        clean_str = re.sub(r",\s*([\]}])", r"\1", clean_str)  # Remove trailing commas

        try:
            return json.loads(clean_str)
        except Exception:
            return {}

    def _sanitize_characters(self, data: Any) -> GeneratedCharacterList:
        raw_list = []
        if isinstance(data, dict):
            raw_list = data.get("characters", [])
            if not raw_list and "name" in data:
                raw_list = [data]
        elif isinstance(data, list):
            raw_list = data

        cleaned_chars: List[CharacterDossier] = []
        for idx, item in enumerate(raw_list):
            if not isinstance(item, dict):
                continue
            name = item.get("name") or f"Nhân Vật {idx + 1}"
            char_id = item.get("character_id") or f"char_{name.lower().replace(' ', '_')}"
            
            # Map role cleanly
            raw_role = str(item.get("role", "")).lower()
            role = CharacterRole.NPC
            if any(k in raw_role for k in ["protagonist", "main", "chính", "nam chính", "nữ chính"]):
                role = CharacterRole.PROTAGONIST
            elif any(k in raw_role for k in ["antagonist", "villain", "phản diện", "kẻ thù", "trưởng lão", "đối thủ"]):
                role = CharacterRole.ANTAGONIST
            elif any(k in raw_role for k in ["mentor", "sư phụ", "tiền bối", "thầy"]):
                role = CharacterRole.MENTOR
            elif any(k in raw_role for k in ["sidekick", "bạn", "muội muội", "đệ tử"]):
                role = CharacterRole.SIDEKICK

            # Parse Personality
            pers = item.get("personality", {})
            if isinstance(pers, str):
                pers = {"core_motivation": pers, "fatal_flaw": "Cố chấp", "moral_boundary": "Bảo vệ người thân"}
            p_obj = PersonalityTraits(
                core_motivation=pers.get("core_motivation") or "Tu luyện cầu trường sinh",
                fatal_flaw=pers.get("fatal_flaw") or "Kiêu ngạo hoặc cố chấp",
                moral_boundary=pers.get("moral_boundary") or "Không hại kẻ vô tội",
                hidden_secret=pers.get("hidden_secret") or "Ẩn giấu thân thế bí ẩn"
            )

            # Parse Status
            st = item.get("status", {})
            if isinstance(st, str):
                st = {"power_tier": st, "health_condition": "Khỏe mạnh", "mental_state": "Bình tĩnh"}
            st_obj = CharacterStatus(
                power_tier=st.get("power_tier") or "Luyện Khí Tầng 1",
                health_condition=st.get("health_condition") or "Khỏe mạnh",
                mental_state=st.get("mental_state") or "Bình tĩnh"
            )

            visual_tags = item.get("visual_tags", [])
            if isinstance(visual_tags, str):
                visual_tags = [t.strip() for t in visual_tags.split(",")]

            cleaned_chars.append(
                CharacterDossier(
                    character_id=char_id,
                    name=name,
                    role=role,
                    visual_tags=visual_tags or ["tu sĩ", "áo dài cổ trang"],
                    personality=p_obj,
                    status=st_obj
                )
            )

        if not cleaned_chars:
            cleaned_chars = [
                CharacterDossier(
                    character_id="char_protagonist",
                    name="Lâm Phong",
                    role=CharacterRole.PROTAGONIST,
                    visual_tags=["thiếu niên tu sĩ", "thanh y", "ánh mắt kiên định"],
                    personality=PersonalityTraits(core_motivation="Đột phá cảnh giới báo thù", fatal_flaw="Cố chấp", moral_boundary="Bảo vệ gia đình"),
                    status=CharacterStatus(power_tier="Luyện Khí Tầng 3")
                ),
                CharacterDossier(
                    character_id="char_antagonist",
                    name="Triệu Vô Cực",
                    role=CharacterRole.ANTAGONIST,
                    visual_tags=["lão giả nham hiểm", "hắc bào", "khí tức sắc bén"],
                    personality=PersonalityTraits(core_motivation="Đoạt bảo vật gia tộc", fatal_flaw="Tham lam tàn nhẫn", moral_boundary="Không từ thủ đoạn"),
                    status=CharacterStatus(power_tier="Luyện Khí Tầng 9")
                )
            ]

        return GeneratedCharacterList(characters=cleaned_chars)

    def _sanitize_events(self, data: Any) -> GeneratedEventList:
        raw_list = []
        if isinstance(data, dict):
            raw_list = data.get("events", [])
            if not raw_list and "title" in data:
                raw_list = [data]
        elif isinstance(data, list):
            raw_list = data

        cleaned_events: List[PlotEvent] = []
        for idx, item in enumerate(raw_list):
            if not isinstance(item, dict):
                continue
            title = item.get("title") or f"Biến Cố Cốt Truyện #{idx + 1}"
            event_id = item.get("event_id") or f"evt_{idx + 1}"
            
            raw_sev = str(item.get("severity", "")).lower()
            severity = EventSeverity.MAJOR
            if "tiểu" in raw_sev or "minor" in raw_sev:
                severity = EventSeverity.MINOR
            elif "đại họa" in raw_sev or "calamity" in raw_sev or "dị biến" in raw_sev:
                severity = EventSeverity.CALAMITY

            inv_chars = item.get("involved_characters", [])
            if isinstance(inv_chars, str):
                inv_chars = [c.strip() for c in inv_chars.split(",")]

            cleaned_events.append(
                PlotEvent(
                    event_id=event_id,
                    title=title,
                    severity=severity,
                    category=item.get("category") or "Tranh Đoạt Tài Nguyên",
                    trigger_cause=item.get("trigger_cause") or "Ân oán môn phái và sự xuất thế của bảo vật.",
                    involved_characters=inv_chars or ["char_protagonist"],
                    location=item.get("location") or "Hội Nghị Đường",
                    impact_summary=item.get("impact_summary") or "Thế cục đảo lộn, buộc nhân vật phải hành động khẩn cấp.",
                    suggested_scene_goal=item.get("suggested_scene_goal") or "Đối đầu trực diện để giải vây và thu hồi bảo vật.",
                    suggested_conflict=item.get("suggested_conflict") or "Kẻ thù dùng uy áp để ép giá và khiêu khích.",
                    suggested_cliffhanger=item.get("suggested_cliffhanger") or "Một thế lực bí ẩn khác xuất hiện phong tỏa toàn trường."
                )
            )

        if not cleaned_events:
            cleaned_events = [
                PlotEvent(
                    event_id="evt_1",
                    title="⚔️ Đại Trưởng Lão Phong Tỏa Tông Môn",
                    severity=EventSeverity.MAJOR,
                    category="Gia Tộc Tranh Đấu",
                    trigger_cause="Trưởng lão muốn cưỡng đoạt ngọc bội tổ truyền.",
                    involved_characters=["char_protagonist", "char_antagonist"],
                    location="Hội Nghị Đường",
                    impact_summary="Nhân vật chính bị dồn vào đường cùng phải dằn mặt kẻ thù.",
                    suggested_scene_goal="Ném đủ linh thạch chuộc lại bảo vật và giải vây.",
                    suggested_conflict="Kẻ địch ép giá gấp đôi nhằm làm nhục trước mặt đệ tử.",
                    suggested_cliffhanger="Nhận ra dao động cổ xưa từ chiếc nhẫn và hạ lệnh vây bắt."
                )
            ]

        return GeneratedEventList(events=cleaned_events)

    def _sanitize_world_bible(self, data: Any) -> WorldBible:
        if not isinstance(data, dict):
            data = {}
        
        rules = data.get("canon_rules", [])
        if not rules or not isinstance(rules, list):
            rules = [
                "Không thể trùng sinh sau khi hồn phi phách tán",
                "Mọi pháp thuật đều tiêu hao linh lực hoặc thọ nguyên",
                "Vượt cấp chiến đấu đòi hỏi pháp bảo hoặc đan dược nghịch thiên"
            ]

        factions = []
        for idx, fac in enumerate(data.get("factions", [])):
            if isinstance(fac, dict) and "name" in fac:
                f_name = fac["name"]
                f_id = fac.get("faction_id") or f"fac_{idx + 1}"
                factions.append(Faction(faction_id=f_id, name=f_name, alignment=fac.get("alignment", "Chính Đạo"), core_doctrine=fac.get("core_doctrine", "Tu tâm cầu đạo")))
        if not factions:
            factions = [Faction(faction_id="fac_1", name="Thương Lam Tông", alignment="Chính Đạo", core_doctrine="Lấy kiếm nhập đạo, diệt trừ ma tu")]

        locations = []
        for idx, loc in enumerate(data.get("locations", [])):
            if isinstance(loc, dict) and "name" in loc:
                l_name = loc["name"]
                l_id = loc.get("location_id") or f"loc_{idx + 1}"
                locations.append(Location(location_id=l_id, name=l_name, climate_and_vibe=loc.get("climate_and_vibe", "Hùng vĩ, mây mù"), key_hazards=loc.get("key_hazards", "Cấm chế cổ xưa")))
        if not locations:
            locations = [Location(location_id="loc_1", name="Thương Lam Sơn Mạch - Hội Nghị Điện", climate_and_vibe="Hùng vĩ, linh khí dồi dào", key_hazards="Trận pháp hộ sơn")]

        tiers = [
            PowerTier(rank=1, name="Luyện Khí Kỳ", description="Hấp thu linh khí sơ khai", hard_limits="Chưa thể ngự kiếm phi hành"),
            PowerTier(rank=2, name="Trúc Cơ Kỳ", description="Ngưng tụ linh dịch", hard_limits="Thọ nguyên 200 năm"),
            PowerTier(rank=3, name="Kim Đan Kỳ", description="Kết thành Kim đan bất hoại", hard_limits="Thọ nguyên 500 năm")
        ]

        return WorldBible(
            world_id=data.get("world_id") or "world_canglan",
            title=data.get("title") or "Thương Lam Giới",
            genre=data.get("genre") or "Xianxia",
            era_setting=data.get("era_setting") or "Mạt Pháp Cổ Đại",
            energy_source=data.get("energy_source") or "Thiên Địa Linh Khí",
            origin_myth=data.get("origin_myth") or "Khai thiên lập địa từ hỗn mang",
            canon_rules=rules,
            power_progression=tiers,
            factions=factions,
            locations=locations
        )

    def _sanitize_world_expansion(self, data: Any) -> WorldExpansionResult:
        if not isinstance(data, dict):
            data = {}

        new_factions = []
        for idx, fac in enumerate(data.get("new_factions", [])):
            if isinstance(fac, dict) and "name" in fac:
                f_id = fac.get("faction_id") or f"fac_new_{idx + 1}"
                new_factions.append(Faction(faction_id=f_id, name=fac["name"], alignment=fac.get("alignment", "Trung Lập"), core_doctrine=fac.get("core_doctrine", "Bảo hộ cấm địa")))
        
        new_locations = []
        for idx, loc in enumerate(data.get("new_locations", [])):
            if isinstance(loc, dict) and "name" in loc:
                l_id = loc.get("location_id") or f"loc_new_{idx + 1}"
                new_locations.append(Location(location_id=l_id, name=loc["name"], climate_and_vibe=loc.get("climate_and_vibe", "Hiểm trở, u tối"), key_hazards=loc.get("key_hazards", "Yêu thú thượng cổ")))

        new_rules = data.get("new_canon_rules", [])
        if not isinstance(new_rules, list):
            new_rules = ["Cấm địa phong tỏa, người ngoài không thể tự do xuất nhập"]

        return WorldExpansionResult(
            new_factions=new_factions or [Faction(faction_id="fac_mo_mon", name="Hắc Ma Môn", alignment="Ma Đạo", core_doctrine="Huyết tế cầu lực lượng")],
            new_locations=new_locations or [Location(location_id="loc_van_ma", name="Vạn Ma Cổ Mộ", climate_and_vibe="Âm u, tử khí nồng nặc", key_hazards="Ma chướng và tàn hồn")],
            new_canon_rules=new_rules or ["Kẻ bước vào cấm địa bị áp chế một nửa tu vi"]
        )

    def _sanitize_unified_scene(self, data: Any, raw_text: str) -> UnifiedSceneResponse:
        """Sanitizes single-pass unified scene drafting output."""
        if not isinstance(data, dict):
            # Fallback if raw markdown was returned
            prose = raw_text.strip()
            return UnifiedSceneResponse(
                scene_title="Phân Cảnh Mới",
                prose_content=prose,
                key_events=["Nhân vật đối mặt với tình huống căng thẳng."],
                discovered_items=[],
                discovered_locations=[],
                discovered_secrets=[],
                hp_change=0,
                reputation_change=10,
                luck_change=5,
                ending_cliffhanger="Cục diện còn nhiều bí ẩn chưa được làm sáng tỏ.",
                next_fate_choices=[
                    {"title": "Lựa chọn 1: Tiếp tục điều tra bí ẩn", "description": "Lần theo các manh mối còn sót lại"},
                    {"title": "Lựa chọn 2: Tạm lánh để đột phá tu vi", "description": "Tìm kiếm nơi yên tĩnh để củng cố thực lực"},
                    {"title": "Lựa chọn 3: Tìm kiếm đồng minh mới", "description": "Kết giao với thế lực trung lập"}
                ]
            )

        prose = str(data.get("prose_content") or data.get("content") or data.get("draft") or raw_text).strip()
        title = str(data.get("scene_title") or "Phân Cảnh").strip()

        key_events = data.get("key_events", [])
        if isinstance(key_events, str):
            key_events = [key_events]

        items = data.get("discovered_items", [])
        if isinstance(items, str):
            items = [items]

        locations = data.get("discovered_locations", [])
        if isinstance(locations, str):
            locations = [locations]

        secrets = data.get("discovered_secrets", [])
        if isinstance(secrets, str):
            secrets = [secrets]

        choices = data.get("next_fate_choices", [])
        if not isinstance(choices, list) or not choices:
            choices = [
                {"title": "Lựa chọn 1: Liều mình phá vây", "description": "Tấn công bất ngờ để mở đường máu"},
                {"title": "Lựa chọn 2: Nhẫn nhịn hoãn binh", "description": "Giao nộp linh thạch tìm cơ hội khác"},
                {"title": "Lựa chọn 3: Chạy vào cấm địa", "description": "Tìm kiếm cơ duyên thượng cổ"}
            ]

        return UnifiedSceneResponse(
            scene_title=title,
            prose_content=prose,
            key_events=key_events,
            discovered_items=items,
            discovered_locations=locations,
            discovered_secrets=secrets,
            hp_change=int(data.get("hp_change", 0)),
            reputation_change=int(data.get("reputation_change", 10)),
            luck_change=int(data.get("luck_change", 5)),
            ending_cliffhanger=str(data.get("ending_cliffhanger") or "").strip(),
            next_fate_choices=choices
        )
