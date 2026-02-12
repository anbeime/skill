# 快速开始指南

## 1. 安装依赖

```bash
cd xiaoyue-assistant
npm install
```

## 2. 配置环境变量

复制 `.env.example` 为 `.env`：

```bash
copy .env.example .env
```

编辑 `.env` 文件，填入你的 API Keys：

```env
# 必填：AI 模型 API Key（至少配置一个）
ANTHROPIC_API_KEY=sk-ant-xxxxx

# 可选：图片生成
FAL_KEY=your_fal_key

# 可选：通讯平台
FEISHU_APP_ID=cli_xxxxx
FEISHU_APP_SECRET=xxxxx
```

## 3. 启动开发服务器

```bash
npm run dev
```

看到以下输出表示启动成功：

```
🚀 Xiaoyue Assistant is running on port 3000
Environment: development
Health check: http://localhost:3000/health
```

## 4. 测试 API

### 健康检查

```bash
curl http://localhost:3000/health
```

### 发送消息

```bash
curl -X POST http://localhost:3000/message \
  -H "Content-Type: application/json" \
  -d '{
    "userId": "test-user-001",
    "message": "你好小跃"
  }'
```

### 生成图片

```bash
curl -X POST http://localhost:3000/generate-image \
  -H "Content-Type: application/json" \
  -d '{
    "scene": "coffee",
    "referenceImage": "https://your-cdn.com/reference.png"
  }'
```

## 5. 接入飞书机器人

详细步骤请查看：[飞书接入指南](./platforms/feishu.md)

## 下一步

- 查看 [完整文档](../README.md)
- 开发自定义 [Skills](./skills.md)
- 配置 [多平台接入](./platforms/)

## 常见问题

**Q: 启动时报错 "Cannot find module"**  
A: 运行 `npm install` 确保所有依赖已安装

**Q: API 调用失败**  
A: 检查 `.env` 文件中的 API Key 是否正确配置

**Q: 如何修改对话风格？**  
A: 编辑 `src/core/agent.ts` 中的 `buildSystemPrompt` 方法
