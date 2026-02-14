# 模型下载指南

## 概览
本文档说明 InfiniteTalk 所需模型权重的下载步骤。总大小约 30GB。

## 模型列表

### 1. Wan2.1-I2V-14B-480P（底座模型）
- 大小：约 27GB
- 用途：视频生成的基础模型
- 下载路径：`./weights/Wan2.1-I2V-14B-480P`

### 2. chinese-wav2vec2-base（音频编码器）
- 大小：约 500MB
- 用途：中文语音特征提取
- 下载路径：`./weights/chinese-wav2vec2-base`

### 3. InfiniteTalk（音频条件权重）
- 大小：约 200MB
- 用途：音频驱动的条件权重
- 下载路径：`./weights/InfiniteTalk/single`

### 4. Kokoro-82M（TTS 模型，可选）
- 大小：约 80MB
- 用途：文本转语音
- 下载路径：`./weights/Kokoro-82M`

## 下载步骤

### 方法一：使用 Hugging Face CLI（推荐）

#### 1. 安装 Hugging Face CLI
```bash
pip install huggingface-hub
```

#### 2. 登录 Hugging Face（如需要）
```bash
huggingface-cli login
```

#### 3. 下载模型

**下载底座模型**（最大，约 27GB）：
```bash
mkdir -p weights/Wan2.1-I2V-14B-480P
huggingface-cli download Wan-AI/Wan2.1-I2V-14B-480P --local-dir ./weights/Wan2.1-I2V-14B-480P
```

**下载中文音频编码器**：
```bash
mkdir -p weights/chinese-wav2vec2-base
huggingface-cli download TencentGameMate/chinese-wav2vec2-base --local-dir ./weights/chinese-wav2vec2-base
```

**下载 InfiniteTalk 权重**：
```bash
mkdir -p weights/InfiniteTalk/single
huggingface-cli download MeiGen-AI/InfiniteTalk --local-dir ./weights/InfiniteTalk/single
```

**下载 TTS 模型**（可选）：
```bash
mkdir -p weights/Kokoro-82M
huggingface-cli download hexgrad/Kokoro-82M --local-dir ./weights/Kokoro-82M
```

### 方法二：手动下载

1. 访问 Hugging Face 页面：
   - Wan2.1：https://huggingface.co/Wan-AI/Wan2.1-I2V-14B-480P
   - Chinese-wav2vec2：https://huggingface.co/TencentGameMate/chinese-wav2vec2-base
   - InfiniteTalk：https://huggingface.co/MeiGen-AI/InfiniteTalk
   - Kokoro-82M：https://huggingface.co/hexgrad/Kokoro-82M

2. 点击 "Files and versions" 标签
3. 下载所有文件到对应的本地目录

### 方法三：使用 Git LFS

```bash
# 安装 git-lfs
sudo apt-get install git-lfs
git lfs install

# 克隆模型仓库
git clone https://huggingface.co/Wan-AI/Wan2.1-I2V-14B-480P ./weights/Wan2.1-I2V-14B-480P
git clone https://huggingface.co/TencentGameMate/chinese-wav2vec2-base ./weights/chinese-wav2vec2-base
git clone https://huggingface.co/MeiGen-AI/InfiniteTalk ./weights/InfiniteTalk/single
git clone https://huggingface.co/hexgrad/Kokoro-82M ./weights/Kokoro-82M
```

## 验证下载

### 检查目录结构
```bash
ls -lh weights/
```

期望输出：
```
drwxr-xr-x  Wan2.1-I2V-14B-480P
drwxr-xr-x  chinese-wav2vec2-base
drwxr-xr-x  InfiniteTalk
drwxr-xr-x  Kokoro-82M
```

### 检查关键文件
```bash
# 检查底座模型
ls weights/Wan2.1-I2V-14B-480P/

# 检查音频编码器
ls weights/chinese-wav2vec2-base/

# 检查 InfiniteTalk 权重
ls weights/InfiniteTalk/single/

# 检查 TTS 模型
ls weights/Kokoro-82M/
```

## 常见问题

### 问题 1：下载速度慢
- 解决：使用镜像站或下载工具，如 `aria2c`

### 问题 2：磁盘空间不足
- 解决：确保至少有 50GB 可用空间
- 备选：仅下载必需模型（Wan2.1 + wav2vec2 + InfiniteTalk），跳过 Kokoro

### 问题 3：权限错误
- 解决：使用 `chmod` 设置正确的权限
```bash
chmod -R 755 weights/
```

### 问题 4：模型损坏
- 解决：删除损坏的文件，重新下载
```bash
rm -rf weights/<model-name>
huggingface-cli download <model-repo> --local-dir ./weights/<model-name>
```

## 模型文件说明

### Wan2.1-I2V-14B-480P
包含以下关键文件：
- `model.safetensors`：模型权重
- `config.json`：模型配置
- 其他配置文件和 tokenizer

### chinese-wav2vec2-base
包含以下关键文件：
- `pytorch_model.bin` 或 `model.safetensors`：模型权重
- `config.json`：模型配置
- `vocab.json`：词表文件

### InfiniteTalk
包含以下关键文件：
- `infinitetalk.safetensors`：音频条件权重

### Kokoro-82M
包含以下关键文件：
- `model.safetensors`：模型权重
- `config.json`：模型配置
- 多个声音权重文件（`*.pt`）
