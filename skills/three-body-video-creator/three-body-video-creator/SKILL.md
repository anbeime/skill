---
name: three-body-video-creator
description: 《三体》赛道AI视频创作工具,提供结构化的多智能体协作流程、素材生成与视频合成,涵盖选题深化、视觉设计、音频生成、视频制作全流程
dependency:
  python:
    - opencv-python>=4.8.0
    - moviepy>=1.0.3
    - Pillow>=10.0.0
    - edge-tts>=6.1.0
    - requests>=2.28.0
---

# 《三体》赛道视频创作工具

## 任务目标
- 本Skill用于: 协助创作团队按照规范化的多智能体协作流程,完成《三体》主题视频的策划、制作与合成
- 能力包含:
  - 选题深化与内容策划(原著考据、剧情架构、台词设计)
  - 视觉呈现设计(场景概念、人物建模、分镜脚本)
  - 素材生成与音频制作(配音生成、音效生成、背景音乐生成)
  - 视频合成与输出(图片/音频/字幕合成、质量检测)
- 触发条件: 用户需要进行《三体》主题视频创作,或需要规范化创作流程指导

## 前置准备
- 依赖说明:
  ```
  opencv-python>=4.8.0
  moviepy>=1.0.3
  Pillow>=10.0.0
  ```
- 非标准文件/文件夹准备:
  ```bash
  # 创建视频素材目录
  mkdir -p ./raw-materials/{scenes,characters,audio}
  mkdir -p ./output/{draft,final}
  ```

## 操作步骤

### 标准流程(72小时周期)

#### 第一阶段:前期筹备(12小时)
- **步骤1:原著考据与设定提取**
  - 阅读 [references/three-body-settings.md](references/three-body-settings.md),提取《三体2》威慑纪元核心设定
  - 建立18小时时间线锚点,明确关键人物(罗辑、联合国秘书长、三体监听员)的行为准则
  - 输出: 《18小时时间线锚点表》《人物行为合规清单》

- **步骤2:剧情架构设计**
  - 搭建"三线并行"叙事框架(罗辑个人线+联合国权力线+三体试探线)
  - 设计3个核心冲突点和1个情感高潮
  - 输出: 《三线平行叙事分镜大纲》《情绪曲线图》
  - 参考 [references/storyboard-template.md](references/storyboard-template.md)

- **步骤3:台词创作**
  - 基于人物性格撰写台词:
    - 罗辑:疲惫却决绝,低沉平静,略带沙哑
    - 联合国秘书长:虚伪焦虑,语速偏快
    - 三体监听员:冰冷客观,电子合成音风格
  - 输出: 《角色对白脚本(含语气/停顿标记)》
  - 参考 [references/character-profiles.md](references/character-profiles.md)

#### 第二阶段:视觉制作(24小时)
- **步骤4:视觉风格规范制定**
  - 阅读 [references/visual-style-guide.md](references/visual-style-guide.md)
  - 确定色调体系(冷灰#333333/科技蓝#0099FF)、光影风格、构图原则
  - 输出: 《视觉风格指南》《场景/人物设计规范》

- **步骤5:场景设计**
  - 设计3个核心场景:
    - 威慑控制室(圆柱形沉浸式终端舱,极简工业风)
    - PDC紧急会议厅(圆形穹顶,庄重却空洞)
    - 三体监听站(地下密闭结构,非欧几里得几何排列)
  - 输出: 《场景概念图提示词》《场景要素清单》
  - 参考 [assets/scene-examples/](assets/scene-examples/)

- **步骤6:人物一致性建模**
  - 罗辑形象锚定:中年40岁左右,面色苍白,眼神锐利却疲惫,头发微乱
  - 生成不同神态版本(掌控者/观察者/守护者)
  - 输出: 《罗辑标准形象锚定图集》《人物状态对照表》
  - 参考 [assets/character-reference/](assets/character-reference/)

- **步骤7:分镜脚本细化**
  - 将剧情大纲转化为专业分镜,标注:
    - 镜头类型(特写/中景/全景)
    - 运镜方式(固定/推轨/切镜)
    - 时长(0.5-1秒/镜头)
    - 光影效果
  - 输出: 《电影分镜脚本(含时间码)》《渲染元数据》
  - 参考 [references/storyboard-template.md](references/storyboard-template.md)

- **步骤8:图片生成**
  - 根据分镜脚本生成1080P关键帧序列图
  - 确保风格统一(冷色调、极简科技感)
  - 输出: 《1080P关键帧序列图》

#### 第三阶段:音频与剪辑(24小时)
- **步骤9:音频设计**
  - 场景音效:
    - 威慑系统:低沉持续电子音
    - 三体信号:尖锐短促脉冲音
    - 联合国会场:轻微交谈声、纸张摩擦声
  - BGM:压抑纯音乐,前期钢琴+弦乐,后期加入鼓点
  - 输出: 《音效设计说明》《BGM情绪-时间对应表》

- **步骤10:配音指导**
  - 制定配音风格指南:
    - 罗辑:低沉平静,语速缓慢,略带沙哑
    - 联合国秘书长:虚伪焦虑,语速偏快
    - 三体监听员:电子合成音,冰冷无起伏
  - 输出: 《配音角色卡》《配音音频文件》

- **步骤11:素材生成与视频合成**
  - 配音生成:
    - 调用 `scripts/voice_generator.py` 生成角色配音
    - 参数: `--input <旁白数据JSON> --output ./output/audio/voice`
    - 使用 Edge-TTS 引擎,支持多音色
    - 输出: 配音文件到 `./output/audio/voice/`
  - 音效生成:
    - 调用 `scripts/sound_generator.py --type sound` 生成音效
    - 参数: `--input <音效配置JSON> --output ./output/audio/sound_effects`
    - 支持转场、冲击、动作、环境等音效类型
    - 输出: 音效文件到 `./output/audio/sound_effects/`
  - 背景音乐生成:
    - 调用 `scripts/sound_generator.py --type music` 生成背景音乐
    - 参数: `--input <音乐配置JSON> --output ./output/audio/background_music`
    - 支持 Suno API(可选)或占位实现
    - 输出: 背景音乐到 `./output/audio/background_music/`
  - 视频合成:
    - 调用 `scripts/video_compositor.py` 合成最终视频
    - 参数: `--images <图片目录> --audio <音频目录> --subtitles <字幕文件> --output <输出路径>`
    - 合成图片、配音、音效、背景音乐、字幕
    - 输出: 最终视频文件 `./output/final/video.mp4`
  - 输出: 《成片视频文件》

- **步骤12:原著合规检测**
  - 检测维度:
    - 人物性格是否符合原著
    - 威慑系统逻辑是否正确
    - 剧情推进是否合理
  - 输出: 《合规性报告》《不合规项修改建议》

- **步骤13:技术指标检测**
  - 调用 `scripts/quality_checker.py` 检测:
    - 视频分辨率、时长、帧率
    - 音频参数(采样率、声道)
    - 字幕格式规范性
  - 输出: 《技术质量检测报告》

- **步骤14:B站适配优化**
  - 标题:含核心关键词(三体/罗辑/威慑纪元/18小时),加入情绪词与悬念
  - 封面:罗辑特写+威慑控制屏背景,冷色调,突出悬念
  - 标签:#三体AI创作大赛 #三体2 #威慑纪元 #罗辑 #科幻剧情
  - 开头钩子:前3秒用三体信号+罗辑特写吸引观众
  - 输出: 《爆款标题/封面/标签方案》《前5秒钩子脚本》

- **步骤15:最终质量检测**
  - 五维评审(每项0-20分,总分100分):
    1. 画面质量(场景/人物贴合度、清晰度)
    2. 剧情流畅度(三线叙事衔接、节奏控制)
    3. 音效适配(BGM与剧情、音效与场景)
    4. 原著合规(设定、人物、逻辑)
    5. B站适配(标题、封面、钩子、标签)
  - 总分≥80分为合格
  - 输出: 《最终审核报告》《发布许可》

### 可选分支
- 当 **原著合规问题严重** → 触发步骤1-3回改,重新考据设定
- 当 **视觉风格不一致** → 触发步骤4-8回改,重新生成场景/人物
- 当 **素材生成失败** → 触发步骤11重新生成配音/音效/音乐
- 当 **技术指标不达标** → 触发步骤13重新检测,调整参数重新剪辑

## 资源索引
- 必要脚本:
  - [scripts/quality_checker.py](scripts/quality_checker.py) - 视频技术指标检测工具
  - [scripts/voice_generator.py](scripts/voice_generator.py) - 配音生成工具(Edge-TTS)
  - [scripts/sound_generator.py](scripts/sound_generator.py) - 音效和背景音乐生成工具
  - [scripts/video_compositor.py](scripts/video_compositor.py) - 视频合成工具
  - [scripts/error_handler.py](scripts/error_handler.py) - 错误处理和重试机制
- 领域参考:
  - [references/three-body-settings.md](references/three-body-settings.md) - 《三体》原著设定与威慑纪元规则(何时读取:前期筹备阶段)
  - [references/visual-style-guide.md](references/visual-style-guide.md) - 视觉风格规范与设计原则(何时读取:视觉制作阶段)
  - [references/storyboard-template.md](references/storyboard-template.md) - 分镜脚本标准模板(何时读取:分镜设计阶段)
  - [references/character-profiles.md](references/character-profiles.md) - 人物档案与行为准则(何时读取:台词创作/人物建模阶段)
- 输出资产:
  - [assets/scene-examples/](assets/scene-examples/) - 场景设计提示词示例(直接用于生成场景描述)
  - [assets/character-reference/](assets/character-reference/) - 人物形象描述参考(直接用于建模指导)
  - [assets/ui-components/](assets/ui-components/) - 界面元素设计规范(直接用于UI设计)

## 注意事项
- 优先使用智能体的创作能力,避免为简单任务编写脚本
- 脚本仅用于技术性检测和验证(质量检测、格式验证)
- 充分利用references中的参考文档,确保内容符合原著设定
- 所有创作内容必须经过原著合规检测,避免OOC问题
- 保持与用户偏好的一致性,根据用户反馈调整创作方向

## 使用示例

### 示例1:快速创作流程
```bash
# 用户请求: "帮我创作一个《三体》威慑纪元的8分钟视频"

# 智能体执行流程:
1. 读取 references/three-body-settings.md,提取核心设定
2. 按照步骤1-3完成前期筹备(时间线、剧情大纲、台词)
3. 按照步骤4-8完成视觉制作(场景、人物、分镜)
4. 按照步骤9-11完成音频与剪辑
5. 调用 scripts/quality_checker.py 检测技术指标
6. 完成步骤12-15的质量检测与优化
```

### 示例2:质量检测
```python
# 检测视频技术指标
from scripts.quality_checker import check_video_quality

result = check_video_quality(
    video_path="./output/final/video.mp4",
    expected_resolution=(1920, 1080),
    expected_duration=510,  # 8分30秒
    expected_fps=30
)

print(result)
# 输出: {'resolution': True, 'duration': True, 'fps': True, 'overall': True}
```

### 示例3:台词创作
```bash
# 用户请求: "为罗辑写一段移交威慑权的台词"

# 智能体执行:
1. 读取 references/character-profiles.md,了解罗辑性格
2. 参考 references/three-body-settings.md,确保符合原著设定
3. 生成台词:
   "控制权移交给你们了。但记住,这是双刃剑——它在你们手中,也在我手中。"
   (标注:语气低沉平静,语速缓慢,略带疲惫但眼神锐利)
```
