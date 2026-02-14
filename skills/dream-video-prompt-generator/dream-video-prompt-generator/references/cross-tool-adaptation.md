# 跨工具适配指南

## 目录
- [1. 概述](#1-概述)
- [2. 目标工具支持](#2-目标工具支持)
- [3. 适配策略](#3-适配策略)
- [4. 工具适配方案](#4-工具适配方案)
- [5. 质量保障](#5-质量保障)

## 1. 概述

### 目的
将标准化五幕提示词适配到多种AI工具（即梦、Suno、AI绘画等），确保跨工具输出质量和一致性。

### 核心原则
1. **保持一致性**：人物、视觉、情绪保持统一
2. **工具特性适配**：根据工具特性调整提示词格式和参数
3. **语言本地化**：中英文版本语义一致
4. **输出质量保障**：确保跨工具输出质量符合商业带货标准

### 适用范围
- 即梦视频生成
- Suno音乐生成
- AI绘画生成（Midjourney、Stable Diffusion等）
- 其他AI视频工具

---

## 2. 目标工具支持

### 2.1 即梦视频生成

**工具特性**：
- 中文提示词支持优秀
- 9:16竖屏支持良好
- 视频时长：3-15秒/分镜
- 强调主体、场景、动作描述

**适配要点**：
- 使用中文提示词
- 强调"9:16竖版"构图
- 每个分镜5秒时长
- 明确镜头语言和光影

### 2.2 Suno音乐生成

**工具特性**：
- 中英文提示词均支持
- 音乐风格定义灵活
- 情绪和氛围描述重要
- 歌词生成能力强

**适配要点**：
- 提取五幕情绪递进
- 提取核心关键词（热情、专业、紧迫等）
- 定义音乐风格（商业化带货风）
- 生成BGM或广告配乐

### 2.3 AI绘画生成

**工具特性**：
- 英文提示词支持更优
- 强调画面细节描述
- 支持风格标签
- 支持画面比例参数

**适配要点**：
- 使用英文提示词
- 提取视觉元素（服饰、场景、光影）
- 添加风格标签（commercial、professional、friendly）
- 明确画面比例（--ar 9:16）

---

## 3. 适配策略

### 3.1 信息提取策略

#### 提取维度
1. **人物信息**：外貌、服饰、气质
2. **场景信息**：背景、前景、道具
3. **情绪信息**：每幕的情绪基调
4. **视觉信息**：镜头语言、光影、氛围

#### 提取规则
- **人物信息**：严格使用固定角色描述，确保一致性
- **场景信息**：提取关键场景元素，保持视觉连贯
- **情绪信息**：提取情绪关键词，用于音乐和氛围生成
- **视觉信息**：提取镜头语言和光影，用于视频生成

### 3.2 信息转换策略

#### 转换规则
1. **即梦视频**：直接使用中文提示词，添加时长参数
2. **Suno音乐**：提取情绪关键词，生成音乐风格描述
3. **AI绘画**：提取视觉元素，转换为英文提示词

#### 转换示例

**原始提示词（中文）**：
```
主体：25岁左右女性数字人，鹅蛋脸、杏眼带笑、浅棕色齐肩卷发，
身穿浅灰色修身西装套裙，内搭白色衬衫，脚踩米色细跟鞋，佩戴银色简约项链，
气质专业又亲和，手部姿态优雅自然。
运动：缓慢抬手指向右侧，姿态挺拔。
场景：现代商务场景，背景是产品展示架，前景摆简约文件。
镜头语言：中景固定镜头，背景虚化，顺光拍摄。
光影：暖调柔光，明亮清晰。
氛围：热情专业，吸引注意力。
```

**即梦视频转换（中文）**：
```
25岁左右女性数字人，鹅蛋脸、杏眼带笑、浅棕色齐肩卷发，肤色白皙，唇色淡粉，
身穿浅灰色修身西装套裙，内搭白色衬衫，脚踩米色细跟鞋，佩戴银色简约项链，
气质专业又亲和，手部姿态优雅自然。
缓慢抬手指向右侧，姿态挺拔。
现代商务场景，背景是产品展示架，前景摆简约文件。
中景固定镜头，背景虚化，顺光拍摄。
暖调柔光，明亮清晰。
热情专业，吸引注意力。
9:16竖版，5秒时长。
```

**Suno音乐转换（情绪提取）**：
```
音乐风格：商业化带货风，轻快专业
情绪：热情、专业、吸引注意力
节奏：中等速度，明亮清晰
配器：电子钢琴、轻快鼓点
建议时长：25秒（5幕×5秒）
```

**AI绘画转换（英文）**：
```
25-year-old female digital human, oval face, almond eyes with smile,
light brown shoulder-length curly hair, fair skin, light pink lips,
wearing light gray tailored suit skirt, white shirt, beige pumps,
simple silver necklace, professional and friendly temperament,
elegant hand gestures.
Slowly raising hand pointing to right, upright posture.
Modern business setting, product display shelf in background,
simple documents in foreground.
Medium fixed shot, bokeh background, front light.
Warm soft light, bright and clear.
Enthusiastic and professional, attention-grabbing.
Commercial style, professional, friendly, 9:16 aspect ratio.
```

---

## 4. 工具适配方案

### 4.1 即梦视频适配

#### 适配要点
1. **使用中文提示词**
2. **添加时长参数**：每个分镜5秒
3. **明确构图比例**：9:16竖版
4. **保持五幕一致性**

#### 完整适配模板（中文）

**第一幕提示词**：
```
主体：25岁左右女性数字人，鹅蛋脸、杏眼带笑、浅棕色齐肩卷发，肤色白皙，唇色淡粉，
身穿浅灰色修身西装套裙，内搭白色衬衫，脚踩米色细跟鞋，佩戴银色简约项链，
气质专业又亲和，手部姿态优雅自然。
运动：缓慢抬手指向右侧，姿态挺拔。
场景：现代商务场景，背景是产品展示架，前景摆简约文件。
镜头语言：中景固定镜头，背景虚化，顺光拍摄。
光影：暖调柔光，明亮清晰。
氛围：热情专业，吸引注意力。
9:16竖版，5秒时长。
```

**参数设置**：
- 视频比例：9:16
- 单个时长：5秒
- 总时长：25秒（5幕）
- 分辨率：1080x1920
- 帧率：30fps

### 4.2 Suno音乐适配

#### 适配要点
1. **提取情绪关键词**
2. **定义音乐风格**
3. **设定节奏和配器**
4. **匹配视频时长**

#### 完整适配模板

**风格描述**：
```
[音乐风格]商业化带货风，轻快专业
[情绪]热情、专业、吸引注意力
[节奏]中等速度，明亮清晰
[配器]电子钢琴、轻快鼓点
[时长]25秒
[结构]前奏（3秒）+ 主歌（19秒）+ 结尾（3秒）
```

**歌词参考**（可选）：
```
宝子们，今天给你们推荐一款超值商品，
性价比超高，闭眼冲不亏！
专业导购，贴心服务，
小省导购员，帮你省更多！
```

### 4.3 AI绘画适配

#### 适配要点
1. **转换为英文提示词**
2. **提取视觉元素**
3. **添加风格标签**
4. **设置画面比例**

#### 完整适配模板（英文）

**提示词**：
```
25-year-old female digital human, oval face, almond eyes with smile,
light brown shoulder-length curly hair, fair skin, light pink lips,
wearing light gray tailored suit skirt, white shirt, beige pumps,
simple silver necklace, professional and friendly temperament,
elegant hand gestures.
Slowly raising hand pointing to right, upright posture.
Modern business setting, product display shelf in background,
simple documents in foreground.
Medium fixed shot, bokeh background, front light.
Warm soft light, bright and clear.
Enthusiastic and professional, attention-grabbing.
Commercial style, professional, friendly, high quality, 9:16 aspect ratio.
```

**参数设置**：
- 画面比例：--ar 9:16
- 风格：--style raw
- 质量：--q 2
- 版本：--v 6.0

---

## 5. 质量保障

### 5.1 一致性保障

#### 人物一致性检查
- [ ] 角色描述完全一致（所有工具）
- [ ] 外貌特征无差异（所有工具）
- [ ] 服饰描述统一（所有工具）
- [ ] 气质描述统一（所有工具）

#### 视觉连贯性检查
- [ ] 色调统一（所有工具）
- [ ] 场景元素一致（所有工具）
- [ ] 构图比例一致（9:16）
- [ ] 镜头语言统一

#### 情绪连贯性检查
- [ ] 情绪递进自然（视频、音乐）
- [ ] 情绪适配光影（视频、绘画）
- [ ] 音乐风格适配情绪（Suno）

### 5.2 输出质量检查

#### 即梦视频质量检查
- [ ] 视频清晰度高
- [ ] 人物一致性强
- [ ] 运动流畅自然
- [ ] 光影效果良好

#### Suno音乐质量检查
- [ ] 音乐风格商业化
- [ ] 节奏适配带货
- [ ] 情绪表达准确
- [ ] 音质清晰

#### AI绘画质量检查
- [ ] 人物形象准确
- [ ] 场景细节丰富
- [ ] 光影效果真实
- [ ] 画面比例正确

### 5.3 质量报告格式

```json
{
  "tool": "即梦/Suno/AI绘画",
  "quality_check": "pass/fail",
  "consistency_check": {
    "character_consistency": "pass/fail",
    "visual_coherence": "pass/fail",
    "emotion_progression": "pass/fail"
  },
  "output_quality": {
    "clarity": "pass/fail",
    "consistency": "pass/fail",
    "details": "pass/fail",
    "style": "pass/fail"
  },
  "issues": [
    {
      "type": "人物不一致/视觉不连贯/质量不达标",
      "description": "具体问题描述",
      "suggestion": "修改建议"
    }
  ],
  "adjustment_needed": "true/false"
}
```

---

## 附录：跨工具适配速查表

| 工具 | 语言 | 主要参数 | 关键字段 | 检查项 |
|-----|------|---------|---------|--------|
| 即梦视频 | 中文 | 9:16, 5秒/幕 | 主体、运动、场景、镜头语言、光影、氛围 | 人物一致、视觉连贯、情绪递进 |
| Suno音乐 | 中英文 | 25秒, 商业化 | 音乐风格、情绪、节奏、配器 | 风格适配、情绪准确、节奏适中 |
| AI绘画 | 英文 | 9:16, --ar | 角色描述、场景、光影、风格标签 | 人物准确、场景丰富、光影真实 |

---

## 注意事项

1. **严格遵循固定描述**：小省导购员角色描述严禁修改
2. **工具特性适配**：根据工具特性调整提示词格式
3. **中英文对应**：中英文版本语义一致
4. **质量优先**：优先保障输出质量，而非盲目适配
5. **及时反馈**：发现质量问题及时反馈调整
6. **避免过度适配**：保持核心信息，避免信息过载
