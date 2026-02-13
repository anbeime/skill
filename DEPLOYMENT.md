# 🚀 小跃伴侣部署指南

让你的小跃伴侣真正"活"起来！本指南将帮助你部署一个可以真实对话和生成图片的 AI 伴侣。

## 📋 目录

- [快速体验（演示版）](#快速体验演示版)
- [完整部署（推荐）](#完整部署推荐)
- [三种部署方案对比](#三种部署方案对比)
- [常见问题](#常见问题)

---

## 🎮 快速体验（演示版）

**在线演示**：https://skill.miyucaicai.cn/chat-demo.html

这是一个模拟版本，可以体验基本的对话流程，但：
- ❌ 不能真正生成图片（使用预设图片）
- ❌ 不能调用真实的 AI 模型
- ✅ 可以了解交互流程和界面

**想要真实体验？** 请继续阅读完整部署方案 👇

---

## 🎯 完整部署（推荐）

### 方案 1：Companion Skill（最完整）

**特点**：
- ✅ 真实的 AI 图片生成（CogView-3）
- ✅ 视觉理解能力（GLM-4V）
- ✅ 自然对话（GLM-4-Flash）
- ✅ 场景识别和情感陪伴

**成本**：约 ¥10-20/月（正常使用）

#### 步骤 1：获取 API Key

1. 访问 [智谱 AI 开放平台](https://open.bigmodel.cn/)
2. 注册并登录账号
3. 进入「API Keys」页面
4. 创建新的 API Key 并保存

#### 步骤 2：克隆项目

```bash
git clone https://github.com/anbeime/skill.git
cd skill/projects/companion-skill
```

#### 步骤 3：安装依赖

```bash
npm install
```

#### 步骤 4：配置环境变量

```bash
# 复制配置文件
cp .env.example .env

# 编辑 .env 文件
# Windows: notepad .env
# macOS/Linux: nano .env
```

填入你的 API Key：
```env
ZHIPU_API_KEY=your-api-key-here
XIAOYUE_PHOTO_MODE=ai  # 使用 AI 生成图片
```

#### 步骤 5：编译运行

```bash
# 编译项目
npm run build

# 运行测试（验证配置）
npm test
```

#### 步骤 6：集成到 OpenClaw

```bash
# Windows
xcopy /E /I dist %USERPROFILE%\.openclaw\skills\xiaoyue-companion

# macOS/Linux
cp -r dist ~/.openclaw/skills/xiaoyue-companion
```

在 `~/.openclaw/openclaw.json` 中启用：

```json
{
  "skills": {
    "entries": {
      "xiaoyue-companion": {
        "enabled": true,
        "env": {
          "ZHIPU_API_KEY": "your-api-key-here"
        }
      }
    }
  }
}
```

#### 步骤 7：开始对话！

打开 OpenClaw，输入：
```
你好小跃！
发张你在咖啡馆的照片
```

---

### 方案 2：Assistant（多平台支持）

**特点**：
- ✅ 支持飞书、钉钉、Telegram
- ✅ 图片生成（fal.ai）
- ✅ 长期记忆系统
- ✅ 多种 AI 模型支持

**成本**：根据使用的 AI 模型而定

#### 快速开始

```bash
cd skill/projects/assistant

# 安装依赖
npm install

# 配置环境变量
cp .env.example .env
# 编辑 .env，填入 API Keys

# 启动开发服务器
npm run dev
```

#### 飞书机器人接入

1. 访问 [飞书开放平台](https://open.feishu.cn/)
2. 创建企业自建应用
3. 配置事件订阅和权限
4. 获取 App ID 和 App Secret
5. 在 `.env` 中配置：

```env
FEISHU_APP_ID=your-app-id
FEISHU_APP_SECRET=your-app-secret
FAL_KEY=your-fal-key  # 用于图片生成
ANTHROPIC_API_KEY=your-claude-key  # 或使用 OpenAI
```

详细教程：[飞书接入指南](./assistant/docs/platforms/feishu.md)

---

### 方案 3：Companion Simple（Web 版）

**特点**：
- ✅ 无需安装，浏览器访问
- ✅ 技能管理和展示
- ✅ 轻量级部署

**成本**：免费（Vercel 部署）

#### 部署到 Vercel

```bash
cd skill/projects/companion-simple

# 安装 Vercel CLI
npm install -g vercel

# 部署
vercel
```

按提示完成部署，几分钟后即可访问！

---

## 📊 三种部署方案对比

| 功能 | Companion Skill | Assistant | Companion Simple |
|------|----------------|-----------|------------------|
| 图片生成 | ✅ CogView-3 | ✅ fal.ai | ❌ |
| 视觉理解 | ✅ GLM-4V | ✅ Claude/GPT | ❌ |
| 自然对话 | ✅ GLM-4-Flash | ✅ Claude/GPT | ❌ |
| 多平台支持 | ❌ | ✅ 飞书/钉钉/TG | ✅ Web |
| 长期记忆 | ❌ | ✅ | ❌ |
| 部署难度 | ⭐⭐ | ⭐⭐⭐ | ⭐ |
| 月成本 | ¥10-20 | ¥20-50 | 免费 |

**推荐选择**：
- 🎯 **个人使用**：Companion Skill（性价比高）
- 🏢 **团队协作**：Assistant + 飞书
- 🌐 **快速展示**：Companion Simple

---

## 🎨 使用示例

### 场景 1：生成图片

```
用户：发张你在咖啡馆的照片
小跃：好的，稍等一下～
      [生成图片]
小跃：刚在咖啡馆点了杯拿铁，准备继续写代码 ☕
```

### 场景 2：任务陪伴

```
用户：帮我整理一下桌面文件
小跃：好的！我这就开始整理～顺便问一下，今天工作还顺利吗？
      [后台执行任务]
用户：有点累
小跃：辛苦啦！[发送休息照片] 
      要不要我帮你生成今日工作总结？
```

### 场景 3：视觉理解

```
用户：[上传图片] 这是什么？
小跃：这是一张代码截图，看起来是 Python 代码。
      我看到了一个数据处理的函数...
      需要我帮你优化这段代码吗？
```

---

## ❓ 常见问题

### Q1: API Key 怎么获取？

**智谱 AI**（Companion Skill）：
1. 访问 https://open.bigmodel.cn/
2. 注册并实名认证
3. 新用户有免费额度

**fal.ai**（Assistant）：
1. 访问 https://fal.ai/
2. 注册账号
3. 获取 API Key

### Q2: 成本大概多少？

**Companion Skill**：
- CogView-3：¥0.05/张图片
- GLM-4-Flash：¥0.001/1K tokens
- 正常使用：¥10-20/月

**Assistant**：
- 根据选择的 AI 模型
- Claude：约 $0.003/1K tokens
- fal.ai：约 $0.05/张图片

### Q3: 可以本地运行吗？

可以！所有项目都支持本地运行：
- Companion Skill：Node.js 环境
- Assistant：Node.js 环境
- Companion Simple：Python 环境

### Q4: 图片生成速度如何？

- CogView-3：约 5-10 秒/张
- fal.ai：约 3-8 秒/张
- 取决于网络和服务器负载

### Q5: 支持哪些语言？

- ✅ 中文（主要）
- ✅ 英文
- ✅ 中英混合

### Q6: 可以自定义人设吗？

可以！编辑对应的配置文件：
- Companion Skill：`src/prompts/personality.ts`
- Assistant：`src/companion/dialogue.ts`

### Q7: 遇到问题怎么办？

1. 查看项目 README
2. 检查 API Key 配置
3. 查看日志输出
4. 提交 GitHub Issue：https://github.com/anbeime/skill/issues

---

## 🔗 相关链接

- **GitHub 仓库**：https://github.com/anbeime/skill
- **在线演示**：https://skill.miyucaicai.cn/chat-demo.html
- **项目展示**：https://skill.miyucaicai.cn/projects.html
- **技能商店**：https://skill.miyucaicai.cn/

---

## 🤝 需要帮助？

- 💬 GitHub Discussions：https://github.com/anbeime/skill/discussions
- 🐛 报告问题：https://github.com/anbeime/skill/issues
- 📧 邮件联系：（在 GitHub Profile 查看）

---

**祝你和小跃相处愉快！** 🎉

Made with ❤️ by anbeime | 最后更新: 2026-02-12
