---
name: infinitetalk
description: 音频驱动的稀疏帧视频配音工具，支持音频驱动的 Video-to-Video 和 Image-to-Video 生成，实现精准的唇形、头部、身体姿态同步，支持无限时长视频生成
dependency:
  python: |
    opencv-python>=4.9.0.80
    diffusers>=0.31.0
    transformers>=4.49.0
    tokenizers>=0.20.3
    accelerate>=1.1.1
    tqdm
    imageio
    easydict
    ftfy
    dashscope
    imageio-ffmpeg
    scikit-image
    loguru
    gradio>=5.0.0
    numpy>=1.23.5,<2
    xfuser>=0.4.1
    pyloudnorm
    optimum-quanto==0.2.6
    scenedetect
    moviepy==1.0.3
    decord
    torch>=2.0.0
    torchvision
    torchaudio
    einops
    soundfile
  system: |
    # 创建模型权重目录
    mkdir -p weights/Wan2.1-I2V-14B-480P
    mkdir -p weights/chinese-wav2vec2-base
    mkdir -p weights/InfiniteTalk/single
    mkdir -p weights/Kokoro-82M
---

# InfiniteTalk - 音频驱动视频生成

## 任务目标
- 本 Skill 用于：将音频（语音）转换为同步的说话人视频，支持从单张图片或现有视频生成音频驱动的说话视频
- 能力包含：
  - Image-to-Video：从单张图片生成音频驱动的说话视频
  - Video-to-Video：对现有视频进行音频驱动的重配音
  - 多维度同步：唇形、头部运动、身体姿态、面部表情与音频精准对齐
  - 无限时长：支持无限制时长的视频生成
  - 低显存适配：支持量化、模型卸载等显存优化方案
- 触发条件：当需要生成音频驱动的数字人视频、视频配音、虚拟主播内容时使用

## 前置准备
- 模型下载：在使用本 Skill 前，必须先下载所需的模型权重文件，具体步骤见 [references/model_download.md](references/model_download.md)
- 硬件要求：
  - GPU：推荐使用 16GB+ 显存的 GPU（可使用量化方案适配低显存设备）
  - 内存：建议 32GB+ 系统内存
  - 磁盘空间：至少 50GB 可用空间（模型权重约 30GB）
- 环境配置：详细依赖安装见 [references/environment_setup.md](references/environment_setup.md)

## 操作步骤

### 模式一：Image-to-Video（图片生成视频）
1. 准备输入
   - 确保有一张清晰的人脸图片作为输入
   - 准备音频文件（支持 mp3、wav 等格式）
   - 可选：使用 TTS 功能从文本生成音频

2. 执行生成
   - 调用 `scripts/infer_infinitetalk.py` 进行推理
   - 参数说明：
     - `input_path`: 输入图片路径
     - `audio_path`: 驱动音频路径（或提供 `text` 使用 TTS）
     - `output_path`: 输出视频路径
     - `mode`: `clip`（单段）或 `streaming`（长视频）
     - `size`: `infinitetalk-480`（480P）或 `infinitetalk-720`（720P）
     - `sample_steps`: 采样步数（默认 40）
     - `sample_audio_guide_scale`: 音频引导强度（默认 4.0）

3. 验证输出
   - 检查生成的视频是否同步良好
   - 确认唇形、头部动作与音频匹配
   - 如有异常，调整 `sample_audio_guide_scale` 参数

### 模式二：Video-to-Video（视频重配音）
1. 准备输入
   - 准备参考视频文件
   - 准备目标音频文件

2. 执行生成
   - 使用相同的脚本，但 `input_path` 指向视频文件
   - 脚本会自动提取视频的首帧作为参考

3. 处理长视频
   - 使用 `streaming` 模式生成无限时长视频
   - 通过 `motion_frame` 参数控制驱动帧长度（默认 9）

### 模式三：使用 TTS 生成音频
1. 文本转语音
   - 提供待合成的文本内容
   - 指定声音模型（Kokoro-82M）
   - 脚本会自动生成音频文件

2. 生成视频
   - 使用生成的音频驱动视频生成
   - 支持双人对话模式（使用标记 `(s1)` 和 `(s2)` 区分说话人）

## 资源索引
- 核心脚本：见 [scripts/infer_infinitetalk.py](scripts/infer_infinitetalk.py)（音频驱动视频生成推理）
- 环境配置：见 [references/environment_setup.md](references/environment_setup.md)（依赖安装和系统配置）
- 模型下载：见 [references/model_download.md](references/model_download.md)（模型权重下载指南）
- 使用示例：见 [references/usage_examples.md](references/usage_examples.md)（典型场景和命令示例）

## 注意事项
- 模型权重较大（约 30GB），首次使用需要提前下载
- 建议使用高显存 GPU（16GB+），低显存设备可使用量化方案
- 输入音频建议采样率为 16000Hz，脚本会自动进行响度归一化
- 输入图片/视频应包含清晰的人脸区域
- 生成速度取决于 GPU 性能，480P 分辨率下生成 1 秒视频约需 5-10 秒
- 如遇到显存不足错误，可尝试：
  - 降低分辨率（使用 `size=infinitetalk-480`）
  - 启用量化（添加 `--quant int8` 参数）
  - 启用模型卸载（添加 `--offload_model true`）

## 使用示例
- 基础图片生成视频：
  ```bash
  python scripts/infer_infinitetalk.py \
    --input_path ./input.jpg \
    --audio_path ./audio.wav \
    --output_path ./output.mp4 \
    --size infinitetalk-480 \
    --mode clip
  ```
- 长视频生成：
  ```bash
  python scripts/infer_infinitetalk.py \
    --input_path ./input.jpg \
    --audio_path ./long_audio.wav \
    --output_path ./long_output.mp4 \
    --size infinitetalk-480 \
    --mode streaming
  ```
- 使用 TTS 生成：
  ```bash
  python scripts/infer_infinitetalk.py \
    --input_path ./input.jpg \
    --text "你好，今天天气真不错" \
    --output_path ./tts_output.mp4 \
    --size infinitetalk-480
  ```
