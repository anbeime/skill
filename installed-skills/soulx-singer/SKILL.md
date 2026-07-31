# SoulX-Singer 技能

零样本歌声合成助手 - 高质量 AI 歌声克隆与生成。

## 功能

- **歌声克隆**: 用任意音频样本克隆声音，生成歌声
- **多语言支持**: 中文、英文、粤语
- **MIDI 控制**: 通过 MIDI 乐谱控制旋律
- **WebUI 操作**: 提供图形界面操作指南

## 触发词

歌声合成、AI 唱歌、翻唱、声音克隆、歌声生成、SoulX、Singer

## 安装信息

| 项目 | 路径/版本 |
|------|----------|
| 项目目录 | `C:\D\projects\SoulX-Singer` |
| Conda 环境 | `soulxsinger` (Python 3.10) |
| Miniconda | `C:\Users\topgo\miniconda3` |
| 主模型 | `pretrained_models/SoulX-Singer/` |
| 预处理模型 | `pretrained_models/SoulX-Singer-Preprocess/` |
| 模型大小 | ~11.7 GB (66 文件) |

## 快速启动

### 方式一：启动脚本（推荐）
双击运行：`C:\D\projects\SoulX-Singer\start-webui.bat`

### 方式二：命令行
```powershell
# 激活环境
C:\Users\topgo\miniconda3\Scripts\activate.bat soulxsinger
# 进入项目目录
cd C:\D\projects\SoulX-Singer
# 启动 WebUI
python webui.py
```

访问地址: **http://localhost:7860**

## 使用流程

1. **准备参考音频**: 一段清晰的人声录音（10-30秒）
2. **准备歌词和旋律**: 歌词文本 + MIDI 文件
3. **启动 WebUI**: 运行 `python webui.py`
4. **上传素材**: 在界面中上传参考音频、歌词、MIDI
5. **生成歌声**: 点击生成，等待输出

## 常见问题

### 内存不足
- 关闭其他应用
- 降低生成长度

### 端口被占用
```bash
# 查找占用端口的进程
netstat -ano | findstr :7860
# 结束进程
taskkill /PID <进程ID> /F
```

### 模型下载失败
使用镜像站:
```bash
export HF_ENDPOINT=https://hf-mirror.com
```

## 技术参数

| 项目 | 规格 |
|------|------|
| 主模型大小 | ~5.2 GB |
| 预处理模型 | ~12 GB |
| 总空间需求 | ~17 GB |
| 推荐内存 | 16 GB+ |
| GPU 加速 | 可选 (CUDA) |

## 参考链接

- [官方教程](https://github.com/Alexanderava/SoulX-Singer-Tutorial)
- [原始项目](https://github.com/Soul-AILab/SoulX-Singer)
- [HuggingFace 模型](https://huggingface.co/Soul-AILab/SoulX-Singer)
