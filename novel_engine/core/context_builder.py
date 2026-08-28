"""Context Builder & Lore Trigger Engine.

Synthesizes laser-focused micro-context (2.5k - 4k tokens) for LLMs,
preventing context pollution and hallucination.
"""

from typing import List, Dict
from novel_engine.core.state import StoryState, SceneContract, CharacterDossier


class ContextBuilder:
    @staticmethod
    def build_scene_prompt(state: StoryState, contract: SceneContract) -> str:
        """Compiles a complete instruction payload for the drafting LLM."""
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
                    f"### Character: {char.name} (Role: {char.role.value})\n"
                    f"- Motivation: {char.personality.core_motivation}\n"
                    f"- Fatal Flaw: {char.personality.fatal_flaw}\n"
                    f"- Speech Style: {char.speech.vocabulary_level}\n"
                    f"- Current Status: Tier {char.status.power_tier}, Health: {char.status.health_condition}, Mental: {char.status.mental_state}\n"
                    f"- Equipped Items: {', '.join(item.name for item in char.inventory) or 'None'}"
                )
                char_dossiers.append(dossiers)

        characters_context = "\n\n".join(char_dossiers)

        # 5. Compile Hard Constraints
        hard_constraints_text = "\n".join(f"[MUST NOT]: {c}" for c in contract.hard_constraints)

        # 6. Final Structured Prompt Template
        prompt = f"""
======================================================================
WORLD CANON & INVARIANT LAWS:
{canon_rules_text}

POWER SCALING LIMITS:
{power_tiers_text}

SETTING & ENVIRONMENT:
{location_context}

CHARACTERS IN SCENE:
{characters_context}
======================================================================

SCENE EXECUTION DIRECTIVE:
- Scene ID: {contract.scene_id}
- POV Character: {contract.pov_character_id}
- Narrative Goal: {contract.narrative_goal}
- Central Conflict: {contract.conflict_dynamic}
- Expected Resolution: {contract.scene_resolution}
- Mandatory Ending Hook (Cliffhanger): {contract.cliffhanger_hook}
- Target Word Count: ~{contract.target_word_count} words

STRICT NEGATIVE CONSTRAINTS (VIOLATIONS WILL BE REJECTED):
{hard_constraints_text}

LANGUAGE DIRECTIVE:
Write strictly in Vietnamese (Tiếng Việt) using rich, expressive novel prose and natural dialogue.

INSTRUCTIONS:
Write vivid, immersive narrative prose following 'Show, Don't Tell'. 
Dialogue must strictly reflect character status and vocabulary style. 
Never break the negative constraints.
"""
        return prompt.strip()
