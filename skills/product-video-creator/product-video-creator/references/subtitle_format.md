# 字幕格式规范

## 概览
本规范定义了商品视频字幕的配置格式，用于指导字幕内容的创作和在视频中的显示。

## 格式定义

### JSON格式结构
字幕配置使用JSON格式，包含字幕内容和显示时间信息：

```json
{
  "subtitles": [
    {
      "id": 1,
      "text": "智能生活，腕间掌控",
      "start_time": 0.5,
      "end_time": 2.5,
      "position": "bottom",
      "font_size": 48,
      "color": "#FFFFFF",
      "background": true,
      "background_color": "rgba(0,0,0,0.5)"
    },
    {
      "id": 2,
      "text": "实时监测，健康常伴",
      "start_time": 3.0,
      "end_time": 5.5,
      "position": "bottom",
      "font_size": 48,
      "color": "#FFFFFF",
      "background": true,
      "background_color": "rgba(0,0,0,0.5)"
    }
  ]
}
```

### 字段说明

#### 字幕对象

**id**（必需）
- 类型：整数
- 说明：字幕唯一标识，与镜头序号对应
- 约束：正整数，从1开始递增

**text**（必需）
- 类型：字符串
- 说明：字幕文本内容
- 约束：
  - 长度：10-20字（特殊情况除外）
  - 内容：简短精炼，与画面配合
  - 避免重复画面中已有的文字

**start_time**（必需）
- 类型：浮点数
- 说明：字幕开始显示的时间点（秒）
- 约束：
  - 大于等于0
  - 小于end_time
  - 通常在镜头开始后0.5-1秒出现

**end_time**（必需）
- 类型：浮点数
- 说明：字幕消失的时间点（秒）
- 约束：
  - 大于start_time
  - 小于等于镜头结束时间
  - 通常在镜头结束前0.5-1秒消失

**position**（可选，默认：bottom）
- 类型：字符串
- 说明：字幕在画面中的位置
- 可选值：
  - "top"：画面上方1/3处
  - "center"：画面中央
  - "bottom"：画面下方1/3处（最常用）

**font_size**（可选，默认：48）
- 类型：整数
- 说明：字体大小（像素）
- 约束：根据视频分辨率调整，通常在36-72之间

**color**（可选，默认：#FFFFFF）
- 类型：字符串
- 说明：字体颜色（十六进制颜色码）
- 约束：确保与背景对比度足够，常用白色

**background**（可选，默认：true）
- 类型：布尔值
- 说明：是否显示背景条
- 建议：设置为true以提高可读性

**background_color**（可选，默认：rgba(0,0,0,0.5)）
- 类型：字符串
- 说明：背景条颜色和透明度（RGBA格式）
- 约束：半透明黑色最为常见，避免完全遮挡背景

## 完整示例

### 示例1：30秒智能手表宣传视频

```json
{
  "subtitles": [
    {
      "id": 1,
      "text": "智能生活，腕间掌控",
      "start_time": 0.5,
      "end_time": 2.5,
      "position": "bottom",
      "font_size": 48,
      "color": "#FFFFFF",
      "background": true,
      "background_color": "rgba(0,0,0,0.5)"
    },
    {
      "id": 2,
      "text": "实时监测，健康常伴",
      "start_time": 3.0,
      "end_time": 5.5,
      "position": "bottom",
      "font_size": 48,
      "color": "#FFFFFF",
      "background": true,
      "background_color": "rgba(0,0,0,0.5)"
    },
    {
      "id": 3,
      "text": "全面数据，一目了然",
      "start_time": 6.5,
      "end_time": 8.5,
      "position": "bottom",
      "font_size": 48,
      "color": "#FFFFFF",
      "background": true,
      "background_color": "rgba(0,0,0,0.5)"
    },
    {
      "id": 4,
      "text": "运动追踪，精准记录",
      "start_time": 9.0,
      "end_time": 11.0,
      "position": "bottom",
      "font_size": 48,
      "color": "#FFFFFF",
      "background": true,
      "background_color": "rgba(0,0,0,0.5)"
    },
    {
      "id": 5,
      "text": "超长续航，无忧使用",
      "start_time": 11.5,
      "end_time": 13.5,
      "position": "bottom",
      "font_size": 48,
      "color": "#FFFFFF",
      "background": true,
      "background_color": "rgba(0,0,0,0.5)"
    },
    {
      "id": 6,
      "text": "智能提醒，从不遗漏",
      "start_time": 14.0,
      "end_time": 16.5,
      "position": "bottom",
      "font_size": 48,
      "color": "#FFFFFF",
      "background": true,
      "background_color": "rgba(0,0,0,0.5)"
    },
    {
      "id": 7,
      "text": "精致设计，彰显品味",
      "start_time": 17.0,
      "end_time": 19.5,
      "position": "bottom",
      "font_size": 48,
      "color": "#FFFFFF",
      "background": true,
      "background_color": "rgba(0,0,0,0.5)"
    },
    {
      "id": 8,
      "text": "XXX智能手表",
      "start_time": 20.0,
      "end_time": 23.0,
      "position": "center",
      "font_size": 64,
      "color": "#FFFFFF",
      "background": true,
      "background_color": "rgba(0,0,0,0.7)"
    }
  ]
}
```

### 示例2：60秒护肤品宣传视频

```json
{
  "subtitles": [
    {
      "id": 1,
      "text": "时光荏苒，美丽不老",
      "start_time": 1.0,
      "end_time": 3.5,
      "position": "bottom",
      "font_size": 52,
      "color": "#FFE4E1",
      "background": true,
      "background_color": "rgba(139,69,19,0.4)"
    },
    {
      "id": 2,
      "text": "臻选成分，奢宠呵护",
      "start_time": 4.0,
      "end_time": 7.5,
      "position": "bottom",
      "font_size": 48,
      "color": "#FFE4E1",
      "background": true,
      "background_color": "rgba(139,69,19,0.4)"
    },
    {
      "id": 3,
      "text": "温和吸收，焕发光彩",
      "start_time": 8.5,
      "end_time": 11.5,
      "position": "bottom",
      "font_size": 48,
      "color": "#FFE4E1",
      "background": true,
      "background_color": "rgba(139,69,19,0.4)"
    },
    {
      "id": 4,
      "text": "7天见证，年轻新生",
      "start_time": 12.0,
      "end_time": 15.0,
      "position": "center",
      "font_size": 56,
      "color": "#FFFFFF",
      "background": true,
      "background_color": "rgba(139,69,19,0.5)"
    },
    {
      "id": 5,
      "text": "紧致提亮，自信绽放",
      "start_time": 16.0,
      "end_time": 19.5,
      "position": "bottom",
      "font_size": 48,
      "color": "#FFE4E1",
      "background": true,
      "background_color": "rgba(139,69,19,0.4)"
    },
    {
      "id": 6,
      "text": "天然植萃，科技加持",
      "start_time": 19.5,
      "end_time": 22.5,
      "position": "bottom",
      "font_size": 48,
      "color": "#FFE4E1",
      "background": true,
      "background_color": "rgba(139,69,19,0.4)"
    },
    {
      "id": 7,
      "text": "适合全年龄段，安心之选",
      "start_time": 23.0,
      "end_time": 26.5,
      "position": "bottom",
      "font_size": 44,
      "color": "#FFE4E1",
      "background": true,
      "background_color": "rgba(139,69,19,0.4)"
    },
    {
      "id": 8,
      "text": "全方位精致",
      "start_time": 27.0,
      "end_time": 30.0,
      "position": "bottom",
      "font_size": 48,
      "color": "#FFE4E1",
      "background": true,
      "background_color": "rgba(139,69,19,0.4)"
    },
    {
      "id": 9,
      "text": "优雅时刻，美丽加分",
      "start_time": 30.5,
      "end_time": 34.5,
      "position": "bottom",
      "font_size": 48,
      "color": "#FFE4E1",
      "background": true,
      "background_color": "rgba(139,69,19,0.4)"
    },
    {
      "id": 10,
      "text": "坚持使用，见证改变",
      "start_time": 35.0,
      "end_time": 38.0,
      "position": "center",
      "font_size": 56,
      "color": "#FFFFFF",
      "background": true,
      "background_color": "rgba(139,69,19,0.5)"
    },
    {
      "id": 11,
      "text": "完美搭配，护肤之道",
      "start_time": 38.5,
      "end_time": 42.0,
      "position": "bottom",
      "font_size": 48,
      "color": "#FFE4E1",
      "background": true,
      "background_color": "rgba(139,69,19,0.4)"
    },
    {
      "id": 12,
      "text": "XXX抗衰老精华",
      "start_time": 42.5,
      "end_time": 47.5,
      "position": "center",
      "font_size": 72,
      "color": "#FFE4E1",
      "background": true,
      "background_color": "rgba(139,69,19,0.6)"
    }
  ]
}
```

## 验证规则

### 完整性检查
- [ ] JSON格式正确，可正常解析
- [ ] 所有必需字段（id, text, start_time, end_time）存在
- [ ] 字幕数量与分镜脚本镜头数量一致

### 时间合理性检查
- [ ] start_time >= 0
- [ ] end_time > start_time
- [ ] end_time - start_time >= 1（确保显示时间足够阅读）
- [ ] 字幕时间区间不重叠（除非是有意为之的多字幕）

### 内容合理性检查
- [ ] 每条字幕长度在10-20字之间（特殊情况除外）
- [ ] 字幕内容与对应镜头的描述配合紧密
- [ ] 字幕颜色与背景对比度足够

### 格式规范
- [ ] 使用UTF-8编码
- [ ] 时间使用浮点数格式
- [ ] 颜色使用十六进制或RGBA格式

## 使用建议

### 字幕显示时间
- **开始时间**：通常在镜头开始后0.5-1秒，给观众先看清画面
- **结束时间**：通常在镜头结束前0.5-1秒，为转场留出空间
- **持续时间**：建议2-4秒，确保观众能够完整阅读

### 字幕位置
- **bottom（底部）**：最常用，不遮挡主体，适合大部分场景
- **center（中央）**：用于强调性字幕或镜头中无重要内容时
- **top（顶部）**：较少使用，可能遮挡重要信息

### 字幕样式
- **字体大小**：根据视频分辨率调整，确保清晰可读
- **颜色**：白色最常用，浅色视频可用深色文字
- **背景**：建议启用背景条，提高在各种背景下的可读性
- **背景颜色**：半透明黑色（rgba(0,0,0,0.5)）最常用

### 字幕内容
- **简洁精炼**：每条10-20字，避免过长
- **配合画面**：字幕应补充或强化画面信息，而非重复
- **情感一致**：字幕语气应与视频整体情感基调一致
- **品牌强化**：品牌相关字幕可更大更醒目

## 常见问题

**Q: 字幕应该多久消失？**
A: 根据字数和阅读速度，通常2-4秒。中文阅读速度约每秒5-8字，10-20字的字幕需要2-4秒。

**Q: 什么时候显示背景条？**
A: 建议始终启用，确保字幕在各种背景下都清晰可读。只有当背景非常简单且对比度足够时才考虑关闭。

**Q: 字幕颜色如何选择？**
A: 白色是最安全的选择，适用于大部分背景。浅色背景可用深色文字。确保文字与背景对比度足够。

**Q: 字幕位置如何选择？**
A: 底部最常用，不遮挡主体。中央用于强调性字幕。顶部较少使用，可能遮挡重要信息。

**Q: 字幕可以重叠显示吗？**
A: 一般不建议重叠，除非有特殊设计需求（如双语字幕）。避免给观众造成阅读困扰。
