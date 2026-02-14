# 路演视频风格导出指南

本指南说明如何将网页设计分析结果导出为路演视频可用的品牌风格配置。

## 概览

通过本功能，您可以将从网页截图中提取的设计系统转换为 PPT 路演视频生成器可用的品牌风格配置，实现从网页设计到视频风格的快速迁移。

## 输出格式

转换后的品牌风格配置 (brand_style.json) 包含以下字段：

```json
{
  "colors": {
    "primary": "#3498db",
    "secondary": "#2980b9",
    "accent": "#e74c3c",
    "background": "#ecf0f1",
    "text": "#2c3e50"
  },
  "fonts": {
    "title": "Arial Bold",
    "body": "Arial",
    "accent": "Arial Italic"
  },
  "design_elements": {
    "logo": "",
    "icons": [],
    "patterns": []
  },
  "layout_style": "minimalist",
  "overall_theme": "Professional Business Style"
}
```

## 导出流程

### 步骤 1：分析网页设计

使用 `web-design-analyzer` 分析网页截图，生成设计系统 JSON。

```bash
python scripts/analyze_design.py \
  --image ./landing-page.png \
  --output ./design_system.json
```

### 步骤 2：转换为路演品牌风格

使用转换脚本将设计系统转换为路演品牌风格。

```bash
python scripts/convert_to_roadshow_style.py \
  --input ./design_system.json \
  --output ./brand_style.json
```

**参数说明**：
- `--input`: web-design-analyzer 输出的 JSON 文件路径
- `--output`: 输出的 brand_style.json 文件路径（默认: brand_style.json）

### 步骤 3：在路演视频生成器中使用

将生成的 `brand_style.json` 传递给 `ppt-roadshow-generator` Skill，作为品牌风格配置。

```
智能体：我已经分析了您的网页设计，并生成了品牌风格配置。现在我可以使用这个风格生成路演视频。
用户：太好了，开始生成吧！
```

## 转换规则

### 颜色映射

转换脚本会智能映射颜色角色：

| web-design-analyzer | ppt-roadshow-generator |
|---------------------|------------------------|
| primary / main | primary |
| secondary / sub | secondary |
| accent / highlight | accent |
| background / bg | background |
| text / foreground | text |

**默认值**：
- background: #ffffff
- text: #2c3e50

### 字体映射

| web-design-analyzer | ppt-roadshow-generator |
|---------------------|------------------------|
| typography 字符串 | fonts.title / fonts.body / fonts.accent |
| title 字段 | fonts.title (加 Bold) |
| body 字段 | fonts.body |
| accent 字段 | fonts.accent |

**默认值**：
- title: Arial Bold
- body: Arial
- accent: Arial Italic

### 布局风格推断

转换脚本会根据设计系统的关键词智能推断布局风格：

| 关键词 | layout_style |
|--------|-------------|
| professional, business, corporate, minimalist, clean, elegant, refined | business |
| modern, tech, cyber, futuristic, digital, innovation, gradient, glassmorphism | tech |
| creative, playful, vibrant, bold, dynamic, energetic, artistic | creative |
| minimalist, simple, minimal, basic, essential | minimalist |

**默认值**：minimalist

## 使用示例

### 示例 1：完整协同流程

```
用户：我有一个网页截图，想要用同样的风格制作路演视频。

智能体：
1. 我先分析这个网页截图，提取设计系统。
   [调用 analyze_design.py]

2. 然后将设计系统转换为路演品牌风格。
   [调用 convert_to_roadshow_style.py]

3. 最后使用这个品牌风格生成路演视频。
   [切换到 ppt-roadshow-generator Skill]
```

### 示例 2：仅导出品牌风格

```
用户：分析这个网页，并导出为路演视频风格配置。

智能体：
1. 分析网页设计...
   [调用 analyze_design.py]

2. 转换为路演品牌风格...
   [调用 convert_to_roadshow_style.py]

3. 品牌风格配置已保存到 brand_style.json，您可以将其用于路演视频生成。
```

## 注意事项

- **颜色完整性**：如果设计系统中颜色信息不完整，转换脚本会使用默认值填充
- **字体解析**：typography 字段如果是字符串，会自动推断 title、body、accent；如果是对象，直接映射
- **风格推断**：布局风格的推断基于关键词匹配，可能不完全准确，建议人工确认
- **设计元素**：web-design-analyzer 不提取 logo、图标、图案等设计元素，转换后这些字段为空

## 与其他 Skill 协同

### 与 ppt-roadshow-generator 协同

完整的"网页设计 → 路演视频"工作流：

1. 使用 `web-design-analyzer` 分析网页截图
2. 调用转换脚本生成品牌风格
3. 使用 `ppt-roadshow-generator` 导入品牌风格
4. 生成风格统一的路演视频

详见 [ppt-roadshow-generator/references/design-system-import-guide.md](../ppt-roadshow-generator/references/design-system-import-guide.md)
