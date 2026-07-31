---
name: remotion-animator
description: "Transform knowledge cards and text content into animated video presentations using Remotion. Convert 4-color cards (facts/interpretations/risks/actions) into engaging visual animations with data charts, transitions, and dynamic elements. Triggers: video, animation, animated PPT, 动态演示, 动画, 视频报告."
license: MIT
metadata:
  version: "2.0.0"
  category: presentation
  sources:
    - https://www.remotion.dev/docs
    - https://remotion.dev/blog
    - https://remotion.dev/docs/cdn-server
---

# Remotion Animator (v2)

基于 Remotion 的知识内容动画视频生成技能。将结构化内容（四色知识卡片、分析结果、思维导图）转换为专业动画视频。

## Overview

```
知识卡片/PPT/文本内容
    ↓
内容解析与结构化 (Slide 数据模型)
    ↓
Remotion 组件生成 (React + useCurrentFrame 驱动)
    ↓
视频渲染与导出 (MP4/WebM/GIF/帧序列)
```

## 核心原则

### 1. 所有动画必须由 `useCurrentFrame()` 驱动

```tsx
// ✅ 正确: 使用 useCurrentFrame()
const frame = useCurrentFrame();
const { fps } = useVideoConfig();
const opacity = interpolate(frame, [0, 2 * fps], [0, 1]);

// ❌ 禁止: CSS transitions/animations — 渲染时不会生效
// ❌ 禁止: Tailwind animate-* 类名 — 渲染时不会生效
// ❌ 禁止: Three.js 的 useFrame() — 会导致闪烁
```

### 2. 资源引用使用 `staticFile()`

本地文件必须放在 `public/` 文件夹并通过 `staticFile()` 引用：

```tsx
import { Img, staticFile } from "remotion";
<Img src={staticFile("logo.png")} />; // ✅
// <img src="/logo.png" />;             // ❌ 不要用原生 img
```

远程 URL 可直接使用（需 CORS）：
```tsx
<Img src="https://example.com/image.png" />; // ✅
```

---

## Quick Start

### 安装依赖

```bash
# 核心依赖
npx remotion add @remotion/media      # 音频/视频组件
npx remotion add @remotion/transitions # 场景转场
npx remotion add @remotion/google-fonts # Google Fonts
npx remotion add @remotion/fonts       # 本地字体
npx remotion add @remotion/lottie      # Lottie 动画
npx remotion add @remotion/gif         # GIF 支持
npx remotion add @remotion/three       # 3D (Three.js)
npx remotion add @remotion/captions    # 字幕
npx remotion add @remotion/layout-utils # 文本测量

# 可选
npm install recharts     # 图表
```

### 基本工作流

**Step 1**: 定义 Composition (`Root.tsx`)
**Step 2**: 创建 Slide 组件
**Step 3**: 使用 Sequence/Series 控制时间轴
**Step 4**: 渲染导出

```bash
npm start                              # Studio 预览
npx remotion render MyComp out/video.mp4 # 渲染输出
```

---

## Reference Files (完整参考文档)

| 文件 | 内容 | 关键 API |
|------|------|----------|
| [compositions.md](references/compositions.md) | Composition 定义、Folder、Still、calculateMetadata | `<Composition>`, `<Still>`, `<Folder>` |
| [animations-raw.md](references/animations-raw.md) | 动画基础规则 | `useCurrentFrame()`, `interpolate()` |
| [timing-raw.md](references/timing-raw.md) | 时序控制: interpolate, spring, easing | `spring()`, `interpolate()`, `Easing` |
| [sequencing.md](references/sequencing.md) | 序列编排: Sequence, Series, 嵌套 | `<Sequence>`, `<Series>` |
| [trimming.md](references/trimming.md) | 裁剪动画开头/结尾 | 负数 `from`, `durationInFrames` |
| [transitions.md](references/transitions.md) | 全屏场景转场 | `<TransitionSeries>`, fade/slide/wipe/flip |
| [assets.md](references/assets.md) | 资源导入: 图片/视频/音频/字体 | `staticFile()`, `<Img>`, `<Video>`, `<Audio>` |
| [images.md](references/images.md) | 图片嵌入规范 | `<Img>`, `getImageDimensions()`, 动态路径 |
| [videos.md](references/videos.md) | 视频嵌入与控制 | `<Video>`, trimBefore/After, volume, playbackRate, loop |
| [audio.md](references/audio.md) | 音频控制 | `<Audio>`, volume 回调, muted, toneFrequency, loop |
| [gifs.md](references/gifs.md) | 动图 (GIF/APNG/AVIF/WebP) | `<AnimatedImage>`, `<Gif>`, loopBehavior |
| [fonts.md](references/fonts.md) | 字体加载 | `@remotion/google-fonts`, `@remotion/fonts`, `loadFont()` |
| [charts.md](references/charts.md) | 图表动画模式 | 柱状图(stagger), 饼图(stroke-dashoffset), D3.js |
| [lottie.md](references/lottie.md) | Lottie 动画嵌入 | `<Lottie>`, delayRender/continueRender |
| [text-animations.md](references/text-animations.md) | 文本动效 | 打字机, 单词高亮 |
| [measuring-text.md](references/measuring-text.md) | 文本测量与排版 | `measureText()`, `fitText()`, `fillTextBox()` |
| [measuring-dom-nodes.md](references/measuring-dom-nodes.md) | DOM 尺寸测量 | `useCurrentScale()`, `getBoundingClientRect` |
| [display-captions.md](references/display-captions.md) | 字幕显示 (TikTok 风格) | `createTikTokStyleCaptions()`, word highlighting |
| [import-srt-captions.md](references/import-srt-captions.md) | SRT 字幕导入 | `parseSrt()` |
| [transcribe-captions.md](references/transcribe-captions.md) | 语音转字幕 | Whisper.cpp / Whisper-web / OpenAI Whisper |
| [calculate-metadata.md](references/calculate-metadata.md) | 动态元数据 | `calculateMetadata`, 视频尺寸匹配, Props 变换 |
| [extract-frames.md](references/extract-frames.md) | 视频帧提取 | `extractFrames()`, 缩略图, filmstrip |
| [can-decode.md](references/can-decode.md) | 编码检测 | `canDecode()`, Mediabunny |
| [get-video-duration.md](references/get-video-duration.md) | 视频时长获取 | `getVideoDuration()` |
| [get-audio-duration.md](references/get-audio-duration.md) | 音频时长获取 | `getAudioDuration()` |
| [get-video-dimensions.md](references/get-video-dimensions.md) | 视频尺寸获取 | `getVideoDimensions()` |
| [3d.md](references/3d.md) | 3D 内容 (Three.js/R3F) | `<ThreeCanvas>`, 禁止 useFrame() |
| [tailwind.md](references/tailwind.md) | TailwindCSS 集成 | 允许样式类, 禁止 transition/animate 类 |

### 示例代码 (assets/)

| 文件 | 描述 |
|------|------|
| [assets/charts-bar-chart.tsx](references/assets/charts-bar-chart.tsx) | 柱状图动画示例 (spring stagger) |
| [assets/text-animations-typewriter.tsx](references/assets/text-animations-typewriter.tsx) | 打字机动效 (光标闪烁+停顿) |
| [assets/text-animations-word-highlight.tsx](references/assets/text-animations-word-highlight.tsx) | 单词高亮动效 (荧光笔效果) |

### 业务参考文档 (原有)

| 文件 | 内容 |
|------|------|
| [slide-types.md](references/slide-types.md) | 幻灯片类型定义 (Cover/Content/Chart/MindMap/Summary) |
| [animations.md](references/animations.md) | 业务级动画预设 (fade/slide/scale/bounce) |
| [rendering.md](references/rendering.md) | 渲染配置与优化 |

---

## Animation Timing 参考表

| 元素 | 时长 | 缓动函数 | 用途 |
|------|------|----------|------|
| 卡片入场 | 0.8s | ease-out / spring `{damping:200}` | 四色卡出现 |
| 文字揭示 | 0.5s | ease-in-out | 标题/正文逐字显示 |
| 图表生长 | 1.5s | spring `{damping:18}` | 柱状图/饼图动画 |
| 场景转场 | 0.5s~0.7s | linearTiming / springTiming | 切片间过渡 |
| 高亮强调 | 0.6s | spring `{damping:200}` | 单词/关键词高亮 |

### Spring 配置速查

| 配置 | 效果 | 适用场景 |
|------|------|----------|
| `{damping: 200}` | 平滑无弹跳 | 入场揭示、UI 元素 |
| `{damping: 20, stiffness: 200}` | 干脆微弹 | 按钮、图标交互 |
| `{damping: 8}` | 明显弹跳 | 强调动画、趣味元素 |
| `{damping: 15, stiffness: 80, mass: 2}` | 沉重缓慢 | 大型元素移动 |
| `{damping: 18, stiffness: 80}` | 有弹性 | 图表柱状条增长 |

---

## Four-Color Card Animations (四色卡片)

| 卡片类型 | 颜色 | 动画风格 | 推荐入场 |
|----------|------|----------|----------|
| 事实 Fact | `#3b82f6` (蓝) | 从左滑入 | slide from-left |
| 解释 Interpretation | `#22c55e` (绿) | 淡入+缩放 | fade + scale up |
| 风险 Risk | `#eab308` (黄) | 抖动+高亮 | shake + color pulse |
| 行动 Action | `#ef4444` (红) | 弹跳入场 | bounce spring |

## Output Formats

| 格式 | 说明 | 用途 |
|------|------|------|
| MP4 (H.264) | 标准视频 | 通用播放、分享 |
| WebM (VP9) | Web 优化 | 网页内嵌 |
| GIF | 动画预览 | 即时通讯、社交 |
| Frame sequence | 帧序列 | 后期合成 |

## Slide 数据模型

```typescript
interface Slide {
  id: string;
  type: 'cover' | 'content' | 'chart' | 'mindmap' | 'summary';
  title: string;
  content: string[];
  color?: string;        // 四色卡颜色
  data?: ChartData;      // 图表数据
  durationInSeconds?: number; // 可选时长覆盖
}
```

## Key Components

| 组件 | 用途 | 核心技术 |
|------|------|----------|
| `SlideSequence` | 幻灯片逐页切换 | TransitionSeries + Sequence |
| `AnimatedCard` | 四色卡片入场动画 | spring + interpolate |
| `DataChart` | 动画图表 | SVG/D3 + useCurrentFrame |
| `MindMapFlow` | 思维导图可视化 | 节点连线 + 递归动画 |
| `TitleSequence` | 标题序列特效 | 文字动画 + 背景粒子 |
| `TimelineControl` | 播放控制 UI | Player 组件 |
