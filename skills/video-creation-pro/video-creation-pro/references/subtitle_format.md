# 字幕格式规范

## 概览
本规范定义字幕信息的标准化格式，确保字幕在不同场景下的显示效果与可读性。

## 字幕信息格式（JSON）

```json
[
  {
    "id": 1,
    "text": "心率监测，实时精准",
    "start_time": 0.0,
    "end_time": 4.0,
    "position": {
      "x": "center",
      "y": 0.75
    },
    "style": {
      "font_size": 24,
      "color": "white",
      "font_family": "Arial",
      "background": "rgba(0,0,0,0.3)"
    }
  },
  {
    "id": 2,
    "text": "全面数据，一目了然",
    "start_time": 4.0,
    "end_time": 8.0,
    "position": {
      "x": "center",
      "y": 0.75
    },
    "style": {
      "font_size": 24,
      "color": "white",
      "font_family": "Arial",
      "background": "rgba(0,0,0,0.3)"
    }
  }
]
```

## 字段说明

| 字段 | 类型 | 必需 | 说明 |
|------|------|------|------|
| id | int | 是 | 字幕序号，从1开始 |
| text | string | 是 | 字幕文本内容 |
| start_time | float | 是 | 开始时间（秒） |
| end_time | float | 是 | 结束时间（秒） |
| position | object | 是 | 字幕位置 |
| position.x | string | 是 | 水平位置：left/center/right |
| position.y | float | 是 | 垂直位置：0.5（居中）- 0.9（底部） |
| style | object | 是 | 字幕样式 |
| style.font_size | int | 是 | 字体大小 |
| style.color | string | 是 | 字体颜色 |
| style.font_family | string | 是 | 字体名称 |
| style.background | string | 否 | 背景颜色（可选） |

## 约束与注意事项

1. **位置约束**：
   - 字幕必须位于画面下方1/3处（y值在0.75-0.9之间）
   - 禁止遮挡商品主体
   - 横屏与竖屏比例需适配

2. **时长约束**：
   - 字幕时长必须与镜头时长匹配
   - 字幕开始时间不早于镜头开始时间
   - 字幕结束时间不晚于镜头结束时间

3. **样式约束**：
   - 字体大小适配画面分辨率（24-36）
   - 字体颜色需与背景对比明显（推荐白色）
   - 背景可选，但不得影响画面美观

## 示例

### 示例1：科技风字幕
```json
[
  {
    "id": 1,
    "text": "心率监测，实时精准",
    "start_time": 0.0,
    "end_time": 4.0,
    "position": {
      "x": "center",
      "y": 0.8
    },
    "style": {
      "font_size": 28,
      "color": "#00BFFF",
      "font_family": "Arial",
      "background": "rgba(0,0,0,0.5)"
    }
  }
]
```

### 示例2：治愈风字幕
```json
[
  {
    "id": 1,
    "text": "温和补水，敏感肌友好",
    "start_time": 0.0,
    "end_time": 5.0,
    "position": {
      "x": "center",
      "y": 0.85
    },
    "style": {
      "font_size": 26,
      "color": "#FFC0CB",
      "font_family": "Arial",
      "background": "rgba(255,255,255,0.3)"
    }
  }
]
```

### 示例3：复古风字幕
```json
[
  {
    "id": 1,
    "text": "复古外观，经典设计",
    "start_time": 0.0,
    "end_time": 4.0,
    "position": {
      "x": "center",
      "y": 0.8
    },
    "style": {
      "font_size": 30,
      "color": "#8B4513",
      "font_family": "Georgia",
      "background": "rgba(139,69,19,0.2)"
    }
  }
]
```
