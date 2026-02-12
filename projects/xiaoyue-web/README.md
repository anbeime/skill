# 🚀 小跃伴侣 Web 版

**真正可运行的 AI 对话和图片生成系统！**

无需复杂配置，3 分钟即可启动一个能真实对话和生成图片的 AI 伴侣。

## ✨ 功能特性

- ✅ **真实 AI 对话**：使用智谱 GLM-4-Flash 模型
- ✅ **图片生成**：使用智谱 CogView-3 生成场景图片
- ✅ **多场景支持**：咖啡馆、办公室、家、健身房、公园
- ✅ **对话记忆**：自动保存对话历史
- ✅ **即开即用**：无需复杂配置

## 🎮 快速开始

### 步骤 1：获取 API Key

1. 访问 [智谱 AI 开放平台](https://open.bigmodel.cn/)
2. 注册并登录（新用户有免费额度）
3. 进入「API Keys」页面
4. 创建新的 API Key 并复制

### 步骤 2：安装依赖

```bash
cd xiaoyue-web
npm install
```

### 步骤 3：配置 API Key

```bash
# 复制配置文件
cp .env.example .env

# 编辑 .env 文件，填入你的 API Key
# Windows: notepad .env
# macOS/Linux: nano .env
```

将 `your-api-key-here` 替换为你的真实 API Key：
```env
ZHIPU_API_KEY=你的API_KEY
PORT=3000
```

### 步骤 4：启动服务器

```bash
npm start
```

看到以下输出表示成功：
```
🚀 小跃伴侣服务器运行在 http://localhost:3000
📝 API Key 状态: ✅ 已配置
```

### 步骤 5：开始对话！

打开浏览器访问：http://localhost:3000

试试这些对话：
- "你好小跃！"
- "发张你在咖啡馆的照片"
- "你在做什么？"
- "今天心情怎么样？"

## 💬 使用示例

### 场景 1：生成图片

```
你：发张你在咖啡馆的照片
小跃：好的，稍等一下～
[真实生成图片]
小跃：刚在咖啡馆点了杯拿铁，准备继续写代码 ☕
```

### 场景 2：自然对话

```
你：今天心情怎么样？
小跃：挺好的！刚完成了一个小项目，很有成就感 😊 你呢？
你：有点累
小跃：辛苦啦！要不要我给你讲个笑话放松一下？
```

### 场景 3：多场景图片

支持的场景：
- 📸 咖啡馆：温馨的咖啡馆工作场景
- 💼 办公室：现代化办公室编程场景
- 🏠 家：舒适的居家环境
- 💪 健身房：充满活力的运动场景
- 🌳 公园：宁静的户外环境

## 📊 API 接口

### POST /api/chat

对话接口

**请求：**
```json
{
  "message": "你好",
  "sessionId": "default"
}
```

**响应：**
```json
{
  "success": true,
  "message": "你好！我是小跃 😊",
  "needImage": false
}
```

### POST /api/generate-image

图片生成接口

**请求：**
```json
{
  "scene": "coffee-shop"
}
```

**响应：**
```json
{
  "success": true,
  "imageUrl": "https://...",
  "scene": "coffee-shop"
}
```

### GET /api/health

健康检查

**响应：**
```json
{
  "status": "ok",
  "hasApiKey": true
}
```

## 💰 成本说明

使用智谱 AI 的费用：
- **GLM-4-Flash**：¥0.001/1K tokens（对话）
- **CogView-3**：¥0.05/张图片

**正常使用成本**：
- 每天对话 50 轮：约 ¥0.1
- 每天生成 5 张图片：约 ¥0.25
- **月成本约 ¥10-15**

新用户有免费额度，足够体验！

## 🔧 开发模式

```bash
# 安装 nodemon（可选）
npm install -g nodemon

# 启动开发模式（自动重启）
npm run dev
```

## 🌐 部署到线上

### Vercel 部署

1. 安装 Vercel CLI：
```bash
npm install -g vercel
```

2. 部署：
```bash
vercel
```

3. 配置环境变量：
在 Vercel 控制台添加 `ZHIPU_API_KEY`

### Railway 部署

1. 访问 [Railway](https://railway.app/)
2. 连接 GitHub 仓库
3. 添加环境变量 `ZHIPU_API_KEY`
4. 自动部署完成！

## 📁 项目结构

```
xiaoyue-web/
├── server.js           # Express 服务器
├── package.json        # 依赖配置
├── .env.example        # 环境变量示例
├── public/
│   └── index.html      # Web 界面
└── README.md          # 本文件
```

## ❓ 常见问题

### Q1: 提示"请配置 ZHIPU_API_KEY"

确保：
1. 已创建 `.env` 文件
2. 填入了正确的 API Key
3. 重启了服务器

### Q2: 图片生成失败

可能原因：
- API Key 余额不足
- 网络连接问题
- 提示词不符合规范

### Q3: 对话没有回复

检查：
1. 服务器是否正常运行
2. 浏览器控制台是否有错误
3. API Key 是否有效

### Q4: 如何修改对话风格？

编辑 `server.js` 中的 `system` 提示词：
```javascript
{
  role: 'system',
  content: `你是小跃，一个...（修改这里）`
}
```

### Q5: 可以添加更多场景吗？

可以！在 `server.js` 的 `scenePrompts` 中添加：
```javascript
const scenePrompts = {
  'coffee-shop': '...',
  'my-scene': '你的场景描述',  // 添加新场景
  ...
};
```

## 🔗 相关链接

- **智谱 AI 平台**：https://open.bigmodel.cn/
- **GitHub 仓库**：https://github.com/anbeime/skill
- **问题反馈**：https://github.com/anbeime/skill/issues

## 📝 更新日志

### v1.0.0 (2026-02-12)
- ✨ 初始版本发布
- ✅ 支持真实 AI 对话
- ✅ 支持图片生成
- ✅ 支持多场景切换

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📄 许可证

MIT License

---

**现在就开始和小跃对话吧！** 🎉

Made with ❤️ by anbeime
