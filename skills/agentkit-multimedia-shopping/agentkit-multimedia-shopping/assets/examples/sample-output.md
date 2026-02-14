# 示例输出

## 概览
本文档提供agentkit-multimedia-shopping Skill的示例输出。

---

## 示例1：生成完整带货视频

### 输入参数
- **角色固定特征**：小省导购员（严格遵循character-profile.md）
- **场景类型**：商务会议室
- **情绪基调**：热情专业
- **话术内容**："宝子们，今天给你们推荐一款超值商品，性价比超高，闭眼冲不亏！"

### 执行步骤

#### 1. 生成角色形象
```bash
python scripts/generate_character.py \
  --prompt "25岁左右女性数字人，鹅蛋脸、杏眼带笑、浅棕色齐肩卷发，肤色白皙，唇色淡粉，身穿浅灰色修身西装套裙，内搭白色衬衫，脚踩米色细跟鞋，佩戴银色简约项链，气质专业又亲和，手部姿态优雅自然。现代商务场景，背景简约，前景清晰。9:16竖屏，高清晰度，商业化带货风格。" \
  --aspect-ratio "9:16" \
  --resolution "1080x1920" \
  --output "./output/character_reference.jpg"
```

**输出**：`./output/character_reference.jpg`

#### 2. 生成场景背景
```bash
python scripts/generate_scene.py \
  --prompt "现代商务会议室，背景模糊大屏投影，前景简约文件，暖调柔光，侧光照明，明暗对比明显，商业化带货风格，9:16竖屏，高清晰度。" \
  --aspect-ratio "9:16" \
  --resolution "1080x1920" \
  --output "./output/scene_reference.jpg"
```

**输出**：`./output/scene_reference.jpg`

#### 3. 合成导购员语音
```bash
python scripts/generate_voice.py \
  --text "宝子们，今天给你们推荐一款超值商品，性价比超高，闭眼冲不亏！" \
  --voice-type "friendly" \
  --emotion "enthusiastic" \
  --format "16khz_mono_wav" \
  --output "./output/voice.wav"
```

**输出**：`./output/voice.wav`

#### 4. 生成背景音乐
```bash
python scripts/generate_music.py \
  --style "piano" \
  --emotion "enthusiastic" \
  --duration 5 \
  --format "16khz_mono_wav" \
  --output "./output/music.wav"
```

**输出**：`./output/music.wav`

#### 5. 生成视频
```bash
python scripts/generate_video.py \
  --character-image "./output/character_reference.jpg" \
  --scene-image "./output/scene_reference.jpg" \
  --voice-file "./output/voice.wav" \
  --music-file "./output/music.wav" \
  --prompt "主体：25岁女性数字人，鹅蛋脸、杏眼带笑、浅棕色齐肩卷发，浅灰修身西装套裙+白衬衫+米色细跟鞋，银色简约项链；动作时序（5s）：0-1s双手轻握平板置于腰侧，1-3s缓慢抬手将平板举至胸前（速度均匀、姿态挺拔），3-5s保持举平板姿势，头部微抬看向镜头方向；场景：现代商务会议室，背景模糊大屏投影，前景简约文件；光影：暖调柔光，侧光勾勒身形，明暗对比明显；氛围：热情专业，面部表情带笑（无夸张），身体无多余晃动。音频类型：导购员语音（语速适中、语气热情）+ 轻快背景音乐（钢琴旋律）；音频对齐：抬手动作匹配音乐节奏，语音节奏与唇形同步，无肢体动作与音频断层。技术约束：9:16竖版构图，中景固定镜头，背景虚化程度≥70%，动作强度0.8，面部一致性启用。" \
  --duration 5 \
  --aspect-ratio "9:16" \
  --output "./output/video.mp4"
```

**输出**：`./output/video.mp4`

### 最终输出
- **角色参考图**：`./output/character_reference.jpg`（9:16竖屏，1080×1920）
- **场景参考图**：`./output/scene_reference.jpg`（9:16竖屏，1080×1920）
- **语音文件**：`./output/voice.wav`（16kHz单声道wav）
- **音乐文件**：`./output/music.wav`（16kHz单声道wav）
- **视频文件**：`./output/video.mp4`（9:16竖屏，5秒）

---

## 示例2：仅生成角色参考图

### 输入参数
- **角色固定特征**：小省导购员（严格遵循character-profile.md）
- **情绪基调**：热情专业

### 执行步骤
```bash
python scripts/generate_character.py \
  --prompt "25岁左右女性数字人，鹅蛋脸、杏眼带笑、浅棕色齐肩卷发，肤色白皙，唇色淡粉，身穿浅灰色修身西装套裙，内搭白色衬衫，脚踩米色细跟鞋，佩戴银色简约项链，气质专业又亲和，手部姿态优雅自然。现代商务场景，背景简约，前景清晰。9:16竖屏，高清晰度，商业化带货风格。" \
  --aspect-ratio "9:16" \
  --resolution "1080x1920" \
  --output "./output/character_reference.jpg"
```

### 输出
- **角色参考图**：`./output/character_reference.jpg`（9:16竖屏，1080×1920）

---

## 示例3：仅生成语音

### 输入参数
- **话术内容**："宝子们，今天给你们推荐一款超值商品，性价比超高，闭眼冲不亏！"
- **语音类型**：亲切
- **情绪基调**：热情

### 执行步骤
```bash
python scripts/generate_voice.py \
  --text "宝子们，今天给你们推荐一款超值商品，性价比超高，闭眼冲不亏！" \
  --voice-type "friendly" \
  --emotion "enthusiastic" \
  --format "16khz_mono_wav" \
  --output "./output/voice.wav"
```

### 输出
- **语音文件**：`./output/voice.wav`（16kHz单声道wav）

---

## 注意事项

1. **提示词质量**：提示词质量直接影响生成效果，建议严格遵循模板
2. **参数格式**：严格按照参数格式要求输入
3. **文件路径**：确保所有文件路径正确且可访问
4. **分辨率匹配**：图像必须为9:16竖屏，分辨率≥1080×1920
5. **音频格式**：音频必须为16kHz单声道wav格式
6. **工作流顺序**：严格按照图像→音频→视频的顺序生成

---

## 与InfiniteTalk的协同

本Skill与`infinitetalk-shopping-avatar` Skill协同工作：

1. **本Skill**：生成角色参考图、场景参考图、语音文件、音乐文件
2. **infinitetalk-shopping-avatar Skill**：生成InfiniteTalk专用提示词
3. **InfiniteTalk**：使用多模态内容和提示词生成视频

协同流程示例：
```
# 步骤1：本Skill生成角色参考图
python scripts/generate_character.py --prompt "..." --output "./output/character_reference.jpg"

# 步骤2：本Skill生成场景参考图
python scripts/generate_scene.py --prompt "..." --output "./output/scene_reference.jpg"

# 步骤3：本Skill合成语音
python scripts/generate_voice.py --text "..." --output "./output/voice.wav"

# 步骤4：本Skill生成音乐
python scripts/generate_music.py --style "piano" --output "./output/music.wav"

# 步骤5：使用infinitetalk-shopping-avatar Skill生成提示词
# （调用infinitetalk-shopping-avatar Skill的提示词生成功能）

# 步骤6：本Skill生成视频（结合InfiniteTalk提示词）
python scripts/generate_video.py \
  --character-image "./output/character_reference.jpg" \
  --scene-image "./output/scene_reference.jpg" \
  --voice-file "./output/voice.wav" \
  --music-file "./output/music.wav" \
  --prompt "InfiniteTalk专用提示词..." \
  --output "./output/video.mp4"
```
