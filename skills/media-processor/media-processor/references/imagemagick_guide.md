# ImageMagick 参数参考指南

## 目录
- [概述](#概述)
- [常用图像格式](#常用图像格式)
- [质量控制参数](#质量控制参数)
- [缩放与尺寸调整](#缩放与尺寸调整)
- [裁剪与填充](#裁剪与填充)
- [滤镜与效果](#滤镜与效果)
- [元数据处理](#元数据处理)
- [批量处理](#批量处理)
- [常见问题](#常见问题)

## 概述

ImageMagick 是一个功能强大的图像处理工具集，本参考文档列出常用的参数及其说明。

**基本语法**：
```bash
convert [输入选项] 输入文件 [操作选项] [输出选项] 输出文件
```

**或使用新的 magick 命令**：
```bash
magick [输入选项] 输入文件 [操作选项] [输出选项] 输出文件
```

## 常用图像格式

| 格式 | 扩展名 | 特点 | 适用场景 |
|------|--------|------|----------|
| JPEG | jpg, jpeg | 有损压缩，体积小 | 照片、网络传输 |
| PNG | png | 无损压缩，支持透明 | 图标、需要透明背景 |
| GIF | gif | 支持动画 | 简单动画、图标 |
| WebP | webp | 现代格式，高压缩 | 网络图像 |
| BMP | bmp | 无压缩 | Windows 兼容 |
| TIFF | tiff, tif | 无损，支持多页 | 打印、归档 |

## 质量控制参数

### Quality 参数

`-quality` 参数控制图像质量，范围 1-100。

| 格式 | Quality 说明 | 推荐值 |
|------|-------------|--------|
| JPEG | 1=最差，100=最佳 | 75-85 |
| PNG | 0-9 压缩级别（转换后） | 默认 75 转为 6 |
| WebP | 0=最差，100=最佳 | 75-85 |
| GIF | 不适用 | 不适用 |

**使用示例**：
```bash
convert input.jpg -quality 85 output.jpg
convert input.png -quality 90 output.png
```

### 压缩方法

| 参数 | 说明 |
|------|------|
| `-strip` | 移除所有元数据（推荐减小文件大小） |
| `-interlace Plane` | 渐进式 JPEG |
| `-interlace None` | 非渐进式 JPEG |
| `-sampling-factor 4:2:0` | 色度采样（减小体积） |

**使用示例**：
```bash
# 标准压缩
convert input.jpg -quality 85 -strip output.jpg

# 渐进式 JPEG
convert input.jpg -quality 85 -interlace Plane -strip output.jpg

# 更小的体积（4:2:0 色度采样）
convert input.jpg -quality 85 -strip -sampling-factor 4:2:0 output.jpg
```

## 缩放与尺寸调整

### 基本缩放

```bash
# 缩放到 800x600
convert input.jpg -resize 800x600 output.jpg

# 缩放到宽度 800，高度按比例
convert input.jpg -resize 800 output.jpg

# 缩放到高度 600，宽度按比例
convert input.jpg -resize x600 output.jpg
```

### 保持宽高比

```bash
# 缩放到 800x600 内，保持宽高比（默认）
convert input.jpg -resize 800x600 output.jpg

# 强制拉伸到 800x600（不推荐）
convert input.jpg -resize 800x600! output.jpg

# 缩放到至少 800x600（保持宽高比）
convert input.jpg -resize 800x600^ output.jpg
```

### 缩放方法

| 滤镜 | 说明 | 适用场景 |
|------|------|----------|
| lanczos | 高质量，慢 | 缩小（默认） |
| bilinear | 中等 | 一般用途 |
| nearest | 低质量，快 | 像素艺术 |
| gaussian | 柔和 | 大幅缩小 |

**使用示例**：
```bash
# 使用 lanczos 滤镜缩小
convert input.jpg -filter lanczos -resize 800x600 output.jpg

# 使用 nearest 滤镜（像素风格）
convert input.png -filter nearest -resize 256x256 output.png
```

## 裁剪与填充

### 裁剪

```bash
# 裁剪 800x600 区域
convert input.jpg -crop 800x600 output.jpg

# 裁剪 800x600，起始坐标 (100, 50)
convert input.jpg -crop 800x600+100+50 output.jpg

# 从中心裁剪
convert input.jpg -gravity center -crop 800x600+0+0 output.jpg
```

### 填充（Padding）

```bash
# 填充到 800x600，背景白色
convert input.jpg -background white -gravity center -extent 800x600 output.jpg

# 填充到 800x600，背景透明（仅 PNG）
convert input.png -background none -gravity center -extent 800x600 output.png
```

## 滤镜与效果

### 模糊与锐化

```bash
# 高斯模糊，半径 2
convert input.jpg -blur 0x2 output.jpg

# 锐化，半径 2，强度 1
convert input.jpg -unsharp 0x2+1.0+0.06 output.jpg

# 自适应锐化
convert input.jpg -adaptive-sharpen 0x1.5 output.jpg
```

### 亮度与对比度

```bash
# 增加亮度 10%
convert input.jpg -brightness-contrast 10x0 output.jpg

# 增加对比度 10%
convert input.jpg -brightness-contrast 0x10 output.jpg

# 同时调整亮度和对比度
convert input.jpg -brightness-contrast 10x15 output.jpg
```

### 旋转与翻转

```bash
# 旋转 90 度
convert input.jpg -rotate 90 output.jpg

# 水平翻转
convert input.jpg -flop output.jpg

# 垂直翻转
convert input.jpg -flip output.jpg
```

### 添加文字水印

```bash
# 添加文字，位置在右下角
convert input.jpg -pointsize 24 -fill white -gravity southeast \
  -draw "text 10,10 'Copyright 2024'" output.jpg

# 添加半透明文字
convert input.jpg -pointsize 24 -fill 'rgba(255,255,255,0.5)' \
  -gravity southeast -draw "text 10,10 'Copyright 2024'" output.jpg
```

## 元数据处理

### 查看元数据

```bash
# 查看所有元数据
identify -verbose input.jpg

# 查看 EXIF 信息
identify -format "%[exif:*]" input.jpg
```

### 移除元数据

```bash
# 移除所有元数据
convert input.jpg -strip output.jpg

# 移除 EXIF 信息
convert input.jpg -strip+profile exif output.jpg
```

### 方向处理

```bash
# 自动旋转（根据 EXIF 方向信息）
convert input.jpg -auto-orient output.jpg
```

## 批量处理

### 使用 Shell 循环

```bash
# 批量转换为 JPG
for file in *.png; do
  convert "$file" "${file%.png}.jpg"
done

# 批量缩放
for file in *.jpg; do
  convert "$file" -resize 800x600 "resized/$file"
done
```

### 使用 Mogrify（原地修改）

```bash
# 批量缩放所有 JPG 文件（原地修改，谨慎使用）
mogrify -resize 800x600 *.jpg

# 批量添加后缀（不覆盖原文件）
mogrify -resize 800x600 -path output_dir *.jpg
```

## 常见问题

### Q: 如何在不损失质量的情况下减小图像体积？
A:
1. 使用 `-strip` 移除元数据
2. 对于 JPEG，尝试 `-sampling-factor 4:2:0`
3. 使用渐进式 JPEG `-interlace Plane`

### Q: PNG 转换为 JPG 后背景变黑了？
A: 先将透明背景填充为白色：
```bash
convert input.png -background white -flatten output.jpg
```

### Q: 如何批量处理大量图像？
A: 使用 `mogrify` 命令或 shell 循环，参考"批量处理"章节。

### Q: 如何处理超大图像？
A: 使用 `-limit memory` 和 `-limit map` 限制内存使用：
```bash
convert -limit memory 256MB -limit map 512MB input.jpg -resize 800x600 output.jpg
```

### Q: 如何保持最佳图像质量？
A:
- JPEG: 使用 `-quality 90-95` 和 `-sampling-factor 4:4:4`
- PNG: 不需要额外参数，PNG 已是无损格式
- 缩放: 使用 `-filter lanczos`

### Q: 如何创建 GIF 动画？
A:
```bash
# 将多个 PNG 转换为 GIF
convert frame1.png frame2.png frame3.png animation.gif

# 设置延迟（单位：1/100 秒）
convert -delay 100 frame*.png animation.gif

# 优化 GIF 大小
convert animation.gif -fuzz 10% -layers Optimize output.gif
```
