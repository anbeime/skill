# GPT-SoVITS 音色克隆修复指南

## 🔴 发现的问题

### 1. 生成的WAV文件是假的
- 文件大小都是 153.84 KB（HTML页面大小）
- 实际内容是 Gradio WebUI 的 HTML 错误页面
- 根本不是音频文件

### 2. 端口配置错误
- voice.html 调用的是 WebUI 端口 9874
- 但应该调用 API 端口 9880
- 已修复：修改 voice.html 使用 `GPT_SOVITS_URL` (9880)

### 3. GPT-SoVITS 服务未运行
- API 服务 (端口 9880) 未启动
- 模型权重文件缺失

### 4. 模型权重缺失
- `GPT_weights/` 文件夹为空
- `SoVITS_weights/` 文件夹为空
- 需要先下载预训练模型

---

## ✅ 修复步骤

### Step 1: 下载预训练模型

#### 方法A: 使用官方下载脚本
```bash
cd D:\GPT-SoVITS
python tools/download_models.py
```

#### 方法B: 手动下载
从以下链接下载模型文件：

**GPT模型** (放入 `GPT_weights/`):
- https://huggingface.co/lj1995/GPT-SoVITS/resolve/main/GPT_SoVITS_pretrained.pth

**SoVITS模型** (放入 `SoVITS_weights/`):
- https://huggingface.co/lj1995/GPT-SoVITS/resolve/main/SoVITS_pretrained.pth

**CNHubert模型** (放入 `GPT_SoVITS/pretrained_models/`):
- https://huggingface.co/lj1995/GPT-SoVITS/resolve/main/chinese-hubert-large-fairseq-ckpt.pt

---

### Step 2: 启动 GPT-SoVITS API 服务

运行启动脚本：
```batch
D:\tool\start_gpt_sovits_api.bat
```

或者手动启动：
```bash
cd D:\GPT-SoVITS
venv\Scripts\activate
python api.py -dr "D:\tool\skill\projects\xiaoyue-web\tts_audio\02_红人面对面_采访.wav" -dt "大家好，我是任嘉伦" -dl "zh" -p 9880
```

---

### Step 3: 验证服务运行

检查端口：
```bash
netstat -ano | findstr :9880
```

测试API：
```bash
curl "http://localhost:9880?text=你好，我是任嘉伦&text_language=zh"
```

---

### Step 4: 重新生成音频文件

使用修复后的脚本：
```bash
cd D:\tool\skill\projects\xiaoyue-web\tts_audio
python tts_test_fixed.py
```

---

## 📝 已完成的修复

### voice.html 修复
- ✅ 修改 API 调用端口：9874 → 9880
- ✅ 使用 `GPT_SOVITS_URL` 代替 `GPT_SOVITS_WEBUI_URL`

### 文件位置
- 启动脚本: `D:\tool\start_gpt_sovits_api.bat`
- 修复指南: `D:\tool\skill\projects\xiaoyue-web\GPT-SoVITS修复指南.md`
- voice.html: `D:\tool\skill\projects\xiaoyue-web\public\voice.html`

---

## 🎯 下一步操作

1. **下载预训练模型**（约2-3GB）
2. **启动 API 服务**
3. **测试语音合成**
4. **重新生成音频文件**

---

## ⚠️ 注意事项

- GPT-SoVITS 需要 NVIDIA GPU 加速（推荐）
- 首次启动需要加载模型，可能需要1-2分钟
- 确保参考音频文件路径正确
- API 服务必须在后台持续运行

---

## 🔧 故障排除

### 问题：API 返回 404
**解决**: 检查模型是否正确加载，查看控制台错误信息

### 问题：音频生成失败
**解决**: 检查参考音频文件是否存在，路径是否正确

### 问题：音色不像任嘉伦
**解决**: 
- 使用更长的参考音频（建议30秒以上）
- 调整 temperature 和 top_p 参数
- 尝试不同的参考音频片段
