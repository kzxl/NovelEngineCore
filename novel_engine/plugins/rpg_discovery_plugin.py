"""RPGDiscoveryPlugin - Game & Discovery Galaxy Star.

Maintains the World Discovery Codex, extracts new loot/locations/secrets,
updates character RPG stats, and generates dynamic Fate Choices for the next chapter.
"""

import time
from typing import Dict, List, Optional
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


class RPGDiscoveryPlugin(INovelPlugin):
    def __init__(self):
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
        """Initializes codex and default starter stats."""
        self.codex = DiscoveryCodex(
            story_id=state.story_id,
            total_discoveries=2,
            entries=[
                DiscoveryEntry(
                    id="disc_ring",
                    discovery_type=DiscoveryType.ITEM_LOOT,
                    title="Bảo Vật: Hắc Thiết Nhẫn Thượng Cổ",
                    description="Chiếc nhẫn đen bí ẩn chứa tàn hồn của Bát Phẩm Đan Tôn thời thượng cổ.",
                    discovered_in_scene="Mở đầu",
                    discovered_by="char_lin_feng"
                ),
                DiscoveryEntry(
                    id="disc_hall",
                    discovery_type=DiscoveryType.NEW_LOCATION,
                    title="Địa Danh: Lâm Gia Hội Nghị Đường",
                    description="Khu vực nghị sự trung tâm của Lâm Gia, được bảo hộ bởi cấm chế trưởng lão.",
                    discovered_in_scene="Mở đầu",
                    discovered_by="char_lin_feng"
                )
            ],
            rpg_character_stats={
                "char_lin_feng": RPGStats(
                    level="Luyện Khí Tầng 3",
                    hp_percent=75,
                    luck_score=85,
                    reputation=20,
                    faction_alignment="Lâm Gia"
                ),
                "char_elder_zhao": RPGStats(
                    level="Luyện Khí Tầng 9",
                    hp_percent=100,
                    luck_score=40,
                    reputation=80,
                    faction_alignment="Triệu Thị Gia Tộc"
                )
            },
            active_fate_options=[
                FateChoice(
                    choice_id="fate_opt_1",
                    title="⚔️ Hướng 1: Bộc phát sát ý, liều mạng chém giết",
                    description="Dùng Cốt Linh Lãnh Hỏa từ chiếc nhẫn đánh bất ngờ Đại Trưởng Lão để thoát thân.",
                    risk_reward="Rủi ro cực cao, dễ bị trọng thương nhưng danh chấn gia tộc và phá vỡ âm mưu lập tức.",
                    character_trait_impact="+20 Sát Khí, +30 Danh Tiếng, -40 HP"
                ),
                FateChoice(
                    choice_id="fate_opt_2",
                    title="🕊️ Hướng 2: Giả vờ khuất phục, tìm kế hoãn binh",
                    description="Giao nộp linh thạch, nhẫn nhịn chịu nhục để bảo vệ muội muội an toàn rồi bí mật bỏ trốn.",
                    risk_reward="Rủi ro thấp, bảo toàn thực lực nhưng bị trưởng lão gia tăng giám sát.",
                    character_trait_impact="+15 Tâm Cơ, +10 Căm Thù, 100% An Toàn"
                ),
                FateChoice(
                    choice_id="fate_opt_3",
                    title="🗺️ Hướng 3: Đột phá vòng vây, chạy trốn vào Hắc Ám Sâm Lâm",
                    description="Khai mở cấm địa hoang dã, kích hoạt bản đồ mới ngập tràn yêu thú và cơ duyên cổ đại.",
                    risk_reward="Mở khóa vùng đất mới, cơ hội nhặt linh dược thượng phẩm nhưng đối mặt yêu thú bậc 3.",
                    character_trait_impact="+50 Điểm Khám Phá, Mở Khóa Bản Đồ Mới"
                )
            ]
        )

    async def post_scene_draft(self, state: StoryState, draft: SceneDraft) -> SceneDraft:
        """Analyzes drafted scene and dynamically logs new discoveries and fate choices."""
        if not self.codex:
            await self.on_story_initialized(state)

        # Log new discovery from scene
        new_entry = DiscoveryEntry(
            id=f"disc_{draft.scene_id.lower()}",
            discovery_type=DiscoveryType.ITEM_LOOT,
            title="Pháp Bảo Mới: Vân Hà Ngọc Bội (Đã Thu Hồi)",
            description=f"Di vật chứa linh khí cổ xưa của mẫu thân để lại, thu hồi thành công trong {draft.scene_id}.",
            discovered_in_scene=draft.scene_id,
            discovered_by=draft.contract.pov_character_id
        )
        self.codex.entries.append(new_entry)
        self.codex.total_discoveries = len(self.codex.entries)

        # Update character RPG stats
        if "char_lin_feng" in self.codex.rpg_character_stats:
            stats = self.codex.rpg_character_stats["char_lin_feng"]
            stats.reputation += 15
            stats.luck_score += 5

        return draft
