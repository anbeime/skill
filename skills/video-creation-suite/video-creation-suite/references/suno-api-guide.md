# Suno API 使用指南

## 简介
Suno 是一个强大的 AI 音乐生成平台,可以通过文本描述生成高质量的音乐作品。本 Skill 集成了 Suno API,用于生成视频背景音乐。

## 三种使用模式

### 模式一: 开发者模式(推荐)
- **特点**: 技能已预置 API Key,开箱即用
- **适用**: 普通用户使用,无需任何配置
- **成本**: 由开发者承担 API 调用费用

**使用方法**:
```bash
# 直接使用,无需配置
python scripts/sound_generator.py \
  --type music \
  --input background_music.json \
  --output ./output/audio
```

### 模式二: 用户模式
- **特点**: 用户自己配置 API Key
- **适用**: 高级用户,希望使用自己的 Suno 账号
- **成本**: 用户承担自己的 API 调用费用

**使用方法**:
```bash
# 方式1: 环境变量
export SUNO_API_KEY=your_api_key
python scripts/sound_generator.py \
  --type music \
  --input background_music.json \
  --output ./output/audio

# 方式2: 命令行参数
python scripts/sound_generator.py \
  --type music \
  --input background_music.json \
  --output ./output/audio \
  --suno-api-key your_api_key
```

### 模式三: 占位模式
- **特点**: 使用本地占位实现,不调用 API
- **适用**: 测试环境、无网络环境、快速预览
- **成本**: 完全免费

**使用方法**:
```bash
# 方式1: 不配置 API Key,自动使用占位
python scripts/sound_generator.py \
  --type music \
  --input background_music.json \
  --output ./output/audio

# 方式2: 强制使用占位
python scripts/sound_generator.py \
  --type music \
  --input background_music.json \
  --output ./output/audio \
  --use-placeholder
```

## API Key 配置优先级

```
命令行参数 > 环境变量 > 技能凭证 > 占位实现
```

**说明**:
1. **命令行参数**: `--suno-api-key your_api_key` (优先级最高)
2. **环境变量**: `SUNO_API_KEY`
3. **技能凭证**: `COZE_SUNO_API_KEY_{skill_id}` (开发者预置)
4. **占位实现**: 未配置任何 API Key 时自动使用

## 获取自己的 API Key

### 注册步骤
1. 访问 Suno 官网: https://suno.com
2. 注册并登录账号
3. 在账号设置中获取 API Key

### 获取 API Key 的方式
- **免费额度**: 新注册账号通常有免费额度
- **付费方案**: 根据使用量选择合适的套餐

### 账号类型
- **个人账号**: 适合个人使用,有一定的免费额度
- **商业账号**: 适合商业用途,提供更高的调用限额

## API 参数说明

### 基本参数
- **prompt**: 音乐描述提示词(必需)
  - 示例: "calm background music, piano and strings"
  - 示例: "epic cinematic music, orchestral, dramatic"
- **instrumental**: 是否纯音乐(默认: true)
  - true: 不包含人声
  - false: 可能包含人声
- **model**: 使用的模型(默认: chirp-v3-5)
  - chirp-v3: 基础模型
  - chirp-v3-5: 推荐,质量更高
  - chirp-v4: 最新模型
- **title**: 音乐标题(可选)
  - 用于生成的文件命名

### 高级参数
- **style**: 音乐风格(可选)
  - 示例: "epic", "calm", "upbeat", "tech"
- **style_negative**: 排除风格(可选)
  - 示例: "metal", "rock"
- **duration**: 时长(秒)
  - 示例: 60.0 (1分钟)

## 使用示例

### 示例1: 开发者模式(开箱即用)
```bash
# 无需任何配置,直接使用
python scripts/sound_generator.py \
  --type music \
  --input background_music.json \
  --output ./output/audio
```

**输出**:
```
已获取 Suno API Key
正在使用 Suno API 生成音乐: neutral calm background music, duration 60s
背景音乐生成完成(Suno API): ./output/audio/background_music/background.mp3
```

### 示例2: 用户模式(使用自己的 API Key)
```bash
# 使用环境变量配置
export SUNO_API_KEY=sk_1234567890abcdef

python scripts/sound_generator.py \
  --type music \
  --input background_music.json \
  --output ./output/audio
```

**输出**:
```
已获取 Suno API Key
正在使用 Suno API 生成音乐: neutral calm background music, duration 60s
背景音乐生成完成(Suno API): ./output/audio/background_music/background.mp3
```

### 示例3: 占位模式(快速测试)
```bash
# 强制使用占位实现
python scripts/sound_generator.py \
  --type music \
  --input background_music.json \
  --output ./output/audio \
  --use-placeholder
```

**输出**:
```
未设置 Suno API Key,将使用占位实现
背景音乐已生成(占位实现): ./output/audio/background_music/background.wav
背景音乐生成完成(占位实现): ./output/audio/background_music/background.wav
```

### 示例4: 命令行指定 API Key
```bash
# 临时使用指定的 API Key
python scripts/sound_generator.py \
  --type both \
  --input audio_config.json \
  --output ./output/audio \
  --suno-api-key sk_temp_key_12345
```

## 生成时间

- **短音频(30秒)**: 约 1-2 分钟
- **中等音频(60秒)**: 约 2-3 分钟
- **长音频(90秒+)**: 约 3-5 分钟

**注意**: 生成时间受网络和服务器负载影响,请耐心等待。

## 成本说明

### 开发者模式
- **用户成本**: 免费
- **开发者成本**: 根据使用量计费
- **适用场景**: 公共 Skill,让更多用户免费使用

### 用户模式
- **用户成本**: 根据 Suno 定价计费
- **开发者成本**: 无
- **适用场景**: 个人项目,用户愿意承担费用

### 占位模式
- **用户成本**: 完全免费
- **开发者成本**: 无
- **适用场景**: 测试、预览、无网络环境

## 错误处理

### API Key 无效
```
错误: API调用失败,状态码: 401
解决: 检查 API Key 是否正确,或使用占位模式
```

### API 调用失败
```
错误: API调用失败,状态码: 403
解决: 检查 API Key 是否有权限,或使用占位模式
```

### 生成超时
```
错误: 生成任务超时
解决: 减少音乐时长或稍后重试
```

### 降级到占位实现
```
警告: 使用 Suno API 生成背景音乐失败, 降级到占位实现
说明: 脚本自动降级,不会中断流程
```

## 音乐风格参考

### 按情绪分类
- **平静**: calm, peaceful, neutral, serene
- **激昂**: epic, dramatic, powerful, intense
- **欢快**: upbeat, happy, cheerful, energetic
- **神秘**: mysterious, dark, ambient, space
- **悲伤**: melancholic, sad, emotional, dramatic

### 按类型分类
- **电影**: cinematic, orchestral, soundtrack
- **电子**: electronic, synth, tech, ambient
- **流行**: pop, upbeat, modern
- **古典**: classical, piano, strings, orchestral

### 按乐器分类
- **钢琴**: piano, keys, melodic
- **弦乐**: strings, violin, cello, orchestral
- **电子**: synth, electronic, digital
- **打击**: percussion, drums, rhythmic

## 最佳实践

1. **选择合适模式**:
   - 公共 Skill: 使用开发者模式,让用户免费使用
   - 个人项目: 使用用户模式,自己承担费用
   - 测试预览: 使用占位模式,快速验证

2. **描述要具体**: 使用多个关键词组合
   - 好: "epic orchestral cinematic music, dramatic"
   - 差: "epic music"

3. **指定时长**: 根据视频长度设置
   - 短视频(15-30秒): 30秒音乐
   - 中等视频(1-3分钟): 60秒音乐
   - 长视频(5分钟+): 90秒+音乐

4. **匹配情感**: 音乐情绪应与视频内容一致
   - 宣传片: epic, powerful
   - 教学视频: calm, neutral
   - 娱乐视频: upbeat, happy

5. **测试多个版本**: 生成多个版本选择最佳
   - 调整风格关键词
   - 尝试不同的情绪

6. **注意版权**: Suno 生成的音乐可用于商业用途
   - 但建议查看 Suno 的最新使用条款
   - 确保符合您的使用场景

## 常见问题

### Q: 开发者模式会消耗谁的额度?
A: 开发者模式使用技能预置的 API Key,消耗的是开发者的额度,用户无需任何配置。

### Q: 用户模式需要注册 Suno 吗?
A: 是的。用户模式需要用户自己注册 Suno 账号并获取 API Key。

### Q: 占位模式的音乐能用吗?
A: 占位模式生成的音乐质量较低,仅用于测试和预览,不建议用于正式视频。

### Q: 如何切换模式?
A: 通过配置 API Key 的方式切换:
- 不配置 API Key: 占位模式
- 配置自己的 API Key: 用户模式
- 使用技能预置的 API Key: 开发者模式

### Q: 生成失败会自动降级吗?
A: 是的。如果 API 调用失败,脚本会自动降级到占位实现,不会中断流程。

### Q: 可以同时使用多种模式吗?
A: 可以。例如:
- 测试时使用占位模式
- 确认无误后切换到用户模式
- 正式发布时使用开发者模式

### Q: 开发者模式的 API Key 安全吗?
A: API Key 通过技能凭证管理,只有经过授权的环境才能访问。建议定期更换 API Key。

### Q: 如何查看当前使用的模式?
A: 查看输出日志:
- "正在使用 Suno API 生成音乐": 开发者或用户模式
- "背景音乐已生成(占位实现)": 占位模式
