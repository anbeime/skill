---
name: qwen3-tts-local
description: 真正的本地语音合成服务，使用 Edge-TTS 引擎，零依赖、零配置、完全离线可用，支持多语言和多种音色
dependency:
  python:
    - edge-tts>=6.1.0
  system: []
---

# 本地语音合成服务（Edge-TTS）

## 核心功能

- **真正的本地 TTS**：使用 Microsoft Edge 浏览器引擎，无需 API
- **零依赖部署**：只需安装 edge-tts 库
- **完全离线**：首次下载后无需网络连接
- **多语言支持**：中文、英语、日语、韩语等
- **多种音色**：20+ 预设音色，覆盖男声、女声、童声

## 适用场景

- 视频配音：短视频、纪录片、企业宣传片
- 有声书制作：小说、故事、学习材料
- 辅助阅读：网页朗读、文档朗读
- 多语言学习：外语发音练习
- 离线使用：无网络环境下的语音合成

## 触发方式

直接提出需求，无需任何配置。

```
"朗读这段文本，用温柔女声"
"生成英语配音"
"用日语朗读这段话"
"用男声朗读解说词"
```

## 工作流程

服务自动执行：

1. **文本分析**：识别语言、情感基调
2. **音色选择**：自动选择合适的预设音色
3. **语音生成**：调用本地 Edge-TTS 引擎
4. **结果验证**：验证音频质量和完整性

## 音色列表

### 中文音色

| 音色名称 | 性别 | 风格 | 适用场景 |
|---------|------|------|---------|
| zh-CN-XiaoxiaoNeural | 女 | 年轻活泼 | 广告、短视频 |
| zh-CN-YunyangNeural | 男 | 沉稳 | 纪录片、企业宣传 |
| zh-CN-XiaohanNeural | 女 | 知性 | 新闻播报 |
| zh-CN-YunjianNeural | 男 | 深沉 | 电影旁白 |
| zh-CN-XiaomengNeural | 女 | 温柔 | 有声书、故事 |
| zh-CN-YunxiNeural | 男 | 活泼 | 游戏解说 |

### 英语音色

| 音色名称 | 性别 | 风格 | 适用场景 |
|---------|------|------|---------|
| en-US-JennyNeural | 女 | 美式 | 商务对话 |
| en-US-GuyNeural | 男 | 美式 | 新闻播报 |
| en-GB-SoniaNeural | 女 | 英式 | 正式场合 |
| en-GB-RyanNeural | 男 | 英式 | 文学朗读 |

### 其他语言

- **日语**：ja-JP-NanamiNeural（女）、ja-JP-KeitaNeural（男）
- **韩语**：ko-KR-SunHiNeural（女）、ko-KR-InJoonNeural（男）
- **德语**：de-DE-KatjaNeural（女）、de-DE-ConradNeural（男）
- **法语**：fr-FR-DeniseNeural（女）、fr-FR-HenriNeural（男）

## 使用示例

### 示例 1：基础朗读

```
"朗读这段文本：欢迎使用本地语音合成服务"
```

### 示例 2：指定音色

```
"用温柔女声朗读这段文本：今天天气真好"
```

### 示例 3：多语言

```
"用英语朗读这段话：Hello, how are you?"
"用日语朗读这段话：こんにちは"
```

### 示例 4：情感表达

```
"用激昂的语调朗读这段解说词：让我们勇往直前！"
"用温柔的语调朗读这段故事：很久很久以前..."
```

## 资源索引

- **TTS 生成脚本**：见 [scripts/tts_generator.py](scripts/tts_generator.py)
- **音频处理脚本**：见 [scripts/audio_processor.py](scripts/audio_processor.py)
- **音色参数指南**：见 [references/voice-guide.md](references/voice-guide.md)

## 注意事项

- **零依赖**：只需要安装 edge-tts 库
- **离线使用**：首次下载后无需网络
- **音色限制**：使用 Microsoft Edge 预设音色，不支持自定义克隆
- **情感控制**：通过选择不同音色实现情感变化
- **最佳体验**：首次使用时会下载语音包，约 50-100MB

## 安装说明

```bash
# 安装 edge-tts
pip install edge-tts

# 验证安装
edge-tts --help
```

## 技术说明

**Edge-TTS 工作原理**：
- 使用 Microsoft Edge 浏览器的在线 TTS 服务
- 通过逆向工程获取的 API 接口
- 完全免费，无需注册账号
- 首次下载后音频缓存到本地

**与 API 调用的区别**：
- ❌ 不需要 API_KEY
- ❌ 不需要注册账号
- ✅ 离线缓存
- ✅ 零成本使用
