---
name: media-processor
description: 提供基于 FFmpeg 和 ImageMagick 的多媒体处理能力，支持视频和图像的格式转换、分辨率调整、压缩等操作
dependency:
  system:
    - apt-get update && apt-get install -y ffmpeg imagemagick
---

# Media Processor

## 任务目标
- 本 Skill 用于：处理视频和图像文件，进行格式转换、分辨率调整、压缩等操作
- 能力包含：
  - 视频格式转换（MP4/AVI/MOV/MKV 等）
  - 视频分辨率调整和压缩
  - 图像格式转换（JPG/PNG/GIF/WebP 等）
  - 图像分辨率调整和压缩
  - 批量处理支持
- 触发条件：当用户需要处理视频或图像文件时触发

## 前置准备
- 依赖说明：本 Skill 依赖以下系统工具
  - FFmpeg：视频处理工具
  - ImageMagick：图像处理工具
- 系统依赖安装：Skill 首次使用时将自动安装系统依赖
  ```bash
  apt-get update && apt-get install -y ffmpeg imagemagick
  ```

## 操作步骤

### 标准流程

1. **需求分析**
   - 识别输入文件类型（视频/图像）
   - 确定目标格式、分辨率、质量要求
   - 评估是否需要批量处理

2. **选择处理方式**
   - 视频处理：调用 `scripts/` 中的视频处理脚本
   - 图像处理：调用 `scripts/` 中的图像处理脚本

3. **执行处理**
   - 对于简单操作（如单一格式转换）：直接调用相应脚本
   - 对于复杂操作（如多步骤处理）：智能体将调用多个脚本组合使用

4. **结果验证**
   - 检查输出文件是否生成
   - 验证文件格式和参数是否符合预期

### 常见操作指南

#### 视频格式转换
- 调用 `scripts/video_convert.py`
- 参数：input_path（输入路径）、output_path（输出路径）、output_format（目标格式）
- 示例：将 AVI 转换为 MP4

#### 视频压缩
- 调用 `scripts/video_compress.py`
- 参数：input_path、output_path、bitrate（目标码率）、crf（质量控制系数）
- 示例：压缩视频到 2Mbps

#### 视频分辨率调整
- 调用 `scripts/video_scale.py`
- 参数：input_path、output_path、width、height
- 示例：调整到 1920x1080

#### 图像格式转换
- 调用 `scripts/image_convert.py`
- 参数：input_path、output_path、output_format、quality
- 示例：将 PNG 转换为 JPG

#### 图像缩放
- 调用 `scripts/image_scale.py`
- 参数：input_path、output_path、width、height、maintain_aspect
- 示例：等比缩放到 1024x768

#### 图像压缩
- 调用 `scripts/image_compress.py`
- 参数：input_path、output_path、quality、method（压缩方法）
- 示例：质量设置为 85%

### 批量处理
- 当需要处理多个文件时，智能体将循环调用相应脚本
- 使用通配符模式匹配文件（如 `*.avi`、`images/*.png`）
- 为每个文件生成对应的输出路径

## 资源索引
- 视频处理脚本：
  - [scripts/video_convert.py](scripts/video_convert.py) - 视频格式转换
  - [scripts/video_compress.py](scripts/video_compress.py) - 视频压缩
  - [scripts/video_scale.py](scripts/video_scale.py) - 视频分辨率调整
- 图像处理脚本：
  - [scripts/image_convert.py](scripts/image_convert.py) - 图像格式转换
  - [scripts/image_scale.py](scripts/image_scale.py) - 图像缩放
  - [scripts/image_compress.py](scripts/image_compress.py) - 图像压缩
- 参考文档：
  - [references/ffmpeg_guide.md](references/ffmpeg_guide.md) - FFmpeg 参数参考（需要高级参数时读取）
  - [references/imagemagick_guide.md](references/imagemagick_guide.md) - ImageMagick 参数参考（需要高级参数时读取）

## 注意事项
- 确保输入文件路径正确，使用相对路径（`./` 开头）
- 输出路径需要包含完整文件名和扩展名
- 质量参数范围：图像质量 1-100，视频 CRF 18-28（数值越小质量越高）
- 处理大文件时请耐心等待，智能体会持续监控执行状态
- 如果需要自定义参数（如编码器、帧率等），请参考相应参考文档

## 使用示例

### 示例1：视频格式转换
```python
# 将 video.avi 转换为 video.mp4
python scripts/video_convert.py \
  --input ./video.avi \
  --output ./video.mp4 \
  --format mp4
```

### 示例2：图像批量转换
```python
# 将所有 PNG 转换为 JPG
for file in ./images/*.png; do
  output="${file%.png}.jpg"
  python scripts/image_convert.py \
    --input "$file" \
    --output "$output" \
    --format jpg \
    --quality 85
done
```

### 示例3：视频压缩与缩放
```python
# 先缩放再压缩
python scripts/video_scale.py \
  --input ./input.mp4 \
  --output ./temp.mp4 \
  --width 1280 \
  --height 720

python scripts/video_compress.py \
  --input ./temp.mp4 \
  --output ./output.mp4 \
  --bitrate 2M
```
