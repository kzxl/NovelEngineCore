"""Context Builder & Lore Trigger Engine.

Synthesizes laser-focused micro-context (2.5k - 4k tokens) for LLMs in clear Technical English,
with strict output language enforcement to prevent plot drift, hallucination, and context confusion.
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
        """Compiles a complete instruction payload in English ensuring 100% causal continuity across chapters."""
        world = state.world_bible
        
        # 1. Extract Canon Rules
        canon_rules_text = "\n".join(f"- {rule}" for rule in world.canon_rules) if world.canon_rules else "No special physical laws specified."
        
        # 2. Extract Power System context
        power_tiers_text = "\n".join(
            f"- Rank {tier.rank} [{tier.name}]: Limit -> {tier.hard_limits}"
            for tier in world.power_progression
        ) if world.power_progression else "Standard progression system."

        # 3. Dynamic Lore Injection based on location & scene
        location_info = next(
            (loc for loc in world.locations if loc.name.lower() in contract.location.lower()),
            None
        )
        location_context = (
            f"Location: {location_info.name} | Atmosphere/Vibe: {location_info.climate_and_vibe} | Key Hazards: {location_info.key_hazards}"
            if location_info else f"Location: {contract.location} (Time: {contract.time_of_day})"
        )

        # 4. Extract Present Characters & OOC Guardrails
        char_dossiers: List[str] = []
        for char_id in contract.present_characters:
            char = state.characters.get(char_id)
            if char:
                dossiers = (
                    f"### Character: {char.name} (Role: {char.role.value})\n"
                    f"- Core Motivation: {char.personality.core_motivation}\n"
                    f"- Fatal Flaw: {char.personality.fatal_flaw}\n"
                    f"- Moral Boundary: {char.personality.moral_boundary}\n"
                    f"- Hidden Secret: {char.personality.hidden_secret or 'None'}\n"
                    f"- Speech Tone: {char.speech.vocabulary_level}\n"
                    f"- Current Status: Tier={char.status.power_tier}, Health={char.status.health_condition}, Mental State={char.status.mental_state}\n"
                    f"- Inventory & Artifacts: {', '.join(item.name for item in char.inventory) or 'None'}"
                )
                char_dossiers.append(dossiers)

        characters_context = "\n\n".join(char_dossiers) if char_dossiers else "Protagonist is navigating the scene."

        # 5. Extract Story Spine & Causal Timeline
        spine_quest = spine.main_questline if spine else state.logline
        previous_recap = spine.get_immediate_previous_context() if spine else "Opening scene of the story arc."
        active_threads = spine.get_active_threads_summary() if spine else "Core survival and clan rivalry conflict."

        # 6. Compile Hard Constraints
        hard_constraints_text = "\n".join(f"[STRICT CONSTRAINT]: {c}" for c in contract.hard_constraints) if contract.hard_constraints else "Follow realistic physical consequences."

        lang = contract.language or (state.language if state else "Tiếng Việt")

        # 7. Final English Structured Prompt Template
        prompt = f"""
======================================================================
[OVERARCHING QUESTLINE & NARRATIVE SPINE]
- Master Story Goal: {spine_quest}
- Active Plot Threads:
{active_threads}

[IMMEDIATE PREVIOUS CONTINUITY & CAUSAL CHAIN]
{previous_recap}
======================================================================

[IMMUTABLE WORLD CANON LAWS]
{canon_rules_text}

[POWER PROGRESSION & TIER LIMITS]
{power_tiers_text}

[SCENE SETTING & LOCATION ATMOSPHERE]
{location_context}

[PARTICIPATING CHARACTERS & PSYCHOLOGICAL PROFILES]
{characters_context}
======================================================================

[SCENE EXECUTION DIRECTIVES]
- Scene ID: {contract.scene_id}
- POV Character: {contract.pov_character_id}
- Scene Narrative Goal: {contract.narrative_goal}
- Central Conflict Dynamic: {contract.conflict_dynamic}
- Scene Resolution Outcome: {contract.scene_resolution}
- Mandatory Ending Cliffhanger: {contract.cliffhanger_hook}
- Required Word Count Range: {contract.min_word_count} - {contract.max_word_count} words (Target: ~{contract.target_word_count} words).

[MANDATORY TARGET OUTPUT LANGUAGE]
>>> TARGET LANGUAGE: {lang} <<<
All generated story text (prose_content), dialogues, descriptions, titles, and JSON text fields MUST be written exclusively in {lang}.

[STRICT CONTINUITY & FOCUS DIRECTIVES]
1. CONTINUITY: You MUST organically continue the immediate consequences and emotional stakes from the previous scene.
2. NO PLOT DRIFT: Every paragraph and dialogue line must serve the active conflict ({contract.conflict_dynamic}).
3. WORD COUNT DISCIPLINE: Strictly maintain the {contract.min_word_count} to {contract.max_word_count} word limit. Do not truncate early or ramble endlessly.
4. SHOW, DON'T TELL: Deliver visceral combat, atmospheric tension, sharp psychological exchanges, and high-stakes pacing.

[ABSOLUTE NEGATIVE CONSTRAINTS]
{hard_constraints_text}
"""
        return prompt.strip()
