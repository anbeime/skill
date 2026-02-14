# 情感标注和适配指南

## 概览
本文档说明如何在语音合成中进行情感标注和适配，以及如何根据文本情绪自动调整语音参数。

## 支持的情感类型

### 基础情感
1. **中性（neutral）**
   - 特征：语调平稳，语速正常，无特殊情绪
   - 应用：新闻播报、知识讲解
   - 参数：speed=1.0, pitch=1.0, volume=1.0

2. **高兴（happy）**
   - 特征：语调上扬，语速略快，声音明亮
   - 应用：庆祝、问候、积极内容
   - 参数：speed=1.1-1.2, pitch=1.1-1.2, volume=1.1

3. **悲伤（sad）**
   - 特征：语调低沉，语速放慢，声音轻柔
   - 应用：安慰、遗憾、沉重内容
   - 参数：speed=0.8-0.9, pitch=0.8-0.9, volume=0.8-0.9

4. **愤怒（angry）**
   - 特征：语调尖锐，语速加快，音量增大
   - 应用：强调、警告、激烈辩论
   - 参数：speed=1.2-1.3, pitch=1.2-1.3, volume=1.2-1.3

### 进阶情感
5. **兴奋（excited）**
   - 特征：语调大幅波动，语速快，音量较大
   - 应用：惊喜、激动、欢呼
   - 参数：speed=1.3-1.5, pitch=1.2-1.4, volume=1.2-1.4

6. **平静（calm）**
   - 特征：语调柔和，语速适中，节奏平稳
   - 应用：催眠、放松、冥想
   - 参数：speed=0.9-1.0, pitch=0.95-1.05, volume=0.9-1.0

7. **疑惑（curious）**
   - 特征：语调末尾上扬，语速稍慢
   - 应用：提问、探索、思考
   - 参数：speed=0.95, pitch=1.05（末尾）, volume=1.0

8. **严肃（serious）**
   - 特征：语调平稳有力，语速正常，音量适中
   - 应用：警告、重要声明、正式场合
   - 参数：speed=1.0, pitch=1.0, volume=1.0

## 文本情绪分析

### 自动情绪识别
智能体将自动分析文本中的情绪特征：

1. **关键词识别**
   - 高兴词：开心、太棒了、真棒、高兴
   - 悲伤词：遗憾、难过、痛苦、可惜
   - 愤怒词：气死、烦人、讨厌、可恶
   - 疑惑词：为什么、怎么办、真的吗

2. **语气词识别**
   - 感叹号（!）：强烈情绪
   - 问号（?）：疑惑或惊讶
   - 省略号（...）：迟疑或沉重

3. **语义分析**
   - 整体情感倾向
   - 情感强度等级
   - 情感转换点

### 情感标注格式
在脚本中使用情感参数：

```bash
python scripts/tts_generate.py \
  --text "今天真是太开心了！" \
  --emotion happy \
  --emotion_strength 0.8 \
  --speed 1.2 \
  --pitch 1.1
```

## 情感适配参数

### 语速调整（speed）
- 范围：0.5 - 2.0
- 0.5-0.7：非常慢（悲伤、沉重）
- 0.8-0.9：较慢（平静、舒缓）
- 1.0：正常（中性、严肃）
- 1.1-1.2：较快（高兴、活跃）
- 1.3-2.0：很快（兴奋、激动）

### 音调调整（pitch）
- 范围：0.5 - 2.0
- 0.5-0.7：很低（悲伤、沉重）
- 0.8-0.9：较低（平静、严肃）
- 1.0：正常（中性）
- 1.1-1.2：较高（高兴、疑惑）
- 1.3-2.0：很高（兴奋、愤怒）

### 音量调整（volume）
- 范围：0.5 - 1.5
- 0.5-0.7：很小（悲伤、轻柔）
- 0.8-0.9：较小（平静）
- 1.0：正常（中性）
- 1.1-1.3：较大（高兴、强调）
- 1.4-1.5：很大（愤怒、激动）

## 情感适配工作流

### 步骤 1：文本分析
```python
# 智能体自动分析文本情绪
text = "今天真是太开心了！"
emotion_analysis = {
    "primary_emotion": "happy",
    "emotion_strength": 0.8,
    "suggested_params": {
        "speed": 1.2,
        "pitch": 1.1,
        "volume": 1.1
    }
}
```

### 步骤 2：参数确定
```bash
# 根据情感分析结果确定参数
emotion=happy
emotion_strength=0.8
speed=1.2
pitch=1.1
volume=1.1
```

### 步骤 3：语音生成
```bash
python scripts/tts_generate.py \
  --text "今天真是太开心了！" \
  --emotion happy \
  --speed 1.2 \
  --pitch 1.1 \
  --volume 1.1
```

### 步骤 4：效果验证
- 听取生成的音频
- 评估情感表达是否准确
- 必要时调整参数重新生成

## 情感转换示例

### 场景一：故事讲述
```bash
# 开头（平静）
python scripts/tts_generate.py \
  --text "很久很久以前，有一个小村庄" \
  --emotion calm \
  --output ./output/story_01.wav

# 高潮（兴奋）
python scripts/tts_generate.py \
  --text "突然，一道光芒划破长空！" \
  --emotion excited \
  --speed 1.4 \
  --pitch 1.2 \
  --output ./output/story_02.wav

# 结尾（平静）
python scripts/tts_generate.py \
  --text "从此，村庄恢复了宁静" \
  --emotion calm \
  --output ./output/story_03.wav
```

### 场景二：客服对话
```bash
# 问候（高兴）
python scripts/tts_generate.py \
  --text "您好！很高兴为您服务" \
  --emotion happy \
  --output ./output/greeting.wav

-- 询问（疑惑）
python scripts/tts_generate.py \
  --text "请问有什么可以帮您的吗？" \
  --emotion curious \
  --output ./output/ask.wav

# 解决问题（平静）
python scripts/tts_generate.py \
  --text "好的，我马上为您处理" \
  --emotion calm \
  --output ./output/solve.wav
```

## 高级情感适配

### 混合情感
一段文本可能包含多种情感：

```bash
# 文本分段处理
python scripts/tts_generate.py \
  --text_file ./mixed_emotion.txt \
  --emotion_per_sentence true \
  --output ./output/mixed.wav
```

### 情感渐变
实现情感之间的平滑过渡：

```bash
python scripts/tts_generate.py \
  --text "刚开始我很担心，但后来看到结果，我就放心了" \
  --emotion_transition \
  --emotion_start worried \
  --emotion_end relieved \
  --output ./output/transition.wav
```

### 情感强度调整
根据情感强度微调参数：

```bash
python scripts/tts_generate.py \
  --text "太棒了！" \
  --emotion happy \
  --emotion_strength 1.0 \
  --speed 1.3 \
  --pitch 1.2 \
  --output ./output/strong_happy.wav
```

## 情感映射表

| 情感 | 关键词示例 | speed | pitch | volume |
|------|------------|-------|-------|--------|
| neutral | 正常、可以、好的 | 1.0 | 1.0 | 1.0 |
| happy | 开心、高兴、太棒了 | 1.2 | 1.1 | 1.1 |
| sad | 遗憾、难过、可惜 | 0.85 | 0.85 | 0.85 |
| angry | 气死、讨厌、烦人 | 1.25 | 1.25 | 1.25 |
| excited | 激动、太兴奋了 | 1.4 | 1.3 | 1.3 |
| calm | 平静、放松 | 0.95 | 1.0 | 0.95 |
| curious | 为什么、怎么办 | 0.95 | 1.05 | 1.0 |
| serious | 重要、注意 | 1.0 | 1.0 | 1.0 |

## 注意事项

1. **情感标注准确性**
   - 依赖智能体的文本分析能力
   - 复杂情感可能需要人工标注
   - 建议先试听再批量生成

2. **参数调整**
   - 不同模型对参数敏感度不同
   - 建议在小范围内微调
   - 避免极端参数值

3. **文本分段**
   - 情感转换处建议分段
   - 每段建议 10-50 字
   - 避免过长段落

4. **音色配合**
   - 不同音色适合不同情感
   - 女声适合高兴、悲伤
   - 男声适合严肃、愤怒

## 常见问题

### 问题 1：情感表达不明显
- 解决：增大 emotion_strength
- 解决：调整 speed、pitch、volume 参数

### 问题 2：情感转换生硬
- 解决：增加情感转换的分段数
- 解决：使用 emotion_transition 功能

### 问题 3：情感与文本不符
- 解决：人工复核情感标注
- 解决：调整情感映射规则
