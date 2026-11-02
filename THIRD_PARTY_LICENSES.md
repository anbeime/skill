# 第三方技能许可证清单（THIRD_PARTY_LICENSES）

> 生成时间：2026-11-02 ｜ 范围：**随仓分发的 `skills/` 目录（81 个技能，其中第三方 65 个 / anbeime 自有 16 个）**
> 最后更新：2026-11-02 已将 Proprietary 技能 `photo-abstract-editorial` 从 `skills/` 与 `public/data/skills.json`、`public/skills.html` 移除，备份置于仓库外 `_quarantine/`。

> 说明：本清单扫描随仓实际分发内容（非本地收集池）。许可证判定依据 LICENSE 文件 / package.json / SKILL.md frontmatter。

## 1. 许可证分布概览（移除后现状）

| 许可证 | 数量 |
|---|---|
| Proprietary | 0（已移除 1） |
| Apache-2.0 | 2 |
| MIT | 3 |
| 未检出 | 60 |
| **合计（第三方）** | **65** |

## 2. 🔴 高风险：Proprietary / 禁商用（已处置）

- **photo-abstract-editorial**（上游 `ZzzLc0405/photo-abstract-editorial`，LICENSE.md 声明 CC BY-NC-SA 4.0 / 仅个人·教育·非商业）→ 违反本仓库 CC BY-NC 分发定位，**已于 2026-11-02 移除**：`skills/` 目录已删（备份 `_quarantine/`）、`public/data/skills.json` 与 `public/skills.html` 引用已清。因 `SKILL_SOURCES.json` 不含该上游，每日自动同步不会复原。

## 3. ✅ 宽松许可（保留版权声明即可）

### MIT（3）

- ip-as-logo — 证据：`ip-as-logo\ip-as-logo\LICENSE`

- obsidian-skills-integrated — 证据：`obsidian-skills-integrated\LICENSE`

- qiaomu-x-article-publisher — 证据：`qiaomu-x-article-publisher\LICENSE`

### Apache-2.0（2）

- img2threejs — 证据：`img2threejs\img2threejs\LICENSE`

- legal-assistant-skills-main — 证据：`legal-assistant-skills-main\contract-review\LICENSE.txt`

## 4. ⚠️ 未检出许可证（默认保留所有权利，使用须向上游核实）

共 60 个。可 fork 查看，但**不得商用或再分发**，除非取得原作者明确许可。

- NanoBanana-PPT-Skills

- agent-team

- agentkit-multimedia-shopping

- ai-drawio

- anything-to-notebooklm

- article-illustrator

- atutun-xhs-cover

- baoyu-skills

- bedtime-story

- chrome-automation

- content-creation-publisher

- content-research-writer

- convert-documents-to-markdown

- data-storytelling

- digital-avatar-shopping-video

- dream-video-prompt-generator

- ecommerce-copywriter

- ecommerce-video-marketing

- frontend-design

- historical-interview-scripts

- historical-science-video-prod

- icon-generator

- infinitetalk

- infinitetalk-shopping-avatar

- intelligent-content-system

- jiamu-skills

- media-processor

- moltbook

- multi-agent-meeting

- nanobanana-ppt-visualizer

- paper-analysis-assistant

- pdf-processing-pro

- pet-commerce-creator

- poetry-music-visual

- pop-up-book-illustration

- ppt-generator

- ppt-roadshow-generator

- pptx-generator

- product-manager-toolkit

- product-marketing-copywriter

- product-video-creator

- qwen3-asr-assistant

- qwen3-tts-local

- remotion-video-enhancer

- stock-analysis

- tailored-resume-generator

- three-body-video-creator

- tts-voice-synthesis

- video-creation-collaborator

- video-creation-pro

- video-creation-suite

- video-frame-extractor

- video-recreation

- video-transcript-downloader

- viral-video-copywriting

- web-design-analyzer

- web-to-app

- wechat-hotspot-publisher

- wechatsync-publisher

- xiaohongshu-makeup

## 5. anbeime 自有技能（本仓库核心 IP，CC BY-NC 4.0 覆盖）

- _template

- antinet-doc-parse

- antinet-four-color-cards

- antinet-provenance

- antinet-security-scan

- archify

- diagram-design

- ecommerce-full-pipeline

- email-concierge

- expert-prompt-migrator

- gpt-image-2-prompt-engine

- hospital_agent_upgrade

- kb-to-mpt

- ontoly-software-graph

- srt-whiteboard-animation

- voltagent-awesome-design-md

## 6. 合规处置建议

- 立即移除 Proprietary 技能（见第 2 节），备份至仓库外 `_quarantine/`。

- 仓库根已加 `LICENSE`（CC BY-NC 4.0）与 `NOTICE`。

- 未检出项建议逐一向上游核实许可；无法核实的考虑移除或仅索引登记。

- 本清单随仓库发布，作为「哪些归你、哪些不归你」的边界证明。
