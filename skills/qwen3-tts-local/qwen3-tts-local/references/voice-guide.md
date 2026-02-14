# 音色参数指南

## 中文音色

### 女性音色

| 音色名称 | 年龄 | 风格 | 适用场景 | 情感特点 |
|---------|------|------|---------|---------|
| zh-CN-XiaoxiaoNeural | 年轻 | 活泼明亮 | 广告、短视频 | 愉悦、亲切 |
| zh-CN-XiaohanNeural | 成年 | 知性优雅 | 新闻播报、商务 | 专业、稳重 |
| zh-CN-XiaomengNeural | 成年 | 温柔柔和 | 有声书、儿童故事 | 温馨、亲切 |
| zh-CN-XiaoyiNeural | 年轻 | 清亮悦耳 | 客服、咨询 | 友好、耐心 |
| zh-CN-XiaoxuanNeural | 年轻 | 活泼可爱 | 游戏、娱乐 | 开朗、活泼 |

### 男性音色

| 音色名称 | 年龄 | 风格 | 适用场景 | 情感特点 |
|---------|------|------|---------|---------|
| zh-CN-YunyangNeural | 中年 | 沉稳大气 | 纪录片、企业宣传 | 严肃、权威 |
| zh-CN-YunjianNeural | 中年 | 深沉厚重 | 电影旁白、有声小说 | 深沉、感性 |
| zh-CN-YunxiNeural | 年轻 | 活泼阳光 | 游戏解说、广告 | 激昂、活力 |
| zh-CN-YunzeNeural | 中年 | 温和亲切 | 教学、培训 | 耐心、友好 |
| zh-CN-YunfengNeural | 成年 | 正式庄重 | 新闻播报、会议 | 正式、严肃 |

## 英语音色

### 美式英语

| 音色名称 | 性别 | 风格 | 适用场景 |
|---------|------|------|---------|
| en-US-JennyNeural | 女 | 自然亲切 | 日常对话、商务 |
| en-US-GuyNeural | 男 | 正式稳重 | 新闻、广播 |
| en-US-AriaNeural | 女 | 温柔柔和 | 儿童故事、教学 |
| en-US-DavisNeural | 男 | 沉稳厚重 | 纪录片、旁白 |

### 英式英语

| 音色名称 | 性别 | 风格 | 适用场景 |
|---------|------|------|---------|
| en-GB-SoniaNeural | 女 | 正式优雅 | 正式场合、文学 |
| en-GB-RyanNeural | 男 | 知性深沉 | 文学朗读、新闻 |
| en-GB-LibbyNeural | 女 | 活泼明亮 | 广告、娱乐 |
| en-GB-ThomasNeural | 男 | 温和亲切 | 教学、咨询 |

## 其他语言

### 日语

| 音色名称 | 性别 | 适用场景 |
|---------|------|---------|
| ja-JP-NanamiNeural | 女 | 动漫、日常对话 |
| ja-JP-KeitaNeural | 男 | 新闻、纪录片 |
| ja-JP-AoiNeural | 女 | 儿童内容、游戏 |
| ja-JP-DaichiNeural | 男 | 企业宣传、广告 |

### 韩语

| 音色名称 | 性别 | 适用场景 |
|---------|------|---------|
| ko-KR-SunHiNeural | 女 | 日常对话、娱乐 |
| ko-KR-InJoonNeural | 男 | 新闻、纪录片 |
| ko-KR-JiMinNeural | 女 | 儿童内容、教学 |
| ko-KR-BongJinNeural | 男 | 企业宣传、广告 |

### 德语

| 音色名称 | 性别 | 适用场景 |
|---------|------|---------|
| de-DE-KatjaNeural | 女 | 新闻、商务 |
| de-DE-ConradNeural | 男 | 纪录片、旁白 |

### 法语

| 音色名称 | 性别 | 适用场景 |
|---------|------|---------|
| fr-FR-DeniseNeural | 女 | 新闻、商务 |
| fr-FR-HenriNeural | 男 | 纪录片、旁白 |

## 语音参数调整

### 语速调整

| 调整范围 | 效果 | 适用场景 |
|---------|------|---------|
| -50% 到 -20% | 缓慢 | 教学、儿童内容 |
| -20% 到 -10% | 稍慢 | 有声书、情感朗读 |
| +0% | 正常 | 大多数场景 |
| +10% 到 +20% | 稍快 | 新闻、广播 |
| +20% 到 +50% | 快速 | 短视频、广告 |

**示例**：
```python
result = generator.generate_speech(
    text="...",
    rate="+20%"  # 快速朗读
)
```

### 音调调整

| 调整范围 | 效果 | 适用场景 |
|---------|------|---------|
| -10Hz 到 -5Hz | 低沉 | 严肃内容、男声 |
| -5Hz 到 0Hz | 稍低 | 沉稳表达 |
| +0Hz | 标准 | 正常语调 |
| 0Hz 到 +5Hz | 稍高 | 活泼内容、女声 |
| +5Hz 到 +10Hz | 高亢 | 儿童内容、游戏 |

**示例**：
```python
result = generator.generate_speech(
    text="...",
    pitch="+5Hz"  # 活泼语调
)
```

### 音量调整

| 调整范围 | 效果 | 适用场景 |
|---------|------|---------|
| -50% 到 -20% | 较小 | 背景音、轻声 |
| -20% 到 -10% | 稍小 | 温柔表达 |
| +0% | 标准 | 正常音量 |
| +10% 到 +20% | 稍大 | 强调、广播 |
| +20% 到 +50% | 较大 | 广告、高呼 |

**示例**：
```python
result = generator.generate_speech(
    text="...",
    volume="+20%"  # 较大音量
)
```

## 情感表达技巧

### 通过音色选择实现情感

| 情感 | 推荐音色 | 参数建议 |
|------|---------|---------|
| 愉悦、活泼 | zh-CN-XiaoxiaoNeural | rate=+10%, pitch=+2Hz |
| 严肃、正式 | zh-CN-YunyangNeural | rate=-10%, pitch=-2Hz |
| 温馨、柔和 | zh-CN-XiaomengNeural | rate=-20%, pitch=+0Hz |
| 激昂、有力 | zh-CN-YunxiNeural | rate=+20%, pitch=+3Hz |
| 悲伤、低沉 | zh-CN-YunjianNeural | rate=-20%, pitch=-3Hz |

### 情感组合

```python
# 愉悦、活泼
result = generator.generate_speech(
    text="今天天气真好！",
    voice="zh-CN-XiaoxiaoNeural",
    rate="+10%",
    pitch="+2Hz",
    volume="+10%"
)

# 严肃、稳重
result = generator.generate_speech(
    text="据气象台预报，今天将有暴雨。",
    voice="zh-CN-YunyangNeural",
    rate="-10%",
    pitch="-2Hz",
    volume="+0%"
)

# 温馨、柔和
result = generator.generate_speech(
    text="很久很久以前，在一个美丽的森林里...",
    voice="zh-CN-XiaomengNeural",
    rate="-20%",
    pitch="+0Hz",
    volume="+0%"
)
```

## 多语言配音

### 同一内容多语言版本

```python
from scripts.tts_generator import LocalTTSGenerator

generator = LocalTTSGenerator()

# 中文版本
result_zh = generator.generate_speech(
    text="欢迎使用语音合成服务",
    voice="zh-CN-XiaoxiaoNeural",
    output_file="welcome_zh.mp3"
)

# 英文版本
result_en = generator.generate_speech(
    text="Welcome to the voice synthesis service",
    voice="en-US-JennyNeural",
    output_file="welcome_en.mp3"
)

# 日语版本
result_ja = generator.generate_speech(
    text="音声合成サービスへようこそ",
    voice="ja-JP-NanamiNeural",
    output_file="welcome_ja.mp3"
)
```

## 最佳实践

1. **选择合适的音色**：
   - 根据内容类型和目标受众选择
   - 测试多个音色，选择最合适的

2. **调整语音参数**：
   - 避免极端参数（超过±50%）
   - 细微调整效果更自然

3. **情感表达**：
   - 通过音色选择实现情感变化
   - 避免过度夸张的参数

4. **多语言配音**：
   - 同一内容使用相同语速和音调
   - 确保各语言版本风格一致
