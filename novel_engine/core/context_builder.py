"""Context Builder & Lore Trigger Engine.

Synthesizes laser-focused micro-context (2.5k - 4k tokens) for LLMs,
preventing context pollution, hallucination, and plot drift.
"""

from typing import List, Dict, Optional
from novel_engine.core.state import StoryState, SceneContract, CharacterDossier
from novel_engine.core.continuity import StorySpine


class ContextBuilder:
    @staticmethod
    def build_scene_prompt(
        state: StoryState,
        contract: SceneContract,
        spine: Optional[StorySpine] = None
    ) -> str:
        """Compiles a complete instruction payload ensuring 100% causal continuity across chapters."""
        world = state.world_bible
        
        # 1. Extract Canon Rules
        canon_rules_text = "\n".join(f"- {rule}" for rule in world.canon_rules)
        
        # 2. Extract Power System context
        power_tiers_text = "\n".join(
            f"- Rank {tier.rank} [{tier.name}]: Limit -> {tier.hard_limits}"
            for tier in world.power_progression
        )

        # 3. Dynamic Lore Injection based on location & scene
        location_info = next(
            (loc for loc in world.locations if loc.name.lower() in contract.location.lower()),
            None
        )
        location_context = (
            f"Location: {location_info.name} | Climate/Vibe: {location_info.climate_and_vibe} | Hazards: {location_info.key_hazards}"
            if location_info else f"Location: {contract.location} (Time: {contract.time_of_day})"
        )

        # 4. Extract Present Characters & OOC Guardrails
        char_dossiers: List[str] = []
        for char_id in contract.present_characters:
            char = state.characters.get(char_id)
            if char:
                dossiers = (
                    f"### Nhân Vật: {char.name} (Vai Trò: {char.role.value})\n"
                    f"- Động Cơ Sâu Kín: {char.personality.core_motivation}\n"
                    f"- Điểm Yếu Chết Người: {char.personality.fatal_flaw}\n"
                    f"- Ranh Giới Đạo Đức: {char.personality.moral_boundary}\n"
                    f"- Bí Mật Ẩn: {char.personality.hidden_secret or 'Chưa rõ'}\n"
                    f"- Khí Chất & Giọng Điệu: {char.speech.vocabulary_level}\n"
                    f"- Trạng Thái Hiện Tại: Tu Vi={char.status.power_tier}, Sức Khỏe={char.status.health_condition}, Tinh Thần={char.status.mental_state}\n"
                    f"- Trang Bị / Pháp Bảo Đang Giữ: {', '.join(item.name for item in char.inventory) or 'Chưa có'}"
                )
                char_dossiers.append(dossiers)

        characters_context = "\n\n".join(char_dossiers)

        # 5. Extract Story Spine & Causal Timeline
        spine_quest = spine.main_questline if spine else state.logline
        previous_recap = spine.get_immediate_previous_context() if spine else "Phân cảnh mở đầu câu chuyện."
        active_threads = spine.get_active_threads_summary() if spine else "Mâu thuẫn giành giật bảo vật gia tộc."

        # 6. Compile Hard Constraints
        hard_constraints_text = "\n".join(f"[CẤM TUYỆT ĐỐI]: {c}" for c in contract.hard_constraints)

        # 7. Final Structured Prompt Template
        prompt = f"""
======================================================================
MẠCH TRUYỆN CHÍNH & NHIỆM VỤ XUYÊN SUỐT (OVERARCHING QUESTLINE):
- Trọng Tâm Cốt Truyện: {spine_quest}
- Tuyến Mâu Thuẫn Đang Diễn Ra (Plot Threads):
{active_threads}

CHUỖI NHÂN QUẢ TIẾP NỐI TỪ CHƯƠNG TRƯỚC (IMMEDIATE PREVIOUS CONTINUITY):
{previous_recap}
======================================================================

LUẬT BẤT BIẾN CỦA THẾ GIỚI (WORLD CANON LAWS):
{canon_rules_text}

GIỚI HẠN CẢNH GIỚI TU LUYỆN:
{power_tiers_text}

BỐI CẢNH & KHÔNG GIAN CẢNH:
{location_context}

DÀN NHÂN VẬT THAM GIA:
{characters_context}
======================================================================

CHỈ THỊ THI CÔNG PHÂN CẢNH (SCENE EXECUTION DIRECTIVE):
- Scene ID: {contract.scene_id}
- POV Character: {contract.pov_character_id}
- Mục Tiêu Cảnh: {contract.narrative_goal}
- Xung Đột Chính: {contract.conflict_dynamic}
- Kết Quả Giải Quyết: {contract.scene_resolution}
- Nút Thắt Bắt Buộc (Ending Cliffhanger): {contract.cliffhanger_hook}
- Độ Dài Yêu Cầu: Từ {contract.min_word_count} đến {contract.max_word_count} từ tiếng Việt (Mục tiêu: ~{contract.target_word_count} từ).

CHỈ THỊ LIÊN TỤC & KHÔNG LỆCH ĐỀ (STRICT CONTINUITY & FOCUS):
1. BẮT BUỘC tiếp nối liền mạch hệ quả từ chương trước ({previous_recap.splitlines()[0] if previous_recap else ''}).
2. MỌI HÀNH ĐỘNG phải bám sát mục tiêu chính ({spine_quest}). Tuyệt đối KHÔNG đưa vào các tình tiết lan man không phục vụ xung đột hiện tại.
3. TUÂN THỦ NGHIÊM NGẶT độ dài {contract.min_word_count} - {contract.max_word_count} từ.

CÁC ĐIỀU CẤM TUYỆT ĐỐI:
{hard_constraints_text}

NGÔN NGỮ & VĂN PHONG:
Viết 100% bằng tiếng Việt văn học chuẩn mực, áp dụng nguyên tắc 'Show, Don't Tell', mô tả chi tiết biểu cảm, luồng khí tức và lời thoại sắc sảo mang tính đe dọa hoặc mưu mô.
"""
        return prompt.strip()
