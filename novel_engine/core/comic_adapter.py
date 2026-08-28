"""Comic & Manga Storyboard Adapter.

Translates drafted prose and scene contracts into visual comic panels,
complete with camera angles, speech bubbles, and image generation prompts.
"""

from typing import Dict
from novel_engine.core.state import (
    SceneContract,
    ComicStoryboard,
    ComicPanel,
    CameraAngle,
    CharacterDossier
)


class ComicStoryboardAdapter:
    @staticmethod
    def build_storyboard_prompt(
        prose: str,
        contract: SceneContract,
        characters: Dict[str, CharacterDossier]
    ) -> str:
        """Builds an LLM prompt to transform prose into a 4-8 panel comic script."""
        visual_tags_summary = []
        for char_id in contract.present_characters:
            char = characters.get(char_id)
            if char and char.visual_tags:
                tags = ", ".join(char.visual_tags)
                visual_tags_summary.append(f"- Character '{char.name}': Visual Tags -> [{tags}]")

        char_visuals_text = "\n".join(visual_tags_summary) or "No specific visual tags provided."

        return f"""
You are a veteran Manga/Webtoon Storyboard Artist and Art Director.
Transform the following novel scene into a dynamic 4 to 6 panel Comic Storyboard.

SCENE CONFLICT & RESOLUTION:
- Conflict: {contract.conflict_dynamic}
- Ending Hook: {contract.cliffhanger_hook}

CHARACTER VISUAL IDENTIFIERS (Must incorporate into image prompts):
{char_visuals_text}

PROSE TEXT:
{prose}

INSTRUCTIONS:
1. Divide the scene into sequential visual panels.
2. Select appropriate camera angles (Wide Shot, Close-up, Low Angle, Dutch Angle).
3. Extract concise dialogue for speech bubbles.
4. Add impact sound effects (SFX) where appropriate.
5. Create a standalone, high-quality Image Generation Prompt (for Flux/Stable Diffusion/Midjourney) for each panel. Include character visual tags, lighting, and composition.

Output must conform to ComicStoryboard schema.
"""
