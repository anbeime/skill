# Antinet · 八官署多智能体基础设施（GOAI 赛道一 · Agent Infra 新智基座）

> **复赛交付物**：一个**可执行的 AgentTeams 代码包** + 一个**可运行 Demo**。
> 本仓库即「复赛 · 可执行 AgentTeams 代码包」：1 个 Manager + 1 个 Team + 7 个 Worker，
> 全部基于真实可运行的八官署（Antinet）纯 Python 代码，零外部依赖、可完全离线运行。

---

## 0. 一句话说明

八官署（指挥使 / 军机处 / 锦衣卫 / 密卷房 / 通政司 / 监察院 / 丞相府 / 太史阁）被建模为
**AgentTeams（agentteams.io/v1beta1）** 的 Manager + Team + 7 Worker。每个 Worker 背后都是
真实可执行代码（非规划文档），并通过 4 个 Skill 暴露能力。系统产出**可溯源的四色卡片**
（事实蓝 / 解释绿 / 风险黄 / 行动红），并以端到端 provenance 证据链支撑可观测与审计。

---

## 1. 两条运行路径（复赛验收用）

### 路径 A · 免 Docker 本地 Demo（推荐评委一键验收）
在不依赖 Docker / MinIO / Matrix 的前提下，按 `manifests/manifest.yaml` 声明的 9 大 CR 在本地
装载八官署并跑通端到端主链路，证明代码包**真实可运行**。

```bash
python run_agentteams_local.py [--topic "SnSe 空位工程导热"] [--no-reset]
```

- 输出 AgentTeams 拓扑 → 指挥使分发 → 各官署 Worker 执行 → 四色卡片 + provenance。
- 产物：`examples/snse_survey/{blue,green,red,yellow}_cards.json`、`cards_index.json`、
  `scan_report.json`、`survey_report.json`、`agentteams_dispatch_trace.json`、
  `provenance/{trace.jsonl,trace_summary.json,knowledge.md}`。
- 最近一次运行日志：`examples/snse_survey/demo_run.log`（已附，全量派发/执行事件）。

### 路径 B · Docker / AgentTeams 集群部署（真实生产形态）
真实集群部署需 Docker；Worker 以 `copaw` 运行时装入 AgentTeams，由 Manager/Team 编排。

```bash
make install            # 安装 AgentTeams + copaw Worker 运行时（见框架文档）
kubectl apply -f manifests/manifest.yaml   # 声明 9 个 CR（Manager/Team/7 Worker）
# 每个 Worker 加载 worker_packages/<name>.zip（见第 3 节）
```

`manifests/manifest.yaml` 中每个 Worker CR 已声明 `state: Running` 与
`package: file://./worker_packages/<name>.zip`，与 `worker_packages/` 下生成的 ZIP 一一对应。

---

## 2. 项目结构

```
antinet-agentteams/
├── manifests/manifest.yaml        # 9 个 AgentTeams CR（Manager/Team/7 Worker）
├── core/                         # 八官署纯 Python 运行时（与集群内同一套代码）
│   ├── runtime.py                 # AgentSession：把八官署装载为 AgentTeams Worker 并编排
│   ├── command/ security/ archive/ comm/ audit/ strategy/ exec/ memory/  # 八官署各署
│   └── common/                   # config_loader / llm_client / card_model / logger
├── skills/                       # 4 个 Skill（赛道一必选项），每个含 SKILL.md + scripts/
│   ├── security-scan/            # 锦衣卫：合规安检
│   ├── doc-parse/                # 密卷房：多格式解析
│   ├── four-color-cards/         # 通政司+监察院+丞相府：四色卡片（--stage extract|review|propose）
│   └── provenance/               # 太史阁：全链路留痕
├── worker_packages/              # build_worker_packages.py 生成的 7 个可执行 Worker ZIP
│   ├── index.json                # 包清单（name/office/skill/stage/size）
│   └── <name>.zip × 7
├── examples/snse_survey/         # 样例调研输入(raw/) + Demo 产物
├── run_agentteams_local.py       # 路径 A：免 Docker 端到端 Demo
├── build_worker_packages.py      # 生成 7 个 Worker ZIP（框架兼容布局）
└── docs/                         # 初赛/方案材料（见第 5 节）
```

---

## 3. Worker 代码包（复赛硬性交付）

`python build_worker_packages.py` 将 7 个 copaw Worker 各打包成一个自包含 ZIP，布局对齐
AgentTeams Worker Package 规范：

```
<name>.zip
├── manifest.json        # apiVersion/runtime(copaw)/entrypoint/ stage
├── Dockerfile           # FROM agentteams/worker-agent:latest
├── run_worker.py        # 入口：AgentSession.run_stage("<stage>")
├── core/                # 八官署运行时（同仓库同一套代码）
├── config/              # AGENTS.md / SOUL.md / memory/
├── skills/<skill>/       # SKILL.md + scripts/（Leader 无 skill 则不含）
├── examples/snse_survey/raw/   # 最小可运行样例输入（保证包内可独立跑通）
├── crons/jobs.json
└── tool-analysis.json
```

> 已验证：抽取 `worker_packages/tongzhengsi.zip` 后直接 `python run_worker.py` 可真实执行并产出蓝卡。
> 每个包零外部依赖、可离线运行。

| Worker | 官署 | Skill | 主链路阶段 |
|--------|------|-------|-----------|
| zhihuiling | 指挥使 | —（Manager, openclaw） | 意图识别/分发 |
| junsicha | 军机处 | —（team_leader） | verify |
| jinyiwei | 锦衣卫 | security-scan | security-scan |
| mijuanfang | 密卷房 | doc-parse | doc-parse |
| tongzhengsi | 通政司 | four-color-cards | extract |
| jianchayuan | 监察院 | four-color-cards | review |
| chengxiangfu | 丞相府 | four-color-cards | propose |
| taishige | 太史阁 | provenance | provenance |

---

## 4. Skill 体系（赛道一必选项）

每个 Skill 都有**真实可执行脚本**（`scripts/run_*.py`），调用 `core.runtime.AgentSession.run_stage()`：

```bash
python skills/security-scan/scripts/run_security_scan.py
python skills/doc-parse/scripts/run_doc_parse.py
python skills/four-color-cards/scripts/run_four_color_cards.py --stage extract
python skills/four-color-cards/scripts/run_four_color_cards.py --stage review
python skills/four-color-cards/scripts/run_four_color_cards.py --stage propose
python skills/provenance/scripts/run_provenance.py
```

四色卡片**溯源铁律**由 `core/common/card_model.py` 强制：绿卡必须 cite 蓝卡、红卡必须 cite
绿卡/蓝卡，无来源不得入库。

---

## 5. 真实服务接入现状（非降级）

本系统在本机 Genie 生态内**真实点亮**了 LLM 与知识中枢，而非降级模拟。实测运行
（`examples/snse_survey/demo_run.log`）结论：

- **LLM 在环（真实）**：本地 NPU 模型端点 `Genie:8910`（OpenAI 兼容）**已接入并实测可用**，
  默认模型 `qwen2.5vl3b-8380-2.42` 实测返回真实文本；`llm_used=True`，端到端生成 3 张真·LLM 卡片
  （通政司抽取事实 / 监察院 Gap 评级 / 丞相府构效假说）。不可达时仍会如实标注 `llm_involved=False`，绝不伪造。
  **统一 LLM 亦支持我们的 FreeLLM**（OpenAI 兼容，默认 `:9000`）：本机用 `FREELLM_API_KEY` 注入 unified key；
  云端/异构环境用 `ANTINET_LLM_BASE_URL` 指向**云端可达的 FreeLLM 端点**，两条路径均为真实在环。
- **材料解析（真实）**：本机 **知易智能知识管家**（Genie 生态知识中枢，:8000）提供真实解析与灌库，
  密卷房调用 `/api/knowledge/import/text` 把论文全文**真实灌入平台知识库并完成向量化**
  （解析器标签：`知易平台-import(真实向量化)`），不再是预存全文模拟。
- **检索（混合·真实）**：太史阁优先调用平台 `/api/knowledge/search` 做真实关键词检索
  （英文术语如 `SnSe` 可命中灌库卡片）；中文查询平台命中为空时回退本地 CJK 二元切分
  （对中文反而更准）。两者均为真实实现，不冒充。
- **构效核验（MP）**：军机处已写入**真实 Materials Project REST 客户端**，已**实测点亮**——在设置
  `MP_API_KEY` 环境变量后，Demo 中 4 张红卡全部 `MP_API=on(真实调用)`，对宿主材料 `SnSe(mp-aaaaabap)`
  给出权威 **STABLE / e_above_hull=0（凸包稳定相）**，单质 `Sn/Se` 给出 MP 官方 **UNSTABLE** 判定，
  全部绑定真实 `material_id` 与 `materials_project_api:<id>` 来源。**缺 key 时如实标注「跳过真实核验」，绝不冒充 MP 结果**
  （这是外部云服务的硬依赖，需运行环境提供 key，非代码降级）。
- **可观测/审计（真实）**：太史阁 provenance 端到端证据链（`trace.jsonl` + `agentteams_dispatch_trace.json`）
  已实装并随每次运行刷新。

> 一句话：LLM、解析、检索三项接的是本机真实服务（Genie / 知易平台）；MP 核验为外部云，已实测可点亮（设 `MP_API_KEY` 即真实调用，缺则透明回退本地规则库）。四项均为真实实现，无降级冒充。

---

## 6. 初赛 / 方案材料（归档于 docs/）

`docs/track1/` 含初赛必交与方案材料：`project_intro.md`（作品简介）、`agent_identity.md`
（Agent Identity 清单·附录 A）、`skill_system.md`（Skill 工程体系）、`agentteams_mapping.md`
（八官署→AgentTeams 五维映射）、`deck_track1.md` + `Antinet_GOAI_track1.pptx`（方案 Deck）、
`Antinet_GOAI_track1_demo*.mp4`（演示视频）、`SUBMISSION_ONE_PAGER.html`（一页纸）。
`docs/submission_checklist.md` 为初赛自检清单。

---

## 7. 快速开始

```bash
# 1) 免 Docker 跑通端到端 Demo（推荐先跑这个，30 秒内出结果）
python run_agentteams_local.py

# 2) （可选）重新生成 7 个 Worker ZIP 包
python build_worker_packages.py

# 3) （可选）单独跑某个 Skill 验证其可独立执行
python skills/four-color-cards/scripts/run_four_color_cards.py --stage extract

# 4) （生产）Docker/AgentTeams 集群部署见路径 B
```

> 运行环境：Python 3.11+，零第三方依赖（仅标准库）。无需联网。
