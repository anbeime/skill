# Qwen3-ASR API 配置说明

## 概览
本文档说明如何配置 Qwen3-ASR API 凭证，使脚本能够正常调用 ASR 服务。

## 凭证设置

### 获取 API 密钥
1. 访问 Qwen3-ASR 官方平台
2. 注册账号并登录
3. 进入开发者中心或 API 管理页面
4. 创建新的 API 密钥（如果已有则使用现有密钥）

### 环境变量配置
在使用 `scripts/asr_transcriber.py` 之前，需要设置以下环境变量：

```bash
# 设置 Qwen3-ASR API 密钥
export COZE_QWEN3ASR_API_7598467069021093924="your_api_key_here"

# 可选：设置自定义 API 基础 URL（如果默认地址不适用）
export QWEN3ASR_BASE_URL="https://api.qwenlm.com/v1/asr"
```

### Skill 凭证配置
Skill 已集成凭证管理，通过以下方式自动获取凭证：
- 凭证名称：`qwen3asr_api`
- 凭证 Key：`COZE_QWEN3ASR_API_7598467069021093924`
- 环境变量：脚本自动从上述环境变量读取 API 密钥

## API 端点

### 默认端点
```
https://api.qwenlm.com/v1/asr
```

### 主要接口

#### 1. 语音识别（/transcribe）
- 方法：POST
- 请求体：
  - audio: 音频文件（二进制）
  - language: 语言代码（zh-CN/en-US 等）
  - format: 音频格式（wav/mp3/m4a/flac）
  - sample_rate: 采样率（8000/16000/48000）
  - return_timestamps: 是否返回时间戳
  - task: 任务类型（transcribe/translate）
- 响应：JSON
  ```json
  {
    "success": true,
    "text": "识别的文字",
    "language": "zh-CN",
    "duration": 120.5,
    "processing_time": 15.2,
    "segments": [...]
  }
  ```

#### 2. 说话人分离（/diarize）
- 方法：POST
- 请求体：
  - audio: 音频文件（二进制）
  - language: 语言代码
  - num_speakers: 说话人数量（可选）
  - return_timestamps: 是否返回时间戳
- 响应：JSON
  ```json
  {
    "success": true,
    "text": "识别的文字",
    "language": "zh-CN",
    "duration": 120.5,
    "speakers": ["SPEAKER_00", "SPEAKER_01"],
    "segments": [
      {
        "speaker": "SPEAKER_00",
        "start": 0.0,
        "end": 5.2,
        "text": "你好，我是张经理"
      }
    ]
  }
  ```

#### 3. 支持语言列表（/languages）
- 方法：GET
- 响应：JSON
  ```json
  {
    "languages": [
      "zh-CN",
      "en-US",
      "ja-JP",
      "ko-KR",
      "fr-FR",
      "de-DE",
      "es-ES",
      "it-IT",
      "ru-RU",
      "pt-BR"
    ]
  }
  ```

## 参数说明

### 语音识别参数
| 参数 | 类型 | 必需 | 说明 | 取值范围 |
|------|------|------|------|---------|
| audio | file | 是 | 音频文件 | wav/mp3/m4a/flac |
| language | string | 是 | 语言代码 | zh-CN/en-US/ja-JP/ko-KR 等 |
| format | string | 否 | 音频格式 | wav/mp3/m4a/flac |
| sample_rate | int | 否 | 采样率 | 8000/16000/48000 |
| return_timestamps | boolean | 否 | 是否返回时间戳 | true/false |
| task | string | 否 | 任务类型 | transcribe/translate |

### 说话人分离参数
| 参数 | 类型 | 必需 | 说明 | 取值范围 |
|------|------|------|------|---------|
| audio | file | 是 | 音频文件 | wav/mp3/m4a/flac |
| language | string | 是 | 语言代码 | zh-CN/en-US/ja-JP/ko-KR 等 |
| num_speakers | int | 否 | 说话人数量 | 自动检测或手动指定 |
| return_timestamps | boolean | 否 | 是否返回时间戳 | true/false |

### 常见错误码
| 错误码 | 说明 | 解决方法 |
|--------|------|---------|
| 401 | 未授权 | 检查 API 密钥是否正确 |
| 429 | 请求过于频繁 | 降低请求频率 |
| 400 | 参数错误 | 检查请求参数是否符合规范 |
| 500 | 服务器错误 | 稍后重试或联系技术支持 |
| 1001 | 音频格式不支持 | 转换音频格式 |
| 1002 | 音频时长超限 | 分段处理音频 |
| 1003 | 识别失败 | 检查音频质量 |

## 测试验证

### 验证凭证配置
```bash
# 检查环境变量是否设置
echo $COZE_QWEN3ASR_API_7598467069021093924
```

### 测试 API 连接
```bash
# 列出支持的语言
python scripts/asr_transcriber.py --list-languages
```

### 测试语音识别
```bash
# 基础识别
python scripts/asr_transcriber.py --audio recording.wav --output text.txt

# 带时间戳
python scripts/asr_transcriber.py --audio recording.wav --timestamps --output text.txt

# 说话人分离
python scripts/asr_transcriber.py --audio meeting.wav --diarize --speakers 3 --output text.txt
```

## 注意事项

1. **API 密钥安全**
   - 不要将 API 密钥硬编码在脚本中
   - 使用环境变量或凭证管理工具
   - 定期更新 API 密钥

2. **音频质量**
   - 确保录音清晰，无过多背景噪音
   - 推荐使用 16kHz 采样率
   - 音频格式推荐 WAV 或 MP3

3. **速率限制**
   - 注意 API 调用的速率限制
   - 避免短时间内大量请求
   - 长音频建议分段处理

4. **语言选择**
   - 根据音频内容选择正确的语言
   - 混合语言音频建议分段处理
   - 使用 `--list-languages` 查看支持的语言

5. **网络环境**
   - 确保网络连接稳定
   - 设置合理的超时时间
   - 实现错误重试机制

## 故障排查

### 问题：提示"未找到 API 凭证"
- 原因：环境变量未设置或为空
- 解决：设置正确的环境变量 `COZE_QWEN3ASR_API_7598467069021093924`

### 问题：API 返回 401 错误
- 原因：API 密钥无效或过期
- 解决：检查密钥是否正确，必要时重新获取

### 问题：识别准确率低
- 原因：音频质量差、语言选择错误、背景噪音
- 解决：
  - 提高音频质量
  - 检查语言选择
  - 使用降噪处理

### 问题：处理速度慢
- 原因：网络问题、音频文件过大
- 解决：
  - 检查网络连接
  - 分段处理长音频
  - 使用较低的采样率
