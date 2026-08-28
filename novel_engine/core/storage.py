"""Storage & File Export Manager for NovelEngineCore.

Saves world state, character dossiers, novel manuscript, and comic storyboards
to disk automatically in Markdown and JSON formats.
"""

import os
import json
from typing import Optional
from novel_engine.core.state import StoryState, SceneDraft, ComicStoryboard


class StoryStorageManager:
    """Manages persistent disk storage and multi-format exports for stories."""

    def __init__(self, base_output_dir: str = "output/stories"):
        self.base_output_dir = base_output_dir
        os.makedirs(self.base_output_dir, exist_ok=True)

    def get_story_dir(self, story_id: str) -> str:
        story_dir = os.path.join(self.base_output_dir, story_id)
        os.makedirs(story_dir, exist_ok=True)
        os.makedirs(os.path.join(story_dir, "chapters"), exist_ok=True)
        os.makedirs(os.path.join(story_dir, "comic_scripts"), exist_ok=True)
        return story_dir

    def save_world_and_characters(self, state: StoryState) -> str:
        """Saves world bible and character matrix to JSON and Markdown summary."""
        story_dir = self.get_story_dir(state.story_id)

        # 1. Save JSON manifests
        world_json_path = os.path.join(story_dir, "world_bible.json")
        with open(world_json_path, "w", encoding="utf-8") as f:
            f.write(state.world_bible.model_dump_json(indent=2))

        chars_json_path = os.path.join(story_dir, "characters.json")
        with open(chars_json_path, "w", encoding="utf-8") as f:
            chars_data = [c.model_dump() for c in state.characters.values()]
            json.dump(chars_data, f, ensure_ascii=False, indent=2)

        # 2. Save Markdown World Overview
        world_md_path = os.path.join(story_dir, "WORLD_LORE.md")
        with open(world_md_path, "w", encoding="utf-8") as f:
            f.write(f"# {state.world_bible.title}\n\n")
            f.write(f"**Thể loại:** {state.genre} | **Kỷ nguyên:** {state.world_bible.era_setting}\n\n")
            f.write(f"**Hệ thống năng lượng:** {state.world_bible.energy_source}\n\n")
            f.write("## 1. Cảnh Giới Tu Luyện (Power Progression)\n")
            for t in state.world_bible.power_progression:
                f.write(f"- **Rank {t.rank} [{t.name}]:** {t.description} *(Giới hạn: {t.hard_limits})*\n")
            f.write("\n## 2. Luật Bất Biến (Canon Laws)\n")
            for r in state.world_bible.canon_rules:
                f.write(f"- ⚡ {r}\n")
            f.write("\n## 3. Môn Phái & Thế Lực\n")
            for fac in state.world_bible.factions:
                f.write(f"- **{fac.name}** ({fac.alignment}): {fac.core_doctrine}\n")
            f.write("\n## 4. Địa Danh & Cấm Địa\n")
            for loc in state.world_bible.locations:
                f.write(f"- **{loc.name}:** {loc.climate_and_vibe} *(Hiểm họa: {loc.key_hazards})*\n")

        return story_dir

    def save_plot_events(self, story_id: str, events: list) -> str:
        """Saves dynamic plot events to disk."""
        story_dir = self.get_story_dir(story_id)
        events_json_path = os.path.join(story_dir, "plot_events.json")
        try:
            with open(events_json_path, "w", encoding="utf-8") as f:
                events_data = [e.model_dump() if hasattr(e, "model_dump") else e for e in events]
                json.dump(events_data, f, ensure_ascii=False, indent=2)
        except Exception:
            pass
        return events_json_path

    def save_story_state(self, state: StoryState) -> str:
        """Saves full story state manifest."""
        self.save_world_and_characters(state)
        story_dir = self.get_story_dir(state.story_id)
        state_json_path = os.path.join(story_dir, "story_manifest.json")
        try:
            with open(state_json_path, "w", encoding="utf-8") as f:
                f.write(state.model_dump_json(indent=2))
        except Exception:
            pass
        return story_dir

    def save_scene_draft(self, state: StoryState, draft: SceneDraft) -> dict:
        """Saves individual scene draft, appends to novel manuscript, and saves comic script."""
        story_dir = self.get_story_dir(state.story_id)
        scene_id = draft.scene_id.lower()

        # 1. Save Scene Structured JSON & Markdown File
        scene_json_path = os.path.join(story_dir, "chapters", f"{scene_id}.json")
        try:
            with open(scene_json_path, "w", encoding="utf-8") as f:
                f.write(draft.model_dump_json(indent=2))
        except Exception:
            pass

        scene_file_path = os.path.join(story_dir, "chapters", f"{scene_id}.md")
        with open(scene_file_path, "w", encoding="utf-8") as f:
            f.write(f"# Phân Cảnh: {draft.scene_id}\n\n")
            f.write(f"- **Địa điểm:** {draft.contract.location} ({draft.contract.time_of_day})\n")
            f.write(f"- **Nhân vật:** {', '.join(draft.contract.present_characters)}\n")
            f.write(f"- **Mục tiêu:** {draft.contract.narrative_goal}\n")
            f.write(f"- **Nút thắt:** {draft.contract.cliffhanger_hook}\n\n")
            f.write("---\n\n")
            f.write("### Nội Dung Bản Thảo:\n\n")
            f.write(draft.prose_content + "\n")

        # 2. Append to Master Novel Manuscript (novel_manuscript.md)
        manuscript_path = os.path.join(story_dir, "novel_manuscript.md")
        is_new = not os.path.exists(manuscript_path)
        with open(manuscript_path, "a", encoding="utf-8") as f:
            if is_new:
                f.write(f"# {state.title}\n\n")
                f.write(f"*{state.logline}*\n\n")
                f.write("======================================================================\n\n")
            f.write(f"\n## [{draft.scene_id}] {draft.contract.location}\n\n")
            f.write(draft.prose_content + "\n\n")
            f.write("----------------------------------------------------------------------\n")

        # 3. Save Comic Storyboard Script (if available)
        comic_file_path = None
        if draft.comic_storyboard and draft.comic_storyboard.panels:
            comic_file_path = os.path.join(story_dir, "comic_scripts", f"{scene_id}_comic.md")
            with open(comic_file_path, "w", encoding="utf-8") as f:
                f.write(f"# Kịch Bản Phân Cảnh Truyện Tranh: {draft.scene_id}\n\n")
                f.write(f"**Layout:** {draft.comic_storyboard.page_layout_type}\n\n")
                for p in draft.comic_storyboard.panels:
                    f.write(f"### [PANEL #{p.panel_index}] - {p.camera_angle.value}\n")
                    f.write(f"- **Mô tả khung hình:** {p.visual_composition}\n")
                    if p.dialogue:
                        dialogue_str = " | ".join(f"{k}: \"{v}\"" for d in p.dialogue for k, v in d.items())
                        f.write(f"- **Bóng thoại:** {dialogue_str}\n")
                    if p.sound_effects_sfx:
                        f.write(f"- **Hiệu ứng âm thanh (SFX):** {p.sound_effects_sfx}\n")
                    f.write(f"- **AI Image Prompt (Flux/SD):**\n```\n{p.image_prompt_for_ai}\n```\n\n")

        return {
            "story_dir": story_dir,
            "scene_file": scene_file_path,
            "manuscript_file": manuscript_path,
            "comic_file": comic_file_path
        }
