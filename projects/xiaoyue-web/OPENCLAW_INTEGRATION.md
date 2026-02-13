# 🤖 小易 + OpenClaw 集成方案

让小易不仅能聊天，还能控制电脑干活！

## 📋 架构设计

```
手机/浏览器 → 小易 Web 界面 → 小易服务器 → OpenClaw API → 电脑执行任务
```

## 🎯 实现方案

### 方案 1：通过 HTTP API 直接调用（推荐）

**优点**：
- ✅ 简单直接
- ✅ 无需额外配置
- ✅ 适合局域网使用

**实现步骤**：

#### 1. 启动 OpenClaw

```bash
# 确保 OpenClaw 已安装并运行
# 默认端口：8181
```

#### 2. 修改小易服务器，添加 OpenClaw 调用

```javascript
// 新增 OpenClaw API 调用接口
app.post('/api/execute-task', async (req, res) => {
    const { task } = req.body;
    
    try {
        // 调用 OpenClaw API
        const response = await axios.post('http://localhost:8181/api/v1/chat', {
            message: task,
            session_id: 'xiaoyi-session'
        }, {
            headers: {
                'Authorization': 'Bearer YOUR_OPENCLAW_TOKEN'
            }
        });
        
        res.json({
            success: true,
            result: response.data
        });
    } catch (error) {
        res.json({
            success: false,
            error: error.message
        });
    }
});
```

#### 3. 前端识别任务指令

在小易的对话中识别任务关键词：
- "帮我整理文件"
- "打开浏览器搜索..."
- "创建文档..."

---

### 方案 2：通过飞书/钉钉接入（适合手机使用）

**优点**：
- ✅ 手机随时随地控制
- ✅ 支持语音输入
- ✅ 消息推送通知

**架构**：

```
手机飞书/钉钉 → OpenClaw Channel → OpenClaw → 电脑执行 → 结果返回手机
```

#### 配置步骤：

**1. 飞书接入**

```bash
# 1. 访问飞书开放平台
https://open.feishu.cn/

# 2. 创建企业自建应用

# 3. 配置权限
- im:message
- im:message:send_as_bot
- im:chat

# 4. 配置事件订阅
- 接收消息 v2.0

# 5. 获取配置信息
App ID: cli_xxxxx
App Secret: xxxxx
Verification Token: xxxxx
Encrypt Key: xxxxx
```

**2. OpenClaw 配置**

编辑 `~/.openclaw/openclaw.json`:

```json
{
  "channels": {
    "feishu": {
      "enabled": true,
      "app_id": "cli_xxxxx",
      "app_secret": "your_app_secret",
      "verification_token": "your_token",
      "encrypt_key": "your_key"
    }
  }
}
```

**3. 重启 OpenClaw**

```bash
# 重启服务
openclaw restart
```

**4. 手机使用**

- 打开飞书
- 找到你的机器人
- 发送消息："帮我整理桌面文件"
- OpenClaw 自动执行并回复结果

---

### 方案 3：小易作为 OpenClaw 的前端界面

**最佳方案**：将小易改造为 OpenClaw 的 Web 前端

#### 实现代码：

```javascript
// server.js 添加 OpenClaw 代理

const OPENCLAW_API = 'http://localhost:8181';
const OPENCLAW_TOKEN = process.env.OPENCLAW_TOKEN;

// 对话接口改为调用 OpenClaw
app.post('/api/chat', async (req, res) => {
    try {
        const { message, sessionId = 'default' } = req.body;
        
        // 判断是否为任务指令
        const isTask = detectTask(message);
        
        if (isTask) {
            // 调用 OpenClaw 执行任务
            const result = await executeOpenClawTask(message);
            res.json({
                success: true,
                message: result.response,
                isTask: true
            });
        } else {
            // 普通对话，调用智谱 AI
            const aiResponse = await callZhipuAI(message);
            res.json({
                success: true,
                message: aiResponse,
                isTask: false
            });
        }
    } catch (error) {
        res.json({
            success: false,
            error: error.message
        });
    }
});

// 检测任务指令
function detectTask(message) {
    const taskKeywords = [
        '帮我', '帮忙', '执行', '运行',
        '打开', '创建', '整理', '搜索',
        '下载', '上传', '发送', '查找'
    ];
    
    return taskKeywords.some(keyword => message.includes(keyword));
}

// 执行 OpenClaw 任务
async function executeOpenClawTask(task) {
    const response = await axios.post(
        `${OPENCLAW_API}/api/v1/chat`,
        {
            message: task,
            session_id: 'xiaoyi'
        },
        {
            headers: {
                'Authorization': `Bearer ${OPENCLAW_TOKEN}`
            }
        }
    );
    
    return response.data;
}
```

---

## 🚀 快速开始

### 步骤 1：确认 OpenClaw 运行

```bash
# 检查 OpenClaw 是否运行
curl http://localhost:8181/api/health

# 应该返回：{"status":"ok"}
```

### 步骤 2：获取 OpenClaw Token

```bash
# 登录获取 token
curl -X POST http://localhost:8181/api/v1/login \
  -d "username=admin" \
  -d "password=your_password"

# 返回：{"token":"your_token_here"}
```

### 步骤 3：配置小易

```bash
# 编辑 .env 文件
cd D:\tool\skill\projects\xiaoyue-web
notepad .env
```

添加：
```env
OPENCLAW_API=http://localhost:8181
OPENCLAW_TOKEN=your_token_here
```

### 步骤 4：重启小易

```bash
# 停止当前服务
taskkill /F /IM node.exe

# 重新启动
npm start
```

---

## 💬 使用示例

### 场景 1：文件管理

```
你：小易，帮我整理桌面文件
小易：好的！正在整理...
      [调用 OpenClaw]
小易：整理完成！共整理了 25 个文件：
      📁 文档 (10个)
      📁 图片 (8个)
      📁 代码 (5个)
      📁 其他 (2个)
```

### 场景 2：浏览器操作

```
你：帮我搜索"OpenClaw 教程"
小易：正在打开浏览器搜索...
      [OpenClaw 打开浏览器并搜索]
小易：已为你打开搜索结果，找到了 10 个相关教程
```

### 场景 3：文档创建

```
你：创建一个会议纪要文档
小易：好的，请告诉我会议内容
你：今天讨论了项目进度...
小易：[调用 OpenClaw 创建文档]
      文档已创建：会议纪要_2026-02-12.md
      保存位置：D:\Documents\
```

---

## 📱 手机远程控制

### 方案 A：内网穿透（推荐）

使用 frp 或 ngrok 将小易暴露到公网：

```bash
# 使用 ngrok
ngrok http 3001

# 获得公网地址
https://xxxx.ngrok.io
```

手机浏览器访问该地址即可控制电脑！

### 方案 B：飞书机器人

配置飞书 Channel 后，手机飞书直接发消息控制电脑。

---

## 🔒 安全建议

1. **Token 认证**：必须配置 OPENCLAW_TOKEN
2. **IP 白名单**：限制只允许特定 IP 访问
3. **HTTPS**：生产环境使用 HTTPS
4. **权限控制**：限制可执行的任务类型

---

## 🎯 下一步

我可以帮你：

1. ✅ 修改小易服务器，集成 OpenClaw API
2. ✅ 添加任务指令识别
3. ✅ 配置飞书/钉钉 Channel
4. ✅ 设置内网穿透实现远程控制

**你想先实现哪个方案？**

---

Made with ❤️ by anbeime | 2026-02-12
