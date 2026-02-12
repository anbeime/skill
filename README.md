# 小跃虚拟伴侣 Skill

参考 Clawra 项目结构，为 OpenClaw 添加温暖的对话陪伴能力。

## 🎯 设计理念

- **参考 Clawra**: 保持简单的 Skill 结构
- **替换 API**: fal.ai → 智谱 AI glm-4.7-flash
- **静态图片**: 不调用 AI 生图，避免额外费用
- **温暖陪伴**: 在任务执行时主动关心用户

## 📁 项目结构

```
xiaoyue-companion-simple/
├── SKILL.md                    # Skill 定义（OpenClaw 读取）
├── scripts/
│   ├── xiaoyue-chat.js         # 对话生成（Node.js）
│   └── xiaoyue-companion.sh    # 完整脚本（Bash）
├── templates/
│   └── soul-injection.md       # SOUL.md 注入内容
├── assets/
│   ├── tired-rest.jpg          # 疲惫休息图片
│   ├── celebration.jpg         # 庆祝图片
│   ├── coffee-break.jpg        # 咖啡休息图片
│   ├── gym-selfie.jpg          # 健身自拍图片
│   └── default.jpg             # 默认图片
└── README.md                   # 使用说明
```

## 🚀 快速开始

### 1. 克隆到 OpenClaw skills 目录

```bash
cp -r xiaoyue-companion-simple ~/.openclaw/skills/xiaoyue-companion
```

### 2. 设置环境变量

```bash
export ZHIPU_API_KEY=da8df5ba954341829f7afd05ca23a889.RrJoTsbaAkGYA6ZU
```

### 3. 测试对话生成

```bash
cd ~/.openclaw/skills/xiaoyue-companion
node scripts/xiaoyue-chat.js "有点累了" "work-tired"
```

### 4. 更新 SOUL.md

将 `templates/soul-injection.md` 的内容添加到 `~/.openclaw/workspace/SOUL.md`

### 5. 重启 OpenClaw

```bash
openclaw restart
```

## 📖 使用示例

### 基础对话

```bash
# 生成回应（不发送）
node scripts/xiaoyue-chat.js "今天工作怎么样" "general"

# 输出: 今天还顺利吗？有什么需要帮忙的吗？😊
```

### 发送到频道

```bash
# 生成回应并发送到飞书
./scripts/xiaoyue-companion.sh "有点累了" "work-tired" "#general"

# 会自动：
# 1. 生成温暖的回应
# 2. 发送消息到 #general
# 3. 发送 tired-rest.jpg 图片
```

## 🎭 场景说明

| 场景 | 使用时机 | 自动发送图片 |
|------|---------|-------------|
| `work-start` | 任务开始 | 无 |
| `work-progress` | 任务进行中 | 无 |
| `work-tired` | 工作疲惫 | tired-rest.jpg |
| `work-done` | 任务完成 | celebration.jpg |
| `life-coffee` | 咖啡时光 | coffee-break.jpg |
| `life-gym` | 健身运动 | gym-selfie.jpg |
| `mood-happy` | 开心庆祝 | celebration.jpg |
| `mood-tired` | 疲惫休息 | tired-rest.jpg |
| `general` | 日常对话 | 无 |

## 💰 费用说明

- **对话生成**: 约 ¥0.001/次（glm-4.7-flash）
- **图片**: 完全免费（静态文件）
- **每日成本**: 约 ¥0.05-0.1（正常使用）

## 🔧 配置 OpenClaw

在 `~/.openclaw/openclaw.json` 中添加：

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

## 📸 准备图片素材

将以下图片放入 `assets/` 目录：

1. `tired-rest.jpg` - 疲惫休息（可以是任意休息场景图片）
2. `celebration.jpg` - 庆祝（可以是任意庆祝图片）
3. `coffee-break.jpg` - 咖啡休息
4. `gym-selfie.jpg` - 健身自拍
5. `default.jpg` - 默认图片

**临时方案**：可以先用同一张图片复制多份，后续再替换。

## ✅ 与 Clawra 的对比

| 特性 | Clawra | 小跃伴侣 |
|------|--------|---------|
| 图片生成 | fal.ai (xAI Grok) | 静态文件 |
| 对话能力 | 无 | glm-4.7-flash |
| 费用 | ¥0.05/张图片 | ¥0.001/次对话 |
| 复杂度 | 简单 | 简单 |
| 依赖 | @fal-ai/client | 无（仅 Node.js） |

## 🎯 核心优势

1. **极简设计** - 参考 Clawra，只有必要文件
2. **零依赖** - 不需要 npm install
3. **低成本** - 仅对话费用，图片免费
4. **易理解** - 代码简单，易于修改

## 📝 后续改进

- [ ] 添加更多场景
- [ ] 支持自定义回复模板
- [ ] 集成 glm-4.6v-flash 图片理解
- [ ] 添加定时关怀功能

---

**版本**: v1.0.0  
**参考项目**: [Clawra](https://github.com/SumeLabs/clawra)  
**许可证**: MIT
