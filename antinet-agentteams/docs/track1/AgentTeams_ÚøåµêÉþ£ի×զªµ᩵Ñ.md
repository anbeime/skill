# AgentTeams 集成真实度核查（GOAI 赛道一 baseline 符合性）

> 核查日期：2026-08-16 | 方法：离线比对 `antinet-agentteams/manifests/manifest.yaml`
> 与框架真实 CRD（`C:/D/zhiyi/AgentTeams/agentteams-controller/config/crd/*.yaml`）+ 拆包验证
> 结论：**声明/设计级 = 真结合；执行级 = 未实证（缺运行证据）**

---

## 0. 一句话结论

`antinet-agentteams` **不是"假结合"**——它的 manifest 确实按 AgentTeams(Hiclaw) 真实 CRD schema 写的，
`apiVersion`/`kind`/`runtime` 枚举/`package` URI 全部命中框架，Worker ZIP 也真实生成。
但存在两类真问题：

1. **装饰性非法字段**：manifest 里混入了框架 CRD 根本不存在的字段
   （`config`/`resources`/`state`/`heartbeatEvery`），说明这份 manifest **从未对活体 schema 校验过**。
2. **执行级缺口（复赛致命）**：本地入口是自建 Python 编排器，不是 AgentTeams 会话；
   本机 Docker 不可用，7 个 Worker ZIP（8/11 构建好）**从未被 `agentteams-apply/import` 进活体集群**。
   因此"结合 AgentTeams 仓库**运行**"在实证层面是缺的。

---

## 1. 字段级对撞（定点 grep 框架 CRD，仅信此结果）

| 资源 | antinet 用的字段 | 框架 CRD 是否真实 | 处置 |
|------|------------------|-------------------|------|
| 全部 | `apiVersion: agentteams.io/v1beta1` | ✅ 真 | — |
| Manager/Team/Worker | `kind` | ✅ 真（CRD 已注册三类） | — |
| Manager | `runtime: openclaw` | ✅ 命中 enum `[openclaw,copaw,hermes,qwenpaw]` | — |
| Worker×7 | `runtime: copaw` | ✅ 命中 enum | — |
| Worker×7 | `package: file://./worker_packages/X.zip` | ✅ 命中官方 Package URI 格式（`file://, http(s)://, nacos://, packages/{name}.zip`） | — |
| Manager/Worker | `soul` / `agents` | ✅ 真（生成 SOUL.md/AGENTS.md） | — |
| Worker（部分） | `skills:`（复数数组） | ✅ 真（array of string） | — |
| Worker | `model: qwen3.5-plus` | ✅ 必填字段存在（值需网关有该模型） | — |
| Team | `workerMembers[].role: team_leader/worker` | ✅ 真（Team CRD 含 role/team_leader） | — |
| **Manager** | `config.heartbeatInterval/workerIdleTimeout/notifyChannel` | ❌ **框架无 `config` 字段** | apply 被裁剪 |
| **Manager** | `resources.requests/limits` | ❌ 框架 Manager CRD 无 `resources` | apply 被裁剪 |
| **Worker×7** | `resources.requests/limits` | ❌ 框架 Worker CRD 无 `resources` | apply 被裁剪 |
| **Worker×7** | `state:` | ❌ 非 spec 字段（应是 status 子资源） | apply 被裁剪 |
| **Team** | `heartbeatEvery: 30m` | ❌ 框架 Team CRD 无此字段 | apply 被裁剪 |

> 说明：被裁剪的字段**不阻断 CR 创建**（CRD 未设 `preserve-unknown-fields` 时服务端会 prune），
> 但它们暴露一个事实——这份 manifest 是"手写对齐文档"而非"对活体 API server 跑通过的"。

---

## 2. 执行级核查（决定复赛能否过关）

| 检查项 | 现状 | 是否真结合 |
|--------|------|-----------|
| `run_agentteams_local.py` 是否启动/连接 AgentTeams controller | ❌ 否，是自建 `AgentSession` Python 编排器，打印 ROLE_MAP 表后直接调八官署方法 | 否（仅"同等代码免容器运行"） |
| 是否对活体集群跑过 `agentteams-apply.sh -f manifest.yaml` | ❌ 否，本机 Docker 不可用，zip 8/11 建好后从未 apply | 否 |
| 是否跑过 `agentteams-import.sh worker --zip ... --runtime copaw` | ❌ 否 | 否 |
| Worker ZIP 内 `manifest.json(kind:WorkerPackage)+run_worker.py` 是否被 copaw 真调用 | ❓ 未验证；copaw 真入口是 `copaw-worker-entrypoint.sh`，`run_worker.py` 是自建约定 | 待 live import 验证 |
| 知识库闭环（前次结论 P0） | ❌ recall 未进主链路、writeback 不灌卡 | 与 AgentTeams 无关，但赛道一"可审计/RAG"硬指标缺 |

---

## 3. 对赛事 baseline 的判定

- **初赛（今天 23:59 截止，只需简介+PPT）**：✅ 满足。
  manifest 合规足以支撑"以 AgentTeams 为设计基点"叙事；PPT(`Antinet_GOAI_track1.pptx`)+
  简介(`project_intro.md` 480字)已就绪。
- **复赛（需可执行 AgentTeams 代码包 + live 演示）**：🔴 当前**缺执行级证据**。
  若评委要求真跑 AgentTeams 调度，本地入口与未 apply 的 zip 会暴露"声明结合但未运行结合"。

---

## 4. 让它"真结合"的最小行动（按优先级）

1. **【立即可做·零依赖】清掉 manifest 非法字段**：删 Manager `config`/`resources`、
   Worker `resources`/`state`、Team `heartbeatEvery`（或改到框架真实字段），
   让 manifest 对 schema 零裁剪。改完用框架校验器/活体 `kubectl apply --dry-run=server` 复核。
2. **【复赛必需】真跑 apply+import**：在 Cloud Studio 形态 B（有 Docker）执行
   `agentteams-apply.sh -f manifest.yaml` + `agentteams-import.sh worker --zip worker_packages/X.zip --runtime copaw`，
   截图活体 CR 状态 + 一次真实 Team 调度日志作为证据。
3. **【复赛必需】对齐 Worker 包入口**：确认 copaw 拉取 `package` zip 后如何触发八官署逻辑，
   若需 `copaw-worker-entrypoint.sh` 风格入口，补齐使 `run_worker.py` 被真调用。
4. **【与 AgentTeams 无关但赛道一硬指标】补知识库闭环 P0**：recall 进 `run_full()` 主链路 +
   writeback 对每张卡调 `zhijia.import_text()`（详见 `GOAI_知识库集成_差距分析_修正.md`）。
5. **【初赛收尾】推公开仓库 + 官网提交**：现仅 Gitee 私有；用 `13632833907@qq.com` 交简介+PPT。
