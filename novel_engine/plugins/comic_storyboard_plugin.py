"""ComicStoryboardPlugin - Visual Galaxy Feature Star.

Transforms drafted novel prose into Manga/Webtoon comic panels and AI image prompts.
"""

from typing import Optional
from novel_engine.plugins.base import INovelPlugin
from novel_engine.core.event_bus import EventBus
from novel_engine.adapters.base import BaseLLMAdapter
from novel_engine.core.state import StoryState, SceneContract, SceneDraft, ComicStoryboard
from novel_engine.core.comic_adapter import ComicStoryboardAdapter


class ComicStoryboardPlugin(INovelPlugin):
    def __init__(self, enabled: bool = True):
        self._enabled = enabled
        self._event_bus: Optional[EventBus] = None
        self._adapter: Optional[BaseLLMAdapter] = None

    @property
    def plugin_name(self) -> str:
        return "ComicStoryboardPlugin"

    @property
    def galaxy(self) -> str:
        return "Visual"

    def initialize(self, event_bus: EventBus, adapter: BaseLLMAdapter):
        self._event_bus = event_bus
        self._adapter = adapter

    async def post_scene_draft(self, state: StoryState, draft: SceneDraft) -> SceneDraft:
        """Transforms prose into comic panels and attaches to SceneDraft."""
        if not self._enabled or not self._adapter:
            return draft

        # Build prompt using existing comic adapter logic
        prompt = ComicStoryboardAdapter.build_storyboard_prompt(
            prose=draft.prose_content,
            contract=draft.contract,
            characters=state.characters
        )

        comic_sb = await self._adapter.generate_structured(
            prompt=prompt,
            response_model=ComicStoryboard,
            temperature=0.3
        )

        draft.comic_storyboard = comic_sb
        return draft
