# TOP 专家团 · 团队 / 调度层

> 本目录收录本地已搭建的 **TOP 专家团** 体系，与 `../skills/`（SkillHub 公开榜单采集）互为补充：
> 前者是「个人/组织的多团队协同调度层」，后者是「公开技能市场快照」。

## 包含内容

| 文件 | 说明 |
|------|------|
| [`agent-dispatcher/SKILL.md`](agent-dispatcher/SKILL.md) | **总调度中心**技能本体。智能任务分解、9 大团队协调、结果汇总。 |
| [`expert-team-config.md`](expert-team-config.md) | 专家团配置总览：9 大团队架构、团长技能、使用指令、技能存档清单。 |
| [`top-expert-team/config.json`](top-expert-team/config.json) | 真实的 WorkBuddy Team 定义（`top-expert-team`），含 lead agent 与工作目录。 |
| [`installed-skills.md`](installed-skills.md) | 用户级已装技能真实目录（扫描 `~/.workbuddy/skills/`，共 29 个），即各团队的实际成员技能。 |

## 九大团队速查

| # | 团队 | 团长技能 | 核心能力 |
|---|------|---------|---------|
| 🎯 | 总调度中心 | agent-dispatcher | 智能任务分解与多团队协调 |
| 📊 | 金融投资团 | investment-research | 选股·量化·财报·QMT |
| ✍️ | 内容创作团 | content-writer | 文案·调研·小红书·多引擎搜索 |
| 🎬 | 视频制作团 | openclaw-video-director | AI视频·抖音·截帧·音频 |
| 💻 | 技术开发团 | fullstack-dev | 全栈·小程序·支付·云开发 |
| 🛒 | 电商运营团 | ecommerce-ai-optimizer | 文案·视频·数字人·品类库 |
| 📚 | 知识管理团 | obsidian | 笔记·知识库·PDF |
| 📋 | 办公效率团 | pdfkit-py | PDF/PPT/Excel/Word/在线文档 |
| 🎮 | 创意娱乐团 | image-creator | 设计·音乐·故事·3D |
| 🌐 | 外部连接团 | qq-mail | 邮件·腾讯文档·金融数据 |

## 使用方式

| 指令 | 效果 |
|------|------|
| `全自动 [任务]` | 调度器自动分解→匹配团队→并行/串行执行→汇总交付 |
| `让 XX 团做 [任务]` | 指定团队执行 |
| `团队分析 [主题]` | 多团队并发出击 |
| `一条龙 [任务]` | 研究→创作→设计→交付 链路接力 |
| `迭代打磨 [内容]` | 初稿→审核→修改→定稿 |

> 注：本层为本地团队配置快照，技能本体仍以 `~/.workbuddy/skills/` 与 `../skills/`（SkillHub 采集）为准；
> `C:\D\skill\` 另存有 206 个扣子平台导出的 `.skill` 存档，可按需加载。
