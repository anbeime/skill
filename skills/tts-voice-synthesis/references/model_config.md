# 模型配置和选择指南

## 概览
本文档说明 TTS 语音合成服务支持的模型、配置方法和选择建议。

## 支持的 TTS 模型

### 1. Fish-Speech 1.5
- **模型大小**：1.5B
- **支持语言**：中文、英文
- **特性**：
  - 支持音色克隆
  - 支持流式生成
  - 音质优秀
  - 中文自然度高
- **硬件要求**：
  - GPU：8GB+ 显存推荐
  - CPU：可运行但速度较慢
- **适用场景**：高质量中文配音、有声书制作

### 2. ChatTTS
- **模型大小**：约 0.6B
- **支持语言**：中文、英文
- **特性**：
  - 对话式语音自然
  - 支持情感表达
  - 支持流式生成
  - 生成速度快
- **硬件要求**：
  - GPU：4GB+ 显存推荐
  - CPU：可运行
- **适用场景**：智能客服、实时对话、游戏角色语音

### 3. CosyVoice
- **模型大小**：1.7B
- **支持语言**：中文、英文、粤语
- **特性**：
  - 阿里开源
  - 多语言支持
  - 支持音色克隆
  - 方言支持（粤语）
- **硬件要求**：
  - GPU：8GB+ 显存推荐
- **适用场景**：多语言配音、粤语配音

## 模型下载

### Fish-Speech 1.5
```bash
# 使用 Hugging Face CLI
pip install huggingface-hub
huggingface-cli download fishaudio/fish-speech-1.5 --local-dir ./models/fish-speech-1.5

# 或使用 Git LFS
git lfs install
git clone https://huggingface.co/fishaudio/fish-speech-1.5 ./models/fish-speech-1.5
```

### ChatTTS
```bash
# 使用 Hugging Face CLI
huggingface-cli download 2noise/ChatTTS --local-dir ./models/chattts

# 或使用 Git LFS
git clone https://huggingface.co/2noise/ChatTTS ./models/chattts
```

### CosyVoice
```bash
# 使用 Hugging Face CLI
huggingface-cli download FunAudioLLM/CosyVoice-300M --local-dir ./models/cosyvoice

# 或使用 Git LFS
git clone https://huggingface.co/FunAudioLLM/CosyVoice-300M ./models/cosyvoice
```

## 模型选择建议

### 场景一：高质量中文配音
- **推荐模型**：Fish-Speech 1.5
- **理由**：音质优秀，中文自然度最高
- **参数**：
  ```python
  model_name = "fish-speech-1.5"
  model_size = "1.7B"
  ```

### 场景二：实时对话和智能客服
- **推荐模型**：ChatTTS
- **理由**：对话自然，生成速度快
- **参数**：
  ```python
  model_name = "chattts"
  model_size = "0.6B"
  ```

### 场景三：多语言和方言支持
- **推荐模型**：CosyVoice
- **理由**：支持粤语和多语言
- **参数**：
  ```python
  model_name = "cosyvoice"
  model_size = "1.7B"
  ```

### 场景四：低资源环境
- **推荐模型**：ChatTTS
- **理由**：模型较小，可在 CPU 上运行
- **参数**：
  ```python
  model_name = "chattts"
  model_size = "0.6B"
  device = "cpu"
  ```

## 预置音色

### Fish-Speech 预置音色
- `default_female`：默认女声
- `default_male`：默认男声
- `child`：儿童声音
- `elder`：老年声音

### ChatTTS 预置音色
- `default`：默认声音
- `calm`：平静声音
- `energetic`：活力声音

### CosyVoice 预置音色
- `zh_female`：中文女声
- `zh_male`：中文男声
- `en_female`：英文女声
- `en_male`：英文男声
- `yue_female`：粤语女声

## 自定义音色

### 音色文件格式
- 支持格式：WAV、MP3、FLAC
- 采样率：建议 22050Hz 或 44100Hz
- 时长：3-30 秒
- 质量：清晰、无背景噪音

### 音色保存目录
```
voices/
├── fish/
│   ├── my_voice_1/
│   │   ├── reference.wav
│   │   ├── speaker_embedding.pt
│   │   └── config.json
│   └── my_voice_2/
│       └── ...
├── chattts/
│   └── ...
└── cosyvoice/
    └── ...
```

## 模型配置参数

### 通用参数
- `model_name`：模型名称（fish-speech-1.5, chattts, cosyvoice）
- `model_path`：模型本地路径
- `device`：运行设备（cuda, cpu）
- `max_length`：最大生成长度（tokens）

### Fish-Speech 参数
- `temperature`：采样温度（0.1-1.0，默认 0.7）
- `top_p`：核采样概率（0.5-1.0，默认 0.9）
- `chunk_size`：流式生成块大小（默认 128）

### ChatTTS 参数
- `refine_text`：是否优化文本（true/false，默认 true）
- `top_k`：Top-K 采样（默认 20）
- `repetition_penalty`：重复惩罚（1.0-2.0，默认 1.2）

### CosyVoice 参数
- `speed`：语速（0.5-2.0，默认 1.0）
- `pitch`：音调（0.5-2.0，默认 1.0）

## 性能对比

| 模型 | 音质 | 速度 | 音色克隆 | 多语言 | 显存需求 |
|------|------|------|----------|--------|----------|
| Fish-Speech 1.5 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ✓ | 中英 | 8GB |
| ChatTTS | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ✓ | 中英 | 4GB |
| CosyVoice | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ✓ | 多语言 | 8GB |

## 常见问题

### 问题 1：模型下载速度慢
- 解决：使用镜像站或国内加速源

### 问题 2：显存不足
- 解决：
  - 使用 0.6B 模型（ChatTTS）
  - 降低 batch_size
  - 使用 CPU 运行

### 问题 3：音色克隆效果不佳
- 解决：
  - 确保参考音频清晰无噪音
  - 参考音频时长 5-15 秒最佳
  - 避免多人混合音频

### 问题 4：流式生成卡顿
- 解决：
  - 增加 chunk_size
  - 使用更快的模型（ChatTTS）
  - 优化文本分段

## 环境变量配置

```bash
# 模型存储路径
export TTS_MODEL_PATH="./models"

# 音色存储路径
export TTS_VOICE_PATH="./voices"

# 输出路径
export TTS_OUTPUT_PATH="./output"

# GPU 设备
export CUDA_VISIBLE_DEVICES="0"
```
