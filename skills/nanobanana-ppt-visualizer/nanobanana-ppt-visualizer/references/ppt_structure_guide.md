# PPT 结构规范（协同兼容版）

本规范与 ppt-generator Skill 完全兼容，确保两个 Skill 可以无缝协作。

## JSON 数据格式

### 根对象结构
```json
{
  "metadata": {
    "title": "演示文稿标题",
    "author": "作者姓名",
    "subject": "主题描述",
    "keywords": "关键词1,关键词2,关键词3"
  },
  "slides": [
    {
      "layout": "TitleSlide",
      "title": "封面标题",
      "content": ["副标题或描述"],
      "notes": "演讲者备注"
    },
    ...
  ]
}
```

### 字段说明

#### metadata（推荐）
- `title`：演示文稿标题（字符串）
- `author`：作者姓名（字符串，可选）
- `subject`：主题描述（字符串，可选）
- `keywords`：关键词，逗号分隔（字符串，可选）

#### slides（必需）
幻灯片对象数组，每个幻灯片包含以下字段：
- `layout`：布局类型（字符串，必需）
- `title`：幻灯片标题（字符串，必需）
- `content`：内容列表（字符串数组，必需）
- `notes`：演讲者备注（字符串，可选）

### 布局类型

| 布局类型 | 用途 | 说明 |
|---------|------|------|
| TitleSlide | 封面页 | 大标题 + 副标题 |
| TitleAndContent | 内容页 | 标题 + 内容区 |
| TwoColumnText | 双栏页 | 左右对比内容 |
| SectionHeader | 章节页 | 章节标题 + 描述 |
| BulletList | 列表页 | 项目符号列表 |
| BlankSlide | 空白页 | 自定义布局 |

### 完整示例

```json
{
  "metadata": {
    "title": "AI 产品发布会",
    "author": "产品团队",
    "subject": "新产品介绍",
    "keywords": "AI,产品,发布"
  },
  "slides": [
    {
      "layout": "TitleSlide",
      "title": "AI 产品发布会",
      "content": ["创新 · 智能 · 未来"],
      "notes": "欢迎来到 AI 产品发布会"
    },
    {
      "layout": "SectionHeader",
      "title": "第一部分：产品概述",
      "content": ["了解我们的核心产品"]
    },
    {
      "layout": "TitleAndContent",
      "title": "产品介绍",
      "content": [
        "智能助手，随时响应",
        "多模态交互，自然对话",
        "持续学习，越来越智能"
      ],
      "notes": "三个核心特性"
    },
    {
      "layout": "TwoColumnText",
      "title": "产品对比",
      "content": [
        "【我们的产品】",
        "更智能的算法",
        "更好的用户体验",
        "【竞品】",
        "功能基础",
        "体验一般"
      ],
      "notes": "与竞品的对比"
    },
    {
      "layout": "BulletList",
      "title": "核心优势",
      "content": [
        "强大的 AI 能力",
        "简洁易用的界面",
        "安全可靠的数据保护",
        "持续更新的功能"
      ],
      "notes": "四大核心优势"
    },
    {
      "layout": "BlankSlide",
      "title": "谢谢",
      "content": []
    }
  ]
}
```

## 与 ppt-generator 的数据流

```
┌─────────────────────────────────────────────────────────┐
│  ppt-generator 输出                                      │
├─────────────────────────────────────────────────────────┤
│  {                                                        │
│    "metadata": {...},                                     │
│    "slides": [                                            │
│      {"layout": "TitleSlide", ...},                       │
│      {"layout": "TitleAndContent", ...},                 │
│      ...                                                  │
│    ]                                                      │
│  }                                                        │
└─────────────────────────────────────────────────────────┘
                          │
                          ▼ 传递 JSON
┌─────────────────────────────────────────────────────────┐
│  nanobanana-ppt-visualizer 输入                          │
├─────────────────────────────────────────────────────────┤
│  接收 JSON                                               │
│  → 选择风格                                              │
│  → 生成图片                                              │
│  → 生成播放器                                            │
│  → 可选：视频合成                                        │
└─────────────────────────────────────────────────────────┘
```

## 输出文件结构

### 图片模式
```
outputs/TIMESTAMP/
├── index.html              # HTML 播放器
├── images/
│   ├── slide-01.png
│   ├── slide-02.png
│   └── ...
└── style.json              # 风格配置
```

### 视频模式（如果生成了视频）
```
outputs/TIMESTAMP_video/
├── video_index.html        # 视频播放器
├── videos/
│   ├── preview.mp4         # 首页预览
│   ├── transition_01_to_02.mp4
│   ├── transition_02_to_03.mp4
│   └── ...
├── images/
│   ├── slide-01.png
│   ├── slide-02.png
│   └── ...
└── full_ppt_video.mp4     # 完整合成视频
```
