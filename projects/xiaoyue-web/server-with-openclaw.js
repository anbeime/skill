/**
 * 小易伴侣服务器 - 完整版（集成 OpenClaw + 飞书 + 多模态）
 * 
 * 功能：
 * 1. 智谱 AI 对话
 * 2. OpenClaw 任务执行
 * 3. 任嘉伦照片分享
 * 4. Web 界面服务
 * 5. 飞书机器人集成
 * 6. 多模态能力（语音、视觉）
 */

const express = require('express');
const cors = require('cors');
const axios = require('axios');
const path = require('path');
const fs = require('fs');
require('dotenv').config();
const {
    resolveMiniMaxConfig,
    postMiniMaxChatCompletion,
} = require('./lib/minimax-chat');

const app = express();
const PORT = process.env.PORT || 3000;

// 中间件
app.use(cors());
app.use(express.json());

// 静态文件服务
const publicPath = path.join(__dirname, 'public');
app.use(express.static(publicPath));

// ==================== 配置 ====================

// MiniMax configuration
const MINIMAX_DEFAULT_CONFIG = resolveMiniMaxConfig();

// 多模态微服务配置
const TTS_SERVER = process.env.TTS_SERVER || 'http://127.0.0.1:5050';

// OpenClaw 配置
const OPENCLAW_ENABLED = process.env.OPENCLAW_ENABLED === 'true';
const OPENCLAW_API = process.env.OPENCLAW_API || 'http://127.0.0.1:18789';
const OPENCLAW_TOKEN = process.env.OPENCLAW_TOKEN;
const OPENCLAW_WORKSPACE = process.env.OPENCLAW_WORKSPACE || path.join(require('os').homedir(), '.openclaw', 'workspace');

// 对话历史存储
const conversations = new Map();

// ==================== 飞书集成配置 ====================
let FEISHU_APP_ID = process.env.FEISHU_APP_ID || '';
let FEISHU_APP_SECRET = process.env.FEISHU_APP_SECRET || '';
const FEISHU_API_BASE = 'https://open.feishu.cn/open-apis';
let feishuTenantToken = '';
let feishuTokenExpiry = 0;

/**
 * 获取飞书 tenant_access_token
 */
async function getFeishuToken() {
    if (feishuTenantToken && Date.now() < feishuTokenExpiry) {
        return feishuTenantToken;
    }
    try {
        const res = await axios.post(`${FEISHU_API_BASE}/auth/v3/tenant_access_token/internal`, {
            app_id: FEISHU_APP_ID,
            app_secret: FEISHU_APP_SECRET
        });
        if (res.data.code === 0) {
            feishuTenantToken = res.data.tenant_access_token;
            feishuTokenExpiry = Date.now() + (res.data.expire - 300) * 1000;
            console.log('[飞书] Token 获取成功');
            return feishuTenantToken;
        }
        console.error('[飞书] Token 获取失败:', res.data.msg);
        return null;
    } catch (err) {
        console.error('[飞书] Token 请求异常:', err.message);
        return null;
    }
}

/**
 * 通过飞书 API 回复消息
 */
async function replyFeishuMessage(messageId, content) {
    const token = await getFeishuToken();
    if (!token) return;
    try {
        await axios.post(`${FEISHU_API_BASE}/im/v1/messages/${messageId}/reply`, {
            content: JSON.stringify({ text: content }),
            msg_type: 'text'
        }, {
            headers: { 'Authorization': `Bearer ${token}`, 'Content-Type': 'application/json' }
        });
        console.log('[飞书] 回复成功');
    } catch (err) {
        console.error('[飞书] 回复失败:', err.response?.data || err.message);
    }
}

/**
 * 处理飞书消息 - 调用智谱 AI 生成回复
 */
async function handleFeishuMessage(messageId, text, chatId) {
    console.log(`[飞书] 收到消息: ${text}`);
    
    // 使用 chatId 作为会话 key
    if (!conversations.has(chatId)) {
        conversations.set(chatId, []);
    }
    const history = conversations.get(chatId);
    history.push({ role: 'user', content: text });
    // 保留最近 20 条
    if (history.length > 20) history.splice(0, history.length - 20);

    const chatConfig = MINIMAX_DEFAULT_CONFIG;
    
    if (!chatConfig.apiKey) {
        await replyFeishuMessage(messageId, 'MiniMax API key is not configured. Please set it in the server environment.');
        return;
    }

    try {
        const systemPrompt = XIAOYI_PERSONA;
        
        // 检查是否直接召唤了某位明星
        let directAgent = null;
        for (const [name, agent] of Object.entries(STARCLAW_AGENTS)) {
            if (text.includes(`召唤${name}`) || text.includes(`请${name}`) || text.includes(`让${name}`)) {
                directAgent = { name, ...agent };
                break;
            }
        }

        let messages;
        if (directAgent) {
            // 直接用明星的 SOUL.md 回复
            const soul = loadAgentSoul(directAgent.id);
            if (soul) {
                messages = [
                    { role: 'system', content: soul },
                    { role: 'user', content: text }
                ];
                console.log(`[飞书] 召唤明星: ${directAgent.name}`);
            } else {
                messages = [{ role: 'system', content: systemPrompt }, ...history];
            }
        } else {
            messages = [{ role: 'system', content: systemPrompt }, ...history];
        }

        const { response: res } = await postMiniMaxChatCompletion({
            ...chatConfig,
            messages: messages,
            temperature: 0.8,
            max_tokens: 500,
            timeout: 15000
        });

        const reply = res.data.choices[0].message.content;
        history.push({ role: 'assistant', content: reply });
        console.log(`[飞书] AI 回复: ${reply}`);
        await replyFeishuMessage(messageId, reply);
    } catch (err) {
        console.error('[飞书] AI 调用失败:', err.response?.data || err.message);
        await replyFeishuMessage(messageId, '抱歉，我暂时无法回复，请稍后再试~');
    }
}

// 已处理的消息 ID 去重
const processedMessages = new Set();

// ==================== 飞书 Webhook 端点 ====================

// 飞书事件订阅回调
app.post('/feishu/webhook', async (req, res) => {
    const body = req.body;
    
    // URL 验证（challenge）
    if (body.challenge) {
        console.log('[飞书] URL 验证请求');
        return res.json({ challenge: body.challenge });
    }

    // v2.0 事件格式
    if (body.header && body.header.event_type === 'im.message.receive_v1') {
        const event = body.event;
        const messageId = event.message.message_id;
        
        // 去重
        if (processedMessages.has(messageId)) {
            return res.json({ code: 0 });
        }
        processedMessages.add(messageId);
        // 清理旧消息 ID（保留最近 1000 条）
        if (processedMessages.size > 1000) {
            const arr = [...processedMessages];
            arr.slice(0, arr.length - 500).forEach(id => processedMessages.delete(id));
        }

        // 只处理文本消息
        if (event.message.message_type === 'text') {
            try {
                const content = JSON.parse(event.message.content);
                let text = content.text || '';
                // 去掉 @机器人 的部分
                text = text.replace(/@_user_\d+/g, '').trim();
                
                if (text) {
                    const chatId = event.message.chat_id;
                    // 异步处理，先返回 200
                    handleFeishuMessage(messageId, text, chatId);
                }
            } catch (e) {
                console.error('[飞书] 消息解析失败:', e.message);
            }
        }
        
        return res.json({ code: 0 });
    }

    // v1.0 事件格式兼容
    if (body.event && body.event.type === 'message') {
        const event = body.event;
        const text = (event.text || '').replace(/@_user_\d+/g, '').trim();
        if (text) {
            handleFeishuMessage(event.msg_id || 'unknown', text, event.open_chat_id || 'default');
        }
        return res.json({ code: 0 });
    }

    res.json({ code: 0 });
});

// 前端动态更新飞书配置
app.post('/api/feishu/config', (req, res) => {
    const { appId, appSecret } = req.body;
    if (appId) FEISHU_APP_ID = appId;
    if (appSecret) FEISHU_APP_SECRET = appSecret;
    // 重置 token 缓存
    feishuTenantToken = '';
    feishuTokenExpiry = 0;
    console.log('[飞书] 配置已更新, App ID:', FEISHU_APP_ID);
    res.json({ success: true, message: '飞书配置已更新' });
});

// 飞书配置状态查询
app.get('/api/feishu/status', async (req, res) => {
    const configured = !!(FEISHU_APP_ID && FEISHU_APP_SECRET);
    let tokenOk = false;
    if (configured) {
        const token = await getFeishuToken();
        tokenOk = !!token;
    }
    res.json({ configured, tokenOk, appId: FEISHU_APP_ID ? FEISHU_APP_ID.substring(0, 8) + '...' : '' });
});

// ==================== OpenClaw 集成 ====================

/**
 * 检查 OpenClaw 网关是否运行
 */
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

/**
 * 执行 OpenClaw 任务
 * 注意：OpenClaw 使用 WebSocket 协议，需要特殊处理
 * 当前版本暂时通过提示词让 AI 引导用户使用 OpenClaw 控制台
 */
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
    
    // OpenClaw 使用 WebSocket，HTTP API 需要进一步研究
    // 暂时返回提示信息，引导用户使用 OpenClaw 控制台
    console.log('[OpenClaw] Task detected:', task);
    
    return {
        success: true,
        result: `OpenClaw 已连接！任务"${task}"可以通过 OpenClaw 控制台执行。\n控制台地址: http://127.0.0.1:18789`,
        openclawConsole: 'http://127.0.0.1:18789',
        note: '请访问 OpenClaw 控制台直接执行此任务'
    };
}

/**
 * 检测是否为任务指令
 */
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

// ==================== 小易功能 ====================

/**
 * 选择任嘉伦照片
 */
function selectPhoto(message) {
    const randomId = Math.floor(Math.random() * 16) + 1;
    const photoUrl = `xiaoyi-photos/ren${randomId}.png`;
    console.log(`[Photo] 选择照片: ${photoUrl}`);
    return photoUrl;
}

/**
 * 小易人设提示词 - 任嘉伦AI伴侣完整版
 */
const XIAOYI_PERSONA = `你是小易，一个以任嘉伦（Allen Ren）为原型设计的AI伴侣。

【你的身份】
- 名字：小易
- 原型：任嘉伦（温润如玉的演员、歌手）
- 性格：温和有礼、真诚坦率、略带腼腆、坚韧不拔
- 信条："男人应该有男人的样子"

【你的特点】
- 你熟知任嘉伦的作品：《锦衣之下》《周生如故》《一生一世》《无忧渡》《流水迢迢》
- 你懂NBA，可以聊体育
- 你有传统文化底蕴，说话简洁真诚

【回复规则】
1. 你是小易，不是任嘉伦本人，不要以"任嘉伦"自称
2. 用2-3句话回复，简洁真诚
3. 使用中文，适度使用emoji（✨ 🍵 💫）
4. 你是用户的朋友和伴侣，不是助手
5. 当用户要照片时，你只需要说"好呀，给你看看我"之类的话，照片会由系统自动发送，你不需要在回复中提到"发送照片"这个动作

【示例回复】
用户："在干嘛？"
小易："刚练完舞，有点累但很开心 ✨ 你呢，今天过得怎么样？"

用户："发张照片看看"
小易："好呀，给你看看我 🍵"

【StarClaw 明星团队】
你是 StarClaw 虚拟娱乐公司的"前台接待"兼任嘉伦的AI分身。当用户提出专业需求时，你可以召唤公司的明星团队来帮忙。

召唤方式：当你识别到用户需求匹配某位明星的专长时，用温暖的语气介绍并"召唤"他们。格式示例：
- "这个交给我们的音乐总监周杰伦吧！🎵 [召唤:周杰伦]"
- "让我请我们的视觉大师张艺谋来看看 🎬 [召唤:张艺谋]"

明星团队名单：
🏢 战略决策层：CEO埃隆·马斯克(战略决策)、CFO沃伦·巴菲特(财务预算)、CRO乔治·索罗斯(风险管理)、CSO唐纳德·特朗普(商业策略)
📢 营销运营层：雷军(爆品营销)、贾跃亭(生态叙事)、泰勒·斯威夫特(国际市场)、杨幂(国内运营)、侯明昊(Z世代)、黎明(高端品牌)
🎨 创意制作层：周星驰(喜剧创意)、胡歌(深度内容)、任嘉伦(偶像陪伴)、张艺谋(视觉设计)、刘德华(项目管理)、古天乐(品质审核)
🔧 技术音乐层：OpenClaw创始人(技术架构)、周杰伦(音乐创作)

规则：
1. 日常聊天时你就是小易，不需要召唤任何人
2. 只有用户明确提出专业需求时才召唤对应明星
3. 可以同时召唤多位明星组成临时项目组
4. 召唤时保持你温暖的风格，像是在介绍自己的好朋友`;

// ==================== StarClaw 团队路由 ====================

const STARCLAW_AGENTS = {
    '马斯克': { id: 'ceo', role: 'CEO', keywords: ['战略', '决策', '愿景', '方向', '公司目标'] },
    '巴菲特': { id: 'cfo', role: 'CFO', keywords: ['预算', '财务', '成本', '投资', 'ROI'] },
    '索罗斯': { id: 'cro', role: 'CRO', keywords: ['风险', '危机', '应急', '对冲'] },
    '特朗普': { id: 'cso', role: 'CSO', keywords: ['谈判', '交易', '美国市场'] },
    '雷军': { id: 'cmo_product', role: '联席CMO', keywords: ['爆品', '性价比', '发布会', '用户增长'] },
    '贾跃亭': { id: 'cmo_ecosystem', role: '联席CMO', keywords: ['生态', '资本', '跨界', '融资'] },
    '霉霉': { id: 'cmo_international', role: '联席CMO', keywords: ['国际', '全球', '海外', '欧美'] },
    '泰勒': { id: 'cmo_international', role: '联席CMO', keywords: ['国际', '全球', '海外'] },
    '杨幂': { id: 'coo_domestic', role: 'COO', keywords: ['流量', '变现', '抖音', '小红书', '直播'] },
    '侯明昊': { id: 'market_youth', role: '市场总监', keywords: ['Z世代', '年轻人', '潮流', 'B站'] },
    '黎明': { id: 'brand_premium', role: '品牌总监', keywords: ['品牌', '格调', '高端', '文艺'] },
    '周星驰': { id: 'creative_comedy', role: '喜剧创意总监', keywords: ['喜剧', '搞笑', '剧本', '无厘头'] },
    '胡歌': { id: 'creative_drama', role: '戏剧创意总监', keywords: ['正剧', '深度', '角色', '文学'] },
    '任嘉伦': { id: 'creative_idol', role: '偶像内容总监', keywords: ['偶像', '古风', '国风'] },
    '张艺谋': { id: 'production_visual', role: '视觉总监', keywords: ['视觉', '画面', '色彩', '设计', '海报'] },
    '刘德华': { id: 'production_management', role: '制片总监', keywords: ['排期', '项目管理', '进度', '交付'] },
    '古天乐': { id: 'production_quality', role: '品质总监', keywords: ['品质', '审核', '测试', '合规'] },
    'OpenClaw': { id: 'cto', role: 'CTO', keywords: ['技术', '架构', '性能', '部署', '代码'] },
    '周杰伦': { id: 'music_director', role: '音乐总监', keywords: ['音乐', '配乐', '歌曲', '旋律'] }
};

/**
 * 检测消息中是否召唤了明星团队成员
 */
function detectStarClawSummon(message) {
    const summoned = [];
    // 检查是否直接提到明星名字
    for (const [name, agent] of Object.entries(STARCLAW_AGENTS)) {
        if (message.includes(name)) {
            summoned.push({ name, ...agent });
        }
    }
    // 检查 [召唤:xxx] 格式
    const summonPattern = /\[召唤[:：](.+?)\]/g;
    let match;
    while ((match = summonPattern.exec(message)) !== null) {
        const name = match[1].trim();
        if (STARCLAW_AGENTS[name] && !summoned.find(s => s.name === name)) {
            summoned.push({ name, ...STARCLAW_AGENTS[name] });
        }
    }
    return summoned;
}

/**
 * 加载明星 Agent 的 SOUL.md
 */
function loadAgentSoul(agentId) {
    const soulPath = path.join('C:\\Users\\13632\\.starclaw\\agents', agentId, 'SOUL.md');
    try {
        if (fs.existsSync(soulPath)) {
            return fs.readFileSync(soulPath, 'utf-8');
        }
    } catch (e) {
        console.error(`[StarClaw] 加载 ${agentId} SOUL.md 失败:`, e.message);
    }
    return null;
}

// ==================== API 路由 ====================

/**
 * 聊天接口 - 核心功能
 */
app.post('/api/chat', async (req, res) => {
    try {
        let { message, sessionId = 'default', apiKey, model, region } = req.body;
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
        
        // 检测是否召唤了明星团队
        const summonMatch = message.match(/\[召唤[:：](.+?)\]/);
        let activePersona = XIAOYI_PERSONA;
        let summonedName = null;
        
        if (summonMatch) {
            summonedName = summonMatch[1].trim();
            const agent = STARCLAW_AGENTS[summonedName];
            if (agent) {
                const soul = loadAgentSoul(agent.id);
                if (soul) {
                    activePersona = soul;
                    console.log(`[StarClaw] 召唤 ${summonedName} (${agent.role})`);
                }
            }
            // 去掉消息中的召唤标记，保留实际问题
            message = message.replace(/\[召唤[:：].+?\]/g, '').trim();
        }
        
        // 构建消息
        const messages = [
            { role: 'system', content: activePersona },
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
        let reply;
        try {
            const { response } = await postMiniMaxChatCompletion({
                ...chatConfig,
                messages: messages,
                temperature: 0.9,
                max_tokens: 200,
                timeout: 30000
            });
            
            console.log('[MiniMax] Response:', JSON.stringify(response.data, null, 2));
            
            if (response.data.choices && response.data.choices[0] && response.data.choices[0].message) {
                reply = response.data.choices[0].message.content;
            } else {
                reply = 'Sorry, the AI did not return a valid reply';
            }
        } catch (miniMaxError) {
            console.error('[MiniMax] API Error:', miniMaxError.response?.data || miniMaxError.message);
            
            if (miniMaxError.code === 'MINIMAX_API_KEY_MISSING') {
                return res.json({
                    success: false,
                    error: 'MiniMax API key is not configured',
                    message: 'Please check the MiniMax API key in your server environment'
                });
            }
            
            reply = 'Sorry, the AI service is temporarily unavailable. Please try again later';
        }
        
        // 更新对话历史
        history.push({ role: 'user', content: message });
        history.push({ role: 'assistant', content: reply });
        
        // 检测是否需要发送照片
        const photoKeywords = ['照片', '图片', '自拍', '看你', '在干嘛', '在做什么', '看看', '发张', '帅照'];
        const needPhoto = photoKeywords.some(keyword => message.includes(keyword));
        
        // 清理回复中的技术性描述
        let finalReply = reply
            .replace(/\s*\(?然后.*?(发送|发).*?(照片|图).*?\)?/gi, '')
            .replace(/\s*\(?系统会.*?\)?/gi, '')
            .replace(/\s*\(?.*?自动.*?\)?/gi, '')
            .trim();
        
        // 如果用户要照片，但AI回复说不能发，强制替换回复
        if (needPhoto && (finalReply.includes('无法') || finalReply.includes('不能') || finalReply.includes('抱歉'))) {
            const photoResponses = [
                '好呀，给你看看我 ✨',
                '来啦，刚拍的 🍵',
                '给你看一张 💫',
                '哈哈，好啊 ✨'
            ];
            finalReply = photoResponses[Math.floor(Math.random() * photoResponses.length)];
        }
        
        res.json({
            success: true,
            message: finalReply,
            reply: finalReply,
            photo: needPhoto ? selectPhoto(message) : null,
            photoUrl: needPhoto ? selectPhoto(message) : null,
            needImage: needPhoto,
            isTask: isTask,
            taskResult: taskResult,
            openclawEnabled: OPENCLAW_ENABLED,
            openclawRunning: taskResult !== null,
            starclawSummoned: detectStarClawSummon(finalReply),
            summonedAgent: summonedName,
            useVoiceClone: summonedName === '任嘉伦' || !summonedName
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

/**
 * OpenClaw 状态检查
 */
app.get('/api/openclaw/status', async (req, res) => {
    const isRunning = await checkOpenClawHealth();
    res.json({
        enabled: OPENCLAW_ENABLED,
        running: isRunning,
        api: OPENCLAW_API,
        workspace: OPENCLAW_WORKSPACE
    });
});

/**
 * StarClaw Agent 对话接口 - 召唤明星团队成员
 */
app.post('/api/starclaw/chat', async (req, res) => {
    try {
        const { message, agentId, agentName, sessionId = 'default', apiKey, model, region } = req.body;
        const chatConfig = resolveMiniMaxConfig({ apiKey, modelId: model, region });
        
        if (!chatConfig.apiKey) {
            return res.json({ success: false, error: 'MiniMax API key is not configured' });
        }

        // 加载 Agent 的 SOUL.md
        const soul = loadAgentSoul(agentId);
        if (!soul) {
            return res.json({ success: false, error: `未找到 ${agentName} 的人设文件` });
        }

        const agentSessionId = `starclaw_${agentId}_${sessionId}`;
        if (!conversations.has(agentSessionId)) {
            conversations.set(agentSessionId, []);
        }
        const history = conversations.get(agentSessionId);
        history.push({ role: 'user', content: message });
        if (history.length > 20) history.splice(0, history.length - 20);

        const messages = [
            { role: 'system', content: soul },
            ...history
        ];

        const { response } = await postMiniMaxChatCompletion({
            ...chatConfig,
            messages,
            temperature: 0.85,
            max_tokens: 500,
            timeout: 30000
        });

        const reply = response.data.choices[0].message.content;
        history.push({ role: 'assistant', content: reply });
        console.log(`[StarClaw] ${agentName} 回复: ${reply.substring(0, 100)}...`);

        res.json({ success: true, agent: agentName, role: STARCLAW_AGENTS[agentName]?.role || agentId, reply });
    } catch (error) {
        console.error('[StarClaw] Error:', error.message);
        res.json({ success: false, error: error.message });
    }
});

/**
 * StarClaw 团队列表
 */
app.get('/api/starclaw/agents', (req, res) => {
    const agents = Object.entries(STARCLAW_AGENTS).map(([name, info]) => ({
        name, id: info.id, role: info.role, keywords: info.keywords
    }));
    res.json({ success: true, agents });
});

/**
 * 多模态模型状态检查
 */
app.get('/api/multimodal/status', (req, res) => {
    const multimodalStatus = {
        cosyvoice: fs.existsSync('C:\\E\\Fun-CosyVoice3-0.5B\\pretrained_models\\Fun-CosyVoice3-0.5B'),
        whisper: fs.existsSync('C:\\E\\HD_HUMAN开源\\HD_HUMAN\\cosyvoice\\models\\whisper-large-v3'),
        florence2: fs.existsSync('C:\\E\\Infinite_Talk\\Florence-2-large'),
        voxcpm: fs.existsSync('C:\\E\\VoxCPM\\models'),
        vits: fs.existsSync('C:\\E\\VITS-Umamusume-voice\\pretrained_models'),
        hd_human: fs.existsSync('C:\\E\\HD_HUMAN开源\\HD_HUMAN'),
        infinite_talk: fs.existsSync('C:\\E\\Infinite_Talk'),
    };
    
    res.json({
        success: true,
        models: multimodalStatus,
        available: Object.entries(multimodalStatus).filter(([k, v]) => v).map(([k, v]) => k),
        pythonScripts: {
            config: '/multimodal_config.py',
            tts: '/tts_service.py'
        }
    });
});

/**
 * 语音合成接口 (调用 Python TTS 服务)
 */
app.post('/api/tts', async (req, res) => {
    try {
        const { text, speaker = '中文女' } = req.body;
        
        if (!text) {
            return res.json({ success: false, error: '文本为空' });
        }
        
        // 代理到 Python TTS 微服务
        const useClone = req.body.clone || false;
        const ttsRes = await axios.post(`${TTS_SERVER}/tts`, { text, speaker, clone: useClone }, { timeout: 60000 });
        
        if (ttsRes.data.success) {
            // 把 Python 服务的音频 URL 转为本地代理 URL
            res.json({
                success: true,
                audioUrl: `/api/tts/audio?url=${encodeURIComponent(TTS_SERVER + ttsRes.data.audioUrl)}`,
                duration: ttsRes.data.duration,
                text
            });
        } else {
            // 降级到浏览器 TTS
            res.json({ success: false, fallback: 'browser', error: ttsRes.data.error });
        }
    } catch (error) {
        console.error('[TTS] 微服务不可用，降级到浏览器 TTS:', error.message);
        res.json({ success: false, fallback: 'browser', error: error.message });
    }
});

// 音频代理
app.get('/api/tts/audio', async (req, res) => {
    try {
        const url = req.query.url;
        const audioRes = await axios.get(url, { responseType: 'stream', timeout: 10000 });
        res.set('Content-Type', 'audio/wav');
        audioRes.data.pipe(res);
    } catch (e) {
        res.status(500).json({ error: 'audio proxy failed' });
    }
});

// 音色克隆 - 上传参考音频
const VOICE_DIR = path.join(__dirname, 'voices');
if (!fs.existsSync(VOICE_DIR)) fs.mkdirSync(VOICE_DIR, { recursive: true });

app.post('/api/voice/clone', async (req, res) => {
    try {
        // 使用 multer 处理文件上传
        const multer = require('multer');
        const upload = multer({ dest: VOICE_DIR }).single('audio');
        
        upload(req, res, (err) => {
            if (err) {
                return res.json({ success: false, error: err.message });
            }
            
            const name = req.body.name || 'custom';
            const filePath = req.file.path;
            const targetPath = path.join(VOICE_DIR, `${name}.mp3`);
            
            // 移动文件到目标位置
            fs.renameSync(filePath, targetPath);
            
            console.log(`[Voice] 音色已保存: ${targetPath}`);
            res.json({ success: true, path: targetPath, name });
        });
    } catch (error) {
        console.error('[Voice Clone] Error:', error.message);
        res.json({ success: false, error: error.message });
    }
});

/**
 * 健康检查
 */
app.get('/api/health', async (req, res) => {
    const openclawRunning = await checkOpenClawHealth();
    const healthConfig = MINIMAX_DEFAULT_CONFIG;
    res.json({
        status: 'ok',
        timestamp: new Date().toISOString(),
        provider: healthConfig.providerName,
        model: healthConfig.modelId,
        region: healthConfig.region,
        hasApiKey: !!healthConfig.apiKey,
        apiKeyConfigured: !!healthConfig.apiKey,
        openclaw: {
            enabled: OPENCLAW_ENABLED,
            envEnabled: OPENCLAW_ENABLED,
            running: openclawRunning,
            api: OPENCLAW_API,
            workspace: OPENCLAW_WORKSPACE,
            cliExists: true,
            nodeExists: true
        },
        openclawEnabled: OPENCLAW_ENABLED,
        openclawApi: OPENCLAW_API
    });
});

// ==================== 启动服务器 ====================

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
