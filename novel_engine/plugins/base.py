"""INovelPlugin - The Contract for Universe Feature Stars."""

from abc import ABC, abstractmethod
from typing import Optional
from novel_engine.core.event_bus import EventBus
from novel_engine.adapters.base import BaseLLMAdapter
from novel_engine.core.state import StoryState, SceneContract, SceneDraft


class INovelPlugin(ABC):
    """Universal Plugin Contract following Universe Architecture v4.0."""

    @property
    @abstractmethod
    def plugin_name(self) -> str:
        """Unique identifier for the feature plugin."""
        pass

    @property
    @abstractmethod
    def galaxy(self) -> str:
        """Domain group (e.g., 'Visual', 'Quality', 'Audio', 'Publishing')."""
        pass

    @abstractmethod
    def initialize(self, event_bus: EventBus, adapter: BaseLLMAdapter):
        """Called upon engine startup to wire up event subscriptions & adapters."""
        pass

    async def on_story_initialized(self, state: StoryState):
        """Lifecycle hook: Story initialized."""
        pass

    async def pre_scene_draft(self, state: StoryState, contract: SceneContract) -> SceneContract:
        """Middleware hook: Modify or augment scene contract before drafting."""
        return contract

    async def post_scene_draft(self, state: StoryState, draft: SceneDraft) -> SceneDraft:
        """Middleware hook: Transform, augment, or inspect draft prose after drafting."""
        return draft
