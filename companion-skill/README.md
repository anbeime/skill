# 小跃虚拟伴侣 Skill

为 OpenClaw 添加虚拟伴侣能力，让 AI 助手更有温度。

## ✨ 功能特性

- 🤗 **任务陪伴**：在执行耗时任务时主动聊天，避免枯燥等待
- 📸 **场景图片**：根据对话内容生成/发送生活照片
- 💬 **自然对话**：基于 glm-4-flash 的流畅对话能力
- 👁️ **视觉理解**：基于 glm-4v-flash 的图片分析能力
- 🎨 **AI 生图**：使用 cogview-3-flash 生成场景图片
- 🎭 **场景识别**：智能识别工作/生活/情绪场景
- 📱 **飞书集成**：通过 OpenClaw Gateway 无缝对接飞书

## 🚀 快速开始

### 1. 安装依赖

```bash
cd xiaoyue-companion-skill
npm install
```

### 2. 配置环境变量

复制 `.env.example` 为 `.env`，填入你的智谱 AI API Key：

```bash
cp .env.example .env
# 编辑 .env 文件
ZHIPU_API_KEY=your-api-key-here
```

### 3. 编译项目

```bash
npm run build
```

### 4. 集成到 OpenClaw

将编译后的 Skill 复制到 OpenClaw skills 目录：

```bash
# Windows
xcopy /E /I dist %USERPROFILE%\.openclaw\skills\xiaoyue-companion

# macOS/Linux
cp -r dist ~/.openclaw/skills/xiaoyue-companion
```

在 `~/.openclaw/openclaw.json` 中启用 Skill：

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

### 5. 更新 SOUL.md

在 `~/.openclaw/workspace/SOUL.md` 中添加小跃的人设（参考 `SKILL.md`）。

## 📖 使用示例

### 场景1：任务陪伴

```
用户：帮我整理一下桌面文件
小跃：好的！我这就开始整理～顺便问一下，今天工作还顺利吗？
     [后台执行任务]
用户：有点累
小跃：辛苦啦！[发送咖啡馆休息照片] 
     要不要我帮你生成今日工作总结？
```

### 场景2：主动分享

```
用户：小跃在吗？
小跃：在的！刚在调试代码呢～[发送工作照]
     有什么需要帮忙的吗?
```

## 🛠️ 技术栈

- **对话生成**: glm-4-flash（智谱 AI）
- **视觉理解**: glm-4v-flash（智谱 AI）
- **图片生成**: cogview-3-flash（智谱 AI）
- **开发语言**: TypeScript
- **运行环境**: Node.js >= 18.0.0

## 🛠️ 开发指南

### 项目结构

```
xiaoyue-companion-skill/
├── src/
│   ├── index.ts              # 主入口
│   ├── companion.ts          # 对话生成 (glm-4-flash + glm-4v-flash)
│   ├── image-generator.ts    # 图片生成 (cogview-3-flash)
│   ├── scene-detector.ts     # 场景识别
│   ├── test.ts               # 测试脚本
│   └── prompts/
│       └── personality.ts    # 人设定义
├── assets/
│   └── reference/            # 参考图片库
├── dist/                     # 编译输出
├── package.json
├── tsconfig.json
└── README.md
```

### 开发模式

```bash
npm run dev  # 监听文件变化，自动编译
```

### 测试

```bash
npm test  # 运行所有测试
```

测试内容包括：
- ✅ 对话生成测试 (glm-4-flash)
- ✅ 多模态视觉测试 (glm-4v-flash)
- ✅ 场景识别测试
- ✅ 图片生成测试 (cogview-3-flash)
- ✅ 参考图片复制

## 📸 图片管理

当前版本支持两种模式：

### 模式1：AI 动态生成（推荐）

使用 cogview-3-flash 实时生成场景图片。

**配置：**
```env
XIAOYUE_PHOTO_MODE=ai
```

**优点：**
- 场景丰富，每次生成都不同
- 可以根据对话内容定制
- 保持人物形象一致

**成本：**
- cogview-3-flash: ¥0.05/张
- 每天正常使用约 5-10 张图片
- 月成本约 ¥10-20

### 模式2：静态图片库

使用预制图片，完全免费。

**配置：**
```env
XIAOYUE_PHOTO_MODE=static
```

**添加图片：**

将图片放入 `assets/reference/` 目录，命名规则：

- `coffee-shop-work.jpg` - 咖啡馆工作
- `office-coding.jpg` - 办公室编码
- `gym-selfie.jpg` - 健身房自拍
- `default.jpg` - 默认图片

### 批量生成图片库

```bash
npm run test:generate
```

⚠️ 注意：此操作会调用 9 次 CogView API，可能产生少量费用（约 ¥0.5-1）

## 🎯 路线图

- [x] **Phase 1**：基础对话 (glm-4-flash) + 静态图片
- [x] **Phase 2**：AI 图片生成 (cogview-3-flash) + 视觉理解 (glm-4v-flash)
- [ ] **Phase 3**：语音交互 + 主动关怀

## 🤝 贡献

欢迎提交 Issue 和 PR！

## 📄 许可证

MIT License

## 🙏 致谢

- OpenClaw 框架
- 智谱 AI GLM 系列模型
- Clawra 项目灵感
