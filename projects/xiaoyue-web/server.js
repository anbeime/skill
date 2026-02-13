const express = require('express');
const cors = require('cors');
const axios = require('axios');
const { exec } = require('child_process');
const { promisify } = require('util');
const execPromise = promisify(exec);
require('dotenv').config();

const app = express();
const PORT = process.env.PORT || 3000;

app.use(cors());
app.use(express.json());
app.use(express.static('public'));

// 智谱 AI 配置
const ZHIPU_API_KEY = process.env.ZHIPU_API_KEY;
const ZHIPU_API_BASE = 'https://open.bigmodel.cn/api/paas/v4';

// OpenClaw 配置
const OPENCLAW_CLI = process.env.OPENCLAW_CLI || 'D:\\openclaw\\npm-global\\node_modules\\openclaw\\dist\\index.js';
const OPENCLAW_NODE = process.env.OPENCLAW_NODE || 'C:\\Users\\ASUS\\.stepfun\\runtimes\\node\\install_1770628825604_th45cs96cig\\node-v22.18.0-win-x64\\node.exe';
const OPENCLAW_ENABLED = process.env.OPENCLAW_ENABLED === 'true';

// 对话历史存储
const conversations = new Map();

// 根据对话内容选择合适的照片（随机返回，更真实）
function selectPhoto(message) {
    // 直接随机返回16张照片中的一张
    const randomId = Math.floor(Math.random() * 16) + 1;
    console.log(`随机选择照片: ren${randomId}.png`);
    return `xiaoyi-photos/ren${randomId}.png`;
}

// 检测是否为任务指令
function detectTask(message) {
    const taskKeywords = [
        '帮我', '帮忙', '执行', '运行', '操作',
        '打开浏览器', '打开文件', '创建文档', '创建', '整理', '搜索', '查找',
        '下载', '上传', '发送邮件', '删除', '移动',
        '复制', '粘贴', '截图', '录屏'
    ];
    
    // 排除照片相关的请求
    if (message.includes('照片') || message.includes('图片') || message.includes('自拍')) {
        return false;
    }
    
    return taskKeywords.some(keyword => message.includes(keyword));
}

// 执行 OpenClaw 任务
async function executeOpenClawTask(task) {
    if (!OPENCLAW_ENABLED) {
        return {
            success: false,
            message: 'OpenClaw 未启用'
        };
    }
    
    try {
        // 使用 OpenClaw agent 命令执行任务
        const command = `"${OPENCLAW_NODE}" "${OPENCLAW_CLI}" agent --local "${task.replace(/"/g, '\\"')}"`;
        
        console.log('执行 OpenClaw 命令:', command);
        
        const { stdout, stderr } = await execPromise(command, {
            timeout: 60000, // 60秒超时
            maxBuffer: 1024 * 1024, // 1MB buffer
            windowsHide: true
        });
        
        if (stderr && !stderr.includes('warning') && !stderr.includes('info')) {
            console.error('OpenClaw stderr:', stderr);
        }
        
        // 清理输出，移除 ANSI 颜色代码
        const cleanOutput = stdout
            .replace(/\x1b\[[0-9;]*m/g, '') // 移除 ANSI 颜色
            .replace(/[\u001b\u009b][[()#;?]*(?:[0-9]{1,4}(?:;[0-9]{0,4})*)?[0-9A-ORZcf-nqry=><]/g, '')
            .trim();
        
        const result = cleanOutput || '任务执行完成';
        
        return {
            success: true,
            message: result
        };
    } catch (error) {
        console.error('OpenClaw task error:', error);
        return {
            success: false,
            message: `任务执行失败：${error.message || '未知错误'}`
        };
    }
}

// 生成对话
app.post('/api/chat', async (req, res) => {
    try {
        const { message, sessionId = 'default' } = req.body;
        
        if (!ZHIPU_API_KEY) {
            return res.json({
                success: false,
                error: '请配置 ZHIPU_API_KEY 环境变量'
            });
        }

        // 检测是否为任务指令
        const isTask = detectTask(message);
        
        if (isTask && OPENCLAW_ENABLED) {
            // 执行 OpenClaw 任务
            const taskResult = await executeOpenClawTask(message);
            
            return res.json({
                success: taskResult.success,
                message: taskResult.message,
                isTask: true,
                needImage: false
            });
        }

        // 获取或创建对话历史
        if (!conversations.has(sessionId)) {
            conversations.set(sessionId, []);
        }
        const history = conversations.get(sessionId);

        // 添加用户消息
        history.push({
            role: 'user',
            content: message
        });

        // 调用智谱 AI
        const response = await axios.post(
            `${ZHIPU_API_BASE}/chat/completions`,
            {
                model: 'glm-4-flash',
                messages: [
                    {
                        role: 'system',
                        content: `你是小易，一个温暖友善的 AI 伴侣。
性格特点：
- 活泼开朗，适度使用 emoji（不要过多）
- 善于倾听，关心用户
- 会主动分享自己的"生活"
- 说话简洁，2-3句话为主

${OPENCLAW_ENABLED ? '你还可以帮用户执行电脑任务，当用户说"帮我"、"帮忙"等词时，你会协助完成任务。' : ''}

当用户要求看照片时，你只需要说"好的，稍等一下～"或类似简短回复即可，系统会自动显示你的照片，不要说"生成图片"之类的话。`
                    },
                    ...history.slice(-10) // 保留最近10轮对话
                ],
                temperature: 0.8,
                top_p: 0.7
            },
            {
                headers: {
                    'Authorization': `Bearer ${ZHIPU_API_KEY}`,
                    'Content-Type': 'application/json'
                }
            }
        );

        const aiMessage = response.data.choices[0].message.content;
        
        // 添加AI回复到历史
        history.push({
            role: 'assistant',
            content: aiMessage
        });

        // 检测是否需要生成图片
        const needImage = message.includes('照片') || 
                         message.includes('图片') || 
                         message.includes('看看') ||
                         message.includes('发张') ||
                         message.includes('自拍') ||
                         message.includes('你在') ||
                         message.includes('现在');

        // 如果需要图片，选择合适的照片
        let selectedPhoto = null;
        if (needImage) {
            selectedPhoto = selectPhoto(message);
        }

        res.json({
            success: true,
            message: aiMessage,
            needImage: needImage,
            photoUrl: selectedPhoto,
            isTask: false
        });

    } catch (error) {
        console.error('Chat error:', error.response?.data || error.message);
        res.json({
            success: false,
            error: error.response?.data?.error?.message || '对话失败，请稍后重试'
        });
    }
});

// 生成图片（使用预设照片，根据场景智能匹配）
app.post('/api/generate-image', async (req, res) => {
    try {
        const { prompt, scene = 'coffee-shop' } = req.body;

        // 场景到照片ID的映射（更详细的匹配规则）
        const scenePhotoMap = {
            'coffee-shop': 5,  // 咖啡照片
            'office': 2,       // 工作照片
            'home': 16,        // 默认/居家照片
            'gym': 7,          // 运动照片
            'park': 13         // 户外照片
        };

        // 如果有 prompt，根据关键词智能匹配
        let photoUrl;
        if (prompt) {
            photoUrl = selectPhoto(prompt);
            console.log(`根据提示词 "${prompt}" 智能匹配照片: ${photoUrl}`);
        } else {
            // 否则使用场景映射
            const photoId = scenePhotoMap[scene] || scenePhotoMap['coffee-shop'];
            photoUrl = `xiaoyi-photos/ren${photoId}.png`;
            console.log(`场景 "${scene}" 使用预设照片: ${photoUrl}`);
        }

        res.json({
            success: true,
            imageUrl: photoUrl,
            scene: scene,
            source: 'preset'
        });

    } catch (error) {
        console.error('Image generation error:', error.message);
        res.json({
            success: false,
            error: '图片加载失败，请稍后重试'
        });
    }
});

// 语音合成（TTS）
app.post('/api/tts', async (req, res) => {
    try {
        const { text } = req.body;

        if (!text) {
            return res.json({
                success: false,
                error: '缺少文本内容'
            });
        }

        // 使用浏览器端 Web Speech API，服务器端只返回文本
        // 如果需要服务器端生成音频，可以集成 Edge-TTS 或其他 TTS 服务
        res.json({
            success: true,
            text: text,
            useClientTTS: true // 标记使用客户端 TTS
        });

    } catch (error) {
        console.error('TTS error:', error.message);
        res.json({
            success: false,
            error: '语音合成失败'
        });
    }
});

// 健康检查
app.get('/api/health', (req, res) => {
    res.json({
        status: 'ok',
        hasApiKey: !!ZHIPU_API_KEY,
        openclawEnabled: OPENCLAW_ENABLED,
        openclawConfigured: !!(OPENCLAW_CLI && OPENCLAW_NODE)
    });
});

app.listen(PORT, () => {
    console.log(`🚀 小易伴侣服务器运行在 http://localhost:${PORT}`);
    console.log(`📝 API Key 状态: ${ZHIPU_API_KEY ? '✅ 已配置' : '❌ 未配置'}`);
    console.log(`🤖 OpenClaw 集成: ${OPENCLAW_ENABLED ? '✅ 已启用' : '❌ 未启用'}`);
    if (OPENCLAW_ENABLED) {
        console.log(`   - CLI 路径: ${OPENCLAW_CLI}`);
        console.log(`   - Node 路径: ${OPENCLAW_NODE}`);
    }
});
