# 🎤 小易语音克隆配置指南

## ✅ 已完成：预设照片功能

小易现在有 16 张预设照片，会根据对话内容自动显示相应的照片：

- **工作场景**：说"工作"、"编程"、"代码"
- **咖啡时光**：说"咖啡"、"喝"
- **思考状态**：说"思考"、"想想"
- **开心时刻**：说"开心"、"高兴"
- **疲惫状态**：说"累"、"休息"
- 等等...

试试对小易说："发张你在工作的照片"

---

## 🎵 Fish-TTS 语音克隆配置

### 方案 1：使用 Fish-TTS 本地克隆（推荐）

#### 步骤 1：检查 Fish-TTS 安装

```bash
# 检查是否已安装
python -c "import fish_speech"

# 如果未安装，克隆仓库
git clone https://github.com/fishaudio/fish-speech.git
cd fish-speech
```

#### 步骤 2：准备音色样本

需要准备 **10-30 秒**的清晰录音：

1. **录制要求**：
   - 格式：WAV 或 MP3
   - 采样率：22050Hz 或 44100Hz
   - 声道：单声道
   - 内容：清晰的中文朗读
   - 时长：10-30 秒

2. **录制工具**：
   - Windows：录音机
   - 在线：https://online-voice-recorder.com/

3. **示例文本**（录制这段话）：
```
你好，我是小易，你的 AI 伴侣。
我可以帮你聊天、执行任务、生成图片。
希望能成为你最好的助手和朋友。
```

#### 步骤 3：克隆音色

```bash
# 进入 Fish-TTS 目录
cd fish-speech

# 克隆音色
python tools/vqgan/inference.py \
    --input "你的音频文件.wav" \
    --output "xiaoyi_voice.pt"
```

#### 步骤 4：配置小易使用克隆音色

编辑 `server.js`，添加 Fish-TTS API 调用：

```javascript
// 新增 TTS 接口
app.post('/api/tts-fish', async (req, res) => {
    const { text } = req.body;
    
    try {
        // 调用 Fish-TTS API
        const response = await axios.post('http://localhost:8080/tts', {
            text: text,
            reference_audio: 'xiaoyi_voice.pt',
            language: 'zh'
        });
        
        res.json({
            success: true,
            audioUrl: response.data.audio_url
        });
    } catch (error) {
        res.json({
            success: false,
            error: error.message
        });
    }
});
```

---

### 方案 2：使用在线 TTS 服务（更简单）

#### 选项 A：智谱 AI TTS（推荐）

智谱 AI 提供高质量中文 TTS：

```javascript
// 在 server.js 中添加
app.post('/api/tts-zhipu', async (req, res) => {
    const { text } = req.body;
    
    try {
        const response = await axios.post(
            'https://open.bigmodel.cn/api/paas/v4/audio/speech',
            {
                model: 'glm-4-voice',
                input: text,
                voice: 'alloy' // 可选：alloy, echo, fable, onyx, nova, shimmer
            },
            {
                headers: {
                    'Authorization': `Bearer ${ZHIPU_API_KEY}`,
                    'Content-Type': 'application/json'
                },
                responseType: 'arraybuffer'
            }
        );
        
        // 保存音频文件
        const audioPath = `public/audio/${Date.now()}.mp3`;
        fs.writeFileSync(audioPath, response.data);
        
        res.json({
            success: true,
            audioUrl: audioPath.replace('public/', '')
        });
    } catch (error) {
        res.json({
            success: false,
            error: error.message
        });
    }
});
```

#### 选项 B：Edge-TTS（完全免费）

使用微软 Edge 的 TTS 引擎：

```bash
# 安装 Edge-TTS
pip install edge-tts

# 列出可用音色
edge-tts --list-voices | grep zh-CN

# 推荐音色：
# zh-CN-XiaoxiaoNeural - 女声（温柔）
# zh-CN-YunyangNeural - 女声（活泼）
# zh-CN-XiaoyiNeural - 女声（专业）
```

创建 Python 服务：

```python
# tts_server.py
from flask import Flask, request, jsonify
import edge_tts
import asyncio

app = Flask(__name__)

@app.route('/tts', methods=['POST'])
async def tts():
    data = request.json
    text = data.get('text')
    voice = data.get('voice', 'zh-CN-XiaoxiaoNeural')
    
    output_file = f"audio/{int(time.time())}.mp3"
    
    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(output_file)
    
    return jsonify({
        'success': True,
        'audioUrl': output_file
    })

if __name__ == '__main__':
    app.run(port=5000)
```

---

### 方案 3：录制真人音色（最简单）

如果你有喜欢的声音，可以：

1. **录制 16 段音频**：
   - 对应 16 张照片的场景
   - 每段 2-5 秒
   - 例如："你好！"、"我在工作呢"、"好的，稍等一下"

2. **保存到目录**：
```
public/xiaoyi-voices/
├── voice1.mp3  # 对应 ren1.png
├── voice2.mp3  # 对应 ren2.png
...
└── voice16.mp3 # 对应 ren16.png
```

3. **修改代码**：
```javascript
// 在 selectPhoto 函数中同时返回音频
function selectPhotoAndVoice(message) {
    for (const photo of XIAOYI_PHOTOS) {
        if (photo.keywords.some(keyword => message.includes(keyword))) {
            return {
                photo: `xiaoyi-photos/ren${photo.id}.png`,
                voice: `xiaoyi-voices/voice${photo.id}.mp3`
            };
        }
    }
    const randomId = Math.floor(Math.random() * 16) + 1;
    return {
        photo: `xiaoyi-photos/ren${randomId}.png`,
        voice: `xiaoyi-voices/voice${randomId}.mp3`
    };
}
```

---

## 🎯 推荐方案

### 快速方案（今天就能用）：
✅ **Edge-TTS** - 完全免费，音质好，无需配置

### 最佳方案（音质最好）：
✅ **Fish-TTS 语音克隆** - 可以克隆任何声音

### 最简单方案（最个性化）：
✅ **录制真人音色** - 16 段预设语音

---

## 🚀 我可以帮你

你想用哪个方案？我可以帮你：

1. ✅ 配置 Edge-TTS（5 分钟搞定）
2. ✅ 配置 Fish-TTS 语音克隆
3. ✅ 配置智谱 AI TTS
4. ✅ 设置预录音频

**你想先试哪个？**

---

Made with ❤️ by anbeime | 2026-02-13
