# NovelEngineCore (The Story Director Shell)

A model-agnostic, deterministic orchestration shell and narrative director engine designed to generate consistent, long-form novels and interactive stories using any Large Language Model (LLM).

---

## 📖 Vision & Core Philosophy

Traditional AI text generation tools suffer from **context drift**, **character deformation (OOC)**, and **world-rule hallucinations** when writing long stories. 

**NovelEngineCore** solves this by decoupling the **Director/Rules Engine (The Shell)** from the **Execution Engine (The LLM)**:
- **The Shell acts as the Showrunner / Game Master (DM):** Maintains the Canon Law, tracks character stats/inventories, injects relevant lore on-demand, and prepares deterministic **Scene Contracts**.
- **The LLM acts as the Actor / Drafter:** Focuses purely on prose generation and dialogue execution within strictly enforced boundaries.

---

## 🏗️ Architectural Pillars

```
+-------------------------------------------------------------------------+
|                         APPLICATION LAYER (UI / API)                    |
+-------------------------------------------------------------------------+
                                     |
+-------------------------------------------------------------------------+
|                         NOVEL ENGINE CORE (SHELL)                       |
|  - Story State Machine (Genesis -> Arc -> Beat -> Draft -> Audit)       |
|  - Dynamic Lorebook & Context Budgeter (~2.5k - 4k tokens/call)        |
|  - Scene Contract Generator (Strict objectives, constraints, hooks)     |
|  - Continuity & Lore Auditor (Fact-checker & Self-healing loop)         |
+-------------------------------------------------------------------------+
                                     |
+-------------------------------------------------------------------------+
|                       UNIFIED LLM ADAPTER LAYER                         |
|  - Universal Provider Interface (Streaming, Structured Output, Retries) |
|  - Smart Hybrid Router (Multi-tier model assignment)                    |
+-------------------------------------------------------------------------+
           |                    |                   |               |
     [Claude 3.5]           [GPT-4o]          [Gemini 1.5]     [Local / Ollama]
```

---

## 📂 Documentation Directory

1. **Architecture**
   - [System Architecture Overview](file:///e:/15.%20Other/NovelEngineCore/docs/01-architecture/system-overview.md)
   - [State Machine & Pipeline](file:///e:/15.%20Other/NovelEngineCore/docs/01-architecture/state-machine-pipeline.md)
   - [Hybrid LLM Routing Strategy](file:///e:/15.%20Other/NovelEngineCore/docs/01-architecture/hybrid-llm-routing.md)

2. **Core Specifications**
   - [World Bible & Lore System Spec](file:///e:/15.%20Other/NovelEngineCore/docs/02-specs/world-bible-spec.md)
   - [Character Matrix & OOC Guard Spec](file:///e:/15.%20Other/NovelEngineCore/docs/02-specs/character-matrix-spec.md)
   - [Scene Contract & Beat Sheet Spec](file:///e:/15.%20Other/NovelEngineCore/docs/02-specs/scene-contract-spec.md)

3. **Implementation & Guardrails**
   - [Universal LLM Adapter Interface](file:///e:/15.%20Other/NovelEngineCore/docs/03-implementation/adapter-interface.md)
   - [Self-Healing & Audit Verification](file:///e:/15.%20Other/NovelEngineCore/docs/03-implementation/self-healing-guardrails.md)

---

## 🚀 Key Advantages

- **100% Model Agnostic:** Works with OpenAI, Anthropic, Google Gemini, DeepSeek, OpenRouter, and local models (Ollama, vLLM).
- **Zero Hallucination Leaks:** Strict pre-generation contracts and post-generation rule audits.
- **Budget Optimized:** Micro-context synthesis ensures high performance even on small local 8B models.
