# 使用示例

## 概览
本文档提供 TTS 语音合成服务的典型使用场景和命令示例。

## 示例 1：基础语音合成

### 场景
将简短文本转换为语音。

### 步骤
```bash
python scripts/tts_generate.py \
  --text "你好，欢迎使用语音合成服务" \
  --output_path ./output/hello.wav \
  --model_name fish-speech-1.5 \
  --voice default_female
```

### 参数说明
- `--text`：待合成的文本
- `--output_path`：输出音频路径
- `--model_name`：模型名称（fish-speech-1.5, chattts, cosyvoice）
- `--voice`：音色名称

## 示例 2：从文件生成语音

### 场景
从文本文件生成长语音。

### 步骤
```bash
python scripts/tts_generate.py \
  --text_file ./input/article.txt \
  --output_path ./output/article.wav \
  --model_name fish-speech-1.5 \
  --voice default_female \
  --speed 1.0
```

### 输入文件格式（article.txt）
```
欢迎使用语音合成服务。

这是一个示例文本文件，演示如何从文件生成语音。
系统将逐行读取文件内容并生成对应的语音。
```

## 示例 3：音色克隆

### 场景
从参考音频提取音色，用于后续语音生成。

### 步骤 1：提取音色特征
```bash
python scripts/voice_clone.py \
  --reference_audio ./reference/my_voice.wav \
  --voice_name my_custom_voice \
  --model_name fish-speech-1.5 \
  --output_dir ./voices
```

### 步骤 2：使用克隆音色生成语音
```bash
python scripts/tts_generate.py \
  --text "这是使用克隆音色生成的语音" \
  --output_path ./output/cloned_voice.wav \
  --voice my_custom_voice \
  --voice_path ./voices/my_custom_voice
```

## 示例 4：情感化配音

### 场景
根据文本情绪生成带有情感的语音。

### 高兴情绪
```bash
python scripts/tts_generate.py \
  --text "今天真是太开心了！任务圆满完成！" \
  --output_path ./output/happy.wav \
  --emotion happy \
  --speed 1.2 \
  --pitch 1.1 \
  --volume 1.1
```

### 悲伤情绪
```bash
python scripts/tts_generate.py \
  --text "听到这个消息，我感到非常遗憾" \
  --output_path ./output/sad.wav \
  --emotion sad \
  --speed 0.85 \
  --pitch 0.85 \
  --volume 0.85
```

### 愤怒情绪
```bash
python scripts/tts_generate.py \
  --text "这种行为是完全不能接受的！" \
  --output_path ./output/angry.wav \
  --emotion angry \
  --speed 1.25 \
  --pitch 1.25 \
  --volume 1.25
```

## 示例 5：多语言语音生成

### 中文语音
```bash
python scripts/tts_generate.py \
  --text "你好，欢迎来到中国" \
  --output_path ./output/zh.wav \
  --model_name fish-speech-1.5 \
  --voice zh_female
```

### 英文语音
```bash
python scripts/tts_generate.py \
  --text "Hello, welcome to China" \
  --output_path ./output/en.wav \
  --model_name cosyvoice \
  --voice en_female
```

### 粤语语音
```bash
python scripts/tts_generate.py \
  --text "你好，欢迎嚟中国" \
  --output_path ./output/yue.wav \
  --model_name cosyvoice \
  --voice yue_female
```

## 示例 6：流式实时配音

### 场景
实时生成语音，适合长文本或实时交互。

### 步骤
```bash
python scripts/tts_generate.py \
  --text_file ./input/long_text.txt \
  --output_path ./output/streaming_output.wav \
  --model_name chattts \
  --streaming true \
  --chunk_size 128
```

### 流式生成参数
- `--streaming true`：启用流式模式
- `--chunk_size`：每次生成的 token 数量（默认 128）
- `--output_per_chunk`：是否输出每个音频片段（可选）

## 示例 7：双模型选择

### 场景 1：高质量配音（1.7B 模型）
```bash
python scripts/tts_generate.py \
  --text "这是高质量配音的示例" \
  --output_path ./output/high_quality.wav \
  --model_name fish-speech-1.5 \
  --model_size 1.7B
```

### 场景 2：快速生成（0.6B 模型）
```bash
python scripts/tts_generate.py \
  --text "这是快速生成的示例" \
  --output_path ./output/fast.wav \
  --model_name chattts \
  --model_size 0.6B
```

## 示例 8：有声书制作

### 场景
将小说章节转换为有声书。

### 步骤 1：准备文本文件（chapter1.txt）
```
第一章：开始

很久很久以前，在一个遥远的小村庄里，住着一位年轻的女孩。

她叫艾丽丝，有一头金色的长发和一双明亮的眼睛。

每天清晨，她都会去森林里采蘑菇。
```

### 步骤 2：生成有声书
```bash
python scripts/tts_generate.py \
  --text_file ./chapter1.txt \
  --output_path ./output/audiobook_chapter1.wav \
  --model_name fish-speech-1.5 \
  --voice default_female \
  --emotion calm \
  --speed 1.0
```

## 示例 9：智能客服对话

### 场景
生成客服常用的对话语音。

### 问候语
```bash
python scripts/tts_generate.py \
  --text "您好，很高兴为您服务。请问有什么可以帮您的吗？" \
  --output_path ./output/greeting.wav \
  --emotion happy \
  --speed 1.1
```

### 等待语音
```bash
python scripts/tts_generate.py \
  --text "请稍等，我正在为您查询相关信息" \
  --output_path ./output/waiting.wav \
  --emotion calm
```

### 结束语
```bash
python scripts/tts_generate.py \
  --text "感谢您的使用，祝您生活愉快！" \
  --output_path ./output/goodbye.wav \
  --emotion happy
```

## 示例 10：游戏角色语音

### 场景
生成游戏角色的语音台词。

### 英雄角色
```bash
python scripts/tts_generate.py \
  --text "为了荣耀，勇往直前！" \
  --output_path ./output/hero.wav \
  --emotion excited \
  --speed 1.3 \
  --pitch 1.2 \
  --volume 1.2
```

### 反派角色
```bash
python scripts/tts_generate.py \
  --text "你们休想阻止我！" \
  --output_path ./output/villain.wav \
  --emotion angry \
  --speed 1.2 \
  --pitch 1.1 \
  --volume 1.3
```

### NPC 对话
```bash
python scripts/tts_generate.py \
  --text "你好，勇敢的冒险者。欢迎来到我们的村庄。" \
  --output_path ./output/npc.wav \
  --emotion calm
```

## 示例 11：批量生成

### 场景
批量处理多个文本文件。

### 步骤
```bash
# 使用 shell 脚本批量处理
for file in ./input/*.txt; do
  filename=$(basename "$file" .txt)
  python scripts/tts_generate.py \
    --text_file "$file" \
    --output_path "./output/$filename.wav" \
    --model_name chattts
done
```

## 示例 12：参数调优

### 场景
通过试听调整最佳参数。

### 步骤 1：生成多个版本
```bash
# 版本 1：默认参数
python scripts/tts_generate.py \
  --text "测试文本" \
  --output_path ./output/v1.wav

# 版本 2：语速加快
python scripts/tts_generate.py \
  --text "测试文本" \
  --output_path ./output/v2.wav \
  --speed 1.2

# 版本 3：音调提高
python scripts/tts_generate.py \
  --text "测试文本" \
  --output_path ./output/v3.wav \
  --pitch 1.1
```

### 步骤 2：试听对比
```bash
# 播放所有版本
play ./output/v1.wav
play ./output/v2.wav
play ./output/v3.wav
```

### 步骤 3：选择最佳版本并应用到完整文本

## 示例 13：混合情感文本

### 场景
一段文本包含多种情感，需要分段处理。

### 步骤
```bash
python scripts/tts_generate.py \
  --text_file ./input/mixed_emotion.txt \
  --output_path ./output/mixed.wav \
  --emotion_per_sentence true
```

### 输入文件示例（mixed_emotion.txt）
```
[emotion:calm] 很久以前，有一个小村庄。
[emotion:excited] 突然，一道光芒划破长空！
[emotion:sad] 村庄被摧毁了，人们都很伤心。
[emotion:happy] 但在废墟中，新的希望诞生了。
```

## 示例 14：低资源环境

### 场景
在显存不足的环境中使用。

### 步骤 1：使用 CPU 运行
```bash
python scripts/tts_generate.py \
  --text "这是在 CPU 上生成的语音" \
  --output_path ./output/cpu.wav \
  --device cpu \
  --model_name chattts
```

### 步骤 2：使用 0.6B 模型
```bash
python scripts/tts_generate.py \
  --text "这是使用 0.6B 模型生成的语音" \
  --output_path ./output/fast.wav \
  --model_name chattts \
  --model_size 0.6B
```

## 示例 15：自定义输出格式

### 场景
生成不同格式的音频文件。

### WAV 格式（默认）
```bash
python scripts/tts_generate.py \
  --text "测试文本" \
  --output_path ./output/test.wav
```

### MP3 格式
```bash
python scripts/tts_generate.py \
  --text "测试文本" \
  --output_path ./output/test.mp3 \
  --audio_format mp3
```

### FLAC 格式
```bash
python scripts/tts_generate.py \
  --text "测试文本" \
  --output_path ./output/test.flac \
  --audio_format flac
```

## 高级示例

### 示例 16：使用环境变量配置
```bash
export TTS_MODEL_NAME=fish-speech-1.5
export TTS_VOICE=default_female
export TTS_OUTPUT_PATH=./output

python scripts/tts_generate.py \
  --text "使用环境变量配置" \
  --output_path ./output/env_config.wav
```

### 示例 17：结合音色克隆和情感
```bash
# 步骤 1：克隆音色
python scripts/voice_clone.py \
  --reference_audio ./reference.wav \
  --voice_name narrator_voice

# 步骤 2：使用克隆音色生成情感化语音
python scripts/tts_generate.py \
  --text "这是一个充满悬念的故事..." \
  --output_path ./output/story.wav \
  --voice narrator_voice \
  --emotion calm \
  --speed 0.95
```

### 示例 18：实时交互场景
```bash
# 监听标准输入，实时生成语音
echo "请输入要合成的文本：" | \
  xargs -I {} python scripts/tts_generate.py \
  --text "{}" \
  --output_path ./output/realtime.wav \
  --model_name chattts
```

## 常见参数组合

### 高质量中文配音
```bash
--model_name fish-speech-1.5 \
--voice zh_female \
--speed 1.0
```

### 快速对话生成
```bash
--model_name chattts \
--voice default \
--speed 1.1
```

### 情感化配音
```bash
--emotion happy \
--speed 1.2 \
--pitch 1.1 \
--volume 1.1
```

### 沉稳朗读
```bash
--emotion calm \
--speed 0.95 \
--volume 0.95
```

## 注意事项

1. **首次运行**
   - 首次运行需要下载模型权重（约 3-5GB）
   - 下载完成后模型会缓存到本地

2. **音色质量**
   - 参考音频应清晰无噪音
   - 时长建议 5-15 秒

3. **文本长度**
   - 单次生成建议不超过 2000 字
   - 长文本建议使用流式模式

4. **性能优化**
   - GPU 生成速度比 CPU 快 10-50 倍
   - 0.6B 模型比 1.7B 模型快 2-3 倍
