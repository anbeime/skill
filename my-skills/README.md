# 我的自定义 Skills 合集

> 从 TRAE 工作区整理归档的个人 Skill 集合，共 **13** 个技能，按业务领域分为 **6** 类。

每个技能都包含完整的 `SKILL.md`，可直接复制到 AI 助手对话中使用，或放入 `~/.trae/skills/` 目录生效。

## 分类导航

| 分类 | 技能数 | 覆盖内容 |
| --- | --- | --- |
| [🚗 汽车营销获客](./01-汽车营销获客/) | 2 | 面向汽车经销商的获客内容生产：品牌视觉海报提示词、小红书爆款文案。 |
| [🎬 短视频创作](./02-短视频创作/) | 4 | 从选题钩子到拍摄台本再到标题文案的短视频全链路生产工具。 |
| [📺 直播运营](./03-直播运营/) | 1 | 售后/维修门店的可持续系列直播策划与台本体系。 |
| [✍️ 内容创作与改写](./04-内容创作与改写/) | 2 | 公众号文章深度改写与日常口播稿生成。 |
| [📊 数据采集与分析](./05-数据采集与分析/) | 2 | 视频号数据采集与商业文章/案例的批判性分析。 |
| [🛠️ 效率工具](./06-效率工具/) | 2 | 网页离线归档与 GitHub CLI 操作参考。 |

## 全部技能一览

### 🚗 汽车营销获客

- **auto-poster-seedance** — Builds paste-ready AI image prompts for 9:16 automotive brand posters (早安/午安/晚安/雨夜/商务/节气) with swappable car model, paint color, scene and lighting. Invoke for 汽车海报提示词/生图提示词/换车型换颜色/海报风格库.
- **小红书爆款文案** — 为宝驰汇·三禾名车生成小红书爆款文案。输入车型/关键词，输出完整标题+正文+标签+投放建议。当用户提供车型关键词（如\"宝马X5\"、\"适合女生的车\"）时立即调用。

### 🎬 短视频创作

- **storyline-video-shooting-script** — 故事线纪实爆款短视频拍摄台本生成器。为汽修/服务类门店生成可直接执行的完整拍摄台本（接单→上门→痛点→维修→交车全流程），坚持真实记录、禁止摆拍。当用户描述一个真实服务事件（如上门修车、售后保养、救援）并要求按故事线拍成爆款视频时调用。
- **video-title-subtitle-copywriter** — 汽修/汽车短视频标题、副标题与话题标签生成器。输入车型、维修项目与亮点，一键产出可直接发布的标题、副标题、#话题标签、封面大字和转发推荐语，适配视频号/抖音/小红书。当用户剪完视频要写标题、副标题、文案或话题标签时调用。
- **car-video-prompt** — Automotive video prompt specialist for Seedream/Seedance. Invoke when user provides a car photo and needs a professional video generation prompt for AI video tools.
- **viral-hooks** — Analyzes Douyin/TikTok videos to extract viral hooks, and generates viral copy using a 200+ hook database. Invoke when user provides a video URL for hook analysis or asks to write viral copy/hooks.

### 📺 直播运营

- **aftersales-live-script** — 为汽修/名车/售后门店生成可持续系列直播的完整脚本体系：板块排期 + 对话式车间走播台本 + 留资钩子话术 + 合规红线 + 复盘口径。当用户要做售后维修保养直播、开播台本、直播话术、板块排期或直播策划时调用。

### ✍️ 内容创作与改写

- **wechat-rewrite** — 微信公众号文章洗稿改写。用户提供公众号文章时触发，进行深度重写、去AI味处理、规避平台违规风险。参考了AIWriteX等多智能体协作框架的洗稿方法论，安全合规地输出高品质原创内容。
- **morning-greeter** — 私人早安播报员 - 生成懂节气、知农历、有温度的30秒早安口播稿。融入汽车行业视角。自动查2026年节气节日。Invoke when user says '早安' '早安文案' '早安播报' 'morning greeting' or asks for daily oral script.

### 📊 数据采集与分析

- **wechat-channels-helper** — 微信视频号数据采集与分析助手。支持视频搜索、博主搜索、评论采集、单条/批量视频数据提取、口播文案提取、视频分析、文案改写。当用户需要采集视频号数据、分析视频号内容、提取视频号博主信息时调用。
- **business-insight-analyzer** — 商业文章与案例的深度批判性分析框架，将分析升级为审计报告。当用户提供文章链接（微信/公众号/网页/PDF）、粘贴全文或商业案例，并要求分析、评价、判断对错、拆解逻辑、验证观点时使用。Deep critical analysis of business articles and cases with evidence audit, logic review, interest analysis and reliability rating. Invoke when the user asks to analyze or evaluate an article, case study, or business insight.

### 🛠️ 效率工具

- **webpage-archiver** — 封装完整网页（HTML+图片+CSS+JS）到本地归档。当用户提供URL需要保存网页离线副本、打包网页做公司背书存档、或批量归档网页内容时使用。保存到 D:\\家富三禾农林\\网页封装\\
- **gh-cli** — GitHub CLI (gh) comprehensive reference for repositories, issues, pull requests, Actions, projects, releases, gists, codespaces, organizations, extensions, and all GitHub operations from the command line.

## 使用方法

1. 复制某个技能的 `SKILL.md` 全文
2. 粘贴到 AI 助手对话中，或保存到 `~/.trae/skills/<技能名>/SKILL.md`
3. 直接说「用 <技能名> 帮我…」即可触发
