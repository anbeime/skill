const express = require('express');
const cors = require('cors');
const axios = require('axios');
const path = require('path');
const fs = require('fs');
const { spawn } = require('child_process');
require('dotenv').config();
const {
    resolveMiniMaxConfig,
    postMiniMaxChatCompletion,
} = require('./lib/minimax-chat');

const app = express();
const PORT = process.env.PORT || 3000;

app.use(cors());
app.use(express.json());

// 静态文件服务
const publicPath = path.join(__dirname, 'public');
app.use(express.static(publicPath));

// MiniMax configuration
const MINIMAX_DEFAULT_CONFIG = resolveMiniMaxConfig();

// OpenClaw 配置 - 硬编码配置
const OPENCLAW_ENABLED = true;  // 强制启用
const OPENCLAW_API = 'http://127.0.0.1:18789';
const OPENCLAW_TOKEN = 'a8351b767e724cf1924a4f9565b8b476.ATNkJF3bScIStuhe';
const OPENCLAW_WORKSPACE = 'C:\\Users\\13632\\.openclaw\\workspace';

// 对话历史存储
const conversations = new Map();

// 检查 OpenClaw 是否运行
async function checkOpenClawHealth() {
    if (!OPENCLAW_ENABLED) return false;
    
    try {
        const response = await axios.get(`${OPENCLAW_API}/health`, {
            timeout: 3000
        });
        return response.status === 200;
    } catch (error) {
        console.log('[OpenClaw] Health check failed:', error.message);
        return false;
    }
}

// 执行 OpenClaw 任务
async function executeOpenClawTask(task, sessionId = 'xiaoyi-session') {
    if (!OPENCLAW_ENABLED || !OPENCLAW_TOKEN) {
        return {
            success: false,
            message: 'OpenClaw 未启用或未配置 Token'
        };
    }
    
    // 检查 OpenClaw 是否运行
    const isRunning = await checkOpenClawHealth();
    if (!isRunning) {
        return {
            success: false,
            message: 'OpenClaw 网关未运行，请先启动：openclaw gateway'
        };
    }
    
    try {
        console.log('[OpenClaw] Executing task:', task);
        
        // 调用 OpenClaw API
        const response = await axios.post(
            `${OPENCLAW_API}/api/v1/chat`,
            {
                message: task,
                session_id: sessionId,
                workspace: OPENCLAW_WORKSPACE
            },
            {
                headers: {
                    'Authorization': `Bearer ${OPENCLAW_TOKEN}`,
                    'Content-Type': 'application/json'
                },
                timeout: 120000 // 2分钟超时
            }
        );
        
        console.log('[OpenClaw] Task completed:', response.data);
        
        return {
            success: true,
            result: response.data.response || response.data.message || '任务执行完成',
            data: response.data
        };
    } catch (error) {
        console.error('[OpenClaw] Task failed:', error.message);
        return {
            success: false,
            message: error.response?.data?.error || error.message,
            error: error.message
        };
    }
}

// 检测是否为任务指令
function detectTask(message) {
    const taskKeywords = [
        '帮我', '帮忙', '执行', '运行', '操作',
        '打开浏览器', '打开文件', '创建文档', '创建', '整理', '搜索', '查找',
        '下载', '上传', '发送邮件', '删除', '移动',
        '复制', '粘贴', '截图', '录屏', '新建',
        '编辑', '修改', '重命名', '压缩', '解压',
        '播放', '暂停', '停止', '音量', '亮度',
        '关机', '重启', '锁屏', '解锁'
    ];
    
    // 排除照片相关的请求
    if (message.includes('照片') || message.includes('图片') || message.includes('自拍')) {
        return false;
    }
    
    return taskKeywords.some(keyword => message.includes(keyword));
}

// 根据对话内容选择照片
function selectPhoto(message) {
    const randomId = Math.floor(Math.random() * 16) + 1;
    const photoUrl = `xiaoyi-photos/ren${randomId}.png`;
    console.log(`[Photo] 选择照片: ${photoUrl}`);
    return photoUrl;
}

// 小易人设提示词
const XIAOYI_PERSONA = `你是小易（知易），一个融合中国传统文化与现代科技的AI助手。
你的形象是：头戴传统官帽，帽上有"知易"二字（蓝色发光），红黑金配色。

人设特点：
1. 引用古语典故（如"一张一弛，文武之道"）
2. 使用传统意象（茶、古今智慧）
3. 体现中国文化底蕴
4. 语气亲切自然，适度使用 emoji（🍵 ✨）
5. 给予实用建议

回复要求：
- 用 1-2 句话回复
- 使用中文
- 适度使用 emoji
- 体现传统文化元素`;

// API 路由
app.post('/api/chat', async (req, res) => {
    try {
        const { message, sessionId = 'default', apiKey, model, region } = req.body;
        const chatConfig = resolveMiniMaxConfig({ apiKey, modelId: model, region });
        
        if (!chatConfig.apiKey) {
            return res.json({
                success: false,
                error: 'Please configure the MiniMax API key or provide apiKey in the request'
            });
        }
        
        // 获取或创建对话历史
        if (!conversations.has(sessionId)) {
            conversations.set(sessionId, []);
        }
        const history = conversations.get(sessionId);
        
        // 检测是否为任务指令
        const isTask = detectTask(message);
        let taskResult = null;
        
        // 如果是任务指令且 OpenClaw 启用，先执行 OpenClaw 任务
        if (isTask && OPENCLAW_ENABLED) {
            console.log('[Task] Detected task:', message);
            taskResult = await executeOpenClawTask(message, sessionId);
            console.log('[Task] Result:', taskResult);
        }
        
        // 构建消息
        const messages = [
            { role: 'system', content: XIAOYI_PERSONA },
            ...history.slice(-10)
        ];
        
        // 如果有任务结果，添加到上下文
        if (taskResult && taskResult.success) {
            messages.push({ 
                role: 'system', 
                content: `用户请求执行电脑任务，任务执行结果：${taskResult.result}` 
            });
        }
        
        messages.push({ role: 'user', content: message });
        
        // Call MiniMax chat completions
        const { response } = await postMiniMaxChatCompletion({
            ...chatConfig,
            messages: messages,
            temperature: 0.9,
            max_tokens: 200
        });
        
        const reply = response.data.choices?.[0]?.message?.content || '抱歉，我没有收到有效的回复';
        
        // 更新对话历史
        history.push({ role: 'user', content: message });
        history.push({ role: 'assistant', content: reply });
        
        // 检测是否需要发送照片
        const shouldSendPhoto = message.includes('照片') || message.includes('图片') || 
                               message.includes('自拍') || message.includes('你在做什么') ||
                               message.includes('在干嘛');
        
        res.json({
            success: true,
            message: reply,
            reply: reply,
            photo: shouldSendPhoto ? selectPhoto(message) : null,
            photoUrl: shouldSendPhoto ? selectPhoto(message) : null,
            needImage: shouldSendPhoto,
            isTask: isTask,
            taskResult: taskResult,
            openclawEnabled: OPENCLAW_ENABLED,
            openclawRunning: taskResult !== null
        });
        
    } catch (error) {
        console.error('[Chat] Error:', error.message);
        res.json({
            success: false,
            error: error.response?.data?.error?.message || error.message,
            message: error.response?.data?.error?.message || '服务暂时不可用'
        });
    }
});

// OpenClaw 状态检查
app.get('/api/openclaw/status', async (req, res) => {
    const isRunning = await checkOpenClawHealth();
    res.json({
        enabled: OPENCLAW_ENABLED,
        running: isRunning,
        api: OPENCLAW_API,
        workspace: OPENCLAW_WORKSPACE
    });
});

// 健康检查
app.get('/health', (req, res) => {
    res.json({
        status: 'ok',
        timestamp: new Date().toISOString(),
        provider: MINIMAX_DEFAULT_CONFIG.providerName,
        model: MINIMAX_DEFAULT_CONFIG.modelId,
        region: MINIMAX_DEFAULT_CONFIG.region,
        apiKeyConfigured: !!MINIMAX_DEFAULT_CONFIG.apiKey,
        openclawEnabled: OPENCLAW_ENABLED,
        openclawApi: OPENCLAW_API
    });
});

// 启动服务器
app.listen(PORT, () => {
    console.log(`========================================`);
    console.log(`🎭 小易伴侣服务器已启动！`);
    console.log(`📍 访问地址: http://localhost:${PORT}`);
    console.log(`🎤 语音版: http://localhost:${PORT}/voice.html`);
    console.log(`========================================`);
    console.log(`🤖 OpenClaw 集成: ${OPENCLAW_ENABLED ? '✅ 已启用' : '❌ 未启用'}`);
    if (OPENCLAW_ENABLED) {
        console.log(`   - API 地址: ${OPENCLAW_API}`);
        console.log(`   - Token: ${OPENCLAW_TOKEN ? '✅ 已配置' : '❌ 未配置'}`);
        console.log(`   - 工作区: ${OPENCLAW_WORKSPACE}`);
        console.log(`   💡 提示: 请确保 OpenClaw 网关正在运行`);
        console.log(`      启动命令: openclaw gateway`);
        console.log(`      控制台: ${OPENCLAW_API}/`);
    }
    console.log(`========================================`);
});

// 检查 OpenClaw 状态
if (OPENCLAW_ENABLED) {
    setTimeout(async () => {
        const isRunning = await checkOpenClawHealth();
        if (!isRunning) {
            console.log('\n⚠️  警告: OpenClaw 网关未运行！');
            console.log('   请运行: openclaw gateway');
            console.log('   或在另一个终端窗口启动 OpenClaw 网关\n');
        } else {
            console.log('\n✅ OpenClaw 网关运行正常！\n');
        }
    }, 2000);
}
