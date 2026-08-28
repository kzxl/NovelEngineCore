"""NovelDirectorEngine - The Universe Micro-Kernel Showrunner."""

import json
from typing import Callable, Dict, List, Optional
from pydantic import BaseModel, Field
from novel_engine.adapters.base import BaseLLMAdapter
from novel_engine.core.event_bus import EventBus
from novel_engine.core.events import (
    StoryInitializedEvent,
    CharacterRegisteredEvent,
    SceneDraftedEvent
)
from novel_engine.core.state import (
    StoryState,
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
    SceneContract,
    SceneDraft
)
from novel_engine.core.plot_events import PlotEvent, GeneratedEventList
from novel_engine.core.continuity import StorySpine, SceneSummary, PlotThread
from novel_engine.core.context_builder import ContextBuilder
from novel_engine.plugins.base import INovelPlugin


class GeneratedCharacterList(BaseModel):
    characters: List[CharacterDossier] = Field(default_factory=list)


class WorldExpansionResult(BaseModel):
    new_factions: List[Faction] = Field(default_factory=list)
    new_locations: List[Location] = Field(default_factory=list)
    new_canon_rules: List[str] = Field(default_factory=list)


class NovelDirectorEngine:
    """Micro-Kernel Director Engine implementing Universe Architecture v4.0."""

    def __init__(self, adapter: BaseLLMAdapter, event_bus: Optional[EventBus] = None):
        self.adapter = adapter
        self.event_bus = event_bus or EventBus()
        self.plugins: List[INovelPlugin] = []
        self.state: Optional[StoryState] = None
        self.spine: Optional[StorySpine] = None

    def register_plugin(self, plugin: INovelPlugin):
        """Self-registers a feature star plugin into the micro-kernel."""
        plugin.initialize(self.event_bus, self.adapter)
        self.plugins.append(plugin)

    async def initialize_story(
        self,
        title: str,
        logline: str,
        genre: str,
        world_bible: Optional[WorldBible] = None
    ) -> StoryState:
        """Initializes story state and notifies the Universe EventBus."""
        if world_bible is None:
            prompt = (
                f"Create a rich, comprehensive WorldBible for a novel titled '{title}'.\n"
                f"Genre: {genre}\n"
                f"Premise / Logline: {logline}\n"
                f"Define cosmology, strict power progression limits, immutable canon laws, key factions, and locations."
            )
            world_bible = await self.adapter.generate_structured(
                prompt=prompt,
                response_model=WorldBible,
                temperature=0.4
            )

        story_id = f"story_{title.lower().replace(' ', '_')}"
        self.state = StoryState(
            story_id=story_id,
            title=title,
            logline=logline,
            genre=genre,
            world_bible=world_bible,
            characters={},
            chapters=[]
        )

        # 1. LLM dynamically generates initial cast (Protagonist, Antagonist, Mentor)
        try:
            initial_chars = await self.auto_generate_characters(count=3, roles_focus="Protagonist, Antagonist, Mentor")
        except Exception as e:
            print(f"[NovelEngine] Character auto-generation notice: {e}")
            initial_chars = []

        # 2. Build Dynamic Story Spine based on real characters generated
        char_ids = list(self.state.characters.keys())
        main_char = char_ids[0] if char_ids else "char_protagonist"
        rival_char = char_ids[1] if len(char_ids) > 1 else main_char

        self.spine = StorySpine(
            story_id=story_id,
            main_questline=logline or f"Hành trình quật khởi tại {title}.",
            current_act="Hồi 1: Thiếu Niên Xuất Thôn & Khởi Đầu Hành Trình",
            active_threads=[
                PlotThread(
                    thread_id="th_main_rivalry",
                    title=f"Xung Đột Đầu Tiên: {self.state.characters[main_char].name if main_char in self.state.characters else 'Nhân Vật Chính'} vs Thế Lực Cản Đường",
                    core_conflict=f"Mâu thuẫn lợi ích và sự tranh đoạt tại {world_bible.locations[0].name if world_bible.locations else 'Tân Thủ Thôn'}.",
                    involved_characters=[main_char, rival_char],
                    introduced_in_scene="VOL01_CH01_SC01"
                )
            ]
        )

        for plugin in self.plugins:
            await plugin.on_story_initialized(self.state)

        await self.event_bus.publish(
            StoryInitializedEvent(
                story_id=self.state.story_id,
                title=title,
                world_bible=world_bible
            )
        )

        return self.state

    async def auto_generate_characters(self, count: int = 3, roles_focus: str = "Protagonist, Antagonist, Mentor") -> List[CharacterDossier]:
        """Automatically generates a cast of consistent, multi-dimensional characters."""
        if not self.state:
            raise ValueError("StoryState not initialized.")

        prompt = f"""
You are a master character designer and novelist.
Based on the following World Bible, generate {count} unique, compelling characters.

WORLD TITLE: {self.state.world_bible.title}
GENRE: {self.state.genre}
POWER SYSTEM: {self.state.world_bible.energy_source}
ROLES FOCUS: {roles_focus}

Each character must have:
- Distinct name and role (Protagonist, Antagonist, Mentor, Deuteragonist, Sidekick)
- Core motivation, fatal flaw, and hidden secret
- Unique speech vocabulary style
- Current power status and health condition
- Detailed Visual Tags (for consistent AI art generation, e.g. age, hairstyle, robe color, physical marks)

Output JSON conforming to GeneratedCharacterList schema.
"""
        result = await self.adapter.generate_structured(
            prompt=prompt,
            response_model=GeneratedCharacterList,
            temperature=0.7
        )

        for char in result.characters:
            self.register_character(char)

        return result.characters

    async def auto_evolve_world(self, focus_topic: str = "Secret Factions & Ancient Locations") -> WorldExpansionResult:
        """Expands and enriches the existing world with new lore, locations, and factions."""
        if not self.state:
            raise ValueError("StoryState not initialized.")

        prompt = f"""
You are a master worldbuilder. Expand the universe lore for:
WORLD: {self.state.world_bible.title}
GENRE: {self.state.genre}
ENERGY SOURCE: {self.state.world_bible.energy_source}
FOCUS: {focus_topic}

Generate 2 new mysterious factions, 2 dangerous uncharted locations, and 2 new canon rules.
Output JSON conforming to WorldExpansionResult schema.
"""
        result = await self.adapter.generate_structured(
            prompt=prompt,
            response_model=WorldExpansionResult,
            temperature=0.6
        )

        # Merge into existing WorldBible
        self.state.world_bible.factions.extend(result.new_factions)
        self.state.world_bible.locations.extend(result.new_locations)
        self.state.world_bible.canon_rules.extend(result.new_canon_rules)

        return result

    async def auto_generate_plot_events(self, count: int = 3, focus_theme: Optional[str] = None) -> List[PlotEvent]:
        """Generates dynamic world events, crises, and plot twists based on world state and characters."""
        if not self.state:
            raise ValueError("StoryState not initialized.")

        char_summary = "\n".join(
            f"- {c.name} ({c.role.value}): Mục tiêu={c.personality.core_motivation}, Điểm yếu={c.personality.fatal_flaw}, Bí mật={c.personality.hidden_secret}"
            for c in self.state.characters.values()
        )

        prompt = f"""
You are an expert story director and drama engineer.
WORLD: {self.state.world_bible.title} ({self.state.genre})
ENERGY: {self.state.world_bible.energy_source}
EXISTING CHARACTERS:
{char_summary or "Chưa có nhân vật cụ thể"}

THEME FOCUS: {focus_theme or "Tranh đoạt tài nguyên, bí cảnh xuất thế, ân oán tông môn"}

Generate {count} dynamic, high-stakes plot events/crises (Biến cố thế giới) that will organically pull the characters into intense conflict.
Each event must contain suggested scene hooks (narrative_goal, conflict, cliffhanger).
Output JSON conforming strictly to GeneratedEventList schema.
"""
        result = await self.adapter.generate_structured(
            prompt=prompt,
            response_model=GeneratedEventList,
            temperature=0.7
        )
        return result.events

    def register_character(self, character: CharacterDossier):
        """Registers a character and stores in character matrix."""
        if not self.state:
            raise ValueError("StoryState not initialized. Call initialize_story first.")
        self.state.characters[character.character_id] = character

    def delete_character(self, character_id: str):
        """Deletes a character from matrix."""
        if self.state and character_id in self.state.characters:
            del self.state.characters[character_id]

    async def draft_scene(
        self,
        contract: SceneContract,
        on_token: Optional[Callable[[str], None]] = None
    ) -> SceneDraft:
        """Executes scene drafting through the Gravitational Middleware Pipeline."""
        if not self.state:
            raise ValueError("StoryState not initialized.")

        # 1. Pre-draft Plugin Middleware Pipeline
        active_contract = contract
        for plugin in self.plugins:
            active_contract = await plugin.pre_scene_draft(self.state, active_contract)

        # 2. Build Micro-Context with Causal Story Spine
        prompt = ContextBuilder.build_scene_prompt(
            state=self.state,
            contract=active_contract,
            spine=self.spine
        )

        # 3. Draft Prose
        if on_token:
            prose = await self.adapter.stream_text(
                prompt=prompt,
                on_chunk=on_token,
                temperature=0.7
            )
        else:
            prose = await self.adapter.generate_text(prompt=prompt, temperature=0.7)

        initial_draft = SceneDraft(
            scene_id=active_contract.scene_id,
            contract=active_contract,
            prose_content=prose
        )

        # 4. Record Scene into Story Spine Timeline
        if self.spine:
            self.spine.add_scene_summary(
                SceneSummary(
                    scene_id=active_contract.scene_id,
                    chapter_id=active_contract.chapter_id,
                    location=active_contract.location,
                    key_actions=active_contract.narrative_goal,
                    ending_cliffhanger=active_contract.cliffhanger_hook,
                    immediate_consequences=active_contract.scene_resolution
                )
            )

        # 5. Post-draft Plugin Middleware Pipeline
        final_draft = initial_draft
        for plugin in self.plugins:
            final_draft = await plugin.post_scene_draft(self.state, final_draft)

        # 6. Broadcast Event
        await self.event_bus.publish(
            SceneDraftedEvent(
                story_id=self.state.story_id,
                scene_draft=final_draft
            )
        )

        return final_draft
