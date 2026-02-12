# 小跃虚拟伴侣 Skill - 最终简化方案

## 🎯 设计思路

参考 Clawra 的简单设计：
- **Clawra**: fal.ai 生图 + 飞书发送
- **小跃**: 智谱 AI 对话 + 静态图片 + 飞书发送

## 📁 最简项目结构

```
xiaoyue-companion/
├── SKILL.md              # Skill 定义（OpenClaw 读取）
├── scripts/
│   └── chat.js           # 对话脚本（调用 glm-4.7-flash）
└── assets/
    └── default.jpg       # 默认图片
```

## 💡 核心实现

### 1. SKILL.md（告诉 OpenClaw 如何使用）

```markdown
# Xiaoyue Companion Skill

为 OpenClaw 添加温暖的陪伴对话能力。

## 使用场景

当用户：
- 说"有点累"时，回复鼓励的话
- 执行任务时，主动关心进度
- 需要陪伴时，发送温暖消息

## 调用方式

\`\`\`bash
node scripts/chat.js "用户消息"
\`\`\`

## 环境变量

- `ZHIPU_API_KEY`: 智谱 AI API Key
```

### 2. scripts/chat.js（核心逻辑）

```javascript
// 简单的对话脚本
const axios = require('axios');

const apiKey = process.env.ZHIPU_API_KEY;
const userMessage = process.argv[2] || '你好';

async function chat() {
  const response = await axios.post(
    'https://open.bigmodel.cn/api/paas/v4/chat/completions',
    {
      model: 'glm-4.7-flash',
      messages: [
        { role: 'system', content: '你是小跃，一个温暖友善的 AI 助手' },
        { role: 'user', content: userMessage }
      ]
    },
    {
      headers: {
        'Authorization': `Bearer ${apiKey}`,
        'Content-Type': 'application/json'
      }
    }
  );
  
  console.log(response.data.choices[0].message.content);
}

chat();
```

## ✅ 优势

1. **极简设计** - 只有 2 个文件
2. **无需编译** - 直接运行 JS
3. **易于理解** - 代码不到 30 行
4. **参考 Clawra** - 遵循相同模式

## 🚫 我之前的问题

- ❌ 过度设计（TypeScript + 多个模块）
- ❌ 重新发明轮子（自己写框架）
- ❌ 忽略现有项目结构

## ✅ 正确做法

- ✅ 参考 Clawra 的简单设计
- ✅ 只做必要的修改（fal.ai → 智谱 AI）
- ✅ 保持 OpenClaw Skill 的标准结构

---

**你说得对！我应该先看看 Clawra 怎么做的，然后照着改。**

需要我：
A. 克隆 Clawra 项目，直接在上面改
B. 创建一个最简版本（参考上面的结构）
C. 其他建议
