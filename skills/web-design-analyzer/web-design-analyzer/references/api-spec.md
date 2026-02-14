# OpenAI Vision API 规范参考

## 目录
- [API 概览](#api-概览)
- [认证方式](#认证方式)
- [请求格式](#请求格式)
- [响应格式](#响应格式)
- [错误处理](#错误处理)
- [使用示例](#使用示例)

## API 概览

**端点**: `https://api.openai.com/v1/chat/completions`

**支持的模型**:
- `gpt-4o`: 最新多模态模型，支持图片和文本
- `gpt-4-turbo`: 支持 Vision 能力
- `gpt-4-vision-preview`: Vision 预览模型

**能力**:
- 图片理解与分析
- 多模态对话（图片 + 文本）
- 结构化数据提取

## 认证方式

**类型**: API Key (Bearer Token)

**头部**:
```http
Authorization: Bearer <YOUR_API_KEY>
Content-Type: application/json
```

**获取 API Key**:
1. 访问 [OpenAI Platform](https://platform.openai.com/)
2. 登录后进入 API Keys 页面
3. 创建新的 API Key

## 请求格式

### HTTP 方法
`POST`

### 请求体结构
```json
{
  "model": "gpt-4o",
  "messages": [
    {
      "role": "system",
      "content": "系统提示词..."
    },
    {
      "role": "user",
      "content": [
        {
          "type": "text",
          "text": "用户文本消息"
        },
        {
          "type": "image_url",
          "image_url": {
            "url": "data:image/png;base64,<base64编码的图片>"
          }
        }
      ]
    }
  ],
  "max_tokens": 2000,
  "temperature": 0.7
}
```

### 关键参数说明

| 参数 | 类型 | 必需 | 说明 |
|------|------|------|------|
| `model` | string | 是 | 模型名称，如 `gpt-4o` |
| `messages` | array | 是 | 消息数组 |
| `max_tokens` | integer | 否 | 最大生成 token 数，默认 2048 |
| `temperature` | number | 否 | 温度参数，0-2，默认 1 |

### 图片格式支持

**支持的格式**:
- PNG
- JPEG
- WEBP
- GIF（非动画）

**图片大小限制**:
- 单张图片建议不超过 20MB
- 宽 x 高建议不超过 7680 x 4320 像素

**图片编码方式**:
```python
import base64

with open("image.png", "rb") as f:
    image_base64 = base64.b64encode(f.read()).decode("utf-8")

# 在 JSON 中使用
{
  "url": f"data:image/png;base64,{image_base64}"
}
```

## 响应格式

### 成功响应
```json
{
  "id": "chatcmpl-xxx",
  "object": "chat.completion",
  "created": 1234567890,
  "model": "gpt-4o",
  "choices": [
    {
      "index": 0,
      "message": {
        "role": "assistant",
        "content": "AI 的回复内容..."
      },
      "finish_reason": "stop"
    }
  ],
  "usage": {
    "prompt_tokens": 1000,
    "completion_tokens": 500,
    "total_tokens": 1500
  }
}
```

### 字段说明

| 字段 | 说明 |
|------|------|
| `id` | 请求 ID |
| `choices[].message.content` | AI 的回复内容 |
| `usage.prompt_tokens` | 输入的 token 数 |
| `usage.completion_tokens` | 生成的 token 数 |
| `usage.total_tokens` | 总 token 数 |

## 错误处理

### 常见错误代码

| HTTP 状态码 | 错误类型 | 说明 |
|-------------|----------|------|
| 401 | `invalid_api_key` | API Key 无效或过期 |
| 429 | `rate_limit_exceeded` | 请求频率超限 |
| 400 | `invalid_request_error` | 请求参数错误 |
| 500 | `server_error` | OpenAI 服务器错误 |

### 错误响应格式
```json
{
  "error": {
    "message": "错误描述信息",
    "type": "invalid_request_error",
    "param": null,
    "code": "invalid_api_key"
  }
}
```

### 处理建议

1. **API Key 无效**: 检查环境变量或重新生成 Key
2. **频率超限**: 实现重试机制（指数退避）
3. **图片格式错误**: 验证图片格式和大小
4. **超时错误**: 增加 timeout 值（建议 60s 以上）

## 使用示例

### Python 示例
```python
import os
import base64
from coze_workload_identity import requests

def analyze_image(image_path: str):
    # 获取 API Key
    api_key = os.getenv("OPENAI_API_KEY")
    
    # 编码图片
    with open(image_path, "rb") as f:
        image_base64 = base64.b64encode(f.read()).decode("utf-8")
    
    # 构建请求
    url = "https://api.openai.com/v1/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    
    payload = {
        "model": "gpt-4o",
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": "请描述这张图片的内容"
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/png;base64,{image_base64}"
                        }
                    }
                ]
            }
        ]
    }
    
    # 发送请求
    response = requests.post(url, headers=headers, json=payload, timeout=60)
    response.raise_for_status()
    
    return response.json()
```

### cURL 示例
```bash
curl https://api.openai.com/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $OPENAI_API_KEY" \
  -d '{
    "model": "gpt-4o",
    "messages": [
      {
        "role": "user",
        "content": [
          {
            "type": "text",
            "text": "What is in this image?"
          },
          {
            "type": "image_url",
            "image_url": {
              "url": "https://example.com/image.png"
            }
          }
        ]
      }
    ]
  }'
```

## 注意事项

1. **费用**: Vision API 的费用比纯文本 API 高，建议控制图片大小和 token 使用量
2. **隐私**: 不要上传包含敏感信息的图片
3. **缓存**: 对于相同的分析请求，可以考虑缓存结果以减少 API 调用
4. **错误重试**: 实现指数退避的重试机制处理临时性错误
