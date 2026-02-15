const express = require('express');
const cors = require('cors');
const { exec } = require('child_process');
const { promisify } = require('util');
const execPromise = promisify(exec);
const fs = require('fs');
const path = require('path');

const app = express();
const PORT = 9881;

app.use(cors());
app.use(express.json());

// GPT-SoVITS 配置
const GPT_SOVITS_DIR = 'D:\\GPT-SoVITS';
const REF_AUDIO = 'D:\\tool\\skill\\projects\\xiaoyue-web\\tts_audio\\02_红人面对面_采访.wav';
const REF_TEXT = '大家好';
const OUTPUT_DIR = 'D:\\tool\\skill\\projects\\xiaoyue-web\\tts_audio\\generated';

// 确保输出目录存在
if (!fs.existsSync(OUTPUT_DIR)) {
    fs.mkdirSync(OUTPUT_DIR, { recursive: true });
}

// TTS API
app.get('/tts', async (req, res) => {
    try {
        const { text } = req.query;
        
        if (!text) {
            return res.status(400).json({ error: '缺少文本参数' });
        }

        console.log(`[TTS] 生成语音: "${text}"`);
        
        // 生成唯一文件名
        const timestamp = Date.now();
        const outputFile = path.join(OUTPUT_DIR, `tts_${timestamp}.wav`);
        
        // 使用 Python 脚本调用 GPT-SoVITS
        const pythonScript = `
import sys
sys.path.insert(0, '${GPT_SOVITS_DIR.replace(/\\/g, '\\\\')}')

# 这里简化处理，实际应该调用 GPT-SoVITS 的推理代码
# 暂时返回错误，提示用户使用 WebUI
print("ERROR: 请使用 GPT-SoVITS WebUI 手动生成音频")
        `;
        
        // 由于直接调用 GPT-SoVITS 比较复杂，我们使用另一种方法
        // 调用命令行工具生成音频
        const command = `cd "${GPT_SOVITS_DIR}" && .\\venv\\Scripts\\python.exe -c "
import sys
sys.path.insert(0, '.')
print('TTS generation would happen here')
print('Output: ${outputFile.replace(/\\/g, '\\\\')}')
"`;

        // 暂时返回一个提示，让用户知道需要使用 WebUI
        res.json({
            success: false,
            message: '请使用 GPT-SoVITS WebUI (http://localhost:9874) 手动生成音频',
            webui_url: 'http://localhost:9874',
            alternative: '使用浏览器自带的语音合成（点击语音按钮）'
        });

    } catch (error) {
        console.error('[TTS] 错误:', error);
        res.status(500).json({ error: error.message });
    }
});

// 提供生成的音频文件
app.use('/audio', express.static(OUTPUT_DIR));

// 健康检查
app.get('/health', (req, res) => {
    res.json({ status: 'ok', service: 'TTS Proxy' });
});

app.listen(PORT, () => {
    console.log(`🎙️ TTS 代理服务运行在 http://localhost:${PORT}`);
});
