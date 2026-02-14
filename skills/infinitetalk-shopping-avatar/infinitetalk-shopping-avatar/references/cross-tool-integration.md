# 跨工具集成方案

## 目录
- [1. 集成流程概述](#1-集成流程概述)
- [2. Suno音乐集成](#2-suno音乐集成)
- [3. AI绘画集成](#3-ai绘画集成)
- [4. InfiniteTalk推理对接](#4-infinitetalk推理对接)
- [5. 跨工具数据流](#5-跨工具数据流)
- [6. 推理脚本调用示例](#6-推理脚本调用示例)

## 概览
本文档定义Suno音乐、AI绘画、InfiniteTalk之间的跨工具集成方案，实现从提示词到成品视频的闭环。

---

## 1. 集成流程概述

### 1.1 整体流程

```
提示词生成 → Suno音乐生成 → 音频编码 → AI绘画生成 → InfiniteTalk推理 → 视频生成
```

### 1.2 四大智能体分工

| 智能体角色 | 核心职责 | 输出物 |
|------------|---------|--------|
| 提示词生成师 | 生成InfiniteTalk专用提示词 | 分幕提示词文本、参数配置表 |
| 质量管控师 | 核查提示词质量 | 质检报告、修正建议 |
| 知识库运维师 | 归档提示词和知识库 | 知识库检索接口（JSON格式） |
| 跨环节适配师 | 跨工具集成 | 音频编码文件、视频生成结果 |

### 1.3 数据流向

```
提示词（文本）→ Suno（音频）→ chinese-wav2vec2-base（音频特征）→ AI绘画（参考图）→ InfiniteTalk（视频）
```

---

## 2. Suno音乐集成

### 2.1 音乐生成流程

#### 步骤1：情绪关键词提取
从五幕提示词中提取情绪关键词：
- 第一幕：热情、神秘
- 第二幕：专业、详细
- 第三幕：专注、生动
- 第四幕：自信、有力
- 第五幕：鼓励、坚决

#### 步骤2：音乐风格生成
根据情绪关键词生成音乐风格描述：

**示例**：
```
第一幕：史诗管弦乐（低沉鼓点）
第二幕：钢琴独奏（舒缓低沉）
第三幕：小提琴+大提琴二重奏（旋律多变）
第四幕：女声吟唱+弦乐（音量由强渐弱）
第五幕：史诗管弦乐（铜管主导）
```

#### 步骤3：Suno音乐生成
使用Suno生成纯音乐：
- 输入：音乐风格描述
- 输出：纯音乐文件

#### 步骤4：音频导出
导出音频文件，确保：
- 格式：16kHz单声道wav
- 时长：5秒/幕
- 声道：单声道
- 采样率：16kHz

### 2.2 音频匹配规则

#### 语音类型匹配

| 幕次 | 语音类型 | 语速 | 语气 |
|-----|---------|------|------|
| 第一幕 | 导购员语音 | 偏缓 | 略带悬念 |
| 第二幕 | 导购员语音 | 轻柔 | 带共情 |
| 第三幕 | 导购员语音 | 平稳 | 从容 |
| 第四幕 | 导购员语音 | 偏慢 | 带哀伤 |
| 第五幕 | 导购员语音 | 沉稳 | 威严 |

#### 音乐风格匹配

| 情绪 | 音乐风格 | 节奏 |
|-----|---------|------|
| 热情、神秘 | 史诗管弦乐（低沉鼓点） | 中等 |
| 专业、详细 | 钢琴独奏（舒缓低沉） | 缓慢 |
| 专注、生动 | 小提琴+大提琴二重奏（旋律多变） | 多变 |
| 悲伤、悠远 | 女声吟唱+弦乐（音量由强渐弱） | 渐变 |
| 威严、权力 | 史诗管弦乐（铜管主导） | 强烈 |

#### 音频对齐规则
- 语音节奏与唇形同步
- 动作节奏与音乐/语音同步
- 音频时长严格对齐（5秒/幕）

---

## 3. AI绘画集成

### 3.1 绘画生成流程

#### 步骤1：提取视觉元素
从五幕提示词中提取视觉元素：
- 角色固定特征
- 场景环境
- 光影描述

#### 步骤2：生成「动作前画面」
使用AI绘画生成「动作前画面」：
- 输入：角色固定特征 + 场景环境 + 光影描述
- 输出：角色参考图

#### 步骤3：参考图裁剪
裁剪参考图，确保：
- 比例：9:16竖版
- 分辨率：≥1080×1920
- 内容：角色完整特征（无遮挡）

### 3.2 参考图要求

**视觉要求**：
- 角色完整特征（脸型、发型、服饰、气质）
- 无遮挡（确保角色特征清晰）
- 光影匹配（与提示词光影描述一致）

**技术要求**：
- 比例：9:16竖版
- 分辨率：≥1080×1920
- 格式：JPG或PNG

---

## 4. InfiniteTalk推理对接

### 4.1 模型加载

**基础配置**：
```python
from infinitetalk import InfiniteTalkPipeline

pipe = InfiniteTalkPipeline.from_pretrained(
    "./weights/Wan2.1-I2V-14B-480P",
    audio_encoder_path="./weights/chinese-wav2vec2-base",
    infinitetalk_weights="./weights/InfiniteTalk",
    torch_dtype=torch.float16,
    use_teacache=True,  # 启用显存优化
    load_in_8bit=True   # int8量化
)
```

### 4.2 单幕生成

**输入参数**：
```python
inputs = {
    "init_image": "./reference/act1_before.jpg",  # AI绘画生成的动作前画面
    "audio": "./audio/act1_audio.wav",            # Suno音乐+导购员语音合成音频
    "prompt": prompt,                             # 生成的提示词
    "duration": 5,                                # 5秒视频
    "aspect_ratio": "9:16",
    "motion_strength": 0.8,                       # 动作强度（保证连贯）
    "face_consistency": True                      # 启用面部一致性管控
}
```

**生成视频**：
```python
video = pipe(**inputs)
video.save("./output/act1_video.mp4")
```

### 4.3 五幕拼接

**拼接流程**：
1. 单幕生成5幕视频（act1_video.mp4 ~ act5_video.mp4）
2. 使用FFmpeg拼接5幕视频
3. 总时长：25秒（5幕×5秒）

**拼接命令**：
```bash
ffmpeg -f concat -i filelist.txt -c copy output_video.mp4
```

**filelist.txt格式**：
```
file './output/act1_video.mp4'
file './output/act2_video.mp4'
file './output/act3_video.mp4'
file './output/act4_video.mp4'
file './output/act5_video.mp4'
```

---

## 5. 跨工具数据流

### 5.1 数据流图

```
提示词生成师
    ↓ (提示词文本)
Suno音乐生成
    ↓ (16kHz单声道wav音频)
chinese-wav2vec2-base编码
    ↓ (音频特征)
AI绘画生成
    ↓ (9:16参考图)
InfiniteTalk推理
    ↓ (5秒/幕视频)
FFmpeg拼接
    ↓ (25秒完整视频)
```

### 5.2 数据格式规范

| 数据类型 | 格式 | 分辨率/采样率 | 时长 |
|---------|------|-------------|------|
| 提示词文本 | 文本 | - | - |
| Suno音频 | 16kHz单声道wav | 16kHz | 5秒/幕 |
| 音频特征 | 编码文件 | - | - |
| 参考图 | JPG/PNG | ≥1080×1920 | - |
| 单幕视频 | MP4 | 1080×1920 | 5秒 |
| 完整视频 | MP4 | 1080×1920 | 25秒 |

---

## 6. 推理脚本调用示例

### 6.1 完整推理脚本

```python
import torch
from infinitetalk import InfiniteTalkPipeline

# 1. 加载模型（基础配置）
pipe = InfiniteTalkPipeline.from_pretrained(
    "./weights/Wan2.1-I2V-14B-480P",
    audio_encoder_path="./weights/chinese-wav2vec2-base",
    infinitetalk_weights="./weights/InfiniteTalk",
    torch_dtype=torch.float16,
    use_teacache=True,  # 启用显存优化
    load_in_8bit=True   # int8量化
)

# 2. 单幕生成（以第一幕为例）
prompt = """
主体：25岁女性数字人，鹅蛋脸、杏眼微凝、浅棕色齐肩卷发，浅灰修身西装套裙+白衬衫+米色细跟鞋，银色简约项链；
动作时序（5s）：0-1s双手轻握平板置于腰侧，1-3s缓慢抬手将平板举至胸前（速度均匀、姿态挺拔），3-5s保持举平板姿势，头部微抬看向镜头方向；
场景：现代商务会议室，背景模糊大屏投影，前景简约文件；
光影：冷调柔光，侧光勾勒身形，明暗对比明显；
氛围：神秘宏大，面部表情微凝（无夸张），身体无多余晃动。
"""

# 输入参数
inputs = {
    "init_image": "./reference/act1_before.jpg",  # AI绘画生成的动作前画面
    "audio": "./audio/act1_audio.wav",            # Suno音乐+导购员语音合成音频
    "prompt": prompt,
    "duration": 5,                                # 5秒视频
    "aspect_ratio": "9:16",
    "motion_strength": 0.8,                       # 动作强度（保证连贯）
    "face_consistency": True                      # 启用面部一致性管控
}

# 生成视频
video = pipe(**inputs)

# 保存视频
video.save("./output/act1_video.mp4")

print("第一幕视频生成完成！")
```

### 6.2 五幕生成循环

```python
# 生成五幕视频
for act_num in range(1, 6):
    # 读取提示词
    with open(f"./prompts/act{act_num}_prompt.txt", "r", encoding="utf-8") as f:
        prompt = f.read()

    # 输入参数
    inputs = {
        "init_image": f"./reference/act{act_num}_before.jpg",
        "audio": f"./audio/act{act_num}_audio.wav",
        "prompt": prompt,
        "duration": 5,
        "aspect_ratio": "9:16",
        "motion_strength": 0.8,
        "face_consistency": True
    }

    # 生成视频
    video = pipe(**inputs)
    video.save(f"./output/act{act_num}_video.mp4")

    print(f"第{act_num}幕视频生成完成！")

print("五幕视频生成完成！")
```

### 6.3 FFmpeg拼接脚本

```python
import subprocess

# 创建filelist.txt
with open("./filelist.txt", "w", encoding="utf-8") as f:
    for act_num in range(1, 6):
        f.write(f"file './output/act{act_num}_video.mp4'\n")

# 拼接视频
subprocess.run([
    "ffmpeg",
    "-f", "concat",
    "-i", "./filelist.txt",
    "-c", "copy",
    "./output/output_video.mp4"
])

print("完整视频拼接完成！总时长25秒。")
```

---

## 附录：跨工具集成速查表

| 工具 | 输入 | 输出 | 格式 |
|-----|------|------|------|
| Suno音乐 | 音乐风格描述 | 纯音乐 | 16kHz单声道wav |
| chinese-wav2vec2-base | 16kHz单声道wav | 音频特征 | 编码文件 |
| AI绘画 | 角色固定特征+场景环境+光影 | 参考图 | 9:16、≥1080×1920 |
| InfiniteTalk | 参考图+音频特征+提示词 | 单幕视频 | 1080×1920、5秒 |
| FFmpeg | 5幕视频 | 完整视频 | 1080×1920、25秒 |

---

## 注意事项

1. **音频格式严格**：16kHz单声道wav，适配chinese-wav2vec2-base编码
2. **参考图无遮挡**：角色完整特征清晰可见
3. **音频严格对齐**：语音节奏与唇形同步，动作节奏与音乐/语音同步
4. **技术参数匹配**：duration=5、aspect_ratio="9:16"、motion_strength=0.8、face_consistency=True
5. **拼接顺序正确**：act1→act2→act3→act4→act5
6. **总时长准确**：25秒（5幕×5秒）
