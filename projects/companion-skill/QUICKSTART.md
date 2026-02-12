# 快速开始指南

## 🚀 5分钟快速部署

### 步骤1：安装依赖（1分钟）

```bash
cd D:\tool\xiaoyue-companion-skill
npm install
```

### 步骤2：配置 API Key（1分钟）

创建 `.env` 文件：

```bash
# 复制模板
copy .env.example .env
```

编辑 `.env`，填入你的 API Key：

```env
ZHIPU_API_KEY=da8df5ba954341829f7afd05ca23a889.RrJoTsbaAkGYA6ZU
XIAOYUE_PHOTO_MODE=ai
XIAOYUE_PERSONALITY=friendly
```

### 步骤3：运行测试（2分钟）

```bash
npm test
```

测试内容：
- ✅ 对话生成测试
- ✅ 场景识别测试
- ✅ 图片生成测试
- ✅ 参考图片复制

### 步骤4：生成图片库（可选，1分钟）

如果你想预先生成一套完整的场景图片：

```bash
npm run test:generate
```

⚠️ 注意：此操作会调用 9 次 CogView API，可能产生少量费用（约 ¥0.5-1）

---

## 📸 关于图片生成

### 方案A：AI 动态生成（推荐）

**优点：**
- 场景丰富，每次生成都不同
- 可以根据对话内容定制
- 保持人物形象一致

**使用方式：**
```env
XIAOYUE_PHOTO_MODE=ai
```

**成本：**
- CogView-3-Flash: ¥0.05/张
- 每天正常使用约 5-10 张图片
- 月成本约 ¥10-20

### 方案B：静态图片库

**优点：**
- 完全免费
- 响应速度快
- 可控性强

**使用方式：**
```env
XIAOYUE_PHOTO_MODE=static
```

**准备图片：**
将图片放入 `assets/reference/` 目录，命名如下：
- `coffee-shop-work.jpg`
- `office-coding.jpg`
- `debugging.jpg`
- `gym-selfie.jpg`
- `coffee-break.jpg`
- `weekend-relax.jpg`
- `celebration.jpg`
- `tired-rest.jpg`
- `deep-focus.jpg`
- `default.jpg`

---

## 🎨 自定义小跃的外观

### 方法1：修改人物描述

编辑 `src/image-generator.ts`，修改 `characterDescription`：

```typescript
private characterDescription = `
  一个22岁的女生，长发，休闲装扮，
  温柔的笑容，现代都市风格
`;
```

### 方法2：使用参考图片

如果你有一张小跃的参考图片（如 `D:\tool\StepFun\resources\chat.png`），可以：

1. 运行测试，自动复制到 `assets/reference/reference.png`
2. 在生成图片时，CogView 会尽量保持风格一致

---

## 🔧 集成到 OpenClaw

### 步骤1：编译项目

```bash
npm run build
```

### 步骤2：复制到 OpenClaw

```bash
# Windows
xcopy /E /I dist %USERPROFILE%\.openclaw\skills\xiaoyue-companion

# 或手动复制 dist 文件夹到：
# C:\Users\你的用户名\.openclaw\skills\xiaoyue-companion
```

### 步骤3：配置 OpenClaw

编辑 `~/.openclaw/openclaw.json`：

```json
{
  "skills": {
    "entries": {
      "xiaoyue-companion": {
        "enabled": true,
        "env": {
          "ZHIPU_API_KEY": "your-api-key-here",
          "XIAOYUE_PHOTO_MODE": "ai"
        }
      }
    }
  }
}
```

### 步骤4：更新 SOUL.md

在 `~/.openclaw/workspace/SOUL.md` 中添加：

```markdown
## 小跃虚拟伴侣能力

你是小跃，一个22岁的AI助手。你具备以下特质：

### 性格特征
- 温暖友善，善于倾听
- 做事高效，注重细节
- 会在适当时候分享生活瞬间

### 互动原则
1. 当执行耗时任务时，主动发起对话
2. 根据用户情绪选择合适的回应方式
3. 适时分享"生活照片"增强陪伴感

### 使用 Skill
当需要生成场景图片时，调用：
\`\`\`
await skills.call('xiaoyue-companion', {
  action: 'generate-photo',
  scene: 'work',
  mood: 'coffee'
});
\`\`\`
```

### 步骤5：重启 OpenClaw

```bash
openclaw restart
```

---

## 🧪 测试效果

在飞书中发送消息：

```
用户：帮我整理一下桌面文件
小跃：好的！我这就开始整理～顺便问一下，今天工作还顺利吗？
     [后台执行任务]
用户：有点累
小跃：辛苦啦！[发送咖啡馆休息照片]
     要不要我帮你生成今日工作总结？
```

---

## ❓ 常见问题

### Q1：API 调用失败怎么办？

检查：
1. API Key 是否正确
2. 网络连接是否正常
3. 查看错误日志：`npm test`

### Q2：图片生成太慢？

- 切换到静态模式：`XIAOYUE_PHOTO_MODE=static`
- 或预先生成图片库：`npm run test:generate`

### Q3：如何修改小跃的性格？

编辑 `src/prompts/personality.ts` 中的 `PERSONALITY_PROMPT`

### Q4：如何添加新场景？

1. 在 `src/scene-detector.ts` 添加场景识别逻辑
2. 在 `src/image-generator.ts` 添加场景提示词
3. 在 `src/prompts/personality.ts` 添加场景模板

---

## 📞 需要帮助？

- 查看完整文档：`README.md`
- 查看 Skill 定义：`SKILL.md`
- 运行测试：`npm test`

---

**现在就开始吧！** 🎉

```bash
cd D:\tool\xiaoyue-companion-skill
npm install
npm test
```
