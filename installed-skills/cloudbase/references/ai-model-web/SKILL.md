---
name: ai-model-web
description: Use this skill when developing browser/Web applications (React/Vue/Angular, static websites, SPAs) that need AI capabilities. Features text generation (generateText) and streaming (streamText) via @cloudbase/js-sdk. Built-in models include Hunyuan (hunyuan-2.0-instruct-20251111 recommended) and DeepSeek (deepseek-v3.2 recommended). NOT for Node.js backend (use ai-model-nodejs), WeChat Mini Program (use ai-model-wechat), or image generation (Node SDK only).
alwaysApply: false
---

## When to use this skill

Use this skill for **calling AI models in browser/Web applications** using `@cloudbase/js-sdk`.

**Use it when you need to:**

- Integrate AI text generation in a frontend Web app
- Stream AI responses for better user experience
- Call Hunyuan or DeepSeek models from browser

**Do NOT use for:**

- Node.js backend or cloud functions → use `ai-model-nodejs` skill
- WeChat Mini Program → use `ai-model-wechat` skill
- Image generation → use `ai-model-nodejs` skill (Node SDK only)
- HTTP API integration → use `http-api` skill

---

## Available Providers and Models

CloudBase provides these built-in providers and models:

| Provider | Models | Recommended |
|----------|--------|-------------|
| `hunyuan-exp` | `hunyuan-turbos-latest`, `hunyuan-t1-latest`, `hunyuan-2.0-thinking-20251109`, `hunyuan-2.0-instruct-20251111` | ✅ `hunyuan-2.0-instruct-20251111` |
| `deepseek` | `deepseek-r1-0528`, `deepseek-v3-0324`, `deepseek-v3.2` | ✅ `deepseek-v3.2` |

---

## Installation

```bash
npm install @cloudbase/js-sdk
```

## Initialization

```js
import cloudbase from "@cloudbase/js-sdk";

const app = cloudbase.init({
  env: "<YOUR_ENV_ID>",
  accessKey: "<YOUR_PUBLISHABLE_KEY>"  // Get from CloudBase console
});

const auth = app.auth();
await auth.signInAnonymously();

const ai = app.ai();
```

**Important notes:**

- Always use synchronous initialization with top-level import
- User must be authenticated before using AI features
- Get `accessKey` from CloudBase console

---

## generateText() - Non-streaming

```js
const model = ai.createModel("hunyuan-exp");

const result = await model.generateText({
  model: "hunyuan-2.0-instruct-20251111",  // Recommended model
  messages: [{ role: "user", content: "你好，请你介绍一下李白" }],
});

console.log(result.text);           // Generated text string
console.log(result.usage);          // { prompt_tokens, completion_tokens, total_tokens }
console.log(result.messages);       // Full message history
console.log(result.rawResponses);   // Raw model responses
```

---

## streamText() - Streaming

```js
const model = ai.createModel("hunyuan-exp");

const res = await model.streamText({
  model: "hunyuan-2.0-instruct-20251111",  // Recommended model
  messages: [{ role: "user", content: "你好，请你介绍一下李白" }],
});

// Option 1: Iterate text stream (recommended)
for await (let text of res.textStream) {
  console.log(text);  // Incremental text chunks
}

// Option 2: Iterate data stream for full response data
for await (let data of res.dataStream) {
  console.log(data);  // Full response chunk with metadata
}

// Option 3: Get final results
const messages = await res.messages;  // Full message history
const usage = await res.usage;        // Token usage
```

---

## Type Definitions

```ts
interface BaseChatModelInput {
  model: string;                        // Required: model name
  messages: Array<ChatModelMessage>;    // Required: message array
  temperature?: number;                 // Optional: sampling temperature
  topP?: number;                        // Optional: nucleus sampling
}

type ChatModelMessage =
  | { role: "user"; content: string }
  | { role: "system"; content: string }
  | { role: "assistant"; content: string };

interface GenerateTextResult {
  text: string;                         // Generated text
  messages: Array<ChatModelMessage>;    // Full message history
  usage: Usage;                         // Token usage
  rawResponses: Array<unknown>;         // Raw model responses
  error?: unknown;                      // Error if any
}

interface StreamTextResult {
  textStream: AsyncIterable<string>;    // Incremental text stream
  dataStream: AsyncIterable<DataChunk>; // Full data stream
  messages: Promise<ChatModelMessage[]>;// Final message history
  usage: Promise<Usage>;                // Final token usage
  error?: unknown;                      // Error if any
}

interface Usage {
  prompt_tokens: number;
  completion_tokens: number;
  total_tokens: number;
}
```

---

## Best Practices

1. **Use streaming for long responses** - Better user experience
2. **Handle errors gracefully** - Wrap AI calls in try/catch
3. **Keep accessKey secure** - Use publishable key, not secret key
4. **Initialize early** - Initialize SDK in app entry point
5. **Ensure authentication** - User must be signed in before AI calls

