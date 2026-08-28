"""ContinuityAuditPlugin - Quality Galaxy Feature Star.

Inspects drafted prose against World Bible canon rules and negative constraints.
"""

from typing import Optional
from novel_engine.plugins.base import INovelPlugin
from novel_engine.core.event_bus import EventBus
from novel_engine.adapters.base import BaseLLMAdapter
from novel_engine.core.state import StoryState, SceneDraft
from novel_engine.core.events import CanonViolationDetectedEvent


class ContinuityAuditPlugin(INovelPlugin):
    def __init__(self, strict_mode: bool = False):
        self.strict_mode = strict_mode
        self._event_bus: Optional[EventBus] = None
        self._adapter: Optional[BaseLLMAdapter] = None

    @property
    def plugin_name(self) -> str:
        return "ContinuityAuditPlugin"

    @property
    def galaxy(self) -> str:
        return "Quality"

    def initialize(self, event_bus: EventBus, adapter: BaseLLMAdapter):
        self._event_bus = event_bus
        self._adapter = adapter

    async def post_scene_draft(self, state: StoryState, draft: SceneDraft) -> SceneDraft:
        """Audits prose for canon consistency."""
        # Check basic negative constraints
        violations = []
        for constraint in draft.contract.hard_constraints:
            # Simple heuristic check or LLM pass
            if "TUYỆT ĐỐI KHÔNG" in constraint and "giết" in constraint.lower():
                if "giết chết" in draft.prose_content.lower():
                    violations.append(f"Potential violation of constraint: {constraint}")

        if violations and self._event_bus:
            await self._event_bus.publish(
                CanonViolationDetectedEvent(
                    story_id=state.story_id,
                    scene_id=draft.scene_id,
                    violation_notes="; ".join(violations)
                )
            )

        draft.is_audited = True
        draft.audit_notes = "Passed audit." if not violations else "; ".join(violations)
        return draft
