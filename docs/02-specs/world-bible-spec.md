# Specification: World Bible & Lorebook System

## 1. Purpose

The **World Bible** represents the immutable constitution and physical/cultural laws of the story universe. It establishes canon constraints that the LLM cannot contradict.

---

## 2. World Bible JSON Schema

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "WorldBible",
  "type": "object",
  "required": ["world_id", "title", "genre", "cosmology", "power_system", "canon_rules", "factions", "locations"],
  "properties": {
    "world_id": { "type": "string" },
    "title": { "type": "string" },
    "genre": { "type": "string", "enum": ["Xianxia", "HighFantasy", "SciFi", "Cyberpunk", "Mystery", "Romance", "Apocalypse"] },
    "era_setting": { "type": "string", "description": "e.g., Medieval, Era of Star Exploration, Post-apocalyptic 2099" },
    "cosmology": {
      "type": "object",
      "properties": {
        "origin_myth": { "type": "string" },
        "planes_or_realms": { "type": "array", "items": { "type": "string" } }
      }
    },
    "power_system": {
      "type": "object",
      "properties": {
        "energy_source": { "type": "string", "description": "e.g., Spiritual Qi, Mana, Cyberware Overclock, Psychic Waves" },
        "tier_progression": {
          "type": "array",
          "items": {
            "type": "object",
            "properties": {
              "rank": { "type": "integer" },
              "name": { "type": "string" },
              "description": { "type": "string" },
              "hard_limits": { "type": "string", "description": "What this tier CANNOT do under any circumstances." }
            },
            "required": ["rank", "name", "hard_limits"]
          }
        }
      }
    },
    "canon_rules": {
      "type": "array",
      "items": { "type": "string" },
      "description": "Hard invariant physical and logic laws that cannot be broken (e.g., 'Dead characters cannot be revived', 'Teleportation causes severe mana drain')."
    },
    "factions": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "faction_id": { "type": "string" },
          "name": { "type": "string" },
          "alignment": { "type": "string" },
          "core_doctrine": { "type": "string" },
          "relations": { "type": "object", "additionalProperties": { "type": "string" } }
        },
        "required": ["faction_id", "name", "core_doctrine"]
      }
    },
    "locations": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "location_id": { "type": "string" },
          "name": { "type": "string" },
          "climate_and_vibe": { "type": "string" },
          "key_hazards": { "type": "string" },
          "connected_locations": { "type": "array", "items": { "type": "string" } }
        },
        "required": ["location_id", "name"]
      }
    }
  }
}
```

---

## 3. Dynamic Lorebook Triggering Engine

Instead of injecting the full World Bible, the engine maintains a dictionary of **Lore Triggers**.

```
[Keywords Match in Scene Setup] 
      ├── Location Trigger: "Dark Forest" ──> Injects "Hazards: poisonous mist, blind beasts"
      └── Item Trigger: "Soul Jade"       ──> Injects "Rule: Shatters if holder dies"
```

### Context Budget Impact
- Full World Bible: ~8,000 – 15,000 tokens (causes distraction and high cost).
- Dynamic Triggered Lore Slice: **~300 – 600 tokens** (laser-focused context for the model).
