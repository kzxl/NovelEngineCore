# Implementation: Universal LLM Adapter Interface

## 1. Overview

The `ILLMAdapter` is the single abstraction boundary between NovelEngineCore and any underlying AI model (OpenAI, Anthropic, Gemini, DeepSeek, Local Ollama).

---

## 2. TypeScript / Node.js Specification

```typescript
export interface PromptMessage {
  role: 'system' | 'user' | 'assistant';
  content: string;
}

export interface GenerationConfig {
  temperature?: number;
  maxTokens?: number;
  topP?: number;
  stopSequences?: string[];
  responseFormat?: 'text' | 'json';
}

export interface ILLMAdapter {
  readonly providerId: string;
  readonly modelName: string;

  /**
   * Generates continuous prose text.
   */
  generateText(
    messages: PromptMessage[],
    config?: GenerationConfig
  ): Promise<string>;

  /**
   * Streams generated tokens in real-time.
   */
  streamText(
    messages: PromptMessage[],
    onToken: (token: string) => void,
    config?: GenerationConfig
  ): Promise<string>;

  /**
   * Enforces structured JSON output matching a specific schema.
   */
  generateStructured<T>(
    messages: PromptMessage[],
    schema: Record<string, unknown>,
    config?: GenerationConfig
  ): Promise<T>;
}
```

---

## 3. Reference Implementation: Multi-Provider Adapter

```typescript
import { ILLMAdapter, PromptMessage, GenerationConfig } from './types';

export class UniversalLLMAdapter implements ILLMAdapter {
  constructor(
    public readonly providerId: string,
    public readonly modelName: string,
    private readonly apiKey: string,
    private readonly baseUrl?: string
  ) {}

  async generateText(messages: PromptMessage[], config?: GenerationConfig): Promise<string> {
    const endpoint = this.baseUrl || this.getDefaultEndpoint();
    const payload = this.transformPayload(messages, config);

    const response = await fetch(endpoint, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${this.apiKey}`
      },
      body: JSON.stringify(payload)
    });

    if (!response.ok) {
      throw new Error(`[${this.providerId}] Request failed with status ${response.status}: ${await response.text()}`);
    }

    const data = await response.json();
    return this.extractResponseText(data);
  }

  private getDefaultEndpoint(): string {
    switch (this.providerId) {
      case 'openai': return 'https://api.openai.com/v1/chat/completions';
      case 'anthropic': return 'https://api.anthropic.com/v1/messages';
      case 'deepseek': return 'https://api.deepseek.com/v1/chat/completions';
      case 'ollama': return 'http://localhost:11434/v1/chat/completions';
      default: return 'https://api.openai.com/v1/chat/completions';
    }
  }

  private transformPayload(messages: PromptMessage[], config?: GenerationConfig): Record<string, unknown> {
    // Transforms universal payload to provider-specific schema
    return {
      model: this.modelName,
      messages: messages,
      temperature: config?.temperature ?? 0.7,
      max_tokens: config?.maxTokens ?? 2048
    };
  }

  private extractResponseText(data: any): string {
    if (data.choices && data.choices[0]?.message?.content) {
      return data.choices[0].message.content;
    }
    if (data.content && Array.isArray(data.content)) {
      return data.content.map((c: any) => c.text).join('');
    }
    throw new Error('Unsupported response payload structure.');
  }

  async streamText(messages: PromptMessage[], onToken: (token: string) => void, config?: GenerationConfig): Promise<string> {
    // Streaming SSE implementation
    throw new Error('StreamText not implemented for mock.');
  }

  async generateStructured<T>(messages: PromptMessage[], schema: Record<string, unknown>, config?: GenerationConfig): Promise<T> {
    const raw = await this.generateText(messages, { ...config, responseFormat: 'json' });
    return JSON.parse(raw) as T;
  }
}
```
