# 🎯 技能商店 - Skill Store

收录最全、更新最快的AI Agent技能库，涵盖**文档处理、内容创作、编程开发、机器学习、自动化工作流**等多个领域的精选技能包。

[![技能数量](https://img.shields.io/badge/技能-140+-blue?style=flat-square)](https://github.com/anbeime/skill)
[![本地已安装](https://img.shields.io/badge/本地已安装-41-green?style=flat-square)](https://github.com/anbeime/skill)
[![备份覆盖](https://img.shields.io/badge/备份覆盖-100%25-success?style=flat-square)](https://github.com/anbeime/skill)
[![自动更新](https://img.shields.io/badge/更新-每24小时-orange?style=flat-square)](https://github.com/anbeime/skill)

## 📊 统计数据

- **官方技能**: 140+ 个（来自 awesome-agent-skills）
- **本地已安装**: 41 个（19独立 + 3技能集 + 22子技能）
- **备份覆盖率**: 100%（73个压缩包，69.20 MB）
- **自动更新**: 每24小时自动爬取最新技能

## 🌟 核心特性

### 🤖 自动更新
每24小时自动爬取 [awesome-agent-skills](https://github.com/VoltAgent/awesome-agent-skills) 仓库，确保技能库始终保持最新状态。

### 📦 即开即用
所有技能已打包完成，下载即可使用，无需额外配置。

### 🏷️ 智能分类
按照功能、来源、Star数量等多维度标签进行分类整理。

### 📊 数据导出
支持JSON和CSV格式导出，方便数据分析和二次开发。

## 📚 技能来源

本技能商店收录了来自以下顶级团队的官方技能：

- **Anthropic** - docx, pptx, xlsx, pdf, mcp-builder, webapp-testing 等
- **Vercel** - react-best-practices, next-best-practices, composition-patterns 等
- **Cloudflare** - agents-sdk, durable-objects, wrangler 等
- **Google Labs** - design-md, enhance-prompt, react-components, remotion 等
- **Hugging Face** - model-trainer, datasets, evaluation, jobs 等
- **Stripe** - stripe-best-practices, upgrade-stripe
- **Trail of Bits** - building-secure-contracts, static-analysis, property-based-testing 等
- **Supabase** - postgres-best-practices
- **Expo** - expo-app-design, expo-deployment, upgrading-expo

## 🚀 快速开始

### 1. 克隆仓库

```bash
git clone https://github.com/anbeime/skill.git
cd skill
```

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

### 3. 运行更新

```bash
# 立即执行一次更新
python main.py --once

# 启动定时更新守护进程
python main.py --daemon

# 显示数据统计
python main.py --stats

# 导出为 CSV 格式
python main.py --export skills.csv

# 详细日志模式
python main.py --once -v
```

## 💾 本地技能库

### 已安装技能（41个）

#### 独立技能（19个）

1. **content-creation-publisher** - 内容创作与发布全流程
2. **intelligent-content-system** - 智能内容系统
3. **NanoBanana-PPT-Skills** - PPT生成
4. **obsidian-skills-integrated** - Obsidian集成
5. **infinitetalk** - 音频驱动视频配音
6. **tts-voice-synthesis** - 语音合成
7. **qwen3-tts-local** - 本地语音合成
8. **qwen3-asr-assistant** - 语音转文字
9. **agent-team** - 智能体团队协作
10. **multi-agent-meeting** - 多智能体会议
11. **product-manager-toolkit** - 产品经理工具包
12. **ai-drawio** - 流程图绘制
13. **three-body-video-creator** - 三体视频创作
14. **poetry-music-visual** - 诗词配乐
15. **moltbook** - AI Agent社交网络
16. **OpenCut-main** - 视频剪辑

#### 技能集（3个，包含22个子技能）

17. **baoyu-skills** - 宝玉技能集（17个子技能）
18. **jiamu-skills** - 佳木技能集（5个子技能）
19. **legal-assistant-skills-main** - 法律助手技能集（2个子技能）

## 📖 文档

- [技能管理数据库](docs/技能管理数据库.md) - 完整的技能索引和说明
- [技能清理与迁移指南](docs/技能清理与迁移指南.md) - 技能迁移和备份指南
- [整理完成报告](docs/D盘tool目录整理完成报告.md) - 详细的整理过程
- [技能数量差异分析](docs/技能数量差异分析报告.md) - 技能数量统计分析

## 🗂️ 技能分类

### 📄 文档处理
docx, pptx, xlsx, pdf 等文档创建和编辑（Anthropic官方）

### 🎨 创意设计
algorithmic-art, canvas-design, frontend-design（Anthropic官方）

### 💻 开发工具
mcp-builder, webapp-testing, web-artifacts-builder（Anthropic官方）

### ⚛️ React/Next.js
react-best-practices, next-best-practices, composition-patterns（Vercel官方）

### ☁️ Cloudflare
agents-sdk, durable-objects, wrangler（Cloudflare官方）

### 🤗 机器学习
model-trainer, datasets, evaluation, jobs（Hugging Face官方）

### 🔒 安全审计
building-secure-contracts, static-analysis, property-based-testing（Trail of Bits官方）

### 💳 支付集成
stripe-best-practices, upgrade-stripe（Stripe官方）

## ⚙️ 配置说明

### 环境变量

- `UPDATE_INTERVAL`: 更新间隔（默认24小时）
- `GITHUB_RAW_README_URL`: GitHub源地址
- `DATA_DIR`: 数据目录（data/）
- `LOG_DIR`: 日志目录（logs/）

### Windows 定时任务

支持两种方式：

1. **任务计划程序**: 使用 `setup_scheduled_task.ps1` 脚本设置
2. **Daemon 模式**: 使用 `start_daemon.bat` 启动守护进程

## 📊 数据格式

### skills.json

```json
{
  "skills": [
    {
      "name": "组织名/技能名",
      "description": "技能描述",
      "link": "GitHub链接",
      "category": "分类名称",
      "source": "来源仓库",
      "crawled_at": "2026-02-02T17:07:33"
    }
  ],
  "total": 140,
  "updated_at": "2026-02-02T17:07:33"
}
```

### local_skills.json

```json
{
  "metadata": {
    "total_skills": 41,
    "independent_skills": 19,
    "skill_collections": 3,
    "sub_skills": 22
  },
  "independent_skills": [...],
  "skill_collections": [...]
}
```

## 🔗 相关链接

- [GitHub仓库](https://github.com/anbeime/skill)
- [Awesome Agent Skills](https://github.com/VoltAgent/awesome-agent-skills)（官方技能源仓库，6.5k+ stars）
- [在线演示](https://skill.vercel.app)（即将上线）

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📄 许可证

MIT License

## 🙏 致谢

- [VoltAgent/awesome-agent-skills](https://github.com/VoltAgent/awesome-agent-skills) - 官方技能源仓库
- 所有贡献技能的开发团队和个人

---

**最后更新**: 2026-02-09  
**维护者**: anbeime  
**联系方式**: GitHub Issues