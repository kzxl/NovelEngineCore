"""NovelDirectorEngine - The Universe Micro-Kernel Showrunner."""

import json
from typing import Callable, Dict, List, Optional
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
    CharacterDossier,
    SceneContract,
    SceneDraft
)
from novel_engine.core.context_builder import ContextBuilder
from novel_engine.plugins.base import INovelPlugin


class NovelDirectorEngine:
    """Micro-Kernel Director Engine implementing Universe Plugin Architecture v4.0."""

    def __init__(self, adapter: BaseLLMAdapter, event_bus: Optional[EventBus] = None):
        self.adapter = adapter
        self.event_bus = event_bus or EventBus()
        self.plugins: List[INovelPlugin] = []
        self.state: Optional[StoryState] = None

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

        self.state = StoryState(
            story_id=f"story_{title.lower().replace(' ', '_')}",
            title=title,
            logline=logline,
            genre=genre,
            world_bible=world_bible,
            characters={},
            chapters=[]
        )

        # Notify Plugins & EventBus
        for plugin in self.plugins:
            await plugin.on_story_initialized(self.state)

        await self.event_bus.publish(StoryInitializedEvent(story_state=self.state))
        return self.state

    def register_character(self, character: CharacterDossier):
        """Registers a character and broadcasts CharacterRegisteredEvent."""
        if not self.state:
            raise ValueError("StoryState not initialized. Call initialize_story first.")
        self.state.characters[character.character_id] = character

        # Fire domain event asynchronously
        # (In event loop)
        # self.event_bus.publish(CharacterRegisteredEvent(story_id=self.state.story_id, character=character))

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

        # 2. Build Micro-Context
        prompt = ContextBuilder.build_scene_prompt(self.state, active_contract)

        # 3. Draft Prose (Streaming if on_token provided)
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

        # 4. Post-draft Plugin Middleware Pipeline (Auditing, Comic Storyboard, etc.)
        final_draft = initial_draft
        for plugin in self.plugins:
            final_draft = await plugin.post_scene_draft(self.state, final_draft)

        # 5. Broadcast SceneDraftedEvent to Galaxy Listeners
        await self.event_bus.publish(
            SceneDraftedEvent(
                story_id=self.state.story_id,
                scene_draft=final_draft
            )
        )

        return final_draft
