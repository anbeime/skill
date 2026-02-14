# PPT 样式模板配置

本目录用于存放 PPT 的自定义样式模板文件。

当前版本使用默认样式，如需自定义字体、颜色、主题等，可以在此添加配置文件。

## 模板文件格式（待扩展）

未来版本支持通过以下方式自定义 PPT 样式：

1. **颜色主题配置**
   - 定义主色调、辅助色、强调色等

2. **字体配置**
   - 定义标题字体、正文字体、字号等

3. **布局模板**
   - 自定义幻灯片布局

## 使用方法（规划中）

```bash
python scripts/generate_pptx.py \
  --input ./ppt_data.json \
  --output ./presentation.pptx \
  --template ./assets/ppt_templates/custom_theme.json
```

## 默认样式说明

当前版本使用 python-pptx 的默认样式：
- 字体：Calibri (中文使用微软雅黑)
- 标题字号：36pt
- 正文字号：20pt
- 颜色：主题色为蓝色
