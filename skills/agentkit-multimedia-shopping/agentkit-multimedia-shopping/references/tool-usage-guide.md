# 工具使用说明

## 概览
本文档说明如何使用ByteDance agentkit-samples多媒体用例的工具进行多模态内容生成。

---

## 工具列表

### 1. AI绘画生成工具
**功能**：生成小省导购员角色形象和场景背景

**使用方式**：
- 调用 `scripts/generate_character.py` 生成角色形象
- 调用 `scripts/generate_scene.py` 生成场景背景

**输入参数**：
- `prompt`：提示词（中文或英文）
- `aspect_ratio`：画面比例（9:16）
- `resolution`：分辨率（1080x1920）

**输出**：图像文件（JPG或PNG）

---

### 2. 语音合成工具
**功能**：合成导购员语音

**使用方式**：
- 调用 `scripts/generate_voice.py` 合成语音

**输入参数**：
- `text`：话术内容
- `voice_type`：语音类型（语速、语气）
- `emotion`：情绪基调
- `format`：音频格式（16kHz单声道wav）

**输出**：音频文件（16kHz单声道wav）

---

### 3. 音乐生成工具
**功能**：生成背景音乐

**使用方式**：
- 调用 `scripts/generate_music.py` 生成音乐

**输入参数**：
- `style`：音乐风格（管弦乐、钢琴、弦乐）
- `emotion`：情绪基调
- `duration`：时长（秒）
- `format`：音频格式（16kHz单声道wav）

**输出**：音频文件（16kHz单声道wav）

---

### 4. 视频生成工具
**功能**：生成多模态视频

**使用方式**：
- 调用 `scripts/generate_video.py` 生成视频

**输入参数**：
- `character_image`：角色参考图路径
- `scene_image`：场景参考图路径
- `voice_file`：语音文件路径
- `music_file`：音乐文件路径
- `prompt`：InfiniteTalk专用提示词
- `duration`：时长（秒）
- `aspect_ratio`：画面比例（9:16）

**输出**：视频文件（MP4）

---

## 工作流程

### 完整流程
```
1. 生成角色形象（generate_character.py）
2. 生成场景背景（generate_scene.py）
3. 合成导购员语音（generate_voice.py）
4. 生成背景音乐（generate_music.py）
5. 生成InfiniteTalk提示词（使用infinitetalk-shopping-avatar Skill）
6. 生成视频（generate_video.py）
```

### 简化流程
```
1. 生成角色形象（generate_character.py）
2. 生成场景背景（generate_scene.py）
3. 生成视频（generate_video.py，使用预设音频）
```

---

## 参数说明

### AI绘画参数
| 参数 | 说明 | 可选值 |
|-----|------|--------|
| prompt | 提示词 | 中文或英文提示词 |
| aspect_ratio | 画面比例 | 9:16 |
| resolution | 分辨率 | 1080x1920 |

### 语音合成参数
| 参数 | 说明 | 可选值 |
|-----|------|--------|
| text | 话术内容 | 中文字符串 |
| voice_type | 语音类型 | 标准/亲切/专业 |
| emotion | 情绪基调 | 热情/专业/亲切 |
| format | 音频格式 | 16kHz单声道wav |

### 音乐生成参数
| 参数 | 说明 | 可选值 |
|-----|------|--------|
| style | 音乐风格 | 管弦乐/钢琴/弦乐 |
| emotion | 情绪基调 | 热情/专业/亲切 |
| duration | 时长 | 5（秒） |
| format | 音频格式 | 16kHz单声道wav |

### 视频生成参数
| 参数 | 说明 | 可选值 |
|-----|------|--------|
| character_image | 角色参考图路径 | 文件路径 |
| scene_image | 场景参考图路径 | 文件路径 |
| voice_file | 语音文件路径 | 文件路径 |
| music_file | 音乐文件路径 | 文件路径 |
| prompt | InfiniteTalk提示词 | 提示词文本 |
| duration | 时长 | 5（秒） |
| aspect_ratio | 画面比例 | 9:16 |

---

## 示例

### 示例1：生成角色形象
```python
from scripts.generate_character import generate_character

# 生成角色形象
character_image = generate_character(
    prompt="25岁左右女性数字人，鹅蛋脸、杏眼带笑、浅棕色齐肩卷发，肤色白皙，唇色淡粉，身穿浅灰色修身西装套裙，内搭白色衬衫，脚踩米色细跟鞋，佩戴银色简约项链，气质专业又亲和，手部姿态优雅自然。现代商务场景，背景简约，前景清晰。9:16竖屏，高清晰度，商业化带货风格。",
    aspect_ratio="9:16",
    resolution="1080x1920"
)

# 保存角色形象
character_image.save("./output/character_reference.jpg")
```

### 示例2：生成语音
```python
from scripts.generate_voice import generate_voice

# 合成语音
voice_file = generate_voice(
    text="宝子们，今天给你们推荐一款超值商品，性价比超高，闭眼冲不亏！",
    voice_type="亲切",
    emotion="热情",
    format="16khz_mono_wav"
)

# 保存语音文件
voice_file.save("./output/voice.wav")
```

### 示例3：生成视频
```python
from scripts.generate_video import generate_video

# 生成视频
video_file = generate_video(
    character_image="./output/character_reference.jpg",
    scene_image="./output/scene_reference.jpg",
    voice_file="./output/voice.wav",
    music_file="./output/music.wav",
    prompt="InfiniteTalk专用提示词...",
    duration=5,
    aspect_ratio="9:16"
)

# 保存视频文件
video_file.save("./output/video.mp4")
```

---

## 注意事项

1. **参数格式**：严格按照参数格式要求输入
2. **文件路径**：确保所有文件路径正确且可访问
3. **分辨率匹配**：图像必须为9:16竖屏，分辨率≥1080×1920
4. **音频格式**：音频必须为16kHz单声道wav格式
5. **提示词质量**：提示词质量直接影响生成效果
6. **工作流顺序**：严格按照图像→音频→视频的顺序生成
