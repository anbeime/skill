---
name: voltagent-awesome-design-md
description: >
  73 个真实网站 DESIGN.md 提取集合（Claude / Cursor / Vercel / Stripe / Apple / Tesla / Ferrari ...）。
  把 DESIGN.md 复制到项目根目录，AI agent 读 DESIGN.md 后能生成风格一致的高质量 UI。
  本仓库同步自 VoltAgent/awesome-design-md。
  关键词：DESIGN.md, Google Stitch, UI 设计, 设计系统, Claude, Cursor, Vercel, Stripe, Apple, Tesla。
license: MIT
source: https://github.com/VoltAgent/awesome-design-md
---

# VoltAgent Awesome DESIGN.md

**73 个真实网站的 DESIGN.md 提取集合。** 每个子目录（如 `design-md/claude/`、`design-md/stripe/`、`design-md/tesla/`）是一份完整的 DESIGN.md 文件 —— Google Stitch 推广的纯 Markdown 设计系统描述语言。

## 是什么

DESIGN.md 是 Google Stitch 推出的设计系统规范：
- **AGENTS.md** —— 给编码 agent 看，定义"项目怎么建"
- **DESIGN.md** —— 给设计 agent 看，定义"UI 应该长什么样"

> 只需在项目根目录放一份 DESIGN.md，任何 AI 编码 agent / Google Stitch 就能立即理解你的 UI 视觉规范。

## 怎么用

1. 浏览 `design-md/<name>/DESIGN.md`，找一个你喜欢的风格
2. 复制对应目录到你的项目根目录
3. 告诉你的 AI agent："build me a page that looks like this"
4. AI 会按 DESIGN.md 里的色板 / 字体 / 间距 / 组件规格生成一致 UI

## 收录分类

- AI & LLM 平台（Claude / Cohere / ElevenLabs / Mistral AI / Ollama / xAI 等 12 个）
- Developer Tools & IDEs（Cursor / Expo / Lovable / Raycast / Vercel / Warp 等 7 个）
- Backend / Database / DevOps（ClickHouse / MongoDB / PostHog / Sentry / Supabase 等 8 个）
- Productivity & SaaS（Cal.com / Linear / Notion / Resend / Zapier 等 7 个）
- Design & Creative Tools（Figma / Framer / Miro / Webflow 等 6 个）
- Fintech & Crypto（Binance / Coinbase / Kraken / Stripe / Wise 等 7 个）
- E-commerce & Retail（Airbnb / Nike / Shopify / Starbucks 等 5 个）
- Media & Consumer Tech（Apple / NVIDIA / PlayStation / Spotify / WIRED 等 12 个）
- Automotive（BMW / Ferrari / Lamborghini / Tesla 等 7 个）
- Retro Web（1996 Dell / 2001 Nintendo.com 等复古 UI）

总计 73 个 DESIGN.md。

## 在 Antinet 里的角色

**资源目录型 skill** —— 不是 agent runtime skill（不进入 SKILL_SOURCES.json 调度），而是设计资源仓库。

前端 `skills.html` 的 🔥 **本周热门** Tab 已收录（与 ip-as-logo / img2threejs / photo-abstract-editorial / anydoc 并列）。

## 与其他 Skill 的关系

- `ip-as-logo`：吉祥物（资产）
- `img2threejs`：3D 重建（资产）
- `photo-abstract-editorial`：编辑作品（资产）
- **`voltagent-awesome-design-md`：UI 设计系统（规范）**

四者合起来构成"AI 创作素材层"。

## License

继承上游仓库 LICENSE。详见 `LICENSE` 文件（MIT）。