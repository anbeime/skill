# 设计系统导入指南

本指南说明如何导入从网页设计中提取的设计系统，并将其应用于路演视频生成。

## 概览

通过本功能，您可以导入从 `web-design-analyzer` 提取的设计系统，并将其转换为品牌风格配置，使生成的路演视频保持与网页设计一致的视觉风格。

## 协同流程

### 完整工作流

```
网页截图 → web-design-analyzer → 设计系统 JSON
            ↓ 转换
        brand_style.json → ppt-roadshow-generator → 路演视频
```

### 步骤 1：分析网页设计（使用 web-design-analyzer）

上传网页截图，分析并提取设计系统。

```bash
# 在 web-design-analyzer Skill 中执行
python scripts/analyze_design.py \
  --image ./landing-page.png \
  --output ./design_system.json
```

### 步骤 2：转换为路演品牌风格（使用 web-design-analyzer）

将设计系统转换为路演视频可用的品牌风格配置。

```bash
# 在 web-design-analyzer Skill 中执行
python scripts/convert_to_roadshow_style.py \
  --input ./design_system.json \
  --output ./brand_style.json
```

### 步骤 3：导入品牌风格（使用 ppt-roadshow-generator）

在路演视频生成器中导入品牌风格配置。

```
智能体：我已准备好品牌风格配置，现在可以开始生成路演视频。
```

## 导入方式

### 方式 1：用户提供 brand_style.json

1. **用户提供文件**：
   ```
   用户：我有一个品牌风格配置文件 brand_style.json，请使用这个风格生成路演视频。
   ```

2. **智能体读取配置**：
   - 读取 brand_style.json 文件
   - 验证格式完整性
   - 确认风格是否符合预期

3. **应用品牌风格**：
   - 在视觉设计中使用配色和字体
   - 在字幕设计中应用字体和配色
   - 在音频设计中选择匹配风格的音效和音乐

### 方式 2：与 web-design-analyzer 完全协同

1. **用户提供网页截图**：
   ```
   用户：分析这个网页，然后用同样的风格制作路演视频。
   ```

2. **智能体切换到 web-design-analyzer**：
   - 分析网页截图
   - 生成设计系统 JSON
   - 转换为 brand_style.json

3. **智能体切换回 ppt-roadshow-generator**：
   - 导入 brand_style.json
   - 生成路演视频

### 方式 3：使用 style_learner.py 导入

如果已有 brand_style.json 文件，可以直接加载：

```bash
python scripts/style_learner.py \
  --load-json ./brand_style.json \
  --output ./brand_style_loaded.json
```

**参数说明**：
- `--load-json`: 已有的 brand_style.json 文件路径
- `--output`: 输出文件路径（可选，默认覆盖原文件）

## 品牌风格应用

### 在视觉设计中应用

智能体生成 PPT 图片时，参考品牌风格：

```python
# 智能体指导
根据 brand_style.json 的配置：
- 使用 primary 颜色 (#3498db) 作为主色调
- 使用 secondary 颜色 (#2980b9) 作为辅助色
- 使用 title 字体 (Arial Bold) 作为标题字体
- 使用 body 字体 (Arial) 作为正文字体
```

### 在字幕设计中应用

字幕文件应用品牌字体和配色：

```python
# 智能体指导
根据 brand_style.json 的配置：
- 标题字幕使用 title 字体和 primary 颜色
- 正文字幕使用 body 字体和 text 颜色
- 强调内容使用 accent 颜色
```

### 在音频设计中应用

根据 layout_style 选择音效和音乐：

| layout_style | 音效风格 | 音乐风格 |
|--------------|---------|---------|
| business | 专业、稳重 | 企业宣传片风格 |
| tech | 现代、科技感 | 电子、未来感 |
| creative | 活泼、动感 | 流行、活力 |
| minimalist | 简洁、轻盈 | 轻音乐、氛围音乐 |

## 使用示例

### 示例 1：从网页设计到路演视频

```
用户：我有一个产品网页，想要制作一个路演视频，风格要和网页一致。

智能体：
1. 我先分析您的网页截图，提取设计系统。
   [切换到 web-design-analyzer]
   [调用 analyze_design.py]
   [调用 convert_to_roadshow_style.py]

2. 品牌风格配置已生成，包含：
   - 主色调：#3498db
   - 辅助色：#2980b9
   - 字体：Arial
   - 布局风格：business

3. 现在我开始生成路演视频，保持与网页设计一致的风格。
   [切换到 ppt-roadshow-generator]
   [导入 brand_style.json]
   [生成路演视频]
```

### 示例 2：导入已有的品牌风格

```
用户：这是我的品牌风格配置文件，请用它生成路演视频。

智能体：
1. 读取 brand_style.json...
   ✓ 配置验证通过

2. 应用品牌风格：
   - 颜色：primary=#3498db, secondary=#2980b9, accent=#e74c3c
   - 字体：title=Arial Bold, body=Arial
   - 布局风格：business

3. 开始生成路演视频...
```

### 示例 3：对比两种风格

```
用户：用网页 A 的风格生成一个视频，再用网页 B 的风格生成一个视频，对比一下。

智能体：
1. 分析网页 A...
   [生成 brand_style_A.json]

2. 生成视频 A...
   [使用 brand_style_A.json]

3. 分析网页 B...
   [生成 brand_style_B.json]

4. 生成视频 B...
   [使用 brand_style_B.json]

5. 对比结果：
   - 视频 A：商务专业风格，蓝色主色调
   - 视频 B：现代科技风格，深色背景 + 霓虹色
```

## 注意事项

- **格式验证**：导入 brand_style.json 时，确保包含必需字段（colors、fonts、layout_style）
- **颜色完整性**：如果配置中缺少某些颜色字段，会使用默认值填充
- **字体兼容性**：确保字体名称在目标系统中可用，否则会回退到默认字体
- **风格一致性**：导入的品牌风格会影响整个视频，包括图片、字幕、音效等
- **设计元素**：web-design-analyzer 不提取 logo、图标等设计元素，这些字段在导入后为空，需要额外补充

## 与其他 Skill 协同

### 与 web-design-analyzer 协同

完整的"网页设计 → 路演视频"工作流：

1. 使用 `web-design-analyzer` 分析网页截图
2. 调用转换脚本生成品牌风格
3. 使用 `ppt-roadshow-generator` 导入品牌风格
4. 生成风格统一的路演视频

详见 [web-design-analyzer/references/roadshow-export-guide.md](../web-design-analyzer/references/roadshow-export-guide.md)

### 协同最佳实践

1. **风格一致性**：确保网页设计和路演视频使用同一品牌风格配置
2. **多次复用**：一旦生成品牌风格配置，可以重复使用于多个视频项目
3. **版本管理**：为不同项目维护不同的 brand_style.json 文件
4. **风格微调**：可以在导入后手动调整 brand_style.json 的某些字段

## 故障排查

### 问题：导入后颜色不一致

**原因**：brand_style.json 中颜色字段缺失或格式错误

**解决**：
1. 检查 brand_style.json 是否包含必需的颜色字段（primary、secondary、accent、background、text）
2. 确保颜色格式为 Hex 格式（如 #3498db）

### 问题：字体未生效

**原因**：字体名称在目标系统中不可用

**解决**：
1. 使用通用字体名称（Arial、Helvetica、Times New Roman）
2. 或手动修改 brand_style.json 中的字体名称为可用字体

### 问题：风格转换不准确

**原因**：web-design-analyzer 提取的设计系统信息不完整

**解决**：
1. 确保提供的网页截图清晰完整
2. 手动编辑 brand_style.json，调整颜色、字体或布局风格
