"""Domain Events for NovelEngineCore."""

import time
from typing import Optional
from novel_engine.core.event_bus import DomainEvent
from novel_engine.core.state import StoryState, CharacterDossier, SceneContract, SceneDraft


class StoryInitializedEvent(DomainEvent):
    story_state: StoryState

    def __init__(self, story_state: StoryState, **data):
        super().__init__(timestamp=time.time(), story_state=story_state, **data)


class CharacterRegisteredEvent(DomainEvent):
    story_id: str
    character: CharacterDossier

    def __init__(self, story_id: str, character: CharacterDossier, **data):
        super().__init__(timestamp=time.time(), story_id=story_id, character=character, **data)


class SceneDraftedEvent(DomainEvent):
    story_id: str
    scene_draft: SceneDraft

    def __init__(self, story_id: str, scene_draft: SceneDraft, **data):
        super().__init__(timestamp=time.time(), story_id=story_id, scene_draft=scene_draft, **data)


class CanonViolationDetectedEvent(DomainEvent):
    story_id: str
    scene_id: str
    violation_notes: str

    def __init__(self, story_id: str, scene_id: str, violation_notes: str, **data):
        super().__init__(timestamp=time.time(), story_id=story_id, scene_id=scene_id, violation_notes=violation_notes, **data)
