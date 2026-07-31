---
name: ai-model-wechat
description: Use this skill when developing WeChat Mini Programs (小程序, 企业微信小程序, wx.cloud-based apps) that need AI capabilities. Features text generation (generateText) and streaming (streamText) with callback support (onText, onEvent, onFinish) via wx.cloud.extend.AI. Built-in models include Hunyuan (hunyuan-2.0-instruct-20251111 recommended) and DeepSeek (deepseek-v3.2 recommended). API differs from JS/Node SDK - streamText requires data wrapper, generateText returns raw response. NOT for browser/Web apps (use ai-model-web), Node.js backend (use ai-model-nodejs), or image generation (not supported).
alwaysApply: false
---

## When to use this skill

Use this skill for **calling AI models in WeChat Mini Program** using `wx.cloud.extend.AI`.

**Use it when you need to:**

- Integrate AI text generation in a Mini Program
- Stream AI responses with callback support
- Call Hunyuan models from WeChat environment

**Do NOT use for:**

- Browser/Web apps → use `ai-model-web` skill
- Node.js backend or cloud functions → use `ai-model-nodejs` skill
- Image generation → use `ai-model-nodejs` skill (not available in Mini Program)
- HTTP API integration → use `http-api` skill

---

## Available Providers and Models

CloudBase provides these built-in providers and models:

| Provider | Models | Recommended |
|----------|--------|-------------|
| `hunyuan-exp` | `hunyuan-turbos-latest`, `hunyuan-t1-latest`, `hunyuan-2.0-thinking-20251109`, `hunyuan-2.0-instruct-20251111` | ✅ `hunyuan-2.0-instruct-20251111` |
| `deepseek` | `deepseek-r1-0528`, `deepseek-v3-0324`, `deepseek-v3.2` | ✅ `deepseek-v3.2` |

---

## Prerequisites

- WeChat base library **3.7.1+**
- No extra SDK installation needed

---

## Initialization

```js
// app.js
App({
  onLaunch: function() {
    wx.cloud.init({ env: "<YOUR_ENV_ID>" });
  }
})
```

---

## generateText() - Non-streaming

⚠️ **Different from JS/Node SDK:** Return value is raw model response.

```js
const model = wx.cloud.extend.AI.createModel("hunyuan-exp");

const res = await model.generateText({
  model: "hunyuan-2.0-instruct-20251111",  // Recommended model
  messages: [{ role: "user", content: "你好" }],
});

// ⚠️ Return value is RAW model response, NOT wrapped like JS/Node SDK
console.log(res.choices[0].message.content);  // Access via choices array
console.log(res.usage);                        // Token usage
```

---

## streamText() - Streaming

⚠️ **Different from JS/Node SDK:** Must wrap parameters in `data` object, supports callbacks.

```js
const model = wx.cloud.extend.AI.createModel("hunyuan-exp");

// ⚠️ Parameters MUST be wrapped in `data` object
const res = await model.streamText({
  data: {                              // ⚠️ Required wrapper
    model: "hunyuan-2.0-instruct-20251111",  // Recommended model
    messages: [{ role: "user", content: "hi" }]
  },
  onText: (text) => {                  // Optional: incremental text callback
    console.log("New text:", text);
  },
  onEvent: ({ data }) => {             // Optional: raw event callback
    console.log("Event:", data);
  },
  onFinish: (fullText) => {            // Optional: completion callback
    console.log("Done:", fullText);
  }
});

// Async iteration also available
for await (let str of res.textStream) {
  console.log(str);
}

// Check for completion with eventStream
for await (let event of res.eventStream) {
  console.log(event);
  if (event.data === "[DONE]") {       // ⚠️ Check for [DONE] to stop
    break;
  }
}
```

---

## API Comparison: JS/Node SDK vs WeChat Mini Program

| Feature | JS/Node SDK | WeChat Mini Program |
|---------|-------------|---------------------|
| **Namespace** | `app.ai()` | `wx.cloud.extend.AI` |
| **generateText params** | Direct object | Direct object |
| **generateText return** | `{ text, usage, messages }` | Raw: `{ choices, usage }` |
| **streamText params** | Direct object | ⚠️ Wrapped in `data: {...}` |
| **streamText return** | `{ textStream, dataStream }` | `{ textStream, eventStream }` |
| **Callbacks** | Not supported | `onText`, `onEvent`, `onFinish` |
| **Image generation** | Node SDK only | Not available |

---

## Type Definitions

### streamText() Input

```ts
interface WxStreamTextInput {
  data: {                              // ⚠️ Required wrapper object
    model: string;
    messages: Array<{
      role: "user" | "system" | "assistant";
      content: string;
    }>;
  };
  onText?: (text: string) => void;     // Incremental text callback
  onEvent?: (prop: { data: string }) => void;  // Raw event callback
  onFinish?: (text: string) => void;   // Completion callback
}
```

### streamText() Return

```ts
interface WxStreamTextResult {
  textStream: AsyncIterable<string>;   // Incremental text stream
  eventStream: AsyncIterable<{         // Raw event stream
    event?: unknown;
    id?: unknown;
    data: string;                      // "[DONE]" when complete
  }>;
}
```

### generateText() Return

```ts
// Raw model response (OpenAI-compatible format)
interface WxGenerateTextResponse {
  id: string;
  object: "chat.completion";
  created: number;
  model: string;
  choices: Array<{
    index: number;
    message: {
      role: "assistant";
      content: string;
    };
    finish_reason: string;
  }>;
  usage: {
    prompt_tokens: number;
    completion_tokens: number;
    total_tokens: number;
  };
}
```

---

## Best Practices

1. **Check base library version** - Ensure 3.7.1+ for AI support
2. **Use callbacks for UI updates** - `onText` is great for real-time display
3. **Check for [DONE]** - When using `eventStream`, check `event.data === "[DONE]"` to stop
4. **Handle errors gracefully** - Wrap AI calls in try/catch
5. **Remember the `data` wrapper** - streamText params must be wrapped in `data: {...}`
