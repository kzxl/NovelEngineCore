# Specification: Character Matrix & OOC Prevention

## 1. Purpose

The **Character Matrix** tracks static profiles and dynamic mutable states for all characters. It prevents **OOC (Out of Character)** behavior, speech pattern homogenization, and inventory/injury hallucinations.

---

## 2. Character Schema Specification

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "CharacterDossier",
  "type": "object",
  "required": [
    "character_id",
    "name",
    "role",
    "personality_traits",
    "speech_style",
    "current_status",
    "inventory",
    "relationship_matrix"
  ],
  "properties": {
    "character_id": { "type": "string" },
    "name": { "type": "string" },
    "aliases": { "type": "array", "items": { "type": "string" } },
    "role": { "type": "string", "enum": ["Protagonist", "Antagonist", "Deuteragonist", "Mentor", "Sidekick", "MinorNPC"] },
    
    "personality_traits": {
      "type": "object",
      "properties": {
        "core_motivation": { "type": "string", "description": "What drives their actions." },
        "fatal_flaw": { "type": "string", "description": "Weakness that leads to mistakes (e.g., hubris, paranoia)." },
        "moral_boundary": { "type": "string", "description": "Line they will never cross." },
        "hidden_secret": { "type": "string", "description": "Information they protect from others." }
      },
      "required": ["core_motivation", "fatal_flaw", "moral_boundary"]
    },

    "speech_style": {
      "type": "object",
      "properties": {
        "vocabulary_level": { "type": "string", "enum": ["Archaic/Poetic", "Coarse/Street", "Scholarly", "Terse/Monosyllabic"] },
        "catchphrases": { "type": "array", "items": { "type": "string" } },
        "address_forms": {
          "type": "object",
          "description": "How they refer to self and others (e.g., 'Bản tọa', 'Tại hạ', 'Lão phu')",
          "additionalProperties": { "type": "string" }
        }
      },
      "required": ["vocabulary_level"]
    },

    "current_status": {
      "type": "object",
      "properties": {
        "power_tier": { "type": "string" },
        "health_condition": { "type": "string", "description": "e.g., 'Right arm broken', 'Poisoned with Bone-Rot', 'Peak healthy'" },
        "mental_state": { "type": "string", "description": "e.g., 'Enraged', 'Despairing', 'Calm and calculating'" },
        "current_location_id": { "type": "string" }
      },
      "required": ["power_tier", "health_condition"]
    },

    "inventory": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "item_id": { "type": "string" },
          "name": { "type": "string" },
          "quantity": { "type": "integer" },
          "state": { "type": "string", "description": "e.g., 'Equipped', 'Hidden in ring', 'Depleted'" }
        },
        "required": ["item_id", "name"]
      }
    },

    "relationship_matrix": {
      "type": "object",
      "description": "Target character ID -> Relationship dynamics and trust score (-100 to +100)",
      "additionalProperties": {
        "type": "object",
        "properties": {
          "sentiment": { "type": "string" },
          "trust_level": { "type": "integer", "minimum": -100, "maximum": 100 },
          "shared_history": { "type": "string" }
        }
      }
    }
  }
}
```

---

## 3. OOC Guardrails & Enforcement

Before every scene is drafted, the Shell generates negative constraints based on the `CharacterDossier`:

```markdown
### Character Guardrails for [Lin Feng]:
- Health: Right shoulder pierced by arrow. CANNOT wield heavy two-handed weapons in this scene.
- Secret: Possesses Ancient Ring. CANNOT mention or reveal the ring to Elder Zhao.
- Tone: Terse and polite on the surface, but strictly guarded.
```
