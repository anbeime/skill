---
name: tts-voice-synthesis
description: 智能语音合成服务，支持音色克隆、拟人化语义适配配音、流式实时生成、多语言与方言支持，提供 1.7B/0.6B 双模型选择
dependency:
  python: |
    torch>=2.0.0
    torchaudio>=2.0.0
    transformers>=4.35.0
    scipy>=1.11.0
    numpy>=1.24.0
    librosa>=0.10.0
    soundfile>=0.12.0
    pydub>=0.25.0
  system: |
    # 创建音色模型保存目录
    mkdir -p voices
    mkdir -p output
---

# TTS 语音合成服务

## 任务目标
- 本 Skill 用于：将文本转换为高质量语音，支持音色克隆、情感适配、流式生成和多语言支持
- 能力包含：
  - 角色音色自动采集与克隆（从参考音频提取音色特征）
  - 拟人化语义适配配音（根据文本情绪自动调整语音语调、语速、音调）
  - 流式实时配音（支持边输入文本边生成语音）
  - 多语言与方言支持（中文、英文及多种方言）
  - 双模型选择（1.7B 高质量模型、0.6B 快速模型）
- 触发条件：当需要将文本转换为语音、克隆特定音色、生成情感化配音时使用

## 前置准备
- 模型下载：根据选择的 TTS 模型下载对应的权重，详见 [references/model_config.md](references/model_config.md)
- 硬件要求：
  - GPU：推荐使用 8GB+ 显存的 GPU（0.6B 模型可在 CPU 上运行）
  - 内存：建议 16GB+ 系统内存
  - 磁盘空间：至少 10GB 可用空间（模型权重约 3-5GB）
- 依赖配置：确保已安装所需的 Python 依赖包

## 操作步骤

### 模式一：基础语音合成
1. 文本准备
   - 确认待合成的文本内容
   - 智能体将分析文本情绪和语义特征

2. 选择音色
   - 使用预置音色（见 references/model_config.md）
   - 或使用已克隆的自定义音色

3. 执行合成
   - 调用 `scripts/tts_generate.py` 进行语音生成
   - 根据情绪分析结果自动设置语音参数

4. 验证输出
   - 检查生成的音频质量和情感匹配度
   - 如有需要，调整参数重新生成

### 模式二：音色克隆
1. 准备参考音频
   - 提供目标音色的参考音频文件（3-30 秒，清晰语音）
   - 确保参考音频无背景噪音、音质清晰

2. 提取音色特征
   - 调用 `scripts/voice_clone.py` 提取音色特征
   - 保存为可复用的音色模型

3. 使用克隆音色
   - 使用提取的音色模型生成语音
   - 可应用于不同文本的配音

### 模式三：流式实时配音
1. 文本分段
   - 将长文本分段处理（智能体自动完成）
   - 确保分段自然，不会截断语义

2. 流式生成
   - 调用 `scripts/tts_generate.py` 启用流式模式
   - 逐步生成并输出音频片段

3. 实时合并
   - 将生成的音频片段实时合并
   - 输出完整的配音文件

### 模式四：情感适配配音
1. 文本情绪分析
   - 智能体分析文本的情绪倾向（高兴、悲伤、愤怒、平静等）
   - 识别关键情感词和语气

2. 语音参数调整
   - 根据情绪自动调整：
     - 语速（悲伤时放慢，兴奋时加快）
     - 音调（悲伤时降低，兴奋时提高）
     - 音量（根据情感强度调整）

3. 生成验证
   - 生成情感化语音
   - 验证情感表达是否准确

## 资源索引
- 核心脚本：
  - [scripts/tts_generate.py](scripts/tts_generate.py)（TTS 语音生成）
  - [scripts/voice_clone.py](scripts/voice_clone.py)（音色克隆）
- 参考文档：
  - [references/model_config.md](references/model_config.md)（模型配置和选择指南）
  - [references/emotion_guide.md](references/emotion_guide.md)（情感标注和适配指南）
  - [references/usage_examples.md](references/usage_examples.md)（使用示例）

## 注意事项
- 模型选择：
  - 1.7B 模型：音质更高，适合高质量配音、有声书等场景
  - 0.6B 模型：速度更快，适合实时交互、智能客服等场景
- 音色克隆：
  - 参考音频应清晰、无背景噪音
  - 时长建议 5-15 秒，最短不少于 3 秒
  - 单人语音效果最佳，避免多人混合音频
- 流式生成：
  - 适合长文本和实时交互场景
  - 会产生多个临时音频片段
- 情感适配：
  - 文本情绪分析由智能体完成
  - 最终效果取决于情感标注的准确性
  - 可手动调整语音参数进行微调

## 使用示例
- 基础语音合成：
  ```bash
  python scripts/tts_generate.py \
    --text "你好，欢迎使用语音合成服务" \
    --output_path ./output/hello.wav \
    --model_size 1.7B \
    --voice default
  ```
- 音色克隆：
  ```bash
  python scripts/voice_clone.py \
    --reference_audio ./reference.wav \
    --voice_name my_voice \
    --output_dir ./voices
  ```
- 情感化配音：
  ```bash
  python scripts/tts_generate.py \
    --text "今天真是太开心了！" \
    --output_path ./output/happy.wav \
    --emotion happy \
    --speed 1.2 \
    --pitch 1.1
  ```
- 流式生成：
  ```bash
  python scripts/tts_generate.py \
    --text_file ./long_text.txt \
    --output_path ./output/stream_output.wav \
    --streaming true
  ```
