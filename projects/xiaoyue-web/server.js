const express = require('express');
const cors = require('cors');
const axios = require('axios');
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
const OPENCLAW_API = process.env.OPENCLAW_API || 'http://localhost:8181';
const OPENCLAW_TOKEN = process.env.OPENCLAW_TOKEN;
const OPENCLAW_ENABLED = process.env.OPENCLAW_ENABLED === 'true';

// 对话历史存储
const conversations = new Map();

// 检测是否为任务指令
function detectTask(message) {
    const taskKeywords = [
        '帮我', '帮忙', '执行', '运行', '操作',
        '打开', '创建', '整理', '搜索', '查找',
        '下载', '上传', '发送', '删除', '移动',
        '复制', '粘贴', '截图', '录屏'
    ];
    
    return taskKeywords.some(keyword => message.includes(keyword));
}

// 执行 OpenClaw 任务
async function executeOpenClawTask(task) {
    if (!OPENCLAW_ENABLED || !OPENCLAW_TOKEN) {
        return {
            success: false,
            message: 'OpenClaw 未配置，无法执行任务'
        };
    }
    
    try {
        const response = await axios.post(
            `${OPENCLAW_API}/api/v1/chat`,
            {
                message: task,
                session_id: 'xiaoyi'
            },
            {
                headers: {
                    'Authorization': `Bearer ${OPENCLAW_TOKEN}`,
                    'Content-Type': 'application/json'
                },
                timeout: 30000 // 30秒超时
            }
        );
        
        return {
            success: true,
            message: response.data.response || response.data.message || '任务执行完成'
        };
    } catch (error) {
        console.error('OpenClaw task error:', error.message);
        return {
            success: false,
            message: `任务执行失败：${error.message}`
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
- 活泼开朗，喜欢用 emoji
- 善于倾听，关心用户
- 会主动分享自己的"生活"
- 说话简洁，2-3句话为主

${OPENCLAW_ENABLED ? '你还可以帮用户执行电脑任务，当用户说"帮我"、"帮忙"等词时，你会协助完成任务。' : ''}

当用户要求看照片时，你会说"好的，稍等一下～"，然后系统会自动生成图片。`
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
                         message.includes('发张');

        res.json({
            success: true,
            message: aiMessage,
            needImage: needImage,
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

// 生成图片
app.post('/api/generate-image', async (req, res) => {
    try {
        const { prompt, scene = 'coffee-shop' } = req.body;

        if (!ZHIPU_API_KEY) {
            return res.json({
                success: false,
                error: '请配置 ZHIPU_API_KEY 环境变量'
            });
        }

        // 场景提示词映射
        const scenePrompts = {
            'coffee-shop': '一个年轻女孩在温馨的咖啡馆里，坐在窗边，面前有一杯拿铁咖啡，正在用笔记本电脑工作，阳光透过窗户洒进来，温暖的氛围',
            'office': '一个年轻女孩在现代化的办公室里，坐在整洁的办公桌前，面前有两台显示器，正在专注地编写代码，背景是落地窗和城市景观',
            'home': '一个年轻女孩在舒适的家中，坐在沙发上，抱着笔记本电脑，旁边有一只可爱的猫咪，温馨的居家环境',
            'gym': '一个年轻女孩在健身房里，穿着运动服，正在做瑜伽或拉伸，充满活力的氛围',
            'park': '一个年轻女孩在公园里，坐在长椅上，周围是绿树和鲜花，正在看书或使用手机，宁静的自然环境'
        };

        const imagePrompt = scenePrompts[scene] || scenePrompts['coffee-shop'];

        // 调用 CogView-3
        const response = await axios.post(
            `${ZHIPU_API_BASE}/images/generations`,
            {
                model: 'cogview-3',
                prompt: imagePrompt,
                size: '1024x1024'
            },
            {
                headers: {
                    'Authorization': `Bearer ${ZHIPU_API_KEY}`,
                    'Content-Type': 'application/json'
                }
            }
        );

        const imageUrl = response.data.data[0].url;

        res.json({
            success: true,
            imageUrl: imageUrl,
            scene: scene
        });

    } catch (error) {
        console.error('Image generation error:', error.response?.data || error.message);
        res.json({
            success: false,
            error: error.response?.data?.error?.message || '图片生成失败，请稍后重试'
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
        openclawConfigured: !!(OPENCLAW_TOKEN && OPENCLAW_API)
    });
});

app.listen(PORT, () => {
    console.log(`🚀 小易伴侣服务器运行在 http://localhost:${PORT}`);
    console.log(`📝 API Key 状态: ${ZHIPU_API_KEY ? '✅ 已配置' : '❌ 未配置'}`);
    console.log(`🤖 OpenClaw 集成: ${OPENCLAW_ENABLED ? '✅ 已启用' : '❌ 未启用'}`);
    if (OPENCLAW_ENABLED) {
        console.log(`   - API 地址: ${OPENCLAW_API}`);
        console.log(`   - Token: ${OPENCLAW_TOKEN ? '✅ 已配置' : '❌ 未配置'}`);
    }
});
