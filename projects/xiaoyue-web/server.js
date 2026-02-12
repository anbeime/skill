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

// 对话历史存储
const conversations = new Map();

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
            needImage: needImage
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
        hasApiKey: !!ZHIPU_API_KEY
    });
});

app.listen(PORT, () => {
    console.log(`🚀 小易伴侣服务器运行在 http://localhost:${PORT}`);
    console.log(`📝 API Key 状态: ${ZHIPU_API_KEY ? '✅ 已配置' : '❌ 未配置'}`);
});
