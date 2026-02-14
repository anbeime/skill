# 品牌风格示例

本目录用于存放品牌风格示例文件。

## 文件类型

- PPT 样例：展示完整的品牌风格
- 图片：品牌 logo、产品图、色板
- 品牌手册：品牌指南文档

## 使用方法

1. 将品牌样例文件放入此目录
2. 执行品牌风格学习：
   ```bash
   python scripts/style_learner.py \
     --examples-dir ./assets/styles/ \
     --output ./brand_style.json
   ```
3. 生成的 brand_style.json 会被后续生成使用

## 示例结构

```
assets/styles/
├── example_ppt.pptx
├── brand_logo.png
├── product_image.png
├── color_palette.png
└── brand_guideline.pdf
```
