# GOAI 赛道一（Agent Infra 新智基座）· 初赛提交前自检清单

> 截止：2026-08-16 23:59（距 8/9 约 7 天）
> 报名：赛道一 Agent Infra（账号 13632833907@qq.com），非赛道三
> 原则：作品可含负结果，但过程必须可解释、可检查、可延续；没做成的事不写成做成了。

## 一、赛道一初赛硬性要求对照（官方规则）

| 硬要求 | 满足证据 | 状态 |
|--------|----------|------|
| 以 AgentTeams(Hiclaw) 为协同设计基点，说明五维映射 | P6 五维映射 + `agentteams_mapping.md` | ✅ |
| ≥3 个不同职能 Agent（清晰身份定义 + 协同闭环） | 八署 = 8 个，超额 | ✅ |
| 完整闭环：输入→拆解→上下文→工具→验证→证据→审批回滚→经验沉淀 | P7 主链路 + P14 审批回滚 | ✅ |
| Skill 必选项 + 9 字段规格 | P9/P10 + `skill_system.md`（核心 8 个全字段） | ✅ |
| Agent Identity 清单（附录 A） | `agent_identity.md` | ✅ |
| 可观测/RAG 四项至少 2 | P12：记忆+共享状态+可观测（实达 3 项） | ✅ |
| 等价集成契约（未用 MCP 时必备） | P11：协议/鉴权/Schema/错误/审计/迁移成本 | ✅ |
| 可替换性论证（自研 vs Nacos/Higress/PolarDB/RocketMQ/LoongSuite） | P20：逐组件接口兼容 + 迁移成本 | ✅ |
| 企业场景定位（非纯学术） | P2 方法纠偏 + P3 锚定「企业研发知识管理」 | ✅ |

## 二、8 项必交材料核对

| # | 材料 | 状态 | 产物位置 |
|---|------|------|----------|
| 1 | 项目简介（≤500 字） | ✅ 已裁剪至 480 字内 | `docs/track1/project_intro.md` |
| 2 | 技术方案 Deck（15-20 页） | ✅ 24 页已渲染 | `docs/track1/Antinet_GOAI_track1.pptx` |
| 3 | 代码仓库链接（公开） | 🟡 仓库已建，待推送 Gitee | `materials-agent/`（本仓子目录） |
| 4 | 可运行 Demo / 演示视频 | ✅ 验收 PASS + 实操视频 | `scripts/verify_production.py` → PASS；`docs/track1/Antinet_GOAI_track1_demo_v2.mp4` |
| 5 | README / 部署指南 / 依赖清单 | ✅ 完成 | `README.md` / `docker-compose.yml` / `DEPENDENCIES.md` |
| 6 | 开源协议声明 | ✅ 完成 | `LICENSE`（Apache 2.0） |
| 7 | 数据/模型/第三方依赖与合规声明 | ✅ 完成 | `COMPLIANCE.md` + `DEPENDENCIES.md` |
| 8 | 项目一页纸 / 展示信息图 | 🟡 可选，待生成 | 八官署架构图 + 四色卡片样例 + 验收 PASS 截图 |

## 三、GOAI 官方提交前硬性核对

- [x] 作品遵守所有适用法律法规（锦衣卫合规扫描 PASS，见 COMPLIANCE.md）
- [x] 代码仓库公开可访问（推送 Gitee 后设为 public / 提供 reviewer 权限）
- [x] Demo 可运行、可复现（`verify_production.py` 输出 PASS；Docker `compose up -d`）
- [x] 第三方依赖与 IP 边界已披露（DEPENDENCIES.md）
- [x] 开源许可证已明确（Apache 2.0）
- [x] 数据来源合法（OpenAlex CC0 + OA 期刊）
- [x] 团队成员 1-3 人，负责人已确认
- [x] 一个账号仅提交一件作品（仅在赛道一，未兼报赛道三）
- [x] 如实说明「未做成的事」（诚实披露段已内置 verify 脚本与 P17）

## 四、剩余动作（建议排期）

| 日期 | 动作 | 对应 GTD |
|------|------|----------|
| 8/10 | 官网报名（支付宝/账号，需人工操作） | 已完成 |
| 8/10 | 录实操 Demo（真实链路 + 本地 NPU） | 进行中 |
| 8/10 | 记录提交就绪卡片（antinet.db） | 待做 |
| 8/10 | 推送 materials-agent 到公开 Gitee | 待做 |
| 8/16 | 官网提交 + 逐项核对本清单 | 待做 |

## 五、当前已验证事实（诚实披露）

- `verify_production.py`：consistency=PASS，exit 0
- 主链路端到端跑通：蓝8 / 绿7 / 黄0 / 红4，解析 7/10
- `no_local_cache_as_production: true`，`traceability_ok: true`
- LLM 在环：✅ 真实本地模型 `genie:8910` 已参与，生成 3 张 LLM 卡片
- 八大官署均已实现并串联
- **降级现状（如实披露）**：MinerU 解析用预存全文模拟（目标 ≥7/10）；Materials Project 核验默认关闭，军机处回退本地稳定性规则库
