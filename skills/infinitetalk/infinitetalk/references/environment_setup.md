# 环境配置指南

## 概览
本文档说明 InfiniteTalk Skill 的环境配置和依赖安装步骤。

## 系统要求
- 操作系统：Linux（推荐 Ubuntu 20.04+）
- Python：3.8+
- CUDA：11.8+（推荐 12.1）
- GPU：NVIDIA GPU（16GB+ 显存推荐）

## 依赖安装

### 1. 创建虚拟环境（推荐）
```bash
# 使用 conda 创建环境
conda create -n infinitetalk python=3.10 -y
conda activate infinitetalk
```

### 2. 安装 PyTorch
```bash
# 根据您的 CUDA 版本安装对应版本的 PyTorch
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
```

### 3. 安装 Python 依赖
```bash
# 安装核心依赖
pip install -r requirements.txt

# 手动安装 librosa（通过 conda）
conda install -c conda-forge librosa -y
```

### 4. 安装 FFmpeg
```bash
# Ubuntu/Debian
sudo apt-get update && sudo apt-get install ffmpeg -y

# 或使用 conda
conda install -c conda-forge ffmpeg -y
```

## 验证安装

### 检查 CUDA
```bash
python -c "import torch; print(f'CUDA available: {torch.cuda.is_available()}')"
```

### 检查依赖
```bash
python -c "import transformers; import diffusers; import librosa; print('All dependencies installed')"
```

## 常见问题

### 问题 1：CUDA 版本不匹配
- 症状：ImportError 或 CUDA 相关错误
- 解决：确保 PyTorch 版本与 CUDA 版本匹配，使用 `nvidia-smi` 检查 CUDA 版本

### 问题 2：librosa 安装失败
- 症状：ImportError: No module named 'librosa'
- 解决：使用 conda 安装 librosa（如上述步骤所示）

### 问题 3：FFmpeg 未找到
- 症状：FileNotFoundError: ffmpeg not found
- 解决：安装 FFmpeg 并确保在 PATH 中

## 显存优化方案

### 低显存设备（<16GB）
使用以下策略降低显存占用：

1. 启用量化
```bash
python scripts/infer_infinitetalk.py \
  --input_path ./input.jpg \
  --audio_path ./audio.wav \
  --output_path ./output.mp4 \
  --quant int8
```

2. 启用模型卸载
```bash
python scripts/infer_infinitetalk.py \
  --input_path ./input.jpg \
  --audio_path ./audio.wav \
  --output_path ./output.mp4 \
  --offload_model true
```

3. 降低分辨率
```bash
python scripts/infer_infinitetalk.py \
  --input_path ./input.jpg \
  --audio_path ./audio.wav \
  --output_path ./output.mp4 \
  --size infinitetalk-480
```

4. 减少 T5 模型显存占用
```bash
python scripts/infer_infinitetalk.py \
  --input_path ./input.jpg \
  --audio_path ./audio.wav \
  --output_path ./output.mp4 \
  --t5_cpu
```

## 多 GPU 支持

对于多 GPU 环境，可以使用以下参数：

- `--ulysses_size <N>`：Ulysses 并行大小
- `--ring_size <N>`：Ring Attention 并行大小

示例：
```bash
python scripts/infer_infinitetalk.py \
  --input_path ./input.jpg \
  --audio_path ./audio.wav \
  --output_path ./output.mp4 \
  --ulysses_size 2 \
  --ring_size 2
```
