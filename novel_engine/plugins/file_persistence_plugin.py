"""FilePersistencePlugin - Publishing Galaxy Star.

Automatically persists world states, character matrices, novel manuscripts,
and comic storyboards to disk in Markdown and JSON formats upon generation.
"""

from typing import Optional
from novel_engine.plugins.base import INovelPlugin
from novel_engine.core.event_bus import EventBus
from novel_engine.adapters.base import BaseLLMAdapter
from novel_engine.core.state import StoryState, SceneDraft
from novel_engine.core.storage import StoryStorageManager
from novel_engine.core.events import StoryInitializedEvent, SceneDraftedEvent


class FilePersistencePlugin(INovelPlugin):
    def __init__(self, base_output_dir: str = "output/stories"):
        self.storage = StoryStorageManager(base_output_dir=base_output_dir)
        self._event_bus: Optional[EventBus] = None
        self._adapter: Optional[BaseLLMAdapter] = None

    @property
    def plugin_name(self) -> str:
        return "FilePersistencePlugin"

    @property
    def galaxy(self) -> str:
        return "Publishing"

    def initialize(self, event_bus: EventBus, adapter: BaseLLMAdapter):
        self._event_bus = event_bus
        self._adapter = adapter

        # Wire up EventBus listeners
        event_bus.subscribe(StoryInitializedEvent, self.on_story_event)
        event_bus.subscribe(SceneDraftedEvent, self.on_scene_event)

    async def on_story_event(self, event: StoryInitializedEvent):
        """Saves world and character manifests when a story is initialized."""
        self.storage.save_world_and_characters(event.story_state)

    async def on_scene_event(self, event: SceneDraftedEvent):
        """Saves scene draft to individual file and master novel manuscript."""
        # We can also call save from post_scene_draft
        pass

    async def on_story_initialized(self, state: StoryState):
        self.storage.save_world_and_characters(state)

    async def post_scene_draft(self, state: StoryState, draft: SceneDraft) -> SceneDraft:
        """Saves scene files immediately after draft is produced."""
        saved_paths = self.storage.save_scene_draft(state, draft)
        # Update draft audit notes with file path
        if not draft.audit_notes:
            draft.audit_notes = f"Saved to {saved_paths['manuscript_file']}"
        else:
            draft.audit_notes += f" | Saved to {saved_paths['manuscript_file']}"
        return draft
