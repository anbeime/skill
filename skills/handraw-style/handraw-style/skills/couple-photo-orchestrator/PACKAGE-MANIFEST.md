# PACKAGE MANIFEST — couple-photo-orchestrator 2.24.26

通用摄影关键词：**高级摄影师风格，创意构图，强烈的戏剧张力**。适用于所有拍摄类型、方案、八宫格和按需单张放大；保持八宫格预览优先流程。

## Release type
完整工程包（full engineering package）

## Core engineering structure
- root orchestration docs and release metadata
- `skills/zongkong/`
- `skills/kefu/`
- `skills/huanzhuang/`
- `skills/paishe/`
- `skills/meihua/`
- `skills/makeup/`
- `skills/hairstyle/`
- scripts / templates / references / tests / archive assets

## 2.24.24 key addition
- Identity Lock v2 for real-person contact sheets
- high-priority global identity lock
- per-panel `PANEL IDENTITY RESET`
- facial geometry preservation contract
- Face Readability Gate for full-body / wide / back-turn / reflection shots
- detail/enlargement rendering cannot inherit the already-generated face from a contact-sheet cell
- canonical original remains face-only; hairstyle remains governed by locked `hairstyle_design`

## Package check
- Actual files before release build: **98**
- Cache directories and `.pyc` files: removed
