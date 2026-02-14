# Remotion 转场效果指南

本文档详细说明了 Remotion 风格的各种转场效果，包括参数说明和使用建议。

## 目录
1. [转场效果分类](#转场效果分类)
2. [基础转场](#基础转场)
3. [动态转场](#动态转场)
4. [创意转场](#创意转场)
5. [动画风格](#动画风格)
6. [最佳实践](#最佳实践)

---

## 转场效果分类

### 基础转场
- **Fade (淡入淡出)**：经典的透明度变化，适用于大多数场景
- **Slide (滑动)**：页面沿某个方向滑动进入，简单直接

### 动态转场
- **Zoom (缩放)**：推拉镜头效果，营造空间感
- **Rotate (旋转)**：旋转过渡，适合强调变化
- **Blur (模糊)**：模糊过渡，柔和的视觉转换

### 创意转场
- **Flip (翻转)**：3D 翻转效果，适合强调对比
- **Dissolve (溶解)**：像素溶解效果，创意感强
- **Bounce (弹性)**：弹性动画，活泼有趣
- **Elastic (弹性效果)**：更强烈的弹性效果

---

## 基础转场

### Fade (淡入淡出)

**描述**：经典的淡入淡出效果，通过透明度变化实现过渡

**适用场景**：
- 商务演示
- 产品介绍
- 数据展示
- 任何需要简洁过渡的场景

**参数**：
```json
{
  "type": "fade",
  "duration": 1.0,
  "easing": "ease-in-out",
  "params": {
    "opacity_start": 0.0,
    "opacity_end": 1.0
  }
}
```

**参数说明**：
- `opacity_start`：起始透明度 (0.0-1.0)
- `opacity_end`：结束透明度 (0.0-1.0)
- `duration`：转场时长（秒）
- `easing`：缓动曲线（可选值见缓动曲线部分）

**示例配置**：
```json
{
  "type": "fade",
  "duration": 0.8,
  "easing": "ease-in-out"
}
```

---

### Slide (滑动)

**描述**：页面沿某个方向滑动进入，适合展示流程或步骤

**适用场景**：
- 步骤说明
- 流程演示
- 时间线展示
- 顺序性强的内容

**参数**：
```json
{
  "type": "slide",
  "duration": 1.0,
  "easing": "ease-in-out",
  "params": {
    "direction": "right",
    "distance": "100%"
  }
}
```

**参数说明**：
- `direction`：滑动方向
  - `right`：从右向左
  - `left`：从左向右
  - `up`：从下向上
  - `down`：从上向下
- `distance`：滑动距离（百分比或像素）

**示例配置**：
```json
{
  "type": "slide",
  "duration": 1.2,
  "easing": "ease-out",
  "params": {
    "direction": "right",
    "distance": "100%"
  }
}
```

---

## 动态转场

### Zoom (缩放)

**描述**：推拉镜头效果，营造空间感和强调感

**适用场景**：
- 产品特写
- 强调重点
- 层级展示
- 视觉冲击

**参数**：
```json
{
  "type": "zoom",
  "duration": 1.0,
  "easing": "ease-in-out",
  "params": {
    "scale": 1.2,
    "direction": "in"
  }
}
```

**参数说明**：
- `scale`：缩放比例（>1 为放大，<1 为缩小）
- `direction`：缩放方向
  - `in`：从小到大（进入）
  - `out`：从大到小（退出）

**示例配置**：
```json
{
  "type": "zoom",
  "duration": 1.5,
  "easing": "ease-out",
  "params": {
    "scale": 1.3,
    "direction": "in"
  }
}
```

---

### Rotate (旋转)

**描述**：旋转过渡，适合强调变化或转换

**适用场景**：
- 对比展示
- 转换说明
- 创意演示
- 强调变化

**参数**：
```json
{
  "type": "rotate",
  "duration": 1.0,
  "easing": "ease-in-out",
  "params": {
    "angle": 90,
    "direction": "clockwise"
  }
}
```

**参数说明**：
- `angle`：旋转角度（度数）
- `direction`：旋转方向
  - `clockwise`：顺时针
  - `counter-clockwise`：逆时针

**示例配置**：
```json
{
  "type": "rotate",
  "duration": 1.2,
  "easing": "ease-out",
  "params": {
    "angle": 90,
    "direction": "clockwise"
  }
}
```

---

### Blur (模糊)

**描述**：模糊过渡，柔和的视觉转换

**适用场景**：
- 情感内容
- 回忆展示
- 梦幻效果
- 柔和过渡

**参数**：
```json
{
  "type": "blur",
  "duration": 1.0,
  "easing": "ease-in-out",
  "params": {
    "blur_radius": 20
  }
}
```

**参数说明**：
- `blur_radius`：模糊半径（像素）

**示例配置**：
```json
{
  "type": "blur",
  "duration": 1.5,
  "easing": "ease-in-out",
  "params": {
    "blur_radius": 15
  }
}
```

---

## 创意转场

### Flip (翻转)

**描述**：3D 翻转效果，适合强调对比或转换

**适用场景**：
- 对比展示
- 前后对比
- 转换说明
- 3D 效果

**参数**：
```json
{
  "type": "flip",
  "duration": 1.0,
  "easing": "ease-in-out",
  "params": {
    "axis": "x",
    "direction": "right"
  }
}
```

**参数说明**：
- `axis`：翻转轴
  - `x`：水平翻转
  - `y`：垂直翻转
- `direction`：翻转方向
  - `left`：向左翻转
  - `right`：向右翻转

**示例配置**：
```json
{
  "type": "flip",
  "duration": 1.2,
  "easing": "ease-out",
  "params": {
    "axis": "x",
    "direction": "right"
  }
}
```

---

### Dissolve (溶解)

**描述**：像素溶解效果，创意感强

**适用场景**：
- 创意展示
- 艺术效果
- 特殊过渡
- 视觉冲击

**参数**：
```json
{
  "type": "dissolve",
  "duration": 1.0,
  "easing": "ease-in-out",
  "params": {
    "pixel_size": 8
  }
}
```

**参数说明**：
- `pixel_size`：像素大小（像素）

**示例配置**：
```json
{
  "type": "dissolve",
  "duration": 1.5,
  "easing": "ease-in-out",
  "params": {
    "pixel_size": 6
  }
}
```

---

### Bounce (弹性)

**描述**：弹性动画，活泼有趣

**适用场景**：
- 教育内容
- 儿童内容
- 活泼展示
- 创意演示

**参数**：
```json
{
  "type": "bounce",
  "duration": 1.0,
  "easing": "ease-out",
  "params": {
    "bounce_factor": 0.3
  }
}
```

**参数说明**：
- `bounce_factor`：弹性因子 (0.0-1.0)

**示例配置**：
```json
{
  "type": "bounce",
  "duration": 1.2,
  "easing": "ease-out",
  "params": {
    "bounce_factor": 0.4
  }
}
```

---

### Elastic (弹性效果)

**描述**：更强烈的弹性效果，适合创意展示

**适用场景**：
- 创意展示
- 艺术效果
- 活泼演示
- 视觉冲击

**参数**：
```json
{
  "type": "elastic",
  "duration": 1.0,
  "easing": "ease-out",
  "params": {
    "elasticity": 0.5
  }
}
```

**参数说明**：
- `elasticity`：弹性强度 (0.0-1.0)

**示例配置**：
```json
{
  "type": "elastic",
  "duration": 1.5,
  "easing": "ease-out",
  "params": {
    "elasticity": 0.6
  }
}
```

---

## 动画风格

### Minimal (极简风格)

**特点**：
- 转场类型：fade
- 时长范围：0.5-1.0 秒
- 缓动曲线：linear

**适用场景**：
- 商务演示
- 专业展示
- 数据报告
- 极简设计

**配置**：
```json
{
  "style": "minimal",
  "transitions": ["fade"],
  "duration_range": [0.5, 1.0],
  "easing": "linear"
}
```

---

### Dynamic (动态风格)

**特点**：
- 转场类型：slide, zoom, fade
- 时长范围：1.0-1.5 秒
- 缓动曲线：ease-in-out

**适用场景**：
- 产品介绍
- 路演视频
- 创意展示
- 互动演示

**配置**：
```json
{
  "style": "dynamic",
  "transitions": ["slide", "zoom", "fade"],
  "duration_range": [1.0, 1.5],
  "easing": "ease-in-out"
}
```

---

### Cinematic (电影风格)

**特点**：
- 转场类型：blur, dissolve, zoom
- 时长范围：1.5-2.0 秒
- 缓动曲线：ease-in-out

**适用场景**：
- 电影感展示
- 艺术效果
- 情感内容
- 高级演示

**配置**：
```json
{
  "style": "cinematic",
  "transitions": ["blur", "dissolve", "zoom"],
  "duration_range": [1.5, 2.0],
  "easing": "ease-in-out"
}
```

---

### Playful (活泼风格)

**特点**：
- 转场类型：bounce, elastic, rotate
- 时长范围：0.8-1.2 秒
- 缓动曲线：ease-out

**适用场景**：
- 教育内容
- 儿童内容
- 活泼展示
- 创意演示

**配置**：
```json
{
  "style": "playful",
  "transitions": ["bounce", "elastic", "rotate"],
  "duration_range": [0.8, 1.2],
  "easing": "ease-out"
}
```

---

## 缓动曲线

缓动曲线决定动画的速度变化。

### 常用缓动曲线

| 名称 | 描述 | 适用场景 |
|------|------|----------|
| linear | 匀速 | 机械效果、循环动画 |
| ease-in | 加速 | 进入效果、强调 |
| ease-out | 减速 | 退出效果、平滑 |
| ease-in-out | 先加速后减速 | 大部分场景 |
| bounce | 弹跳 | 活泼效果 |
| elastic | 弹性 | 创意效果 |

---

## 最佳实践

### 1. 选择合适的转场类型

- **商务演示**：使用 fade 或 slide
- **产品介绍**：使用 zoom 或 dynamic 风格
- **艺术展示**：使用 blur 或 dissolve
- **教育内容**：使用 bounce 或 playful 风格

### 2. 控制转场时长

- 短转场（0.5-1.0 秒）：快节奏、极简风格
- 中等转场（1.0-1.5 秒）：标准、大多数场景
- 长转场（1.5-2.0 秒）：电影感、艺术效果

### 3. 混合使用转场

不要在整个视频中使用同一种转场，建议：
- 封面使用 zoom in
- 内容页使用 slide
- 总结页使用 fade
- 强调页使用 rotate

### 4. 考虑观众体验

- 避免过于频繁的转场
- 保持转场风格一致
- 不要过度使用创意转场
- 确保转场不会分散注意力

### 5. 测试和调整

- 生成后预览效果
- 根据反馈调整参数
- 多次测试不同配置
- 选择最佳方案

---

## 完整示例

### 示例 1：商务演示（极简风格）

```json
{
  "metadata": {
    "style": "minimal",
    "page_count": 10
  },
  "transitions": [
    {"type": "fade", "duration": 0.8, "easing": "linear"},
    {"type": "fade", "duration": 0.8, "easing": "linear"},
    {"type": "fade", "duration": 0.8, "easing": "linear"}
  ]
}
```

### 示例 2：产品介绍（动态风格）

```json
{
  "metadata": {
    "style": "dynamic",
    "page_count": 15
  },
  "transitions": [
    {"type": "zoom", "duration": 1.5, "easing": "ease-out", "params": {"scale": 1.2, "direction": "in"}},
    {"type": "slide", "duration": 1.2, "easing": "ease-in-out", "params": {"direction": "right"}},
    {"type": "fade", "duration": 1.0, "easing": "ease-in-out"},
    {"type": "zoom", "duration": 1.5, "easing": "ease-out", "params": {"scale": 0.8, "direction": "out"}}
  ]
}
```

### 示例 3：创意展示（活泼风格）

```json
{
  "metadata": {
    "style": "playful",
    "page_count": 8
  },
  "transitions": [
    {"type": "bounce", "duration": 1.2, "easing": "ease-out", "params": {"bounce_factor": 0.3}},
    {"type": "rotate", "duration": 1.0, "easing": "ease-out", "params": {"angle": 90}},
    {"type": "elastic", "duration": 1.5, "easing": "ease-out", "params": {"elasticity": 0.5}}
  ]
}
```
