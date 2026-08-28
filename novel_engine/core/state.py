"""Core State & Schema Definitions for NovelEngineCore using Pydantic v2."""

from enum import Enum
from typing import Dict, List, Optional
from pydantic import BaseModel, Field


# ----------------------------------------------------------------------
# 1. World Bible & Canon Law
# ----------------------------------------------------------------------

class PowerTier(BaseModel):
    rank: int
    name: str
    description: str
    hard_limits: str = Field(description="What characters in this tier CANNOT do.")


class Faction(BaseModel):
    faction_id: str = Field(default="fac_main")
    name: str
    alignment: str = "Trung Lập"
    core_doctrine: str = "Bảo vệ môn phái"
    relations: Dict[str, str] = Field(default_factory=dict)


class Location(BaseModel):
    location_id: str = Field(default="loc_main")
    name: str
    climate_and_vibe: str = "Linh khí dồi dào"
    key_hazards: str = "Trận pháp cấm chế"
    connected_locations: List[str] = Field(default_factory=list)


class WorldBible(BaseModel):
    world_id: str
    title: str
    genre: str
    era_setting: str
    origin_myth: Optional[str] = None
    energy_source: str = Field(description="E.g., Spiritual Qi, Mana, Cyberware Overclock")
    power_progression: List[PowerTier] = Field(default_factory=list)
    canon_rules: List[str] = Field(
        default_factory=list,
        description="Immutable physical and narrative laws that cannot be broken."
    )
    factions: List[Faction] = Field(default_factory=list)
    locations: List[Location] = Field(default_factory=list)


class WorldExpansionResult(BaseModel):
    new_factions: List[Faction] = Field(default_factory=list)
    new_locations: List[Location] = Field(default_factory=list)
    new_canon_rules: List[str] = Field(default_factory=list)


# ----------------------------------------------------------------------
# 2. Character Matrix & OOC Guard
# ----------------------------------------------------------------------

class CharacterRole(str, Enum):
    PROTAGONIST = "Protagonist"
    ANTAGONIST = "Antagonist"
    DEUTERAGONIST = "Deuteragonist"
    MENTOR = "Mentor"
    SIDEKICK = "Sidekick"
    NPC = "MinorNPC"


class PersonalityTraits(BaseModel):
    core_motivation: str
    fatal_flaw: str
    moral_boundary: str
    hidden_secret: Optional[str] = None


class SpeechStyle(BaseModel):
    vocabulary_level: str = "Standard"
    catchphrases: List[str] = Field(default_factory=list)
    address_forms: Dict[str, str] = Field(default_factory=dict)


class CharacterStatus(BaseModel):
    power_tier: str
    health_condition: str = "Healthy"
    mental_state: str = "Calm"
    current_location_id: Optional[str] = None


class InventoryItem(BaseModel):
    item_id: str
    name: str
    quantity: int = 1
    state: str = "Equipped"


class Relationship(BaseModel):
    sentiment: str
    trust_level: int = Field(ge=-100, le=100, default=0)
    shared_history: Optional[str] = None


class CharacterDossier(BaseModel):
    character_id: str
    name: str
    aliases: List[str] = Field(default_factory=list)
    role: CharacterRole = CharacterRole.NPC
    visual_tags: List[str] = Field(
        default_factory=list,
        description="Tags for consistent visual image generation (e.g. 'black hair, blue robe, scar on left cheek')."
    )
    personality: PersonalityTraits
    speech: SpeechStyle = Field(default_factory=SpeechStyle)
    status: CharacterStatus
    inventory: List[InventoryItem] = Field(default_factory=list)
    relationships: Dict[str, Relationship] = Field(default_factory=dict)


class GeneratedCharacterList(BaseModel):
    characters: List[CharacterDossier] = Field(default_factory=list)


# ----------------------------------------------------------------------
# 3. Scene Contract & Beat Sheets
# ----------------------------------------------------------------------

class MutationType(str, Enum):
    HP_LOSS = "HP_LOSS"
    ITEM_ACQUIRED = "ITEM_ACQUIRED"
    ITEM_LOST = "ITEM_LOST"
    RELATION_CHANGE = "RELATION_CHANGE"
    SECRET_REVEALED = "SECRET_REVEALED"


class StateMutation(BaseModel):
    target_entity: str
    mutation_type: MutationType
    description: str


class SceneContract(BaseModel):
    scene_id: str
    chapter_id: str
    scene_index: int
    location: str
    time_of_day: str = "Daytime"
    pov_character_id: str
    present_characters: List[str] = Field(default_factory=list)
    target_word_count: int = 1200
    min_word_count: int = 800
    max_word_count: int = 1500
    narrative_goal: str
    conflict_dynamic: str
    scene_resolution: str
    cliffhanger_hook: str
    hard_constraints: List[str] = Field(default_factory=list)
    expected_mutations: List[StateMutation] = Field(default_factory=list)


# ----------------------------------------------------------------------
# 4. Comic / Manga Storyboard Extension
# ----------------------------------------------------------------------

class CameraAngle(str, Enum):
    WIDE_SHOT = "Wide Shot (Toàn cảnh)"
    MEDIUM_SHOT = "Medium Shot (Trung cảnh)"
    CLOSE_UP = "Close-up (Cận cảnh)"
    EXTREME_CLOSE_UP = "Extreme Close-up (Đặc tả mắt/biểu cảm)"
    LOW_ANGLE = "Low Angle (Góc thấp kịch tính)"
    DUTCH_ANGLE = "Dutch Angle (Góc nghiêng căng thẳng)"


class ComicPanel(BaseModel):
    panel_index: int
    camera_angle: CameraAngle
    visual_composition: str = Field(description="Detailed visual prompt describing characters, pose, background, lighting.")
    active_characters: List[str] = Field(default_factory=list)
    dialogue: List[Dict[str, str]] = Field(
        default_factory=list,
        description="Speaker -> Speech text for dialogue bubbles"
    )
    sound_effects_sfx: Optional[str] = Field(None, description="E.g., 'BOOM!', 'SLASH!', 'CRACK!'")
    image_prompt_for_ai: str = Field(description="Direct prompt tailored for Flux/Stable Diffusion/Midjourney.")


class ComicStoryboard(BaseModel):
    storyboard_id: str
    scene_id: str
    chapter_id: str
    page_layout_type: str = "Webtoon Vertical Scroll"
    panels: List[ComicPanel] = Field(default_factory=list)


# ----------------------------------------------------------------------
class UnifiedSceneResponse(BaseModel):
    scene_title: str = "Phân Cảnh Mới"
    prose_content: str = Field(description="Toàn bộ nội dung văn xuôi chi tiết của chương truyện")
    key_events: List[str] = Field(default_factory=list, description="Tóm tắt các sự kiện chính trong cảnh")
    discovered_items: List[str] = Field(default_factory=list, description="Vật phẩm/pháp bảo xuất hiện")
    discovered_locations: List[str] = Field(default_factory=list, description="Địa danh mới")
    discovered_secrets: List[str] = Field(default_factory=list, description="Bí mật / manh mối hé lộ")
    hp_change: int = Field(default=0, description="Biến động HP nhân vật chính")
    reputation_change: int = Field(default=10, description="Biến động danh vọng")
    luck_change: int = Field(default=5, description="Biến động khí vận")
    ending_cliffhanger: str = Field(default="", description="Nút thắt kết thúc phân cảnh")
    next_fate_choices: List[Dict[str, str]] = Field(default_factory=list, description="3 ngã rẽ số phận tiếp theo")


class SceneDraft(BaseModel):
    scene_id: str
    contract: SceneContract
    prose_content: str
    unified_data: Optional[UnifiedSceneResponse] = None
    comic_storyboard: Optional[ComicStoryboard] = None
    is_audited: bool = False
    audit_notes: Optional[str] = None


class Chapter(BaseModel):
    chapter_id: str
    title: str
    summary: str
    scene_contracts: List[SceneContract] = Field(default_factory=list)
    drafted_scenes: List[SceneDraft] = Field(default_factory=list)


class StoryState(BaseModel):
    story_id: str
    title: str
    logline: str
    genre: str
    world_bible: WorldBible
    characters: Dict[str, CharacterDossier] = Field(default_factory=dict)
    chapters: List[Chapter] = Field(default_factory=list)
    active_chapter_index: int = 0
    active_scene_index: int = 0
