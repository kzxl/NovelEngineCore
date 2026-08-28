"""Test Ollama real generation with pre-seeded World Bible for instant speed."""

import sys
import asyncio

if sys.platform.startswith("win"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from novel_engine.adapters.ollama_adapter import OllamaAdapter
from novel_engine.engine import NovelDirectorEngine
from novel_engine.plugins.comic_storyboard_plugin import ComicStoryboardPlugin
from novel_engine.plugins.continuity_audit_plugin import ContinuityAuditPlugin
from novel_engine.core.state import (
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
    SceneContract
)


async def main():
    print("=" * 70)
    print(" Testing Real Local Inference with Ollama (qwen2.5-coder:3b)")
    print("=" * 70)

    adapter = OllamaAdapter(model_name="qwen2.5-coder:3b")
    engine = NovelDirectorEngine(adapter=adapter)
    engine.register_plugin(ContinuityAuditPlugin(strict_mode=True))
    engine.register_plugin(ComicStoryboardPlugin(enabled=True))

    # Provide pre-seeded World Bible to avoid slow JSON generation on 3B model
    world_bible = WorldBible(
        world_id="w_canglan",
        title="Thương Lam Giới",
        genre="Xianxia",
        era_setting="Kỷ nguyên Mạt Pháp",
        energy_source="Thiên Địa Linh Khí",
        power_progression=[
            PowerTier(rank=1, name="Luyện Khí", description="Luyện thể sơ nhập", hard_limits="Không thể bay lượn"),
            PowerTier(rank=2, name="Trúc Cơ", description="Linh khí hóa dịch", hard_limits="Chưa thể ngưng kết Kim Đan")
        ],
        canon_rules=[
            "Phàm nhân không có linh căn không thể tu luyện.",
            "Linh thạch cạn kiệt sẽ hóa thành cát bụi."
        ],
        locations=[
            Location(location_id="loc_hall", name="Lâm Gia - Hội Nghị Đường", climate_and_vibe="Uy nghiêm", key_hazards="Áp lực trưởng lão")
        ]
    )

    state = await engine.initialize_story(
        title="Thương Lam Tiên Tôn",
        logline="Thiếu niên tìm được chiếc nhẫn cổ quật khởi tu tiên.",
        genre="Xianxia",
        world_bible=world_bible
    )
    print(f"\n[1] World Bible Loaded: {state.world_bible.title}")

    # Register Character
    char = CharacterDossier(
        character_id="char_lin_feng",
        name="Lâm Phong",
        role=CharacterRole.PROTAGONIST,
        visual_tags=["young cultivator", "black ponytail", "blue robe"],
        personality=PersonalityTraits(
            core_motivation="Bảo vệ muội muội",
            fatal_flaw="Cố chấp",
            moral_boundary="Không hại người vô tội"
        ),
        speech=SpeechStyle(),
        status=CharacterStatus(power_tier="Luyện Khí Tầng 3", health_condition="Bị thương vai phải"),
        inventory=[InventoryItem(item_id="item_ring", name="Hắc Thiết Nhẫn")]
    )
    engine.register_character(char)
    print(f"[2] Registered Character: {char.name}")

    # Draft Scene
    contract = SceneContract(
        scene_id="SC_OLLAMA_01",
        chapter_id="CH01",
        scene_index=1,
        location="Lâm Gia - Hội Nghị Đường",
        pov_character_id="char_lin_feng",
        present_characters=["char_lin_feng"],
        target_word_count=300,
        narrative_goal="Lâm Phong ném linh thạch trả nợ để lấy ngọc bội.",
        conflict_dynamic="Đại Trưởng Lão Triệu sỉ nhục và đòi tăng giá lên 1,000 linh thạch.",
        scene_resolution="Lâm Phong trả đủ tiền nhưng bộc lộ sát khí.",
        cliffhanger_hook="Trưởng lão nhận ra linh khí cổ xưa trên ngọc bội.",
        hard_constraints=[
            "Lâm Phong chưa đạt Trúc Cơ, TUYỆT ĐỐI KHÔNG được giết Trưởng Lão trong cảnh này.",
            "Không được để lộ danh tính linh hồn trong chiếc nhẫn."
        ]
    )

    print("\n[3] Streaming Real Prose Generation from Ollama...")
    print("-" * 70)
    
    def on_token(token):
        print(token, end="", flush=True)

    draft = await engine.draft_scene(contract, on_token=on_token)
    
    print("\n" + "-" * 70)
    print(" [✓] Real Generation Completed Successfully!")
    print(f" Audited: {draft.is_audited} | Notes: {draft.audit_notes}")
    if draft.comic_storyboard:
        print(f"\n[4] Generated {len(draft.comic_storyboard.panels)} Comic Panels via Local Ollama:")
        for p in draft.comic_storyboard.panels:
            print(f"\n  Panel #{p.panel_index} [{p.camera_angle}]:")
            print(f"  Visual: {p.visual_composition}")
            print(f"  Prompt: {p.image_prompt_for_ai}")


if __name__ == "__main__":
    asyncio.run(main())
