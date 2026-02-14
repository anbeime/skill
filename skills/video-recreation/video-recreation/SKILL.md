---
name: video-recreation
description: 完整的视频二创工具，支持视频反推、素材生成(图片/音效/背景音乐/配音/字幕)、视频合成、文件下载的全流程，集成Coze Bot API进行视觉分析，使用Edge-TTS进行语音合成
dependency:
  python:
    - opencv-python>=4.8.0
    - pillow>=10.0.0
    - moviepy>=1.0.3
    - numpy>=1.24.0
    - requests>=2.28.0
    - edge-tts>=6.1.0
  system:
    - pip install -r requirements.txt 2>/dev/null || true
---

# video-recreation

## 任务目标
- 本Skill用于:视频二创创作，从原视频反推分析到新视频合成的完整流程
- 能力包含:视频分析、素材生成(图片/音频/配音/字幕)、视频合成、文件下载
- 触发条件:用户要求"二创视频"、"反推视频"、"视频重制"、"根据参考视频创作"等

## 前置准备
- 环境依赖:
  ```
  opencv-python>=4.8.0
  pillow>=10.0.0
  moviepy>=1.0.3
  numpy>=1.24.0
  requests>=2.28.0
  edge-tts>=6.1.0
  ```
- Edge-TTS安装:
  ```bash
  pip install edge-tts
  ```
- Suno API(可选):
  - 用于生成真实的背景音乐
  - 三种配置方式:
    1. **开发者模式**: 技能已预置 API Key,开箱即用
    2. **用户模式**: 设置环境变量 `export SUNO_API_KEY=your_api_key`
    3. **命令行模式**: 执行时指定 `--suno-api-key your_api_key`
  - 配置优先级: 命令行参数 > 环境变量 > 技能凭证
  - 占位模式: 未配置 API Key 时自动使用占位实现
  - 官网: https://suno.com
- 环境变量:
  - `COZE_BOT_ID`: Coze Bot ID (默认: 7572557757883383858)
  - `COZE_API_KEY`: Coze API Key (需配置)
- 输出目录结构:
  ```
  ./output/
    ├── frames/          # 视频关键帧
    ├── analysis.json    # 反推分析结果
    ├── images/          # 生成的图片素材
    ├── audio/           # 音效和背景音乐
    ├── voice/           # 配音音频
    ├── subtitles/       # 字幕文件
    └── final.mp4        # 最终合成视频
  ```

## 操作步骤

### 第一阶段:视频反推分析
1. **提取视频关键帧**
   - 调用 `scripts/video_frame_extractor.py` 提取关键帧
   - 参数: `--input <原视频路径> --output ./output/frames --interval 2`
   - 输出:序列图片到 `./output/frames/`

2. **视觉分析**
   - 调用 `scripts/coze_bot_client.py` 分析关键帧
   - 智能体描述分析需求:"分析这些视频帧，提取:1.画面风格 2.色调特征 3.构图方式 4.节奏模式"
   - 参数: `--message "<分析提示>" --image_path <关键帧路径>`
   - 输出:分析结果保存到 `./output/analysis.json`

3. **生成创作方案**
   - 智能体根据分析结果,生成二创方案:
     - 新视频主题
     - 画面风格调整
     - 脚本大纲
     - 素材需求清单

### 第二阶段:素材生成
4. **生成图片素材**
   - 智能体根据脚本生成关键帧提示词
   - 调用 `scripts/image_generator.py` 生成图片
   - 参数: `--prompt "<提示词>" --output ./output/images/frame_xxxx.png`
   - **重要**:图像生成应由智能体创作,脚本仅负责技术实现
   - 输出:图片到 `./output/images/`

5. **生成音效和背景音乐**
   - 智能体描述音效需求:"根据场景生成音效:1.转场音效 2.背景音乐风格 3.环境音"
   - 调用 `scripts/sound_generator.py` 生成音效和背景音乐
   - 参数: `--type sound --input <音效配置JSON> --output ./output/audio` (生成音效)
   - 参数: `--type music --input <音乐配置JSON> --output ./output/audio` (生成背景音乐)
   - 参数: `--type both --input <完整配置JSON> --output ./output/audio` (同时生成两者)
   - **API Key 配置**(可选):
     - 不配置: 自动使用占位实现(开箱即用,无需任何配置)
     - 环境变量: `export SUNO_API_KEY=your_api_key`
     - 命令行参数: `--suno-api-key your_api_key`
     - 强制占位: `--use-placeholder` (即使有 API Key 也使用占位)
   - 输出:音效到 `./output/audio/sound_effects/`, 背景音乐到 `./output/audio/background_music/`
   - **模式说明**:
     - **开发者模式**: 技能已预置 API Key,直接使用
     - **用户模式**: 用户自己配置 API Key
     - **占位模式**: 未配置 API Key 时自动降级

6. **生成配音**
   - 智能体作为配音师,创作旁白脚本:
     - 分析原视频节奏
     - 创作贴合画面的旁白
     - 选择合适的音色(中文/英文/日文等20+音色)
     - 调整语速、音调、音量参数
   - 调用 `scripts/voice_generator.py` 合成配音(基于Edge-TTS)
   - 参数: `--input <旁白脚本JSON> --output ./output/voice`
   - 参数: `--list-voices` (列出所有可用音色)
   - 输出:配音文件到 `./output/voice/`
   - **音色示例**:
     - 中文女声: zh-CN-XiaoxiaoNeural(活泼)、zh-CN-XiaohanNeural(知性)、zh-CN-XiaomengNeural(温柔)
     - 中文男声: zh-CN-YunyangNeural(沉稳)、zh-CN-YunjianNeural(深沉)、zh-CN-YunxiNeural(活泼)
     - 英文女声: en-US-JennyNeural(美式)、en-GB-SoniaNeural(英式)

7. **生成字幕**
   - 智能体创作字幕内容,确保:
     - 文字简洁有力
     - 与画面同步
     - 符合视频节奏
   - 调用 `scripts/subtitle_generator.py` 生成字幕文件
   - 参数: `--input <字幕数据JSON> --output ./output/subtitles`
   - 输出:SRT字幕到 `./output/subtitles/`

### 第三阶段:视频合成
8. **合成最终视频**
   - 调用 `scripts/video_compositor.py` 合成视频
   - 参数: `--images ./output/images --audio ./output/audio --voice ./output/voice --subtitles ./output/subtitles --output ./output/final.mp4`
   - 输出:最终视频 `./output/final.mp4`

9. **文件下载**
   - 启动HTTP服务器供下载
   - 调用 `scripts/file_server.py`
   - 参数: `--port 8080 --directory ./output`
   - 输出:下载链接 `http://localhost:8080/final.mp4`

### 错误处理与断点续传
- **重试机制**:所有API调用已配置最大重试次数(2-3次),避免无限消耗Token
- **错误日志**:错误自动记录到 `./output/error_log.json`,可用于问题诊断
- **断点续传**:
  - 检查 `./output/error_log.json` 确认失败步骤
  - 从失败步骤重新执行,已生成的素材可复用
  - 例如:仅重新生成失败的音频,不重复已有图片
- **重试限制**:
  - Coze Bot API调用:最多重试3次,每次间隔1秒
  - 图像生成:最多重试2次,每次间隔0.5秒
  - 音频生成:最多重试2次,每次间隔0.5秒
  - 音效和背景音乐:最多重试2次,每次间隔0.5秒

## 资源索引
- **视频处理**:见 [scripts/video_frame_extractor.py](scripts/video_frame_extractor.py)(提取关键帧)
- **视觉分析**:见 [scripts/coze_bot_client.py](scripts/coze_bot_client.py)(调用Coze Bot API)
- **图像生成**:见 [scripts/image_generator.py](scripts/image_generator.py)(生成图片素材)
- **音频生成**:见 [scripts/audio_generator.py](scripts/audio_generator.py)(生成旁白/配音)
- **音效和音乐**:见 [scripts/sound_generator.py](scripts/sound_generator.py)(生成环境音效和背景音乐,集成Suno API)
- **配音合成**:见 [scripts/voice_generator.py](scripts/voice_generator.py)(合成旁白,基于Edge-TTS)
- **字幕生成**:见 [scripts/subtitle_generator.py](scripts/subtitle_generator.py)(生成字幕)
- **视频合成**:见 [scripts/video_compositor.py](scripts/video_compositor.py)(合成最终视频)
- **文件服务**:见 [scripts/file_server.py](scripts/file_server.py)(HTTP下载服务器)
- **错误处理**:见 [scripts/error_handler.py](scripts/error_handler.py)(重试和错误日志)
- **创作指南**:见 [references/recreation-guide.md](references/recreation-guide.md)(视频二创方法论)
- **提示词模板**:见 [references/prompt-templates.md](references/prompt-templates.md)(分析提示词示例)
- **Suno API指南**:见 [references/suno-api-guide.md](references/suno-api-guide.md)(Suno API使用说明)

## 注意事项
- **智能体职责**:内容创作(剧本、旁白、字幕、图像提示词)由智能体完成,脚本负责技术处理
- **重试限制**:避免无限重试消耗Token,已配置合理重试次数
- **错误日志**:遇到错误时检查 `./output/error_log.json`,从失败步骤恢复
- **断点续传**:重复执行时,已存在的素材会被复用,无需重新生成
- **Coze Bot API**:视觉分析依赖用户发布的Coze Bot,需配置API Key
- **文件路径**:所有输出使用相对路径 `./output/`,确保下载时能正确访问

## 使用示例

### 示例1:完整二创流程
```bash
# 1. 提取关键帧
python scripts/video_frame_extractor.py \
  --input original_video.mp4 \
  --output ./output/frames \
  --interval 2

# 2. 视觉分析(智能体描述分析需求)
python scripts/coze_bot_client.py \
  --message "分析这些视频帧,提取:画面风格、色调特征、构图方式、节奏模式" \
  --image_path ./output/frames/frame_0001.jpg

# 3. 生成图片素材(智能体创作提示词)
python scripts/image_generator.py \
  --prompt "现代科技风格,蓝色调,未来城市景观" \
  --output ./output/images/frame_0001.png

# 4. 生成音效和背景音乐

# 方式1: 使用技能预置的 API Key(开箱即用)
python scripts/sound_generator.py \
  --type both \
  --input audio_config.json \
  --output ./output/audio

# 方式2: 使用自己的 API Key
export SUNO_API_KEY=your_api_key
python scripts/sound_generator.py \
  --type both \
  --input audio_config.json \
  --output ./output/audio

# 方式3: 命令行指定 API Key
python scripts/sound_generator.py \
  --type both \
  --input audio_config.json \
  --output ./output/audio \
  --suno-api-key your_api_key

# 方式4: 强制使用占位实现(不调用 API)
python scripts/sound_generator.py \
  --type both \
  --input audio_config.json \
  --output ./output/audio \
  --use-placeholder

# 其中audio_config.json示例:
{
  "sound_effects": [
    {"name": "transition_01", "type": "transition", "duration": 2.0, "description": "转场音效"},
    {"name": "impact_01", "type": "impact", "duration": 0.5, "description": "冲击音效"}
  ],
  "background_music": {
    "name": "background",
    "style": "calm",
    "duration": 60.0,
    "tempo": 90,
    "mood": "neutral"
  }
}

# API Key 配置优先级: 命令行参数 > 环境变量 > 技能凭证 > 占位实现

# 5. 生成配音(Edge-TTS)
# 查看可用音色
python scripts/voice_generator.py --list-voices

# 生成配音
python scripts/voice_generator.py \
  --input narration.json \
  --output ./output/voice

# 其中narration.json示例:
{
  "segments": [
    {
      "segment_id": "S01",
      "text": "欢迎来到这个美丽的世界",
      "voice": "zh-CN-XiaomengNeural",
      "rate": "-10%",
      "pitch": "+0Hz",
      "volume": "+0%"
    },
    {
      "segment_id": "S02",
      "text": "让我们开始这段奇妙的旅程",
      "voice": "zh-CN-YunyangNeural",
      "rate": "-5%",
      "pitch": "-2Hz",
      "volume": "+5%"
    }
  ]
}

# 6. 生成字幕
python scripts/subtitle_generator.py \
  --input subtitle_data.json \
  --output ./output/subtitles

# 7. 合成视频
python scripts/video_compositor.py \
  --images ./output/images \
  --audio ./output/audio \
  --voice ./output/voice \
  --subtitles ./output/subtitles \
  --output ./output/final.mp4

# 8. 启动下载服务器
python scripts/file_server.py \
  --port 8080 \
  --directory ./output
```

### 示例2:单独生成音效
```bash
python scripts/sound_generator.py \
  --type sound \
  --input sound_effects.json \
  --output ./output/audio
```

### 示例3:单独生成背景音乐
```bash
python scripts/sound_generator.py \
  --type music \
  --input background_music.json \
  --output ./output/audio
```

### 示例4:断点续传
```bash
# 检查错误日志
cat ./output/error_log.json

# 从失败步骤重新执行(例如仅重新生成失败的音效)
python scripts/sound_generator.py \
  --type sound \
  --input sound_effects.json \
  --output ./output/audio
```

## 智能体角色分工
1. **视觉分析师**:分析原视频,提取风格、色调、构图等特征
2. **脚本策划师**:根据分析结果创作新视频脚本和大纲
3. **提示词设计师**:为图像生成工具创作精准的提示词
4. **配音师**:创作旁白脚本,确定音色、节奏、情感
5. **音效师**:设计音效方案,确定音效类型、时长和位置
6. **音乐师**:选择背景音乐风格,确定节奏和情绪基调
7. **字幕师**:创作字幕内容,确保与画面同步
8. **技术协调员**:调用脚本完成技术处理,管理文件路径,启动下载服务
