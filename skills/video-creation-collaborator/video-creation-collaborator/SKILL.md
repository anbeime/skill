---
name: video-creation-collaborator
description: 影品智创多智能体协同视频创作管理工具,提供11个智能体结构化分工、5阶段协同流程、质量管控标准与数据反馈机制,解决生图失真、视频合成瑕疵等问题,确保输出统一可控
dependency:
  python:
    - opencv-python>=4.8.0
    - pillow>=10.0.0
    - moviepy>=1.0.3
    - numpy>=1.24.0
---

# 影品智创 - 多智能体协同视频创作管理

## 任务目标
- 本Skill用于: 规范化和指导10个智能体的协同创作流程,解决生图失真(多肢体/畸形)、视频合成瑕疵等问题
- 能力包含:
  - 11个智能体结构化分工(文案创作/故事策划/脚本创作/分镜导演/分镜画师/字幕师/配音师/音效师/视频工程师/质检/数据反馈)
  - 5阶段协同流程管理(需求承接→内容创作→生图创作→音频字幕→视频合成→全流程质检→数据迭代)
  - 质量管控与闭环反馈(前置质检拦截、数据沉淀迭代)
  - 素材生成支持(图片/音频/字幕/音乐)
  - 技术检测工具支持(图片质量、视频质量、音画同步)
- 触发条件: 用户需要进行短视频创作,或需要规范化多智能体协同流程

## 前置准备
- 依赖说明:
  ```
  opencv-python>=4.8.0
  pillow>=10.0.0
  moviepy>=1.0.3
  numpy>=1.24.0
  ```
- 非标准文件/文件夹准备:
  ```bash
  # 创建工作目录
  mkdir -p ./input/{materials,scripts}
  mkdir -p ./output/{drafts,storyboards,final}
  mkdir -p ./cache/{images,audio}
  ```

## 操作步骤

### 标准流程(5个阶段,10个智能体)

#### 第一阶段: 需求承接与内容框架搭建

**触发节点**: 用户输入核心需求(商品信息+视频需求)

**步骤1: 文案创作师智能体(首节点)**
- 职责: 基于商品信息提炼核心卖点,生成适配短视频的文案
- 输入: 商品品类、核心卖点、目标受众、视频风格、时长
- 输出: 
  - 核心Slogan(8-12字,简洁有力)
  - 分镜适配文案(3-5句,每句4-8字)
- 质量标准: 无歧义、无夸大,贴合视频调性
- 下一级触发: 立即触发【故事策划师】、【字幕师】(暂存)

**步骤2: 故事策划师智能体**
- 职责: 基于卖点、文案,设计适配短视频时长的场景化故事线
- 输入: Slogan、分镜文案、商品信息、视频时长、风格
- 输出: 
  - 场景化故事线(镜头拆分、场景/动作标注)
  - 镜头数量(30秒8-10个、45秒12-15个、60秒15-18个)
- 质量标准: 逻辑连贯,时长严格匹配,无无关场景
- 下一级触发: 立即触发【脚本创作师】

**步骤3: 脚本创作师智能体**
- 职责: 将故事线转化为标准化、可执行的分镜脚本
- 输入: 故事线、文案、视频时长、分辨率、比例
- 输出: 
  - 标准化分镜脚本(镜头序号、时长、场景描述、画面动作、文案、音效备注)
  - 画面动作描述(明确人体肢体姿态,规避模糊表述)
- 质量标准: 时长精准分配,画面动作具体,格式统一
- 下一级触发: 立即触发【分镜导演】、【分镜画师】、【字幕师】、【音效师】

#### 第二阶段: 视觉内容创作与质检

**触发节点**: 分镜脚本确认

**步骤4: 分镜导演智能体**
- 职责: 规划每个镜头的画面细节、光影、构图,为分镜画师提供精准依据
- 输入: 分镜脚本、商品细节图(如有)、视频风格
- 输出: 
  - 镜头画面规范(构图/光影/色调/肢体规范/商品细节)
  - 负面规避清单(禁止多余肢体、畸形、虚化等)
- 质量标准: 构图清晰,光影均匀,肢体规范,商品细节明确
- 下一级触发: 立即触发【分镜画师】

**步骤5: 分镜画师智能体**
- 职责: 基于画面规范,生成高质量、无瑕疵的分镜图片
- 输入: 画面描述、分镜脚本、商品信息
- 输出: 1080P合格分镜图片(单张对应单个镜头,命名规范)
- 质量标准: 
  - 人体结构正常(无多余肢体/畸形/重影)
  - 商品细节精准(无变形/模糊)
  - 画质细腻(1080P,无颗粒感)
- 负面规避: 禁止多余肢体、手部畸形、商品变形、画面噪点等
- 下一级触发: 
  - 图片生成后,触发【视频工程师】素材预处理
  - 同时触发【质检智能体】分镜图片专项质检

#### 第三阶段: 音频字幕创作(并行执行)

**触发节点**: 分镜脚本确认(可并行启动,无需等待视觉内容)

**步骤6: 配音师智能体**
- 职责: 根据分镜文案生成高质量旁白/配音
- 输入: 分镜文案、视频风格、情感基调
- 输出:
  - 旁白文本(与分镜文案对应,可适当口语化)
  - 音色建议(活力男声/专业女声/稳重男声/亲切女声等)
  - 语速要求(中等/稍快/稍慢)
  - 情感标注(积极/专业/沉稳/亲切等)
- 质量标准: 语音自然流畅,情感贴合场景,无明显机械感
- 下一级触发: 输出同步至【音效师】,调用`audio_generator.py`生成音频文件

**步骤7: 字幕师智能体**
- 职责: 创作适配画面的字幕,确保显示效果与可读性
- 输入: 分镜文案、分镜脚本、视频风格、画面比例
- 输出: 
  - 字幕信息包(文本+对应镜头时长+叠加位置)
  - 格式规范(字体/字号/颜色/位置)
- 质量标准: 无错别字,字数适配(每秒1-2字),避开商品主体
- 下一级触发: 输出同步至【视频工程师】

**步骤8: 音效师智能体**
- 职责: 推荐适配的背景音乐与场景音效,确保音画协调
- 输入: 分镜脚本、视频风格、时长、核心场景
- 输出: 
  - 音效方案包(背景音乐+场景音效+时间节点+音量参数)
  - 音效名称、风格描述、时长、音量建议
- 质量标准: 风格贴合,节奏匹配,音量适中,无版权问题
- 下一级触发: 输出同步至【视频工程师】

#### 第四阶段: 视频合成与成品质检

**触发节点**: 分镜图片质检合格

**步骤9: 视频工程师智能体**
- 职责: 基于各智能体输出素材,完成高质量视频合成
- 输入: 合格分镜图片、字幕信息、音效方案
- 输出: 合成后的MP4成品视频
- 质量标准: 
  - 素材预处理(调用质量检测脚本,识别瑕疵)
  - 合成参数(1080P, 25fps, 8Mbps,无黑边/卡顿)
  - 转场效果(淡入淡出,0.3-0.5秒,过渡自然)
  - 音画同步(音频偏移≤0.1秒)
- 下一级触发: 成品输出后立即触发【质检智能体】

**步骤10: 质检智能体(全流程穿插)**
- 职责: 对各智能体输出物进行全环节质检,拦截瑕疵,推动整改
- 输入: 各环节输出物、质量标准、负面规避清单
- 输出: 
  - 分环节质检报告(合格/不合格,瑕疵类型,整改建议)
  - 质检台账(瑕疵数据、整改结果、合格率)
- 质检维度:
  - 内容层(文案/故事线/脚本/字幕)
  - 视觉层(分镜图片/成品视频)
  - 音频层(背景音乐/音效/音画同步)
  - 格式层(比例/脚本格式/视频参数)
- 处理规则:
  - 轻微瑕疵(文案语序微调)→直接反馈优化
  - 重大瑕疵(多肢体/画面撕裂)→拦截输出,要求重制
  - 前置质检→分镜图片/成品视频强制质检,不合格驳回
- 下一级触发: 
  - 不合格→触发对应智能体重做
  - 合格→触发【数据反馈智能体】

#### 第五阶段: 数据沉淀与迭代优化

**触发节点**: 全流程质检合格

**步骤11: 数据反馈智能体**
- 职责: 收集分析全流程数据,输出迭代建议,优化智能体提示词与协同逻辑
- 输入: 质检台账、创作耗时数据、用户反馈
- 输出: 
  - 数据统计报告(合格率、高频瑕疵、创作耗时、整改率)
  - 迭代优化建议(针对高频瑕疵优化提示词、调整协同流程)
  - 数据沉淀(瑕疵类型-优化方案-效果验证闭环)
- 分析维度:
  - 瑕疵分析(TOP3高频瑕疵,定位根因)
  - 效率分析(识别流程瓶颈)
  - 优化效果(验证迭代有效性)
- 下一级触发: 输出同步至技能开发端,更新智能体配置,完成迭代闭环

## 并行协同与闭环管控

### 并行执行
- **字幕师、音效师**可在脚本创作师输出分镜脚本后并行启动,无需等待视觉内容完成
- **效率提升**: 减少等待时间,整体创作周期缩短

### 闭环管控
- **所有输出物需经质检智能体校验**合格后方可进入下一环节
- **重大瑕疵直接拦截**,避免问题流转
- **跟踪整改结果**,确保100%解决

### 迭代联动
- **数据反馈智能体的优化建议**直接作用于各智能体底层配置
- **形成"创作-质检-优化"**持续迭代机制

## 质量检测工具使用

### 图片质量检测
```bash
# 调用图片质量检测脚本
python scripts/image_quality_checker.py --image ./cache/images/shot_001.jpg --resolution 1920x1080
```

检测维度:
- 肢体异常(多余肢体/畸形/重影)
- 画面质量(模糊/噪点/变形)
- 商品细节(纹理/轮廓/按键)
- 分辨率/比例

### 视频质量检测
```bash
# 调用视频质量检测脚本
python scripts/video_quality_checker.py --video ./output/final/video.mp4 --resolution 1920x1080 --duration 30 --fps 25
```

检测维度:
- 分辨率/时长/帧率/码率
- 画面质量(卡顿/撕裂/转场瑕疵)
- 音频质量(清晰度/杂音)
- 音画同步(偏移≤0.1秒)
- 字幕遮挡检测

## 素材生成与视频合成流程

### 素材生成流程

#### 1. 图片素材生成
**触发时机**: 分镜画师智能体完成画面设计后

**执行步骤**:
```bash
# 准备分镜脚本JSON文件
cat > ./scripts/storyboard.json << 'EOF'
{
  "shots": [
    {
      "shot_id": "L01",
      "description": "智能手表特写,手指滑动屏幕",
      "duration": 3.0,
      "resolution": "1920x1080"
    }
  ],
  "style": "科技风,冷色调,清晰锐利"
}
EOF

# 调用图片生成脚本
python scripts/image_generator.py \
  --storyboard ./scripts/storyboard.json \
  --output ./output/images \
  --style "科技风,冷色调"
```

**输出规范**:
- 路径: `./output/images/shot_{shot_id}.jpg`
- 格式: JPG, 1080P (1920x1080)
- 质量要求: 无肢体异常,商品细节清晰,画质细腻

**参考**: [references/asset-specifications.md](references/asset-specifications.md) - 图片素材规范

#### 2. 音频素材生成
**触发时机**: 配音师智能体完成旁白文本,音效师智能体完成音效方案后

**执行步骤**:
```bash
# 生成旁白音频
python scripts/audio_generator.py \
  --mode narration \
  --text "腕上未来,触手可及" \
  --voice "professional_male" \
  --output ./output/audio/narration_S01.wav

# 生成背景音乐
python scripts/music_generator.py \
  --style "科技风,轻快" \
  --duration 30 \
  --output ./output/audio/background_music.wav

# 混合音频(旁白+背景+音效)
python scripts/audio_generator.py \
  --mode mix \
  --narration ./output/audio/narration_S01.wav \
  --background ./output/audio/background_music.wav \
  --effects ./output/audio/sound_effects/ \
  --output ./output/audio/merged_audio.wav
```

**输出规范**:
- 路径: `./output/audio/`
- 格式: WAV (44.1kHz, 16bit/24bit)
- 质量要求: 无杂音,音量平衡,音质清晰

**参考**: [references/asset-specifications.md](references/asset-specifications.md) - 音频素材规范

#### 3. 字幕素材生成
**触发时机**: 字幕师智能体完成字幕设计后

**执行步骤**:
```bash
# 准备分镜脚本
cat > ./scripts/storyboard.json << 'EOF'
{
  "shots": [
    {
      "shot_id": "L01",
      "duration": 3.0,
      "text": "腕上未来"
    },
    {
      "shot_id": "L02",
      "duration": 3.0,
      "text": "触手可及"
    }
  ]
}
EOF

# 生成SRT字幕
python scripts/subtitle_generator.py \
  --storyboard ./scripts/storyboard.json \
  --format srt \
  --output ./output/subtitles/subtitle.srt
```

**输出规范**:
- 路径: `./output/subtitles/subtitle.srt` 或 `.ass`
- 格式: SRT/ASS (UTF-8编码)
- 质量要求: 无错别字,字数适配,位置无遮挡

**参考**: [references/asset-specifications.md](references/asset-specifications.md) - 字幕素材规范

### 视频合成流程

**触发时机**: 所有素材(图片/音频/字幕)准备完成并质检合格后

**执行步骤**:
```bash
# 准备项目配置
cat > ./scripts/project_config.json << 'EOF'
{
  "images_dir": "./output/images",
  "audio_file": "./output/audio/merged_audio.wav",
  "subtitle_file": "./output/subtitles/subtitle.srt",
  "shots": [
    {
      "shot_id": "L01",
      "duration": 3.0,
      "transition": "fade"
    },
    {
      "shot_id": "L02",
      "duration": 3.0,
      "transition": "cut"
    }
  ],
  "width": 1920,
  "height": 1080,
  "fps": 25,
  "duration": 30,
  "bitrate": "8000k"
}
EOF

# 验证项目配置
python scripts/video_compositor.py \
  --config ./scripts/project_config.json \
  --output ./output/temp/validate.mp4 \
  --validate_only

# 合成最终视频
python scripts/video_compositor.py \
  --config ./scripts/project_config.json \
  --output ./output/final/final_video_$(date +%Y%m%d).mp4
```

**输出规范**:
- 路径: `./output/final/final_video_{日期}.mp4`
- 格式: MP4 (H.264编码)
- 参数: 1080P, 25fps, 8Mbps
- 质量要求: 无卡顿,音画同步≤0.1秒,字幕同步无延迟

**参考**: [references/asset-specifications.md](references/asset-specifications.md) - 视频输出规范

### 质量检测流程

#### 1. 图片质量检测
```bash
python scripts/image_quality_checker.py \
  --image ./output/images/shot_L01.jpg \
  --resolution 1920x1080 \
  --check_limb_anomaly \
  --check_blur \
  --check_deformation
```

#### 2. 音频质量检测
```bash
python scripts/audio_quality_checker.py \
  --audio ./output/audio/narration_S01.wav \
  --sample_rate 44100 \
  --check_noise
```

#### 3. 视频质量检测
```bash
python scripts/video_quality_checker.py \
  --video ./output/final/final_video_20240122.mp4 \
  --resolution 1920x1080 \
  --duration 30 \
  --fps 25 \
  --check_sync
```

**参考**: [references/quality-standards.md](references/quality-standards.md) - 质检标准

## 资源索引
- 必要脚本:
  - [scripts/image_generator.py](scripts/image_generator.py) - 图片生成脚本(根据分镜脚本生成1080P图片)
  - [scripts/audio_generator.py](scripts/audio_generator.py) - 音频生成脚本(TTS旁白+背景音乐混合)
  - [scripts/subtitle_generator.py](scripts/subtitle_generator.py) - 字幕生成脚本(SRT/ASS格式)
  - [scripts/music_generator.py](scripts/music_generator.py) - 背景音乐生成脚本
  - [scripts/video_compositor.py](scripts/video_compositor.py) - 视频合成主脚本(整合图片/音频/字幕)
  - [scripts/image_quality_checker.py](scripts/image_quality_checker.py) - 图片质量检测工具(肢体异常/模糊/变形)
  - [scripts/video_quality_checker.py](scripts/video_quality_checker.py) - 视频质量检测工具(含音画同步)
- 领域参考:
  - [references/agent-prompts.md](references/agent-prompts.md) - 11个智能体的详细提示词模板
  - [references/quality-standards.md](references/quality-standards.md) - 质检标准与负面规避清单
  - [references/asset-specifications.md](references/asset-specifications.md) - 素材生成与输出规范(图片/音频/字幕/视频)
  - [references/data-analysis.md](references/data-analysis.md) - 数据统计与迭代优化模板
- 输出资产:
  - [assets/templates/storyboard-template.md](assets/templates/storyboard-template.md) - 分镜脚本标准模板
  - [assets/reports/quality-report-template.md](assets/reports/quality-report-template.md) - 质检报告模板

## 注意事项
- **智能体协同**: 严格按照11个智能体的触发顺序和协同规则执行
- **素材规范**: 所有素材生成必须遵循[asset-specifications.md](references/asset-specifications.md)中的规范
- **视频合成**: 合成前必须确保所有素材(图片/音频/字幕)就位并质检合格
- **质量优先**: 所有输出物必须经质检智能体校验,重大瑕疵直接拦截
- **闭环迭代**: 数据反馈智能体的优化建议必须应用于下一轮创作
- **技术检测**: 视频合成前必须调用质量检测脚本,素材不合格不得合成
- **数据沉淀**: 质检台账和创作数据必须完整记录,用于迭代优化

## 使用示例

### 示例1:完整创作流程
```bash
# 用户请求: "为智能手表创作30秒短视频,科技风,目标年轻人"

# 智能体执行流程:
1. 文案创作师: 输出Slogan "腕上未来,触手可及" + 分镜文案
2. 故事策划师: 输出9个镜头的故事线
3. 脚本创作师: 输出标准化分镜脚本(时长、场景、动作、文案)
4. 分镜导演: 输出9个镜头的画面规范 + 负面规避清单
5. 分镜画师: 生成9张1080P分镜图片(调用质量检测脚本)
6. 字幕师: 输出字幕信息包(并行执行)
7. 音效师: 输出音效方案包(并行执行)
8. 质检智能体: 检测分镜图片,发现第3张图片肢体异常,反馈分镜画师重绘
9. 分镜画师: 重新生成第3张图片,质检合格
10. 视频工程师: 合成视频(调用视频质量检测脚本)
11. 质检智能体: 检测成品视频,音画同步0.08秒,合格
12. 数据反馈: 输出数据统计报告 + 迭代建议
```

### 示例2:图片质量检测
```python
from scripts.image_quality_checker import check_image_quality

result = check_image_quality(
    image_path="./cache/images/shot_003.jpg",
    expected_resolution=(1920, 1080),
    check_limb_anomaly=True,
    check_blur=True,
    check_deformation=True
)

if not result['overall']:
    print(f"发现瑕疵: {result['issues']}")
    # 触发分镜画师重绘
else:
    print("图片质量合格,可用于合成")
```

### 示例3:质检闭环示例
```
质检智能体检测:
- 分镜图片: 合格率92%(10张图片,8张合格,1张轻微瑕疵,1张重大瑕疵)
  - 重大瑕疵: shot_007.jpg 发现多余肢体,驳回分镜画师重绘
  - 轻微瑕疵: shot_003.jpg 轻微模糊,反馈优化

成品视频: 合格
- 分辨率: 1920x1080 ✓
- 帧率: 25fps ✓
- 音画同步: 0.08秒 ✓
- 字幕遮挡: 无 ✓

数据反馈智能体:
- 高频瑕疵TOP3: 
  1. 肢体异常(占比8%) → 优化分镜导演/画师提示词
  2. 轻微模糊(占比6%) → 调整画质标准
  3. 字幕位置偏差(占比4%) → 优化字幕师模板
- 效率瓶颈: 分镜画师重绘耗时过长 → 调整前置质检规则
```
