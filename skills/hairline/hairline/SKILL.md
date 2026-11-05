---
name: hairline
description: 一句话生成跟随鼠标的交互式等轴测线框图（单文件、零依赖、双击即开），或把已有 SVG/Logo 重建为可交互线框。
source: https://github.com/lucasmarkes/hairline
type: collection
license: MIT
---

# hairline

> 一句话画出跟随鼠标的交互式线框图。零运行时依赖、约 35 kB、MIT，React 和原生 JS 都能用。

本目录是 [lucasmarkes/hairline](https://github.com/lucasmarkes/hairline) 的完整仓库快照，内含：

- **图形库**：33 个等轴测细线图形（鼠标靠近会抬起卡片、抽出机柜、逐行浮起）。
- **`skills/hairline-create`**：把一句想法（如"销售漏斗"）先给 2–3 个构思，按十条硬规则生成并自检，交付**单文件、无依赖、双击即开的 HTML**。
- **`skills/hairline-adopt`**：把已有 SVG 图标 / Logo 重建成可交互线框图。

## 设计硬规则（克制风格）

- 只有描边，无填充 / 渐变 / 发光
- 图内不放文字
- 一个图只讲一个概念

适合官网首屏和技术文档配图。

## 安装

```bash
npx skills add lucasmarkes/hairline
```

## 子技能入口

- `skills/hairline-create/SKILL.md`
- `skills/hairline-adopt/SKILL.md`
