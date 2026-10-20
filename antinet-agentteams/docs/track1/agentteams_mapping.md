# 八官署 → AgentTeams（Hiclaw）映射说明

> 赛道一要求：多 Agent 协同设计**必须以 AgentTeams 为设计基点**，说明角色编排、任务拆解、上下文传递、协同执行与状态追踪如何映射到该框架能力。
> 本说明是设计映射（初赛不强制提交可运行 AgentTeams 代码；复赛阶段再将八署实现迁移至 AgentTeams 运行时）。

---

## 一、AgentTeams 五大能力 ↔ 八官署映射

| AgentTeams 能力维度 | 八官署对应机制 | 说明 |
|--------------------|--------------|------|
| **角色编排 (Role Orchestration)** | 八署各司其职，指挥使=主控 Agent | 8 个具名角色，身份/边界/协同见《Agent Identity 清单》。指挥使持有全局角色注册表，类似 AgentTeams 的 AgentRegistry。 |
| **任务拆解 (Task Decomposition)** | 指挥使状态机 | 主题 → 检索/解析/抽取/审查/假说/核验/回流 子任务，逐署分发。 |
| **上下文传递 (Context Passing)** | 四色卡片结构化介质 | 蓝→绿→红 的 cite 链即上下文传递；每署只接收上游客官的卡片，不读原始噪声。 |
| **协同执行 (Collaborative Execution)** | 八署 pipeline 串联 | 各署产出卡片 → 下一署消费；支持并行（密卷房可批量解析多文档）。 |
| **状态追踪 (State Tracking)** | 太史阁 + provenance 日志 | 全链路 Trace/Log/Metrics 落盘，状态可被任意时刻回放。 |

---

## 二、迁移到 AgentTeams 运行时的等价契约

八署当前以 Python 类 + 标准库实现，复赛迁移到 AgentTeams 时**只需协议适配，不需重新设计工具调用链**：

| 八署概念 | AgentTeams 等价物 | 迁移成本 |
|---------|------------------|---------|
| `OrchestratorAgent` | 主控 Agent / Supervisor | 低：角色职责直接映射 |
| `JinYiWeiAgent` 等七署 | Worker Agent（具名 role） | 低：每个类包一层 AgentTeams Agent 包装 |
| 四色卡片 | AgentTeams Message / SharedState | 低：卡片 JSON 即消息 schema |
| `ProvenanceLogger` | AgentTeams Trace 后端 | 中：接入 LoongSuite / AgentScope Studio |
| `TaiShiGeAgent` 向量检索 | RAG / 共享状态管理 | 低：接 PolarDB 或既有向量库 |

**结论**：八署的工具调用链（解析→抽取→审查→假说→核验）与 AgentTeams 的 Agent→Skill→Tool 模型同构，迁移主要是协议适配，评审要求的"后续迁移成本"可控。

---

## 三、为何不直接用单 Agent

AgentTeams 的价值在于职责隔离与状态可见。八署将"检索/解析/抽取/审查/假说/核验"分离，使每个环节可独立验证、独立降级——单 Agent 把这些职责搅在一起，是参赛者"一周大半时间修 Docker"的根因。八署 + AgentTeams 角色模型，正是多智能体在复杂知识任务中的推荐架构。
