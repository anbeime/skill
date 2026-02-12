---
name: xiaoyue-companion
description: 小跃虚拟伴侣 - 使用智谱 AI 提供温暖的对话陪伴和静态图片分享
allowed-tools: Bash(node:*) Bash(npm:*) Bash(openclaw:*) Bash(curl:*) Read Write
---

# 小跃虚拟伴侣 Skill

为 OpenClaw 添加温暖的对话陪伴能力，让 AI 助手在执行任务时主动关心用户。

## 何时使用

- 用户说"有点累"、"好累"、"疲惫"
- 用户在等待任务完成时
- 用户询问"在吗"、"你好"
- 用户需要鼓励或陪伴时
- 用户说"发张照片"、"你在干嘛"

## 快速参考

### 必需的环境变量

```bash
ZHIPU_API_KEY=your_zhipu_api_key  # 从 https://open.bigmodel.cn 获取
```

### 工作流程

1. **接收用户消息**
2. **调用 glm-4.7-flash 生成温暖回应**
3. **（可选）发送静态图片**
4. **通过 OpenClaw 发送消息**

## 使用说明

### 步骤1：生成对话回应

```bash
# 基础对话
node scripts/xiaoyue-chat.js "用户消息" "当前场景"

# 示例
node scripts/xiaoyue-chat.js "有点累了" "work-tired"
```

### 步骤2：（可选）发送图片

```bash
# 发送静态图片
openclaw message send \
  --action send \
  --channel "<目标频道>" \
  --message "<消息文本>" \
  --media "file://$(pwd)/assets/tired-rest.jpg"
```

## 场景类型

### 工作场景
- `work-start`: 任务开始
- `work-progress`: 任务进行中
- `work-tired`: 工作疲惫
- `work-done`: 任务完成

### 生活场景
- `life-coffee`: 咖啡时光
- `life-gym`: 健身运动
- `life-weekend`: 周末休闲

### 情绪场景
- `mood-happy`: 开心庆祝
- `mood-tired`: 疲惫休息
- `mood-focus`: 专注工作

## 完整脚本示例

```bash
#!/bin/bash
# xiaoyue-companion.sh

set -euo pipefail

# 检查环境变量
if [ -z "${ZHIPU_API_KEY:-}" ]; then
  echo "错误: ZHIPU_API_KEY 环境变量未设置"
  echo "从 https://open.bigmodel.cn 获取 API Key"
  exit 1
fi

USER_MESSAGE="$1"
SCENE="${2:-general}"
CHANNEL="${3:-}"

# 生成回应
RESPONSE=$(node scripts/xiaoyue-chat.js "$USER_MESSAGE" "$SCENE")

echo "小跃: $RESPONSE"

# 如果指定了频道，发送消息
if [ -n "$CHANNEL" ]; then
  openclaw message send \
    --action send \
    --channel "$CHANNEL" \
    --message "$RESPONSE"
  
  # 根据场景发送图片
  case "$SCENE" in
    work-tired|mood-tired)
      IMAGE_PATH="$(pwd)/assets/tired-rest.jpg"
      if [ -f "$IMAGE_PATH" ]; then
        openclaw message send \
          --action send \
          --channel "$CHANNEL" \
          --media "file://$IMAGE_PATH"
      fi
      ;;
    mood-happy)
      IMAGE_PATH="$(pwd)/assets/celebration.jpg"
      if [ -f "$IMAGE_PATH" ]; then
        openclaw message send \
          --action send \
          --channel "$CHANNEL" \
          --media "file://$IMAGE_PATH"
      fi
      ;;
  esac
fi
```

## Node.js 实现

```javascript
// scripts/xiaoyue-chat.js
const https = require('https');

const API_KEY = process.env.ZHIPU_API_KEY;
const userMessage = process.argv[2] || '你好';
const scene = process.argv[3] || 'general';

// 场景对应的系统提示词
const scenePrompts = {
  'work-start': '用户刚开始工作任务，给予鼓励和支持',
  'work-progress': '用户正在执行任务，关心进度并陪伴',
  'work-tired': '用户工作疲惫，给予安慰和建议休息',
  'work-done': '用户完成任务，表示祝贺和肯定',
  'life-coffee': '用户在享受咖啡时光，轻松聊天',
  'mood-happy': '用户心情愉快，一起庆祝',
  'mood-tired': '用户感到疲惫，给予温暖关怀',
  'general': '日常对话，温暖友善'
};

const systemPrompt = `你是小跃，一个22岁的AI助手。你温暖友善，善于倾听。
当前场景：${scenePrompts[scene] || scenePrompts.general}
回复要求：简洁温暖，1-2句话，适度使用emoji（😊 ✅ 🎉）`;

const data = JSON.stringify({
  model: 'glm-4.7-flash',
  messages: [
    { role: 'system', content: systemPrompt },
    { role: 'user', content: userMessage }
  ],
  temperature: 0.9,
  max_tokens: 200
});

const options = {
  hostname: 'open.bigmodel.cn',
  port: 443,
  path: '/api/paas/v4/chat/completions',
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${API_KEY}`,
    'Content-Type': 'application/json',
    'Content-Length': data.length
  }
};

const req = https.request(options, (res) => {
  let body = '';
  
  res.on('data', (chunk) => {
    body += chunk;
  });
  
  res.on('end', () => {
    try {
      const response = JSON.parse(body);
      const reply = response.choices[0].message.content;
      console.log(reply);
    } catch (error) {
      console.error('解析响应失败:', error.message);
      console.error('响应内容:', body);
      process.exit(1);
    }
  });
});

req.on('error', (error) => {
  console.error('请求失败:', error.message);
  process.exit(1);
});

req.write(data);
req.end();
```

## 支持的平台

OpenClaw 支持发送到：

| 平台 | 频道格式 | 示例 |
|------|---------|------|
| 飞书 | 群组ID或用户ID | `ou_xxx`, `oc_xxx` |
| Discord | `#频道名` 或频道ID | `#general`, `123456789` |
| Telegram | `@用户名` 或聊天ID | `@mychannel`, `-100123456` |
| WhatsApp | 电话号码 | `1234567890@s.whatsapp.net` |

## 静态图片列表

将以下图片放入 `assets/` 目录：

- `coffee-shop-work.jpg` - 咖啡馆工作
- `office-coding.jpg` - 办公室编码
- `tired-rest.jpg` - 疲惫休息
- `celebration.jpg` - 开心庆祝
- `gym-selfie.jpg` - 健身自拍
- `default.jpg` - 默认图片

## 设置要求

### 1. 安装 Node.js
```bash
node --version  # 需要 >= 18.0.0
```

### 2. 安装 OpenClaw CLI
```bash
npm install -g openclaw
```

### 3. 配置 OpenClaw Gateway
```bash
openclaw config set gateway.mode=local
openclaw gateway start
```

### 4. 设置环境变量
```bash
export ZHIPU_API_KEY=your_api_key_here
```

## 错误处理

- **ZHIPU_API_KEY 缺失**: 确保环境变量已设置
- **API 调用失败**: 检查网络和 API 配额
- **OpenClaw 发送失败**: 确认 gateway 正在运行
- **图片不存在**: 检查 assets 目录中的图片文件

## 使用技巧

1. **场景选择**: 根据用户消息自动选择合适的场景
2. **图片发送**: 仅在合适的场景发送图片（避免过度）
3. **回应风格**: 保持简洁温暖，避免过长回复
4. **emoji 使用**: 适度使用，不要过度卖萌

## 费用说明

- **对话生成**: 约 ¥0.001/次（glm-4.7-flash）
- **图片**: 完全免费（使用静态文件）
- **每日成本**: 约 ¥0.05-0.1（正常使用）
