# Specification: Scene Contract & Beat Sheet

## 1. Purpose

The **Scene Contract** is the definitive task specification passed to the LLM for drafting. It transforms generic storytelling into micro-level scene execution with clear goals, conflict dynamics, and strict negative constraints.

---

## 2. Scene Contract Schema

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "SceneContract",
  "type": "object",
  "required": [
    "scene_id",
    "chapter_id",
    "scene_index",
    "location",
    "pov_character_id",
    "present_characters",
    "target_word_count",
    "narrative_goal",
    "conflict_dynamic",
    "scene_resolution",
    "cliffhanger_hook",
    "hard_constraints"
  ],
  "properties": {
    "scene_id": { "type": "string" },
    "chapter_id": { "type": "string" },
    "scene_index": { "type": "integer" },
    "location": { "type": "string" },
    "time_of_day": { "type": "string" },
    "pov_character_id": { "type": "string" },
    "present_characters": { "type": "array", "items": { "type": "string" } },
    "target_word_count": { "type": "integer", "default": 1200 },
    
    "narrative_goal": {
      "type": "string",
      "description": "What the POV character wants to achieve in this scene."
    },
    "conflict_dynamic": {
      "type": "string",
      "description": "The obstacle or antagonist resisting the goal."
    },
    "scene_resolution": {
      "type": "string",
      "description": "How the scene concludes (Yes, but... / No, and furthermore...)."
    },
    "cliffhanger_hook": {
      "type": "string",
      "description": "The unanswered question, arrival, or shock ending the scene."
    },

    "hard_constraints": {
      "type": "array",
      "items": { "type": "string" },
      "description": "Strict negative rules (what MUST NOT happen in this scene)."
    },

    "state_mutations_expected": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "target_entity": { "type": "string" },
          "mutation_type": { "type": "string", "enum": ["HP_LOSS", "ITEM_ACQUIRED", "ITEM_LOST", "RELATION_CHANGE", "SECRET_REVEALED"] },
          "description": { "type": "string" }
        }
      }
    }
  }
}
```

---

## 3. Practical Example: Scene Contract Payload

```json
{
  "scene_id": "VOL01_CH04_SC02",
  "chapter_id": "CH04",
  "scene_index": 2,
  "location": "Lâm Gia - Hội Nghị Đường",
  "time_of_day": "Hoàng hôn",
  "pov_character_id": "char_lin_feng",
  "present_characters": ["char_lin_feng", "char_elder_zhao", "char_lin_yan"],
  "target_word_count": 1500,
  "narrative_goal": "Lâm Phong trả đủ 500 linh thạch để chuộc lại di vật của mẫu thân.",
  "conflict_dynamic": "Đại Trưởng Lão Triệu cố ý đòi tăng lên 1,000 linh thạch và công khai sỉ nhục tư chất phế vật của Lâm Phong.",
  "scene_resolution": "Lâm Phong dùng linh thạch thượng phẩm ném thẳng vào mặt đối phương, lấy lại di vật nhưng làm bại lộ việc chàng có cơ duyên bí mật.",
  "cliffhanger_hook": "Triệu trưởng lão nhận ra luồng linh khí cổ xưa trên ngọc bội và ra lệnh phong tỏa toàn bộ cửa ra vào.",
  "hard_constraints": [
    "Lâm Phong chưa đạt cảnh giới Trúc Cơ, TUYỆT ĐỐI KHÔNG được giết Triệu trưởng lão trong cảnh này.",
    "Không được để lộ danh tính của Dược Lão trong chiếc nhẫn.",
    "Tập trung tả ánh mắt sắc lạnh và nhịp thở dồn dập (Show, don't tell)."
  ],
  "state_mutations_expected": [
    {
      "target_entity": "char_lin_feng",
      "mutation_type": "ITEM_LOST",
      "description": "Mất 5 viên linh thạch thượng phẩm."
    },
    {
      "target_entity": "char_lin_feng",
      "mutation_type": "ITEM_ACQUIRED",
      "description": "Nhận lại Vân Hà Ngọc Bội."
    },
    {
      "target_entity": "char_elder_zhao",
      "mutation_type": "RELATION_CHANGE",
      "description": "Mức độ căm thù tăng từ -40 lên -85 (Sát ý)."
    }
  ]
}
```
