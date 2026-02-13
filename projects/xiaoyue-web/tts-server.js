const express = require('express');
const cors = require('cors');
const { exec } = require('child_process');
const { promisify } = require('util');
const fs = require('fs').promises;
const path = require('path');
const execPromise = promisify(exec);

const app = express();
const PORT = 3002;

app.use(cors());
app.use(express.json());
app.use('/audio', express.static('audio'));

// 确保音频目录存在
async function ensureAudioDir() {
    const audioDir = path.join(__dirname, 'audio');
    try {
        await fs.access(audioDir);
    } catch {
        await fs.mkdir(audioDir, { recursive: true });
    }
}

// 检查 edge-tts 是否安装
async function checkEdgeTTS() {
    try {
        await execPromise('edge-tts --version');
        return true;
    } catch {
        return false;
    }
}

// 安装 edge-tts
async function installEdgeTTS() {
    try {
        console.log('正在安装 edge-tts...');
        await execPromise('pip install edge-tts', { timeout: 120000 });
        console.log('edge-tts 安装成功！');
        return true;
    } catch (error) {
        console.error('edge-tts 安装失败:', error);
        return false;
    }
}

// 获取可用音色列表
app.get('/api/voices', async (req, res) => {
    try {
        const { stdout } = await execPromise('edge-tts --list-voices');
        const voices = stdout.split('\n')
            .filter(line => line.includes('zh-CN'))
            .map(line => {
                const match = line.match(/Name: ([\w-]+)/);
                return match ? match[1] : null;
            })
            .filter(Boolean);
        
        res.json({
            success: true,
            voices: voices,
            recommended: [
                'zh-CN-XiaoxiaoNeural',  // 晓晓（女声，温柔）
                'zh-CN-YunxiNeural',      // 云希（男声，温暖）
                'zh-CN-XiaoyiNeural',     // 晓伊（女声，活泼）
                'zh-CN-YunjianNeural',    // 云健（男声，稳重）
                'zh-CN-XiaochenNeural',   // 晓辰（女声，甜美）
            ]
        });
    } catch (error) {
        res.json({
            success: false,
            error: error.message
        });
    }
});

// 文本转语音
app.post('/api/tts', async (req, res) => {
    try {
        const { text, voice = 'zh-CN-XiaoxiaoNeural', rate = '+0%', pitch = '+0Hz' } = req.body;
        
        if (!text) {
            return res.json({
                success: false,
                error: '缺少文本内容'
            });
        }
        
        // 生成唯一文件名
        const filename = `tts_${Date.now()}_${Math.random().toString(36).substr(2, 9)}.mp3`;
        const filepath = path.join(__dirname, 'audio', filename);
        
        // 调用 edge-tts
        const command = `edge-tts --voice "${voice}" --rate="${rate}" --pitch="${pitch}" --text "${text.replace(/"/g, '\\"')}" --write-media "${filepath}"`;
        
        await execPromise(command, { timeout: 30000 });
        
        // 检查文件是否生成
        await fs.access(filepath);
        
        res.json({
            success: true,
            audioUrl: `/audio/${filename}`,
            voice: voice
        });
        
        // 5分钟后删除文件
        setTimeout(async () => {
            try {
                await fs.unlink(filepath);
            } catch (err) {
                console.error('删除临时文件失败:', err);
            }
        }, 5 * 60 * 1000);
        
    } catch (error) {
        console.error('TTS error:', error);
        res.json({
            success: false,
            error: error.message || '语音合成失败'
        });
    }
});

// 健康检查
app.get('/api/health', async (req, res) => {
    const hasEdgeTTS = await checkEdgeTTS();
    res.json({
        status: 'ok',
        edgeTTS: hasEdgeTTS
    });
});

// 启动服务器
async function start() {
    await ensureAudioDir();
    
    // 检查并安装 edge-tts
    const hasEdgeTTS = await checkEdgeTTS();
    if (!hasEdgeTTS) {
        console.log('未检测到 edge-tts，正在安装...');
        const installed = await installEdgeTTS();
        if (!installed) {
            console.error('⚠️  edge-tts 安装失败，TTS 功能将不可用');
            console.log('请手动运行: pip install edge-tts');
        }
    }
    
    app.listen(PORT, () => {
        console.log(`🎤 TTS 服务器运行在 http://localhost:${PORT}`);
        console.log(`📝 Edge-TTS 状态: ${hasEdgeTTS ? '✅ 已安装' : '❌ 未安装'}`);
    });
}

start();
