"""Universe Architecture Demo for NovelEngineCore.

Demonstrates:
1. Micro-Kernel Director Engine initialization
2. Self-Registration of Galaxy Plugins (Visual Galaxy & Quality Galaxy)
3. In-Memory EventBus Domain Events
4. Middleware Pipeline (Pre-draft & Post-draft transforms)
"""

import sys
import asyncio

# Ensure UTF-8 output on Windows console
if sys.platform.startswith("win"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from novel_engine.adapters.mock_adapter import MockLLMAdapter
from novel_engine.engine import NovelDirectorEngine
from novel_engine.plugins.comic_storyboard_plugin import ComicStoryboardPlugin
from novel_engine.plugins.continuity_audit_plugin import ContinuityAuditPlugin
from novel_engine.core.events import SceneDraftedEvent, CanonViolationDetectedEvent
from novel_engine.core.state import (
    CharacterDossier,
    CharacterRole,
    PersonalityTraits,
    SpeechStyle,
    CharacterStatus,
    InventoryItem,
    SceneContract
)


# EventBus Listener Example (Cross-Galaxy Observer)
async def on_scene_drafted_logger(event: SceneDraftedEvent):
    print(f"\n📢 [EventBus Notification] SceneDraftedEvent received for Story '{event.story_id}', Scene '{event.scene_draft.scene_id}'!")


async def main():
    print("=" * 80)
    print(" 🌌 NOVEL ENGINE CORE - UNIVERSE PLUGIN ARCHITECTURE v4.0 DEMO")
    print("=" * 80)

    # 1. Initialize Micro-Kernel Engine
    adapter = MockLLMAdapter()
    engine = NovelDirectorEngine(adapter=adapter)

    # 2. Register Feature Star Plugins into the Micro-Kernel
    print("\n[Spacetime] Registering Galaxy Plugins into Universe Micro-Kernel...")
    engine.register_plugin(ContinuityAuditPlugin(strict_mode=True))
    engine.register_plugin(ComicStoryboardPlugin(enabled=True))
    for p in engine.plugins:
        print(f"  ⭐ Registered Star: '{p.plugin_name}' in Galaxy: [{p.galaxy}]")

    # 3. Subscribe to In-Memory EventBus
    engine.event_bus.subscribe(SceneDraftedEvent, on_scene_drafted_logger)

    # 4. Genesis Galaxy: Initialize World Bible
    print("\n[Genesis Galaxy] Initializing World Bible & Canon Law...")
    state = await engine.initialize_story(
        title="Thuong Lam Tien Ton (Azure Immortal)",
        logline="Mot thieu nien tim duoc chiec nhan co, tung buoc doi dau voi cac tong mon.",
        genre="Xianxia"
    )
    print(f"  [+] World Title: {state.world_bible.title}")
    print(f"  [+] Energy Source: {state.world_bible.energy_source}")
    print(f"  [+] Canon Rules: {len(state.world_bible.canon_rules)} invariant laws")

    # 5. Character Matrix Setup
    protagonist = CharacterDossier(
        character_id="char_lin_feng",
        name="Lâm Phong",
        role=CharacterRole.PROTAGONIST,
        visual_tags=["young male 18yo", "long black hair in ponytail", "sharp cold eyes", "ragged blue disciple robe"],
        personality=PersonalityTraits(
            core_motivation="Bảo vệ muội muội và rửa oan cho phụ thân",
            fatal_flaw="Cố chấp và đa nghi",
            moral_boundary="Không làm hại kẻ vô tội"
        ),
        speech=SpeechStyle(vocabulary_level="Đanh thép, ít lời"),
        status=CharacterStatus(power_tier="Luyện Khí Tầng 3", health_condition="Bị thương vai phải"),
        inventory=[InventoryItem(item_id="item_ring", name="Hắc Thiết Nhẫn (Chiếc nhẫn đen)")],
    )
    engine.register_character(protagonist)
    print(f"  [+] Character Registered: '{protagonist.name}' (Role: {protagonist.role.value})")

    # 6. Drafting Galaxy: Execute Scene Contract
    print("\n[Drafting Galaxy] Executing Scene Contract via Gravitational Pipeline...")
    contract = SceneContract(
        scene_id="VOL01_CH01_SC01",
        chapter_id="CH01",
        scene_index=1,
        location="Lâm Gia - Hội Nghị Đường",
        time_of_day="Hoàng hôn",
        pov_character_id="char_lin_feng",
        present_characters=["char_lin_feng"],
        target_word_count=1200,
        narrative_goal="Lâm Phong đến chuộc lại Vân Hà Ngọc Bội của mẫu thân.",
        conflict_dynamic="Đại Trưởng Lão Triệu ép giá tăng gấp đôi lên 1,000 linh thạch.",
        scene_resolution="Lâm Phong dằn mặt trưởng lão bằng cách ném đủ linh thạch.",
        cliffhanger_hook="Triệu trưởng lão nhận ra luồng linh khí cổ xưa trên ngọc bội và ra lệnh phong tỏa toàn bộ cửa ra vào.",
        hard_constraints=[
            "Lâm Phong chưa đạt Trúc Cơ, TUYỆT ĐỐI KHÔNG được giết Trưởng Lão trong cảnh này.",
            "Không được để lộ danh tính linh hồn trong chiếc nhẫn.",
            "Văn phong sắc sảo, dồn dập (Show, don't tell)."
        ]
    )

    draft = await engine.draft_scene(contract=contract)

    # 7. Output Novel Prose
    print("\n" + "=" * 80)
    print(f" [NOVEL PROSE OUTPUT] Scene: {draft.scene_id} | Audited: {draft.is_audited}")
    print("=" * 80)
    print(draft.prose_content)

    # 8. Output Visual Galaxy (Comic Storyboard Plugin)
    if draft.comic_storyboard:
        print("\n" + "=" * 80)
        print(" [VISUAL GALAXY] COMIC / WEBTOON STORYBOARD (From ComicStoryboardPlugin)")
        print("=" * 80)
        for p in draft.comic_storyboard.panels:
            print(f"\n--- PANEL #{p.panel_index} [{p.camera_angle.value}] ---")
            print(f"Visual Composition: {p.visual_composition}")
            if p.dialogue:
                dialogues = ", ".join(f"{k}: \"{v}\"" for d in p.dialogue for k, v in d.items())
                print(f"Speech Bubble: {dialogues}")
            if p.sound_effects_sfx:
                print(f"Sound Effect (SFX): [{p.sound_effects_sfx}]")
            print(f"AI Image Prompt (Flux/Midjourney):\n   \"{p.image_prompt_for_ai}\"")

    print("\n" + "=" * 80)
    print(" 🌌 UNIVERSE ARCHITECTURE DEMO COMPLETED SUCCESSFULLY!")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())
