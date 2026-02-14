# FFmpeg 参数参考指南

## 目录
- [概述](#概述)
- [常用视频编码器](#常用视频编码器)
- [常用音频编码器](#常用音频编码器)
- [质量控制参数](#质量控制参数)
- [分辨率与缩放](#分辨率与缩放)
- [视频裁剪](#视频裁剪)
- [高级参数](#高级参数)
- [常见问题](#常见问题)

## 概述

FFmpeg 是一个功能强大的多媒体处理工具，本参考文档列出常用的参数及其说明。

**基本语法**：
```bash
ffmpeg [全局选项] [输入选项] -i 输入文件 [输出选项] 输出文件
```

## 常用视频编码器

| 编码器 | 说明 | 适用场景 | 质量/压缩比 |
|--------|------|----------|------------|
| libx264 | H.264 编码 | 通用视频编码，兼容性好 | 高/平衡 |
| libx265 | H.265 (HEVC) 编码 | 高压缩需求，支持 4K/8K | 很高/更高 |
| libvpx | VP8 编码 | WebM 格式 | 中/高 |
| libvpx-vp9 | VP9 编码 | WebM 格式，高压缩 | 高/很高 |
| copy | 直接复制流 | 不重新编码（快速） | 无损 |

**使用示例**：
```bash
ffmpeg -i input.mp4 -c:v libx264 output.mp4
ffmpeg -i input.mp4 -c:v libx265 -crf 28 output.mp4
```

## 常用音频编码器

| 编码器 | 说明 | 适用场景 |
|--------|------|----------|
| aac | AAC 编码 | 通用音频编码 |
| libmp3lame | MP3 编码 | MP3 格式 |
| libopus | Opus 编码 | 高质量音频 |
| copy | 直接复制流 | 不重新编码 |

**使用示例**：
```bash
ffmpeg -i input.mp4 -c:a aac -b:a 128k output.mp4
ffmpeg -i input.mp4 -c:a libmp3lame -b:a 192k output.mp3
```

## 质量控制参数

### CRF（Constant Rate Factor）

CRF 是控制视频质量的主要参数，数值越小质量越高，文件越大。

| CRF 值 | 质量 | 适用场景 |
|--------|------|----------|
| 18-23 | 很高 | 高质量视频，归档 |
| 23-28 | 高 | 通用用途（默认 23） |
| 28-34 | 中 | 网络传输，节省空间 |
| 34+ | 低 | 极度压缩 |

**使用示例**：
```bash
ffmpeg -i input.mp4 -crf 23 output.mp4
```

### 码率控制

| 参数 | 说明 | 示例 |
|------|------|------|
| -b:v | 视频码率 | `-b:v 2M` (2 Mbps) |
| -b:a | 音频码率 | `-b:a 128k` (128 kbps) |

**使用示例**：
```bash
ffmpeg -i input.mp4 -b:v 2M -b:a 128k output.mp4
```

### 预设（Preset）

预设影响编码速度和压缩效率：

| 预设 | 速度 | 压缩效率 | 适用场景 |
|------|------|----------|----------|
| ultrafast | 最快 | 最低 | 快速预览 |
| superfast | 很快 | 很低 | 快速处理 |
| veryfast | 快 | 低 | 实时编码 |
| faster | 较快 | 较低 | 通用快速 |
| fast | 中 | 中 | 平衡选择 |
| medium | 中等 | 中等 | 默认值 |
| slow | 慢 | 高 | 高质量 |
| slower | 更慢 | 更高 | 最高质量 |
| veryslow | 很慢 | 很高 | 最终输出 |

**使用示例**：
```bash
ffmpeg -i input.mp4 -preset medium output.mp4
```

## 分辨率与缩放

### 使用 -vf 参数

**缩放到指定尺寸**：
```bash
ffmpeg -i input.mp4 -vf scale=1920:1080 output.mp4
```

**保持宽高比**：
```bash
# 宽度 1280，高度自动调整（必须是偶数）
ffmpeg -i input.mp4 -vf scale=1280:-2 output.mp4

# 高度 720，宽度自动调整
ffmpeg -i input.mp4 -vf scale=-2:720 output.mp4

# fit 到 1280x720 内
ffmpeg -i input.mp4 -vf scale="'min(1280,iw)':'min(720,ih)'" output.mp4
```

## 视频裁剪

### 时间裁剪

```bash
# 裁剪前 10 秒
ffmpeg -i input.mp4 -t 10 output.mp4

# 从第 30 秒开始，裁剪 15 秒
ffmpeg -i input.mp4 -ss 30 -t 15 output.mp4

# 从第 30 秒开始到结束
ffmpeg -i input.mp4 -ss 30 output.mp4
```

### 区域裁剪

```bash
# 裁剪 1920x1080 视频的左上角 640x480 区域
ffmpeg -i input.mp4 -vf crop=640:480:0:0 output.mp4

# 裁剪中心区域
ffmpeg -i input.mp4 -vf crop=640:480:(iw-640)/2:(ih-480)/2 output.mp4
```

## 高级参数

### 帧率控制

```bash
# 设置帧率为 30 fps
ffmpeg -i input.mp4 -r 30 output.mp4

# 设置最小/最大帧率
ffmpeg -i input.mp4 -rmin 15 -rmax 60 output.mp4
```

### 关键帧间隔

```bash
# 每 2 秒一个关键帧
ffmpeg -i input.mp4 -g 60 output.mp4  # 假设帧率 30 fps
```

### 音频处理

```bash
# 提取音频
ffmpeg -i input.mp4 -vn output.mp3

# 移除音频
ffmpeg -i input.mp4 -an output.mp4

# 调整音量
ffmpeg -i input.mp4 -af "volume=2" output.mp4
```

### 多通道处理

```bash
# 选择特定流
ffmpeg -i input.mp4 -map 0:v:0 -map 0:a:0 output.mp4

# 处理多输入
ffmpeg -i input1.mp4 -i input2.mp4 -filter_complex "[0:v][1:v]concat=n=2:v=1" output.mp4
```

## 常见问题

### Q: 如何提高转码速度？
A: 使用 `-preset` 参数选择更快的预设，如 `ultrafast` 或 `superfast`。

### Q: 如何减小文件大小？
A:
1. 降低 CRF 值（如 28 或 32）
2. 使用更高效的编码器（如 H.265）
3. 降低分辨率
4. 降低音频码率

### Q: 如何保持最高质量？
A: 使用 `-crf 18` 和 `-preset slow` 或 `-preset veryslow`。

### Q: 输出文件有黑边怎么办？
A: 使用 `crop` 滤镜移除黑边，或使用 `pad` 滤镜填充。

### Q: 如何批量处理文件？
A: 使用 shell 循环：
```bash
for file in *.avi; do
  ffmpeg -i "$file" "${file%.avi}.mp4"
done
```
