"""Game-like Narrative Engine, Fate Choices & RPG Discovery Codex."""

import time
from enum import Enum
from typing import Dict, List, Optional
from pydantic import BaseModel, Field
from novel_engine.core.state import InventoryItem, Location


class DiscoveryType(str, Enum):
    ITEM_LOOT = "ITEM_LOOT"
    NEW_LOCATION = "NEW_LOCATION"
    NEW_NPC = "NEW_NPC"
    SECRET_CLUE = "SECRET_CLUE"
    RELATION_SHIFT = "RELATION_SHIFT"


class DiscoveryEntry(BaseModel):
    id: str
    discovery_type: DiscoveryType
    title: str
    description: str
    discovered_in_scene: str
    discovered_by: str
    timestamp: float = Field(default_factory=time.time)


class FateChoice(BaseModel):
    choice_id: str
    title: str
    description: str
    risk_reward: str
    character_trait_impact: str
    recommended_for: Optional[str] = None


class ChapterPlanningConfig(BaseModel):
    chapter_number: int = 1
    cast_size: int = Field(ge=1, le=8, default=2, description="Number of characters involved in this chapter.")
    spotlight_character_id: str = "char_lin_feng"
    selected_fate_choice: Optional[FateChoice] = None
    custom_player_directive: Optional[str] = None
    target_pacing: str = "Căng thẳng cao trào (High Tension)"


class RPGStats(BaseModel):
    level: str = "Luyện Khí Tầng 3"
    hp_percent: int = 85
    luck_score: int = 70
    reputation: int = 10
    faction_alignment: str = "Lâm Gia"


class DiscoveryCodex(BaseModel):
    story_id: str
    total_discoveries: int = 0
    entries: List[DiscoveryEntry] = Field(default_factory=list)
    rpg_character_stats: Dict[str, RPGStats] = Field(default_factory=dict)
    active_fate_options: List[FateChoice] = Field(default_factory=list)
