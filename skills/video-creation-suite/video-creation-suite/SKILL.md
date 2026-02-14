---
name: video-creation-suite
description: 完整的视频创作套件，支持原创创作、视频二创、视频分析三种模式，集成Coze Bot API、Edge-TTS、Suno API，涵盖多智能体协同、素材生成、视频合成全流程
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

# 视频创作套件

## 任务目标
- 本 Skill 用于: 提供完整的视频创作能力，支持三种创作模式
- 能力包含:
  - **模式一: 原创创作**: 11个智能体协同原创视频创作（《三体》IP创作、通用原创）
  - **模式二: 视频二创**: 从原视频反推到新视频合成的完整二创流程
  - **模式三: 视频分析**: 视频抽帧、视觉分析、内容提取
  - **技术能力**: 配音生成、音效生成、背景音乐生成、视频合成
- 触发条件: 用户需要进行视频创作（原创/二创/分析）

## 三种创作模式

### 模式一: 原创创作
- **适用场景**: 从零开始创作原创视频
- **子模式**:
  - 《三体》IP创作（专门针对《三体》IP）
  - 通用多智能体协同（11个智能体分工）
- **流程**: 选题策划 → 视觉设计 → 素材生成 → 视频合成 → 质量检测

### 模式二: 视频二创
- **适用场景**: 基于现有视频进行二次创作
- **流程**: 视频反推分析 → 素材生成 → 视频合成 → 文件下载
- **能力**: 视频抽帧、视觉分析、图片生成、配音、音效、音乐、合成

### 模式三: 视频分析
- **适用场景**: 分析视频内容、提取分镜参考、生成创作提示词
- **流程**: 视频抽帧 → 视觉分析 → 结构化输出
- **能力**: 抽帧、视觉模型调用、提示词生成

## 前置准备

### 环境依赖
```
opencv-python>=4.8.0
pillow>=10.0.0
moviepy>=1.0.3
numpy>=1.24.0
requests>=2.28.0
edge-tts>=6.1.0
```

### API 配置（可选）
- **Coze Bot API**: 视觉分析
  - 环境变量: `COZE_BOT_ID`, `COZE_API_KEY`
- **Edge-TTS**: 配音生成
  - 安装: `pip install edge-tts`
- **Suno API**: 背景音乐生成
  - 环境变量: `SUNO_API_KEY`
  - 三种模式: 开发者、用户、占位

## 操作步骤

### 模式选择

智能体根据用户输入自动选择模式：

#### 判断原创创作模式
- 用户提到"创作《三体》视频"、"三体IP创作" → 《三体》IP创作
- 用户提到"多智能体协同"、"原创视频"、"从零创作" → 通用多智能体协同

#### 判断视频二创模式
- 用户提到"二创视频"、"反推视频"、"视频重制"、"根据参考视频创作" → 视频二创

#### 判断视频分析模式
- 用户提到"分析视频"、"提取分镜"、"生成提示词" → 视频分析

---

## 模式一: 原创创作

### 子模式1: 《三体》IP创作

#### 第一阶段: 前期筹备
1. **原著考据与设定提取**
   - 阅读 [references/three-body-settings.md](references/three-body-settings.md)
   - 提取《三体2》威慑纪元核心设定
   - 输出: 时间线锚点表、人物行为合规清单

2. **剧情架构设计**
   - 搭建"三线并行"叙事框架
   - 设计3个核心冲突点和1个情感高潮
   - 输出: 三线平行叙事分镜大纲、情绪曲线图

3. **台词创作**
   - 基于人物性格撰写台词
   - 输出: 角色对白脚本（含语气/停顿标记）

#### 第二阶段: 视觉制作
4. **视觉风格规范制定**
   - 阅读 [references/visual-style-guide.md](references/visual-style-guide.md)
   - 输出: 视觉风格指南、场景/人物设计规范

5. **场景设计**
   - 设计3个核心场景
   - 输出: 场景概念图提示词、场景要素清单

6. **人物一致性建模**
   - 罗辑形象锚定
   - 输出: 罗辑标准形象锚定图集、人物状态对照表

7. **分镜脚本细化**
   - 将剧情大纲转化为专业分镜
   - 输出: 电影分镜脚本（含时间码）、渲染元数据

#### 第三阶段: 音频与剪辑
8. **素材生成**
   - **配音生成**: 调用 `scripts/voice_generator.py` 生成角色配音
     - 参数: `--input <旁白数据JSON> --output ./output/audio/voice`
   - **音效生成**: 调用 `scripts/sound_generator.py --type sound` 生成音效
     - 参数: `--input <音效配置JSON> --output ./output/audio/sound_effects`
   - **背景音乐生成**: 调用 `scripts/sound_generator.py --type music` 生成背景音乐
     - 参数: `--input <音乐配置JSON> --output ./output/audio/background_music`
   - **视频合成**: 调用 `scripts/video_compositor.py` 合成最终视频
     - 参数: `--images <图片目录> --audio <音频目录> --subtitles <字幕文件> --output <输出路径>`

9. **质量管控**
   - 调用 `scripts/quality_checker.py` 检测技术指标
   - 原著合规检测
   - B站适配优化

### 子模式2: 通用多智能体协同

#### 11个智能体分工
1. 文案创作
2. 故事策划
3. 脚本创作
4. 分镜导演
5. 分镜画师
6. 字幕师
7. 配音师
8. 音效师
9. 视频工程师
10. 质检
11. 数据反馈

#### 5阶段协同流程
1. 需求承接
2. 内容创作
3. 生图创作
4. 音频字幕
5. 视频合成
6. 全流程质检
7. 数据迭代

---

## 模式二: 视频二创

### 第一阶段: 视频反推分析
1. **提取视频关键帧**
   - 调用 `scripts/video_frame_extractor.py` 提取关键帧
   - 参数: `--input <原视频路径> --output ./output/frames --interval 2`
   - 输出: 序列图片到 `./output/frames/`

2. **视觉分析**
   - 调用 `scripts/coze_bot_client.py` 分析关键帧
   - 智能体描述分析需求: "分析这些视频帧，提取:画面风格、色调特征、构图方式、节奏模式"
   - 输出: 分析结果保存到 `./output/analysis.json`

3. **生成创作方案**
   - 智能体根据分析结果，生成二创方案
   - 输出: 新视频主题、画面风格调整、脚本大纲、素材需求清单

### 第二阶段: 素材生成
4. **生成图片素材**
   - 智能体根据脚本生成关键帧提示词
   - 调用 `scripts/image_generator.py` 生成图片
   - 输出: 图片到 `./output/images/`

5. **生成配音**
   - 智能体作为配音师，创作旁白脚本
   - 调用 `scripts/voice_generator.py` 合成配音（基于Edge-TTS）
   - 参数: `--input <旁白脚本JSON> --output ./output/voice`
   - 输出: 配音文件到 `./output/voice/`

6. **生成音效和背景音乐**
   - 调用 `scripts/sound_generator.py --type both` 生成音效和背景音乐
   - 参数: `--input <完整配置JSON> --output ./output/audio`
   - 输出: 音效到 `./output/audio/sound_effects/`, 背景音乐到 `./output/audio/background_music/`

7. **生成字幕**
   - 智能体创作字幕内容
   - 调用 `scripts/subtitle_generator.py` 生成字幕文件
   - 参数: `--input <字幕数据JSON> --output ./output/subtitles`
   - 输出: SRT字幕到 `./output/subtitles/`

### 第三阶段: 视频合成
8. **合成最终视频**
   - 调用 `scripts/video_compositor.py` 合成视频
   - 参数: `--images ./output/images --audio ./output/audio --voice ./output/voice --subtitles ./output/subtitles --output ./output/final.mp4`
   - 输出: 最终视频 `./output/final.mp4`

9. **文件下载**
   - 调用 `scripts/file_server.py` 启动HTTP服务器
   - 参数: `--port 8080 --directory ./output`
   - 输出: 下载链接 `http://localhost:8080/final.mp4`

---

## 模式三: 视频分析

### 分析流程
1. **视频抽帧**
   - 调用 `scripts/video_frame_extractor.py` 提取关键帧
   - 参数: `--input <视频路径> --output <输出目录> --interval <间隔秒数>`

2. **视觉分析**
   - 调用 `scripts/coze_bot_client.py` 分析每帧内容
   - 参数: `--message "<分析提示>" --image_path <图片路径>`
   - 输出: 结构化分析结果（JSON格式）

3. **批量处理**
   - 自动遍历所有关键帧
   - 批量调用视觉模型
   - 汇总分析结果

---

## 资源索引

### 技术脚本
- **视频处理**: [scripts/video_frame_extractor.py](scripts/video_frame_extractor.py) - 提取关键帧
- **视觉分析**: [scripts/coze_bot_client.py](scripts/coze_bot_client.py) - 调用Coze Bot API
- **图像生成**: [scripts/image_generator.py](scripts/image_generator.py) - 生成图片素材
- **配音生成**: [scripts/voice_generator.py](scripts/voice_generator.py) - 生成配音（Edge-TTS）
- **音效和音乐**: [scripts/sound_generator.py](scripts/sound_generator.py) - 生成音效和背景音乐（Suno API）
- **字幕生成**: [scripts/subtitle_generator.py](scripts/subtitle_generator.py) - 生成字幕
- **视频合成**: [scripts/video_compositor.py](scripts/video_compositor.py) - 合成最终视频
- **文件服务**: [scripts/file_server.py](scripts/file_server.py) - HTTP下载服务器
- **质量检测**: [scripts/quality_checker.py](scripts/quality_checker.py) - 检测技术指标
- **错误处理**: [scripts/error_handler.py](scripts/error_handler.py) - 重试和错误日志

### 参考文档
- **《三体》IP创作**:
  - [references/three-body-settings.md](references/three-body-settings.md) - 《三体》原著设定与威慑纪元规则
  - [references/visual-style-guide.md](references/visual-style-guide.md) - 视觉风格规范与设计原则
  - [references/storyboard-template.md](references/storyboard-template.md) - 分镜脚本标准模板
  - [references/character-profiles.md](references/character-profiles.md) - 人物档案与行为准则

- **视频二创**:
  - [references/recreation-guide.md](references/recreation-guide.md) - 视频二创方法论
  - [references/prompt-templates.md](references/prompt-templates.md) - 分析提示词示例
  - [references/suno-api-guide.md](references/suno-api-guide.md) - Suno API使用指南

### 资源文件
- [assets/scene-examples/](assets/scene-examples/) - 场景设计提示词示例
- [assets/character-reference/](assets/character-reference/) - 人物形象描述参考

## 注意事项

- **模式自动选择**: 智能体根据用户输入自动选择合适的创作模式
- **脚本共享**: 所有模式共享同一套技术脚本，避免重复
- **API配置**: 所有API通过环境变量配置，支持多种模式
- **错误处理**: 所有脚本都包含错误处理和重试机制
- **容错降级**: API不可用时自动降级为占位实现

## 使用示例

### 示例1: 《三体》IP创作
```
用户: "帮我创作一个《三体》威慑纪元的8分钟视频"

智能体执行:
1. 自动选择模式一: 《三体》IP创作
2. 按照前期筹备 → 视觉制作 → 音频与剪辑 → 质量管控流程
3. 调用相应脚本生成配音、音效、背景音乐
4. 合成最终视频
```

### 示例2: 视频二创
```
用户: "这个视频帮我二创一下，换个风格"

智能体执行:
1. 自动选择模式二: 视频二创
2. 提取原视频关键帧
3. 视觉分析，提取风格特征
4. 生成新素材（图片、配音、音效、音乐）
5. 合成新视频
```

### 示例3: 视频分析
```
用户: "分析这个视频，提取分镜和提示词"

智能体执行:
1. 自动选择模式三: 视频分析
2. 抽取视频关键帧
3. 分析每帧内容
4. 输出结构化分析结果
```

## API 配置说明

### Suno API 三种模式
- **开发者模式**: 技能预置 API Key，开箱即用
- **用户模式**: 用户配置自己的 API Key
- **占位模式**: 自动降级，完全免费

### Edge-TTS 音色列表
- 中文: zh-CN-XiaoxiaoNeural(活泼)、zh-CN-XiaomengNeural(温柔)、zh-CN-YunyangNeural(沉稳)
- 英文: en-US-JennyNeural(美式)、en-GB-SoniaNeural(英式)

### Coze Bot API
- 用于视觉分析
- 环境变量: COZE_BOT_ID, COZE_API_KEY
