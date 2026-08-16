---
name: security-scan
description: 对进入系统的文件或 URL 执行安全与合规扫描，输出 pass/reject 判定与扫描报告，作为所有文档处理的强制前置关卡。
assign_when: 该 Worker 是文档入口的安全守门人，负责域名黑名单、OA 许可校验与可疑来源拦截；任何文件进入系统前必须经其把关。
---

# 合规安检 Skill（锦衣卫）

## 使用方式
- 由锦衣卫 Worker 在收到文件/URL 时调用，作为流水线的第一道闸门。
- 输出结构化判定（`pass` / `reject`），并写入 provenance 交由太史阁留痕。

## 输入（Input）
- `target`：待检对象，二选一
  - 本地文件路径（PDF / PPT / Excel / Word / 图片）
  - 外部 URL（需先解析域名）
- `policy_ref`：（可选）覆盖默认策略的合规规则集引用

## 输出（Output）
- `verdict`：`pass` 或 `reject`
- `report`：安全扫描报告，含命中的黑名单项、许可状态、风险等级
- `trace_id`：本次扫描的 provenance 追踪 ID（用于太史阁留痕）

## 依赖（Dependencies）
- Sci-Hub 等已知违规域名黑名单（本地 CSV/JSON）
- OA 文档许可校验库（本地规则）
- 文件类型探测（`python-magic`）

## 失败处理（Failure Handling）
- 扫描服务不可用：**拒绝文件并告警**，绝不降级放行（零信任底线）。
- 文件类型无法识别：标记 `reject` 并写入原因，交由管理员确认。
- 黑名单库读取失败：回退到「全拒 + 告警」保守策略，并提示运维修复。

## 复用价值（Reuse Value）
- 与具体业务解耦：任何文档处理系统（RAG、知识库、合同审查）均可直接挂载此 Skill 作入口安检。
- 判定标准可配置：通过替换 `policy_ref` 适配不同行业的合规基线。

## 复赛代码包执行（runnable package）
- 真实入口：`scripts/run_security_scan.py`
- 执行等价于 `core.runtime.AgentSession.run_stage("security-scan")`，调用 `security.jinyiwei.JinYiWeiAgent`（纯 Python，零外部依赖，可离线运行）。
- 运行：`python skills/security-scan/scripts/run_security_scan.py`
- 产物：`examples/snse_survey/skill_outputs/security_scan.json`（黄卡 + 扫描报告）。
