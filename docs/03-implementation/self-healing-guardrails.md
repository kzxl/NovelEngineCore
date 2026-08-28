# Implementation: Self-Healing & Continuity Guardrails

## 1. Overview

Because LLMs can intermittently fail to follow negative constraints, hallucinate, or return corrupted JSON, NovelEngineCore applies a dual-stage safety net:
1. **Pre-commit Schema & JSON Repair (Self-Healing)**
2. **Post-Draft Canon Rule Auditor**

---

## 2. Self-Healing JSON Parser

When calling models that don't have native strict structured outputs (e.g., small local models), raw outputs often contain backtick markdown fences (` ```json `), trailing commas, or conversational preambles.

```typescript
export class SelfHealingJSONParser {
  /**
   * Extracts and parses valid JSON from noisy LLM output.
   */
  static parse<T>(rawText: string): T {
    try {
      // 1. First attempt: Direct parse
      return JSON.parse(rawText) as T;
    } catch {
      // 2. Second attempt: Extract content between markdown fences or first/last braces
      const cleaned = this.extractJSONBlock(rawText);
      try {
        return JSON.parse(cleaned) as T;
      } catch (err) {
        // 3. Third attempt: Common syntax repairs (trailing commas, quotes)
        const repaired = this.repairCommonSyntaxErrors(cleaned);
        return JSON.parse(repaired) as T;
      }
    }
  }

  private static extractJSONBlock(text: string): string {
    const fenceMatch = text.match(/```(?:json)?\s*([\s\S]*?)\s*```/i);
    if (fenceMatch) return fenceMatch[1].trim();

    const firstBrace = text.indexOf('{');
    const lastBrace = text.lastIndexOf('}');
    if (firstBrace !== -1 && lastBrace !== -1 && lastBrace > firstBrace) {
      return text.substring(firstBrace, lastBrace + 1).trim();
    }
    return text.trim();
  }

  private static repairCommonSyntaxErrors(jsonStr: string): string {
    return jsonStr
      .replace(/,\s*([}\]])/g, '$1') // Remove trailing commas
      .replace(/([{,]\s*)([a-zA-Z0-9_]+)\s*:/g, '$1"$2":'); // Quote unquoted keys
  }
}
```

---

## 3. Post-Draft Canon Rule Auditor

The Auditor runs a fast evaluation pass using a low-cost model (e.g., Gemini 1.5 Flash / DeepSeek) to audit the draft prose against the `SceneContract` and `WorldBible`.

```typescript
export interface AuditResult {
  passed: boolean;
  violations: Array<{
    ruleId: string;
    description: string;
    offendingExcerpt: string;
    fixSuggestion: string;
  }>;
}

export class ContinuityAuditor {
  constructor(private adapter: ILLMAdapter) {}

  async auditScene(prose: string, contract: SceneContract, worldBible: WorldBible): Promise<AuditResult> {
    const auditPrompt: PromptMessage[] = [
      {
        role: 'system',
        content: `You are a strict Literary Continuity Auditor. Inspect the draft prose against the Hard Constraints and World Canon. Return JSON matching the AuditResult schema.`
      },
      {
        role: 'user',
        content: `
        CANON RULES:
        ${worldBible.canon_rules.join('\n')}

        SCENE HARD CONSTRAINTS:
        ${contract.hard_constraints.join('\n')}

        DRAFT PROSE:
        ${prose}
        `
      }
    ];

    return await this.adapter.generateStructured<AuditResult>(auditPrompt, {});
  }
}
```
