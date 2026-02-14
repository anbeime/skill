# JSON 格式规范

本文档定义了 pptx-generator Skill 所需的 JSON 数据格式规范。

## 目录
1. [整体结构](#整体结构)
2. [元数据 (metadata)](#元数据-metadata)
3. [幻灯片 (slides)]#幻灯片-slides)
4. [布局类型 (layout)](#布局类型-layout)
5. [示例](#示例)
6. [验证规则](#验证规则)

---

## 整体结构

JSON 数据必须包含以下顶层字段：

```json
{
  "metadata": { ... },
  "slides": [ ... ]
}
```

| 字段 | 必需性 | 类型 | 说明 |
|------|--------|------|------|
| metadata | 推荐 | Object | 演示文稿元数据 |
| slides | 必需 | Array | 幻灯片数组 |

---

## 元数据 (metadata)

元数据包含演示文稿的基本信息：

```json
{
  "metadata": {
    "title": "演示文稿标题",
    "author": "作者姓名",
    "theme": "主题风格"
  }
}
```

| 字段 | 必需性 | 类型 | 说明 | 示例 |
|------|--------|------|------|------|
| title | 推荐 | String | 演示文稿标题 | "产品介绍" |
| author | 可选 | String | 作者姓名 | "张三" |
| theme | 可选 | String | 主题风格 | "科技感" |

---

## 幻灯片 (slides)

每个幻灯片对象包含以下字段：

```json
{
  "layout": "ContentSlide",
  "title": "幻灯片标题",
  "content": ["内容要点1", "内容要点2"],
  "notes": "备注内容"
}
```

| 字段 | 必需性 | 类型 | 说明 | 示例 |
|------|--------|------|------|------|
| layout | 可选 | String | 布局类型 | "ContentSlide" |
| title | 必需 | String | 幻灯片标题 | "核心功能" |
| content | 必需 | Array | 内容数组 | ["功能1", "功能2"] |
| notes | 可选 | String | 备注内容 | "详细说明" |

---

## 布局类型 (layout)

支持的布局类型：

| 布局类型 | 说明 | 使用场景 |
|----------|------|----------|
| TitleSlide | 标题页 | 封面、标题页 |
| ContentSlide | 内容页 | 标题 + 内容 |
| TwoColumnSlide | 两栏页 | 对比、并列内容 |
| SectionHeaderSlide | 章节页 | 章节分隔 |
| ContentWithCaptionSlide | 带说明的内容页 | 图片 + 说明 |
| SummarySlide | 总结页 | 总结、结尾 |

---

## 示例

### 完整示例

```json
{
  "metadata": {
    "title": "产品介绍演示",
    "author": "张三",
    "theme": "科技感"
  },
  "slides": [
    {
      "layout": "TitleSlide",
      "title": "AI 智能助手",
      "content": [
        "新一代人工智能助手",
        "提升工作效率",
        "智能对话交互"
      ],
      "notes": "开场白，介绍产品定位"
    },
    {
      "layout": "ContentSlide",
      "title": "核心功能",
      "content": [
        "自然语言理解",
        "智能内容生成",
        "多模态交互",
        "个性化定制"
      ],
      "notes": "详细介绍产品核心功能"
    },
    {
      "layout": "ContentSlide",
      "title": "技术优势",
      "content": [
        "先进的语言模型",
        "高效的知识检索",
        "安全的数据处理",
        "灵活的部署方案"
      ],
      "notes": "说明技术优势"
    },
    {
      "layout": "SummarySlide",
      "title": "总结",
      "content": [
        "AI 智能助手",
        "提升效率，创造价值",
        "开启智能新时代"
      ],
      "notes": "总结发言"
    }
  ]
}
```

### 最小示例

```json
{
  "metadata": {
    "title": "演示文稿"
  },
  "slides": [
    {
      "title": "第一页",
      "content": ["内容1", "内容2"]
    }
  ]
}
```

---

## 验证规则

### 必需字段

以下字段为必需：
- `slides` 数组
- 每个幻灯片的 `title` 字段
- 每个幻灯片的 `content` 数组

### 数据类型

| 字段 | 期望类型 | 说明 |
|------|----------|------|
| metadata | Object | 元数据对象 |
| title | String | 标题字符串 |
| author | String | 作者字符串 |
| theme | String | 主题字符串 |
| layout | String | 布局类型字符串 |
| content | Array | 内容数组 |
| notes | String | 备注字符串 |

### 内容要求

1. **标题**：
   - 不能为空字符串
   - 建议长度：1-50 个字符

2. **内容数组**：
   - 不能为空数组
   - 每个元素必须是字符串
   - 建议每页 3-7 个要点

3. **备注**：
   - 可选字段
   - 可为空字符串

### 验证命令

使用 `json_validator.py` 验证 JSON 格式：

```bash
python scripts/json_validator.py --input ./ppt_data.json
```

验证结果：
- ✓ 验证通过：JSON 格式正确
- ⚠️ 警告：JSON 格式基本正确，但有建议
- ❌ 错误：JSON 格式不正确，需要修复
