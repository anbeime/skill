# 使用示例

## 概览
本文档提供 InfiniteTalk 的典型使用场景和命令示例。

## 示例 1：基础图片生成视频

### 场景
从一张人物照片生成音频驱动的说话视频。

### 步骤
1. 准备输入：
   - 输入图片：`./examples/person.jpg`
   - 驱动音频：`./examples/speech.wav`

2. 执行命令：
```bash
python scripts/infer_infinitetalk.py \
  --input_path ./examples/person.jpg \
  --audio_path ./examples/speech.wav \
  --output_path ./output/video_1.mp4 \
  --size infinitetalk-480 \
  --mode clip \
  --frame_num 81 \
  --sample_steps 40 \
  --sample_audio_guide_scale 4.0
```

3. 参数说明：
   - `--input_path`：输入图片路径
   - `--audio_path`：驱动音频路径
   - `--output_path`：输出视频路径
   - `--size`：分辨率配置（480P 或 720P）
   - `--mode`：生成模式（clip=单段，streaming=长视频）
   - `--frame_num`：生成帧数（必须是 4n+1）
   - `--sample_steps`：采样步数（40-50）
   - `--sample_audio_guide_scale`：音频引导强度（3.0-6.0）

## 示例 2：长视频生成（Streaming 模式）

### 场景
生成较长的说话视频（超过 10 秒）。

### 步骤
```bash
python scripts/infer_infinitetalk.py \
  --input_path ./examples/person.jpg \
  --audio_path ./examples/long_speech.wav \
  --output_path ./output/video_long.mp4 \
  --size infinitetalk-480 \
  --mode streaming \
  --frame_num 81 \
  --max_frame_num 1000 \
  --motion_frame 9
```

### 参数说明：
   - `--mode streaming`：启用流式生成模式
   - `--max_frame_num`：最大帧数限制
   - `--motion_frame`：驱动帧长度（控制流畅度）

## 示例 3：视频重配音（Video-to-Video）

### 场景
对现有视频进行音频驱动的重配音。

### 步骤
```bash
python scripts/infer_infinitetalk.py \
  --input_path ./examples/original_video.mp4 \
  --audio_path ./examples/new_audio.wav \
  --output_path ./output/redubbed_video.mp4 \
  --size infinitetalk-480 \
  --mode clip
```

### 说明：
- 脚本会自动提取视频的首帧作为参考
- 生成结果会保持原视频的分辨率

## 示例 4：使用 TTS 生成音频

### 场景
从文本生成音频，然后用该音频驱动视频。

### 步骤
```bash
python scripts/infer_infinitetalk.py \
  --input_path ./examples/person.jpg \
  --text "你好，欢迎使用 InfiniteTalk 视频生成工具" \
  --output_path ./output/tts_video.mp4 \
  --size infinitetalk-480 \
  --voice1 ./weights/Kokoro-82M/voices/female_01.pt
```

### 参数说明：
   - `--text`：待合成的文本内容
   - `--voice1`：TTS 声音模型路径

## 示例 5：双人对话视频

### 场景
生成双人对话的说话视频。

### 步骤
```bash
python scripts/infer_infinitetalk.py \
  --input_path ./examples/person.jpg \
  --text "(s1) 你好，最近怎么样？(s2) 我很好，谢谢关心。(s1) 今天天气真不错。(s2) 是啊，适合出去走走。" \
  --output_path ./output/dialogue_video.mp4 \
  --size infinitetalk-480 \
  --voice1 ./weights/Kokoro-82M/voices/female_01.pt \
  --voice2 ./weights/Kokoro-82M/voices/male_01.pt
```

### 说明：
- `(s1)` 和 `(s2)` 用于区分不同说话人
- 需要指定两个声音模型

## 示例 6：低显存优化

### 场景
在显存不足的设备上运行（<16GB）。

### 方案 1：启用量化
```bash
python scripts/infer_infinitetalk.py \
  --input_path ./examples/person.jpg \
  --audio_path ./examples/speech.wav \
  --output_path ./output/video_quantized.mp4 \
  --quant int8
```

### 方案 2：启用模型卸载
```bash
python scripts/infer_infinitetalk.py \
  --input_path ./examples/person.jpg \
  --audio_path ./examples/speech.wav \
  --output_path ./output/video_offloaded.mp4 \
  --offload_model true
```

### 方案 3：T5 放到 CPU
```bash
python scripts/infer_infinitetalk.py \
  --input_path ./examples/person.jpg \
  --audio_path ./examples/speech.wav \
  --output_path ./output/video_t5_cpu.mp4 \
  --t5_cpu
```

## 示例 7：高清视频生成（720P）

### 场景
生成更高分辨率（720P）的视频。

### 步骤
```bash
python scripts/infer_infinitetalk.py \
  --input_path ./examples/person.jpg \
  --audio_path ./examples/speech.wav \
  --output_path ./output/video_720p.mp4 \
  --size infinitetalk-720 \
  --sample_shift 11
```

### 说明：
- 720P 模式需要更多显存和计算资源
- `--sample_shift` 需要设置为 11（480P 模式为 7）

## 示例 8：使用 LoRA 微调权重

### 场景
使用训练好的 LoRA 权重增强特定风格。

### 步骤
```bash
python scripts/infer_infinitetalk.py \
  --input_path ./examples/person.jpg \
  --audio_path ./examples/speech.wav \
  --output_path ./output/video_lora.mp4 \
  --lora_dir ./weights/your_lora.safetensors \
  --lora_scale 1.2
```

### 参数说明：
   - `--lora_dir`：LoRA 权重路径（支持多个）
   - `--lora_scale`：LoRA 影响强度（0.0-2.0）

## 高级参数调整

### 采样步数
- `--sample_steps 30`：快速但质量较低
- `--sample_steps 40`：默认值，平衡速度和质量
- `--sample_steps 50`：高质量但较慢

### 音频引导强度
- `--sample_audio_guide_scale 3.0`：音频影响较弱
- `--sample_audio_guide_scale 4.0`：默认值
- `--sample_audio_guide_scale 6.0`：音频影响较强，可能过度同步

### 文本引导强度
- `--sample_text_guide_scale 5.0`：默认值
- 调整范围：3.0-10.0

## 性能优化建议

1. **快速预览**：
   - 使用 `--sample_steps 30`
   - 使用 `--frame_num 17`（约 1.7 秒）

2. **高质量输出**：
   - 使用 `--sample_steps 50`
   - 使用 `--size infinitetalk-720`

3. **低显存设备**：
   - 组合使用 `--quant int8` 和 `--offload_model true`
   - 使用 `--t5_cpu`

4. **批量生成**：
   - 编写 Shell 脚本批量处理多个输入
   - 使用 `--base_seed` 控制随机性

## 常见问题排查

### 问题 1：生成的视频音频不同步
- 解决：调整 `--sample_audio_guide_scale` 参数

### 问题 2：显存溢出
- 解决：使用量化或模型卸载（见示例 6）

### 问题 3：生成速度太慢
- 解决：减少 `--sample_steps` 或降低分辨率

### 问题 4：视频质量不佳
- 解决：增加 `--sample_steps`，检查输入图片质量
