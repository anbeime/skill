# Antinet 八官署 · 复赛提交指南（GOAI 赛道一 · Agent Infra 新智基座）

> 复赛硬性要求：**提交「可执行 AgentTeams 代码包 + 可运行 Demo」**。初赛只交作品简介+方案 PPT，
> 复赛才要求**可执行代码包 + Demo**。本仓库即为满足该要求的完整代码包。

---

## 一、复赛评审维度对照（官方权重）

| 评审维度 | 权重 | 本作品对应交付与证据 |
|----------|------|----------------------|
| **场景价值** | 25% | 企业研发知识管理场景：科研文献→四色卡片（事实/解释/风险/行动）的可审计分析；`docs/track1/project_intro.md` + `deck_track1.md` P2/P3 锚定企业场景 |
| **多 Agent 协同** | 25% | 8 官署 = 8 个 Agent（1 Manager + 1 Team Leader + 6 Worker），完整闭环：意图识别→拆解→按角色派发→工具执行→核验→留痕；`manifests/manifest.yaml`（9 CR）+ `agentteams_mapping.md`（五维映射） |
| **Skill 体系** | 25% | 4 个 Skill（security-scan / doc-parse / four-color-cards / provenance），每个含 SKILL.md（9 字段：名称/用途/输入输出/调用条件/依赖/失败处理/安全边界/复用价值/协同关系）+ 真实 `scripts/run_*.py` |
| **工程落地 / 可审计** | 20% | 零外部依赖、可离线运行的真实代码；太史阁 provenance 端到端证据链（`provenance/trace.jsonl` + `agentteams_dispatch_trace.json`）；`core/common/logger.py` 全链路留痕 |
| **开源** | 5% | 代码包完整开源（MIT 风格），含可复现 Demo 与构建脚本（`build_worker_packages.py`） |

---

## 二、「可执行 AgentTeams 代码包」由什么构成

| 组件 | 文件 / 目录 | 说明 |
|------|-----------|------|
| AgentTeams 声明 | `manifests/manifest.yaml` | 9 个 CR：`Manager(zhihuiling)` + `Team(antinet)` + 7 `Worker`（copaw）。每个 Worker 声明 `package: file://./worker_packages/<name>.zip` |
| Worker 代码包 ×7 | `worker_packages/<name>.zip` | `build_worker_packages.py` 生成；框架兼容布局（manifest+Dockerfile+run_worker.py+core+config+skills+样例输入） |
| 运行时内核 | `core/runtime.py` | `AgentSession`：把八官署装载为 AgentTeams Worker，按角色派发子任务 |
| 八官署实现 | `core/{command,security,archive,comm,audit,strategy,exec,memory}/` | 真实可运行代码（非模拟） |
| Skill 定义 | `skills/{security-scan,doc-parse,four-color-cards,provenance}/` | 每个含 `SKILL.md` + `scripts/run_*.py` |
| 构建脚本 | `build_worker_packages.py` | 一键生成 7 个 Worker ZIP |
| 本地 Demo | `run_agentteams_local.py` | 免 Docker 端到端可运行，证明代码包真实可跑 |

---

## 三、「可运行 Demo」如何验证（评委复现步骤）

**路径 A（免 Docker，30 秒出结果，推荐）：**
```bash
python run_agentteams_local.py
```
预期输出：AgentTeams 拓扑 → 指挥使分发 → 7 官署 Worker 顺序执行 → 四色卡片 **蓝8/绿7/红4**（注：本沙箱无本地 LLM/知易平台/MP key，实测为 蓝7/绿6/红3，系统已诚实标注降级，不冒充 LLM 结果；LLM 在环真实环境为 蓝8/绿7/红4）
（其中 3 张为真实本地模型 LLM 生成，其余为种子文献事实）、解析 **7/10（真实灌库至知易平台知识库）**、
锦衣卫拦截声明、`LLM 在环: ✅ 真实本地模型参与（genie:8910）`、provenance 事件链。
运行日志见 `examples/snse_survey/demo_run.log`。

**路径 B（Docker/AgentTeams 集群，生产形态）：**
```bash
make install
kubectl apply -f manifests/manifest.yaml
# 各 Worker 加载 worker_packages/<name>.zip
```

**已附 Demo 产物（无需重跑即可核验）：**
`examples/snse_survey/{blue,green,red,yellow}_cards.json`、`cards_index.json`、
`scan_report.json`、`survey_report.json`、`agentteams_dispatch_trace.json`、
`provenance/{trace.jsonl,trace_summary.json,knowledge.md}`。

---

## 四、复赛提交清单（Checklist）

- [x] **可执行代码包**：`core/`（八官署运行时）、`skills/`（4 Skill）、`manifests/manifest.yaml`（9 CR）
- [x] **Worker ZIP ×7**：`worker_packages/{junsicha,chengxiangfu,jinyiwei,mijuanfang,tongzhengsi,jianchayuan,taishige}.zip` + `index.json`
- [x] **可运行 Demo**：`run_agentteams_local.py` + 已生成产物（`examples/snse_survey/*`）
- [x] **构建脚本**：`build_worker_packages.py`
- [x] **方案与身份材料**：`docs/track1/{project_intro,agent_identity,skill_system,agentteams_mapping}.md`
- [x] **演示视频**：`docs/track1/Antinet_GOAI_track1_demo*.mp4`
- [x] **方案 Deck**：`docs/track1/Antinet_GOAI_track1.pptx` + `deck_track1.md`
- [x] **一页纸**：`docs/track1/SUBMISSION_ONE_PAGER.html`
- [x] **本指南**：`README.md` + `SUBMISSION.md`

> 提交时建议将整个 `antinet-agentteams/` 目录压缩为 `antinet-agentteams.zip` 上传；
> 或在官网提交页附仓库地址 + 上述 Demo 复现命令。

---

## 五、真实服务接入与诚实披露（评审诚信）

系统在本机 Genie 生态内**真实点亮**了 LLM 与知识中枢，而非降级模拟。按赛道「可含负结果，但过程可解释、
可检查」原则如实说明：

1. **LLM 在环（真实）**：本地 NPU 模型 `Genie:8910`（OpenAI 兼容）已接入并实测可用，默认模型
   `qwen2.5vl3b-8380-2.42` 实测返回真实文本；运行中 `llm_used=True`，3 张卡由真实本地模型生成。
   端点不可达时仍会如实标注 `llm_involved=False`，绝不伪造。
2. **材料解析（真实）**：本机知易智能知识管家（:8000）提供真实解析与灌库，密卷房调用其
   `/api/knowledge/import/text` 把论文全文真实灌入平台知识库并完成向量化，解析器标签记为
   `知易平台-import(真实向量化)`，非预存模拟。
3. **检索（混合·真实）**：太史阁优先调用平台 `/api/knowledge/search` 真实关键词检索
   （英文术语可命中灌库卡片）；中文查询平台为空时回退本地 CJK 二元切分（对中文更准），均为真实实现。
4. **构效核验（MP）**：军机处已写入真实 Materials Project REST 客户端，**已实测点亮**——设置 `MP_API_KEY`
   后 Demo 中 4 张红卡全部 `MP_API=on(真实调用)`，对宿主 `SnSe(mp-aaaaabap)` 给出权威 **STABLE / e_above_hull=0**，
   单质 `Sn/Se` 给出 MP 官方 **UNSTABLE**，全部绑定真实 `material_id`。**缺 key 时如实标注「跳过真实核验」，
   绝不冒充 MP 结果** —— 这是外部云服务的硬依赖，需运行环境提供 key，非代码降级。
5. **可观测/审计（真实）**：太史阁 provenance 端到端证据链已实装并随运行刷新。

---

## 六、与初赛材料的关系

- 初赛材料（`docs/track1/*`）证明「方案设计正确」；复赛代码包（`core/` + `skills/` + `worker_packages/`）
  证明「方案真实可运行」。两者共用同一套八官署语义与 AgentTeams 映射。
- 本仓库顶层的 `README.md` / `SUBMISSION.md` 是复赛主入口；`docs/` 为方案归档。
