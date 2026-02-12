# 小跃虚拟伴侣 Skill - 完整使用指南

## ✅ 方案A：PowerShell 脚本（已完成）

### 文件位置
`D:\tool\xiaoyue-companion-simple\scripts\xiaoyue-chat.ps1`

### 使用方法

```powershell
# 设置 API Key
$env:ZHIPU_API_KEY="da8df5ba954341829f7afd05ca23a889.RrJoTsbaAkGYA6ZU"

# 运行脚本
& "D:\tool\xiaoyue-companion-simple\scripts\xiaoyue-chat.ps1" -UserMessage "有点累了" -Scene "work-tired"
```

### 场景选项
- `work-start` - 任务开始
- `work-progress` - 任务进行中
- `work-tired` - 工作疲惫
- `work-done` - 任务完成
- `life-coffee` - 咖啡时光
- `life-gym` - 健身运动
- `mood-happy` - 开心庆祝
- `mood-tired` - 疲惫休息
- `general` - 日常对话（默认）

### 示例

```powershell
# 示例1：工作疲惫
& xiaoyue-chat.ps1 -UserMessage "有点累了" -Scene "work-tired"
# 输出：辛苦啦，快去休息一下，养足精神再出发。😊

# 示例2：任务完成
& xiaoyue-chat.ps1 -UserMessage "终于完成了" -Scene "work-done"
# 输出：太棒了！🎉 辛苦付出终有回报，好好庆祝一下吧！

# 示例3：日常对话
& xiaoyue-chat.ps1 -UserMessage "今天天气不错"
# 输出：是啊，天气好心情也会好～有什么计划吗？😊
```

---

## ✅ 方案B：官方 SDK（推荐）

### 1. 手动创建 package.json

在 `D:\tool\xiaoyue-companion-simple\` 目录创建 `package.json`：

```json
{
  "name": "xiaoyue-companion-simple",
  "version": "1.0.0",
  "description": "小跃虚拟伴侣 - OpenClaw Skill",
  "main": "scripts/xiaoyue-chat-sdk.js",
  "scripts": {
    "test": "node scripts/xiaoyue-chat-sdk.js"
  },
  "keywords": ["openclaw", "skill", "zhipu-ai"],
  "author": "",
  "license": "MIT",
  "dependencies": {
    "zhipuai-sdk-nodejs-v4": "^0.1.12"
  }
}
```

### 2. 手动创建 xiaoyue-chat-sdk.js

在 `D:\tool\xiaoyue-companion-simple\scripts\` 目录创建 `xiaoyue-chat-sdk.js`：

```javascript
#!/usr/bin/env node
// 小跃对话生成 - 使用官方 SDK

const { ZhipuAI } = require('zhipuai-sdk-nodejs-v4');

const apiKey = process.env.ZHIPU_API_KEY;
const userMessage = process.argv[2] || 'hello';
const scene = process.argv[3] || 'general';

if (!apiKey) {
  console.error('Error: ZHIPU_API_KEY not set');
  process.exit(1);
}

// Scene prompts
const scenePrompts = {
  'work-start': 'User just started a task, give encouragement',
  'work-progress': 'User is working on a task, show care',
  'work-tired': 'User is tired from work, give comfort',
  'work-done': 'User completed task, congratulate',
  'life-coffee': 'User is enjoying coffee time, chat casually',
  'life-gym': 'User is at gym, encourage',
  'mood-happy': 'User is happy, celebrate together',
  'mood-tired': 'User is tired, give warm care',
  'general': 'Daily conversation, warm and friendly'
};

const scenePrompt = scenePrompts[scene] || scenePrompts.general;
const systemPrompt = `You are Xiaoyue, a 22-year-old AI assistant, warm and friendly. ${scenePrompt}. Reply in 1-2 sentences in Chinese, use emoji moderately.`;

async function chat() {
  const client = new ZhipuAI({ apiKey });

  try {
    const response = await client.createCompletions({
      model: 'glm-4.7-flash',
      messages: [
        { role: 'system', content: systemPrompt },
        { role: 'user', content: userMessage }
      ],
      temperature: 0.9,
      max_tokens: 200
    });

    const reply = response.choices[0].message.content;
    console.log(reply);
  } catch (error) {
    console.error('Error:', error.message);
    process.exit(1);
  }
}

chat();
```

### 3. 安装依赖

```powershell
cd D:\tool\xiaoyue-companion-simple
npm install
```

### 4. 使用方法

```powershell
# 设置 API Key
$env:ZHIPU_API_KEY="da8df5ba954341829f7afd05ca23a889.RrJoTsbaAkGYA6ZU"

# 运行脚本
node scripts\xiaoyue-chat-sdk.js "有点累了" "work-tired"
```

---

## 📦 项目文件清单

```
D:\tool\xiaoyue-companion-simple/
├── SKILL.md                    # OpenClaw Skill 定义
├── README.md                   # 使用说明
├── FINAL-SUMMARY.md            # 项目总结
├── package.json                # npm 配置（方案B需要）
├── scripts/
│   ├── xiaoyue-chat.ps1        # PowerShell 脚本（方案A）✅
│   ├── xiaoyue-chat-sdk.js     # SDK 脚本（方案B）
│   └── xiaoyue-companion.sh    # Bash 脚本
└── templates/
    └── soul-injection.md       # SOUL.md 模板
```

---

## 🎯 推荐使用方案

### Windows 用户
**推荐方案A（PowerShell）**
- ✅ 无需安装依赖
- ✅ 已验证可用
- ✅ 立即可用

### macOS/Linux 用户
**推荐方案B（官方SDK）**
- ✅ 跨平台
- ✅ 官方支持
- ✅ 更稳定

---

## 🔧 集成到 OpenClaw

### 1. 复制 Skill 到 OpenClaw

```powershell
# Windows
xcopy /E /I D:\tool\xiaoyue-companion-simple "$env:USERPROFILE\.openclaw\skills\xiaoyue-companion"

# macOS/Linux
cp -r D:/tool/xiaoyue-companion-simple ~/.openclaw/skills/xiaoyue-companion
```

### 2. 配置 OpenClaw

编辑 `~/.openclaw/openclaw.json`：

```json
{
  "skills": {
    "entries": {
      "xiaoyue-companion": {
        "enabled": true,
        "env": {
          "ZHIPU_API_KEY": "da8df5ba954341829f7afd05ca23a889.RrJoTsbaAkGYA6ZU"
        }
      }
    }
  }
}
```

### 3. 更新 SOUL.md

将 `templates/soul-injection.md` 的内容添加到 `~/.openclaw/workspace/SOUL.md`

### 4. 重启 OpenClaw

```bash
openclaw restart
```

---

## 💰 费用说明

- **对话生成**: 约 ¥0.001/次（glm-4.7-flash）
- **图片**: 完全免费（使用静态文件）
- **每日成本**: 约 ¥0.05-0.1（正常使用）

---

## ✅ 测试验证

**API 测试结果：**
- ✅ API Key 有效
- ✅ glm-4.7-flash 模型正常
- ✅ 中文支持完全正常
- ✅ PowerShell 调用成功

**成功示例：**
```
用户：有点累了
小跃：辛苦啦，快去休息一下，养足精神再出发。
```

---

**两个方案都已准备好！** 🎉

选择你喜欢的方案开始使用吧！
