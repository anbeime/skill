# 品牌风格学习指南

本指南说明如何使用品牌风格学习功能，确保生成的 PPT 保持一致的品牌形象。

## 概览

品牌风格学习功能允许用户上传品牌样例（PPT、图片、品牌手册），系统将分析并提取：
- 配色方案（主色、辅助色、强调色）
- 字体类型（标题字体、正文字体）
- 设计元素（logo、图标、装饰）
- 布局风格（简约/商务/创意/科技）

## 品牌风格结构

### JSON 格式

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
    "logo": "logo.png",
    "icons": ["icon1.png", "icon2.png"],
    "patterns": ["pattern1.png"]
  },
  "layout_style": "minimalist",
  "overall_theme": "Professional Business Style"
}
```

### 字段说明

#### colors
- `primary`：品牌主色调，用于标题、关键元素
- `secondary`：辅助色，用于背景、次要元素
- `accent`：强调色，用于重要信息、按钮
- `background`：背景色
- `text`：文本颜色

#### fonts
- `title`：标题字体
- `body`：正文字体
- `accent`：强调字体（斜体、粗体等）

#### design_elements
- `logo`：logo 文件路径
- `icons`：图标文件列表
- `patterns`：装饰图案列表

#### layout_style
- `minimalist`：极简风格
- `business`：商务风格
- `creative`：创意风格
- `tech`：科技风格

#### overall_theme
- 整体风格描述，由智能体分析后生成

## 学习流程

### 方式 1：上传品牌样例

1. **准备样例文件**：
   - PPT 样例（包含多页，展示完整风格）
   - 品牌手册（PDF 或图片）
   - 关键图片（logo、产品图、品牌色板）

2. **上传到指定目录**：
   ```bash
   mkdir -p brand_examples
   # 将样例文件放入 brand_examples/ 目录
   ```

3. **执行品牌风格学习**：
   ```bash
   python scripts/style_learner.py \
     --examples-dir ./brand_examples \
     --output ./brand_style.json
   ```

### 方式 2：提供风格描述

1. **提供风格描述**：
   ```
   品牌风格：
   - 主色调：蓝色 (#3498db)
   - 辅助色：浅蓝色 (#2980b9)
   - 强调色：红色 (#e74c3c)
   - 字体：Arial
   - 风格：商务专业
   ```

2. **执行品牌风格学习**：
   ```bash
   python scripts/style_learner.py \
     --style-description "蓝色主色调，商务专业风格" \
     --output ./brand_style.json
   ```

### 方式 3：智能体分析

1. **用户提供品牌样例**
2. **智能体分析样例**：
   - 提取配色方案
   - 识别字体
   - 分析布局风格
3. **智能体生成结构化品牌风格数据**
4. **保存为 brand_style.json**

## 应用品牌风格

### 在视觉设计中应用

智能体生成图片时，参考品牌风格：

```
根据品牌风格配置：
- 主色调：#3498db
- 辅助色：#2980b9
- 生成 PPT 图片，保持色调一致
```

### 在音频设计中应用

选择与品牌风格匹配的音效和音乐：

```
商务风格 → 专业、稳重的背景音乐
创意风格 → 活泼、轻快的背景音乐
科技风格 → 现代、电子感的背景音乐
```

### 在字幕设计中应用

使用品牌字体和配色：

```
标题：使用品牌标题字体和主色调
正文：使用品牌正文字体和文本颜色
强调：使用品牌强调色
```

## 常见品牌风格模板

### 商务专业风格

```json
{
  "colors": {
    "primary": "#2c3e50",
    "secondary": "#34495e",
    "accent": "#3498db",
    "background": "#ecf0f1",
    "text": "#2c3e50"
  },
  "fonts": {
    "title": "Helvetica Bold",
    "body": "Helvetica",
    "accent": "Helvetica Italic"
  },
  "layout_style": "business",
  "overall_theme": "Professional Business Style"
}
```

### 科技创新风格

```json
{
  "colors": {
    "primary": "#00d4ff",
    "secondary": "#0a84ff",
    "accent": "#ff2d55",
    "background": "#0f0f23",
    "text": "#ffffff"
  },
  "fonts": {
    "title": "SF Pro Display Bold",
    "body": "SF Pro Text",
    "accent": "SF Pro Display Medium"
  },
  "layout_style": "tech",
  "overall_theme": "Modern Technology Style"
}
```

### 创意活泼风格

```json
{
  "colors": {
    "primary": "#ff6b6b",
    "secondary": "#feca57",
    "accent": "#48dbfb",
    "background": "#f7f1e3",
    "text": "#2d3436"
  },
  "fonts": {
    "title": "Poppins Bold",
    "body": "Poppins",
    "accent": "Poppins SemiBold"
  },
  "layout_style": "creative",
  "overall_theme": "Creative Playful Style"
}
```

### 简约极简风格

```json
{
  "colors": {
    "primary": "#000000",
    "secondary": "#333333",
    "accent": "#666666",
    "background": "#ffffff",
    "text": "#000000"
  },
  "fonts": {
    "title": "Arial Black",
    "body": "Arial",
    "accent": "Arial Bold"
  },
  "layout_style": "minimalist",
  "overall_theme": "Minimalist Style"
}
```

## 保持风格一致性的技巧

### 1. 颜色使用规范
- 主色调占比 60%
- 辅助色占比 30%
- 强调色占比 10%

### 2. 字体层级
- 标题：大字号，粗体
- 副标题：中字号，中等粗细
- 正文：小字号，常规字重
- 注释：最小字号，斜体

### 3. 布局原则
- 保持对齐和间距一致
- 留白充足，避免拥挤
- 视觉重心明确

### 4. 元素复用
- 复用 logo、图标、装饰元素
- 保持设计语言一致
- 避免混用过多不同元素

## 验证品牌风格

### 视觉检查清单
- [ ] 主色调应用正确
- [ ] 辅助色使用恰当
- [ ] 强调色突出重点
- [ ] 字体层级清晰
- [ ] 布局风格一致

### 自动验证（脚本）
```bash
# 验证品牌风格 JSON 格式
python scripts/style_learner.py \
  --load-style ./brand_style.json \
  --validate
```

## 常见问题

### Q1：如何更新品牌风格？
A：重新执行品牌风格学习，覆盖原有的 brand_style.json

### Q2：可以保存多个品牌风格吗？
A：可以，使用不同的文件名保存，如 brand_style_companyA.json、brand_style_companyB.json

### Q3：品牌风格学习失败怎么办？
A：
- 确保样例文件清晰、多样
- 提供足够的样例（建议 5-10 张图片）
- 手动创建 brand_style.json

### Q4：如何应用到已有的 PPT？
A：
- 学习品牌风格
- 重新生成图片
- 应用新的品牌风格

## 总结

品牌风格学习是保持 PPT 一致性的关键功能：
1. 上传品牌样例
2. 系统分析并提取风格
3. 保存为配置文件
4. 后续生成时自动应用

通过品牌风格学习，可以一次性生成 15-100 页风格统一的 PPT！
