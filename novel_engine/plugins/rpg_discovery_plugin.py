"""RPGDiscoveryPlugin - Game & Discovery Galaxy Star.

Maintains the World Discovery Codex, actively extracts real loot/locations/secrets
from the drafted prose using LLM structured analysis, updates character RPG stats,
and proposes contextually accurate Fate Choices for the next chapter.
"""

import json
import time
import os
from typing import Dict, List, Optional
from pydantic import BaseModel, Field

from novel_engine.plugins.base import INovelPlugin
from novel_engine.core.event_bus import EventBus
from novel_engine.adapters.base import BaseLLMAdapter
from novel_engine.core.state import StoryState, SceneDraft
from novel_engine.core.game_engine import (
    DiscoveryCodex,
    DiscoveryEntry,
    DiscoveryType,
    FateChoice,
    RPGStats
)


class ExtractedDiscoveryItem(BaseModel):
    discovery_type: DiscoveryType
    title: str
    description: str


class ExtractedStatUpdate(BaseModel):
    character_id: str
    hp_loss_or_gain: int = 0  # e.g. -15 if wounded, +10 if healed
    reputation_gain: int = 5
    luck_gain: int = 5
    power_tier_update: Optional[str] = None


class SceneRPGExtractionResult(BaseModel):
    discoveries: List[ExtractedDiscoveryItem] = Field(default_factory=list)
    stat_updates: List[ExtractedStatUpdate] = Field(default_factory=list)
    next_fate_choices: List[FateChoice] = Field(default_factory=list)


class RPGDiscoveryPlugin(INovelPlugin):
    def __init__(self, output_dir: str = "output/stories"):
        self.output_dir = output_dir
        self.codex: Optional[DiscoveryCodex] = None
        self._event_bus: Optional[EventBus] = None
        self._adapter: Optional[BaseLLMAdapter] = None

    @property
    def plugin_name(self) -> str:
        return "RPGDiscoveryPlugin"

    @property
    def galaxy(self) -> str:
        return "Game & RPG"

    def initialize(self, event_bus: EventBus, adapter: BaseLLMAdapter):
        self._event_bus = event_bus
        self._adapter = adapter

    async def on_story_initialized(self, state: StoryState):
        """Initializes starter RPG stats dynamically based on world characters."""
        starter_stats = {}
        for char_id, char in state.characters.items():
            starter_stats[char_id] = RPGStats(
                level=char.status.power_tier or "Luyện Khí Tầng 1",
                hp_percent=100 if char.status.health_condition == "Khỏe mạnh" else 75,
                luck_score=80 if char.role.value == "Protagonist" else 50,
                reputation=20 if char.role.value == "Protagonist" else 50,
                faction_alignment=state.world_bible.factions[0].name if state.world_bible.factions else "Vô Môn Phái"
            )

        self.codex = DiscoveryCodex(
            story_id=state.story_id,
            total_discoveries=1,
            entries=[
                DiscoveryEntry(
                    id="disc_genesis",
                    discovery_type=DiscoveryType.NEW_LOCATION,
                    title=f"Địa Danh Khởi Đầu: {state.world_bible.locations[0].name if state.world_bible.locations else 'Tân Thủ Thôn'}",
                    description=f"Điểm khởi nguồn hành trình tu luyện trong thế giới {state.world_bible.title}.",
                    discovered_in_scene="Mở Đầu Cốt Truyện",
                    discovered_by=next(iter(state.characters.keys()), "char_main")
                )
            ],
            rpg_character_stats=starter_stats,
            active_fate_options=[
                FateChoice(
                    choice_id="fate_1",
                    title="⚔️ Hướng 1: Trực diện đối đầu, chớp thời cơ phản kích",
                    description="Khai triển toàn bộ thực lực để áp chế đối phương ngay lập tức.",
                    risk_reward="Rủi ro trung bình, tạo tiếng vang lớn nhưng tiêu hao linh lực.",
                    character_trait_impact="+15 Quyết Đoán, +20 Danh Tiếng"
                ),
                FateChoice(
                    choice_id="fate_2",
                    title="🕊️ Hướng 2: Nhẫn nhịn quan sát, tìm kiếm sơ hở",
                    description="Tạm thời lùi bước, bảo toàn thực lực và điều tra hành tung đối thủ.",
                    risk_reward="An toàn cao, thu thập được nhiều thông tin quan trọng.",
                    character_trait_impact="+15 Tâm Cơ, +10 Phòng Thủ"
                ),
                FateChoice(
                    choice_id="fate_3",
                    title="🗺️ Hướng 3: Tìm đường rút lui, khai phá cấm địa mới",
                    description="Chuyển hướng hành động sang khu vực bí mật để tìm kiếm cơ duyên.",
                    risk_reward="Mở khóa bản đồ mới, cơ hội nhặt kỳ ngộ cổ đại.",
                    character_trait_impact="+30 Điểm Khám Phá, Kích Hoạt Bản Đồ Mới"
                )
            ]
        )

    async def post_scene_draft(self, state: StoryState, draft: SceneDraft) -> SceneDraft:
        """Actively extracts real in-story discoveries & stats from the drafted prose."""
        if not self.codex:
            await self.on_story_initialized(state)

        pov_char_id = draft.contract.pov_character_id

        # 1. Check if unified_data was already generated in single-pass
        if draft.unified_data:
            # Direct instant extraction without extra LLM call
            u = draft.unified_data
            for item in u.discovered_items:
                self.codex.entries.append(
                    DiscoveryEntry(
                        id=f"disc_{int(time.time())}_{len(self.codex.entries)}",
                        discovery_type=DiscoveryType.ITEM_LOOT,
                        title=item,
                        description=f"Vật phẩm xuất hiện trong phân cảnh {draft.scene_id}",
                        discovered_in_scene=draft.scene_id,
                        discovered_by=pov_char_id
                    )
                )
            for loc in u.discovered_locations:
                self.codex.entries.append(
                    DiscoveryEntry(
                        id=f"disc_{int(time.time())}_{len(self.codex.entries)}",
                        discovery_type=DiscoveryType.NEW_LOCATION,
                        title=loc,
                        description=f"Địa danh khám phá trong {draft.scene_id}",
                        discovered_in_scene=draft.scene_id,
                        discovered_by=pov_char_id
                    )
                )
            for sec in u.discovered_secrets:
                self.codex.entries.append(
                    DiscoveryEntry(
                        id=f"disc_{int(time.time())}_{len(self.codex.entries)}",
                        discovery_type=DiscoveryType.SECRET_CLUE,
                        title=sec,
                        description=f"Bí mật hé lộ trong {draft.scene_id}",
                        discovered_in_scene=draft.scene_id,
                        discovered_by=pov_char_id
                    )
                )

            # Update stats
            if pov_char_id in self.codex.rpg_character_stats:
                c_stat = self.codex.rpg_character_stats[pov_char_id]
                c_stat.hp_percent = max(10, min(100, c_stat.hp_percent + u.hp_change))
                c_stat.reputation += u.reputation_change
                c_stat.luck_score = min(100, c_stat.luck_score + u.luck_change)

            # Update Fate Choices
            if u.next_fate_choices:
                self.codex.active_fate_options = [
                    FateChoice(
                        choice_id=f"fate_{idx + 1}",
                        title=c.get("title") if isinstance(c, dict) else str(c),
                        description=c.get("description", "") if isinstance(c, dict) else "",
                        risk_reward_summary="Ảnh hưởng đến số phận và hướng đi tiếp theo."
                    )
                    for idx, c in enumerate(u.next_fate_choices)
                ]
            else:
                self._update_fallback_fate_choices(draft)

        else:
            # 1. Ask LLM to extract organic discoveries from the actual prose
            extraction = await self._extract_rpg_data_from_prose(draft)

            if extraction and extraction.discoveries:
                for item in extraction.discoveries:
                    new_entry = DiscoveryEntry(
                        id=f"disc_{int(time.time())}_{len(self.codex.entries)}",
                        discovery_type=item.discovery_type,
                        title=item.title,
                        description=item.description,
                        discovered_in_scene=draft.scene_id,
                        discovered_by=pov_char_id
                    )
                    self.codex.entries.append(new_entry)
            else:
                # Fallback heuristic: log the scene's key items/locations
                self._fallback_heuristic_extraction(draft, pov_char_id)

            # 2. Update Character RPG Stats from extracted consequences
            if extraction and extraction.stat_updates:
                for stat_up in extraction.stat_updates:
                    c_id = stat_up.character_id if stat_up.character_id in self.codex.rpg_character_stats else pov_char_id
                    if c_id in self.codex.rpg_character_stats:
                        c_stat = self.codex.rpg_character_stats[c_id]
                        c_stat.hp_percent = max(10, min(100, c_stat.hp_percent + stat_up.hp_loss_or_gain))
                        c_stat.reputation += stat_up.reputation_gain
                        c_stat.luck_score = min(100, c_stat.luck_score + stat_up.luck_gain)
                        if stat_up.power_tier_update:
                            c_stat.level = stat_up.power_tier_update
            else:
                # Default mild progression
                if pov_char_id in self.codex.rpg_character_stats:
                    st = self.codex.rpg_character_stats[pov_char_id]
                    st.reputation += 10
                    st.luck_score = min(100, st.luck_score + 5)

            # 3. Update active Fate Choices for next chapter based on ending cliffhanger
            if extraction and extraction.next_fate_choices and len(extraction.next_fate_choices) >= 2:
                self.codex.active_fate_options = extraction.next_fate_choices
            else:
                self._update_fallback_fate_choices(draft)

        self.codex.total_discoveries = len(self.codex.entries)

        # 4. Save updated Codex to story output folder
        self._save_codex_to_disk(state.story_id)

        return draft

    async def _extract_rpg_data_from_prose(self, draft: SceneDraft) -> Optional[SceneRPGExtractionResult]:
        """Calls LLM structured extraction to extract discoveries from prose."""
        if not self._adapter:
            return None

        lang = draft.contract.language or "Tiếng Việt"
        prompt = f"""
You are an expert RPG narrative analyst and game mechanics engineer.
Analyze the following story prose excerpt and extract tangible story discoveries, character stat changes, and 3 organic Fate Choices.

[STORY PROSE EXCERPT]
{draft.prose_content}

[SCENE METADATA]
- Location: {draft.contract.location}
- Ending Cliffhanger: {draft.contract.cliffhanger_hook}
- POV Character: {draft.contract.pov_character_id}

[MANDATORY TARGET LANGUAGE]
All extracted item titles, descriptions, location names, and fate choice descriptions MUST be written in {lang}.

[EXTRACTION GOALS]
1. discoveries: Genuine items/artifacts looted (ITEM_LOOT), new locations visited (NEW_LOCATION), or lore secrets revealed (SECRET_CLUE) in the excerpt.
2. stat_updates: Realistic changes to HP, reputation, or cultivation power tier based on what happened.
3. next_fate_choices: Exactly 3 high-stakes, logically divergent Fate Choices for the next chapter based on the ending cliffhanger.

Output strictly a valid JSON matching the SceneRPGExtractionResult schema.
"""
        try:
            res = await self._adapter.generate_structured(
                prompt=prompt,
                response_model=SceneRPGExtractionResult,
                temperature=0.3
            )
            return res
        except Exception as e:
            print(f"[RPGDiscoveryPlugin] Extraction notice: {e}")
            return None

    def _fallback_heuristic_extraction(self, draft: SceneDraft, pov_char_id: str):
        """Extracts items and secrets mentioned in prose using keywords."""
        prose_lower = draft.prose_content.lower()

        if "ngọc bội" in prose_lower or "bảo vật" in prose_lower or "linh thạch" in prose_lower:
            self.codex.entries.append(
                DiscoveryEntry(
                    id=f"disc_{int(time.time())}_item",
                    discovery_type=DiscoveryType.ITEM_LOOT,
                    title=f"Pháp Bảo: Vân Hà Ngọc Bội / Linh Thạch ({draft.scene_id})",
                    description=f"Vật phẩm xuất hiện trong tình tiết của phân cảnh {draft.scene_id}.",
                    discovered_in_scene=draft.scene_id,
                    discovered_by=pov_char_id
                )
            )

        if "bí mật" in prose_lower or "nhẫn" in prose_lower or "linh hồn" in prose_lower:
            self.codex.entries.append(
                DiscoveryEntry(
                    id=f"disc_{int(time.time())}_clue",
                    discovery_type=DiscoveryType.SECRET_CLUE,
                    title=f"Manh Mối Ẩn: Bí Ẩn Chiếc Nhẫn Thượng Cổ",
                    description=f"Tàn hồn cổ xưa trong chiếc nhẫn bắt đầu phát ra dao động trong phân cảnh {draft.scene_id}.",
                    discovered_in_scene=draft.scene_id,
                    discovered_by=pov_char_id
                )
            )

    def _update_fallback_fate_choices(self, draft: SceneDraft):
        """Generates dynamic choices based on cliffhanger hook."""
        hook = draft.contract.cliffhanger_hook
        self.codex.active_fate_options = [
            FateChoice(
                choice_id="fate_dyn_1",
                title="⚔️ Hướng 1: Bộc phát thực lực, phá vỡ phong tỏa",
                description=f"Đối phó trực tiếp với tình thế: '{hook}' bằng vũ lực tuyệt đối.",
                risk_reward="Rủi ro cao, dễ bị thương nhưng đột phá danh tiếng tông môn.",
                character_trait_impact="+20 Sát Khí, +30 Danh Vọng, -15% HP"
            ),
            FateChoice(
                choice_id="fate_dyn_2",
                title="🕊️ Hướng 2: Tương kế tựu kế, tìm đường đào thoát",
                description=f"Lợi dụng địa hình và điểm yếu đối phương để âm thầm thoát thân an toàn.",
                risk_reward="An toàn cao, bảo toàn 100% sinh lực.",
                character_trait_impact="+20 Tâm Cơ, +15 Phòng Thủ"
            ),
            FateChoice(
                choice_id="fate_dyn_3",
                title="🗺️ Hướng 3: Nhảy vào cấm địa, kích hoạt kỳ ngộ cổ xưa",
                description="Khai mở di tích bí ẩn để lật ngược tình thế trước mặt kẻ địch.",
                risk_reward="Mở khóa cấm địa mới, cơ hội tìm thấy công pháp thượng cổ.",
                character_trait_impact="+40 Điểm Khám Phá, Mở Khóa Bản Đồ Mới"
            )
        ]

    def _save_codex_to_disk(self, story_id: str):
        """Persists the live RPG Codex to disk in Markdown and JSON."""
        story_dir = os.path.join(self.output_dir, story_id)
        os.makedirs(story_dir, exist_ok=True)

        # 1. Save JSON
        json_path = os.path.join(story_dir, "rpg_codex.json")
        try:
            with open(json_path, "w", encoding="utf-8") as f:
                f.write(self.codex.model_dump_json(indent=2))
        except Exception:
            pass

        # 2. Save Markdown Journal
        md_path = os.path.join(story_dir, "RPG_DISCOVERY_JOURNAL.md")
        try:
            with open(md_path, "w", encoding="utf-8") as f:
                f.write("# 🎮 NHẬT KÝ KHÁM PHÁ THẾ GIỚI & CHỈ SỐ NHÂN VẬT\n\n")
                f.write("## 1. Chỉ Số & Khí Vận Nhân Vật\n")
                for c_id, stat in self.codex.rpg_character_stats.items():
                    f.write(f"- **{c_id}:** Cảnh giới: `{stat.level}` | HP: `{stat.hp_percent}%` | Khí vận: `{stat.luck_score}/100` | Danh vọng: `{stat.reputation}`\n")
                f.write("\n## 2. Nhật Ký Chiến Lợi Phẩm & Bí Mật Đã Mở Khóa\n")
                for e in self.codex.entries:
                    f.write(f"### [{e.discovery_type.value}] {e.title}\n")
                    f.write(f"- **Mô tả:** {e.description}\n")
                    f.write(f"- **Khám phá trong:** `{e.discovered_in_scene}` bởi `{e.discovered_by}`\n\n")
                f.write("## 3. Ngã Rẽ Số Phận Tiếp Theo (Fate Directives)\n")
                for fc in self.codex.active_fate_options:
                    f.write(f"- **{fc.title}:** {fc.description} *(Tác động: {fc.character_trait_impact})*\n")
        except Exception:
            pass
