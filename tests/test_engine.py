"""Unit tests for NovelEngineCore following Universe Architecture v4.0."""

import unittest
from novel_engine.adapters.mock_adapter import MockLLMAdapter
from novel_engine.engine import NovelDirectorEngine
from novel_engine.plugins.comic_storyboard_plugin import ComicStoryboardPlugin
from novel_engine.plugins.continuity_audit_plugin import ContinuityAuditPlugin
from novel_engine.core.events import SceneDraftedEvent
from novel_engine.core.state import (
    CharacterDossier,
    CharacterRole,
    PersonalityTraits,
    SpeechStyle,
    CharacterStatus,
    SceneContract
)


class TestUniverseNovelDirectorEngine(unittest.IsolatedAsyncioTestCase):
    async def test_universe_pipeline_and_plugins(self):
        # 1. Setup Micro-Kernel
        adapter = MockLLMAdapter()
        engine = NovelDirectorEngine(adapter=adapter)

        # 2. Register Plugins (Stars)
        audit_plugin = ContinuityAuditPlugin(strict_mode=True)
        comic_plugin = ComicStoryboardPlugin(enabled=True)
        engine.register_plugin(audit_plugin)
        engine.register_plugin(comic_plugin)
        self.assertEqual(len(engine.plugins), 2)

        # 3. Test EventBus Subscription
        event_received = []
        async def handler(event: SceneDraftedEvent):
            event_received.append(event.scene_draft.scene_id)
        engine.event_bus.subscribe(SceneDraftedEvent, handler)

        # 4. Genesis Galaxy
        state = await engine.initialize_story(
            title="Vo Than Tai Sinh",
            logline="Mot vo than chuyen sinh vao co the yeu ot.",
            genre="Xianxia"
        )
        self.assertEqual(state.world_bible.title, "Thương Lam Giới (Canglan Realm)")

        # 5. Register Character
        char = CharacterDossier(
            character_id="char_mc",
            name="Vân Triệt",
            role=CharacterRole.PROTAGONIST,
            visual_tags=["silver hair", "crimson eyes"],
            personality=PersonalityTraits(
                core_motivation="Đỉnh phong đại đạo",
                fatal_flaw="Lạnh lùng",
                moral_boundary="Không bắt nạt kẻ yếu"
            ),
            speech=SpeechStyle(),
            status=CharacterStatus(power_tier="Luyện Khí")
        )
        engine.register_character(char)

        # 6. Drafting Galaxy & Gravitational Pipeline
        contract = SceneContract(
            scene_id="SC01",
            chapter_id="CH01",
            scene_index=1,
            location="Lâm Gia",
            pov_character_id="char_mc",
            narrative_goal="Kiểm tra tu vi",
            conflict_dynamic="Bị kẻ khác coi thường",
            scene_resolution="Bộc lộ thiên phú ẩn",
            cliffhanger_hook="Trưởng lão kinh ngạc",
            hard_constraints=["Không tiết lộ bí mật chuyển sinh"]
        )

        draft = await engine.draft_scene(contract)

        # 7. Assertions across Galaxies
        self.assertTrue(draft.is_audited)
        self.assertIsNotNone(draft.comic_storyboard)
        self.assertEqual(len(draft.comic_storyboard.panels), 3)
        self.assertIn("SC01", event_received)


if __name__ == "__main__":
    unittest.main()
