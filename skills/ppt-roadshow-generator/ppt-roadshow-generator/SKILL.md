---
name: ppt-roadshow-generator
description: PPT 路演视频全流程生成器，支持品牌风格学习、智能配音、音效音乐、字幕和一键视频合成。可一次性生成 15-100 页风格统一的完整路演视频。
dependency:
  python:
    - moviepy>=1.0.3
    - pillow>=9.0.0
    - pydub>=0.25.1
    - requests>=2.28.0
  system:
    - ffmpeg
---

# PPT 路演视频生成器

## 任务目标
- 本 Skill 用于：从文档分析到完整路演视频的全流程生成，包含配音、音效、音乐、字幕和转场动画
- 能力包含：文档分析、品牌风格学习、结构化规划、内容生成、视觉设计、演讲稿撰写、配音、音效、字幕、视频合成
- 触发条件：用户需要制作路演视频、产品发布演示、公司介绍视频等

## 前置准备
- 依赖说明：scripts 脚本所需的依赖包
  ```
  moviepy>=1.0.3
  pillow>=9.0.0
  pydub>=0.25.1
  requests>=2.28.0
  ```
- 系统依赖：FFmpeg（必需，用于视频和音频处理）
  ```bash
  # Ubuntu/Debian
  sudo apt-get install ffmpeg

  # macOS
  brew install ffmpeg
  ```

## 操作步骤

### 标准流程（完整路演视频生成）

#### 角色一：文档分析师
1. 分析用户提供的文档，提取核心信息：
   - 主题和目标
   - 目标受众
   - 核心论点
   - 关键数据和案例
2. 输出文档分析摘要供后续角色使用

#### 角色二：结构规划师（关键角色）
1. 生成结构化文档，明确每一页 PPT 讲什么：
   - 页面编号
   - 页面标题
   - 核心内容要点（3-5 条）
   - 演讲时长（建议每页 30-60 秒）
   - 页面类型（封面/内容/数据/总结）
2. 输出结构化 JSON，确保逻辑连贯
3. 此结构将作为后续所有角色的基础

#### 角色三：品牌风格分析师
1. **导入设计系统**（新增功能）：
   - 如果用户提供从 `web-design-analyzer` 导出的 `brand_style.json`，直接导入
   - 使用 `scripts/style_learner.py --load-json ./brand_style.json` 加载配置
   - 验证配置完整性（colors、fonts、layout_style）
2. **学习品牌风格**（传统方式）：
   - 学习用户提供的品牌风格（如样例 PPT、图片、品牌手册）：
     - 分析配色方案（主色、辅助色、强调色）
     - 识别字体类型（标题字体、正文字体）
     - 提取设计元素（logo、图标、装饰）
     - 分析布局风格（简约/商务/创意/科技）
3. 生成品牌风格配置文件（brand_style.json）
4. 为后续视觉设计提供风格指导

#### 角色四：内容策划师
1. 基于结构化文档，规划每页的详细内容：
   - 标题和副标题
   - 内容要点（精炼为短语）
   - 数据和图表说明
   - 演讲提示
2. 应用品牌风格，确保内容与视觉一致
3. 输出完整的内容规划

#### 角色五：视觉设计师
1. 基于品牌风格和内容规划，生成 PPT 图片：
   - 使用智能体的图像生成能力
   - 应用品牌配色和风格
   - 确保所有图片风格统一
   - 生成 slide-01.png 到 slide-N.png
2. 参考品牌风格配置，调整图片色调、字体等

#### 角色六：路演撰稿师
1. 为每一页撰写详细的演讲稿/脚本：
   - 开场白（10-15 秒）
   - 核心内容讲解（每页 30-60 秒）
   - 过渡语（衔接下一页）
   - 总结语（10-15 秒）
2. 确保语言流畅自然，适合口语表达
3. 输出演讲稿（roadshow_script.txt）

#### 角色七：转场设计师
1. 设计页面过渡动画：
   - 选择转场类型（淡入淡出/滑动/缩放/翻转等）
   - 设置转场时长（建议 1-2 秒）
   - 确保转场风格与品牌一致
2. 生成转场配置（transitions.json）

#### 角色八：音频设计师
1. 处理音频内容：
   - **配音**：调用 TTS API 生成语音解说
   - **音效**：添加页面切换音效、强调音效
   - **音乐**：添加背景音乐（从 assets/music/ 或用户上传）
2. 调用 `scripts/audio_processor.py`：
   ```bash
   python scripts/audio_processor.py \
     --script ./roadshow_script.txt \
     --style-brand ./brand_style.json \
     --output ./audio/
   ```
3. 输出音频文件（voiceover.mp3, sound_effects/, background_music.mp3）

#### 角色九：字幕设计师
1. 生成和同步字幕：
   - 根据演讲稿生成字幕文本
   - 计算每句字幕的开始和结束时间
   - 应用品牌字体和样式
2. 调用 `scripts/subtitle_generator.py`：
   ```bash
   python scripts/subtitle_generator.py \
     --script ./roadshow_script.txt \
     --style-brand ./brand_style.json \
     --output ./subtitles.srt
   ```
3. 输出字幕文件（subtitles.srt）

#### 角色十：视频合成师
1. 一键合成完整路演视频：
   - 合并所有图片、转场、配音、音效、音乐、字幕
   - 统一分辨率和帧率（1920x1080, 30fps）
   - 确保音画同步
2. 调用 `scripts/roadshow_composer.py`：
   ```bash
   python scripts/roadshow_composer.py \
     --images ./images/ \
     --audio ./audio/ \
     --subtitles ./subtitles.srt \
     --style-brand ./brand_style.json \
     --output ./roadshow_video.mp4
   ```
3. 输出完整的路演视频

### 品牌风格学习模式

当用户希望保持品牌风格一致时：

1. 用户提供品牌风格样例：
   - PPT 样例文件
   - 品牌手册
   - 关键图片（logo、产品图等）
2. 执行角色三（品牌风格分析师）
3. 保存品牌风格配置供后续使用
4. 后续生成时自动应用此风格

### 与其他 Skill 协同

#### 与 web-design-analyzer 协同（新增）
- web-design-analyzer 分析网页截图，提取设计系统
- 转换为 brand_style.json（使用 `convert_to_roadshow_style.py`）
- ppt-roadshow-generator 导入品牌风格，生成路演视频
- 适用于用户希望路演视频与网页设计保持一致的场景
- 详见：[references/design-system-import-guide.md](references/design-system-import-guide.md)

#### 与 ppt-generator 协同
- ppt-generator 生成 PPT 内容（JSON）
- ppt-roadshow-generator 接收 JSON，继续处理
- 适用于用户已使用 ppt-generator 生成内容的场景

#### 与 nanobanana-ppt-visualizer 协同
- nanobanana 生成图片和播放器
- ppt-roadshow-generator 使用图片，添加配音、音效、字幕
- 适用于用户已有图片，需要完整路演视频的场景

### 可选分支
- 仅生成结构化文档：执行角色一、角色二
- 仅生成图片：执行角色一到角色五
- 仅生成演讲稿：执行角色一到角色六
- 快速模式：使用默认品牌风格，跳过角色三

## 资源索引
- 品牌风格学习：见 [scripts/style_learner.py](scripts/style_learner.py)（用途：学习用户提供的品牌风格，或加载已有配置）
- 音频处理：见 [scripts/audio_processor.py](scripts/audio_processor.py)（用途：TTS 配音、音效、音乐）
- 字幕生成：见 [scripts/subtitle_generator.py](scripts/subtitle_generator.py)（用途：生成和同步字幕）
- 视频合成：见 [scripts/roadshow_composer.py](scripts/roadshow_composer.py)（用途：一键合成完整视频）
- 品牌风格指南：见 [references/brand_style_guide.md](references/brand_style_guide.md)（用途：品牌风格学习指南）
- 设计系统导入：见 [references/design-system-import-guide.md](references/design-system-import-guide.md)（用途：从 web-design-analyzer 导入设计系统）
- 演讲稿模板：见 [references/roadshow_script_template.md](references/roadshow_script_template.md)（用途：演讲稿写作参考）
- 协同指南：见 [references/collaboration_guide.md](references/collaboration_guide.md)（用途：与其他 Skill 协同）
- 示例音乐：见 [assets/music/](assets/music/)（可选：背景音乐文件）
- 品牌风格示例：见 [assets/styles/](assets/styles/)（可选：品牌风格示例）

## 注意事项
- 十角色协作流程，确保每一步输出为下一步输入
- 品牌风格学习是保持一致性的关键，建议用户首次使用时提供样例
- 配音功能需要 TTS API 密钥，通过 `skill_credentials` 工具配置
- 音乐使用 assets/music/ 中的示例或用户上传的文件
- 视频合成使用 FFmpeg，确保已安装
- 支持一次性生成 15-100 页，风格保持一致
- 保持与用户的互动，在关键节点（如风格确认）征求反馈

## 使用示例

### 示例 1：从文档生成完整路演视频
- 功能说明：完整的十角色协作流程
- 执行方式：智能体（10 个角色） + 脚本
- 关键参数：文档路径、品牌样例（可选）、页数（如 15 页）
- 输出：完整路演视频（含配音、音效、音乐、字幕）

### 示例 2：学习品牌风格后生成
- 功能说明：先学习品牌风格，再生成视频
- 执行方式：智能体 + 脚本
- 流程：
  1. 用户提供品牌样例
  2. 品牌风格分析师学习并保存
  3. 后续生成时自动应用

### 示例 3：从网页设计导入品牌风格（新增）
- 功能说明：导入从网页分析中提取的设计系统，生成风格一致的路演视频
- 执行方式：web-design-analyzer + ppt-roadshow-generator
- 流程：
  1. web-design-analyzer 分析网页截图
  2. 转换为 brand_style.json
  3. ppt-roadshow-generator 导入品牌风格
  4. 生成路演视频

### 示例 4：与 ppt-generator 协同
- 功能说明：使用 ppt-generator 的内容，生成路演视频
- 执行方式：ppt-generator + ppt-roadshow-generator
- 流程：
  1. ppt-generator 生成 JSON
  2. ppt-roadshow-generator 接收 JSON，继续处理

### 示例 5：批量生成 100 页视频
- 功能说明：一次性生成 100 页风格统一的视频
- 执行方式：智能体 + 脚本
- 关键：品牌风格学习确保一致性
- 优势：风格统一，无需人工干预
