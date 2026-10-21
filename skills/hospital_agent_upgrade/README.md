# Hospital Agent Upgrade

基于 `hospital-agent-sdk` 的虚拟诊疗比赛医生 Agent 升级版。在官方 baseline 的诊疗闭环之上，进一步强化了**漏斗式多轮问诊、鉴别诊断驱动、检查维度评估、单例预算控制与临床安全网**，目标是让单例患者在「问诊 → 检查 → 诊断 → 治疗」全流程中做出与客观证据一致、可解释、个体化且不偏离金标准的诊疗决策。

> 仓库根目录对应原 baseline 示例目录（非 `baseline_example/` 子目录），所有命令直接在仓库根目录下运行。

## 升级版相对 Baseline 的关键改进

- **单例预算管理（`PatientCaseBudget` / `WorkflowLimits`）**：对每例患者单独跟踪 LLM 调用次数、主循环迭代次数和剩余时间；常规病例按 3 分钟目标收口，复杂病例最多使用 4 分钟兜底预算。
- **漏斗式多轮问诊**：`min_doctor_turns` / `max_doctor_turns` 控制 2-3 轮问诊，由宽到窄（主诉 → 既往史/用药/暴露 → 阴性体征/经济心理 → 鉴别关键点），并在关键病史（用药、过敏、激素/免疫抑制剂）不完整时强制补问。
- **病例画像（`case_profile`）**：每轮用 LLM 抽取结构化画像（人口学、主诉时间线、既往史、用药过敏史、暴露史、红旗征象、缺失关键字段等），并按上下文指纹缓存，避免重复调用。
- **鉴别诊断驱动（`differential`）**：不限科室先做鉴别诊断，作为后续科室选择、疾病候选、检查补齐和最终诊断对齐的核心线索；最终诊断会与 reasoning、differential 对齐，避免被单项阳性结果（如培养阳性、局部淋巴结肿大）错误锚定。
- **检查维度评估与分层补齐（`build_exam_need_summary` / `suggest_comprehensive_examinations`）**：按「基础严重程度 / 确诊或病因证据 / 治疗安全 / 受累器官或分型 / 红旗并发症」五个维度评估缺口，结合问诊结果、解剖路由与鉴别诊断推荐检查，采用少量多次开单；每轮只开当前疾病判断所需的关键检查，结果仍不明确时再补开下一项，并屏蔽当前病例下冗余的检查。
- **去单病种硬编码、证据驱动通用化**（本次升级重点，满足「所有诊断不针对单一疾病，按实际场景结合问诊与检查」）：
  - 诊断：移除 `DISEASE_ALIAS_TARGETS` 别名表与 `_apply_mechanism_evidence_overrides` 单病种强制覆盖，诊断候选只来自「鉴别诊断 + 病例/检查文本中出现的标准病名 + 科室目录」，由证据对齐管线（`_filter_unsupported_diagnoses → _rank_by_evidence → fallback`）确定，不再把特定疾病写死提为主诊断。
  - 治疗：`align_treatment_plan_with_mechanism` 不再按病名注入整段治疗模板（该模板曾在鉴别错位时把急性电解质危象误套成慢性冠心病方案），改为保留 LLM 生成的个体化方案，仅做通用安全网——按受累「生理系统」（电解质/肾/骨代谢/心血管）补齐可执行饮食细则。
  - 检查：`examiner.py` 移除 `_looks_like_<具体疾病>` 综合征识别器与固定检查清单，改为通用「症状→系统」路由（`_anatomy_exam_priorities`）、按病情广度生成候选预算后由执行层限制为 1-2 项/轮，并用通用局部性/感染信号判定冗余检查（`_redundant_exam_names`）以提升检查精确率。
  - 问诊：`planner._domain_specific_history_question` 由针对特定病的写死追问改为「主诉系统→高价值病史维度」通用探针，命中系统且关键病史缺失才追问。
  - Prompt：`DISEASE_AND_TREATMENT_PROMPT` / `FINAL_SELF_CHECK_PROMPT` 中的具体病名治疗协议（冠心病分型、瓣膜病术式、结缔组织病康复等）替换为按机制表述的通用原则（感染 vs 非感染、综合征 vs 病因、急性 vs 慢性分型、多问题并列）。
- **可迁移记忆（`agent/memory.py`）**：`MarkdownMemory` 只读取 `general_diagnosis_rules` / `general_examination_rules` / `general_treatment_rules` / `general_personalization_rules` 等可迁移规则，不注入单个病例细节；训练阶段按病例 upsert 反思块。
- **LLM 调用健壮性**：每次 LLM 调用带超时（`llm_call_timeout_seconds`）、JSON 解析失败时自动调用一次 `JSON_REPAIR_SYSTEM_PROMPT` 修复，并对返回 action / 检查名 / 疾病名做标准目录归一化匹配。
- **可选第三方术语匹配增强**：项目支持接入 `rapidfuzz` 这类第三方模糊匹配库，用于疾病名、检查名和科室名的标准化对齐；未安装时自动退化为纯 Python 匹配，不影响主流程运行。

## 目录说明

```text
hospital_agent_upgrade/
├── agent/
│   ├── __init__.py
│   ├── agent.py          # 医生 Agent 主编排：问诊/检查/诊断/治疗闭环、预算控制、服务调用
│   ├── diagnoser.py      # 诊断与治疗对齐：候选疾病归一化、证据过滤、治疗安全网
│   ├── examiner.py       # 检查路由：检查类别/项目选择、冗余过滤、检查目的说明
│   ├── memory.py         # Markdown 记忆：只读取可迁移 general_* 规则，按病例 upsert 反思
│   ├── planner.py       # 问诊与流程编排：阶段机、问题生成、自检门禁
│   ├── prompt.py         # Prompt 模板：系统提示、问诊/鉴别/检查/诊断/治疗/自检/反思
│   ├── terminology.py    # 可选第三方术语匹配：rapidfuzz 增强，纯 Python 兜底
│   └── utils.py          # 通用工具：标准名归一化、目录加载、JSON 解析、去重等
├── data/
│   ├── memory_data/
│   │   └── memory.md     # 本地文件记忆（可迁移规则 + 各病例反思块）
│   └── ref_data/
│       ├── departments.json
│       ├── diseases_catalog.json
│       └── examinations_catalog.json
├── outputs/               # 本地训练/测试产物：events、final_results、评测报告、prompt trace
├── tests/                 # 回归测试：诊疗流程、记忆、检查、诊断与测试脚本
├── config.yaml           # 训练/测试/memory/workflow 等配置
├── train.py              # 本地训练入口
├── test.py               # 本地测试与批量评估示例
├── requirements.txt      # 第三方依赖（hospital-agent-sdk）
├── Dockerfile            # 部署入口，默认启动 python3 -m agent.agent
└── README.md
```

如果你要继续细化临床细节，通常会按职责拆到这些文件：

- `agent/planner.py`：问诊轮次、阶段切换、补问逻辑、流程门禁。
- `agent/examiner.py`：检查类别选择、具体检查项选择、冗余检查过滤。
- `agent/diagnoser.py`：最终诊断候选、证据对齐、治疗方案安全网与个体化兜底。
- `agent/prompt.py`：临床规则、输出 JSON 结构、反思字段、失败兜底提示。
- `agent/terminology.py`：可选术语匹配层，优先使用第三方模糊匹配库，缺失时回退到内置实现。
- `agent/utils.py`：标准名称归一化、目录加载、病例上下文指纹、JSON 解析。
- `tests/`：回归测试，优先在这里补新增病例模式和规则修正。

注意：

- `data/memory_data/` 可以根据你选用的记忆存储形式自定义。baseline 默认使用本地 `memory.md`，你也可以改成 JSON、SQLite、向量数据库或其他形式。
- 记忆的存储形式不限定；如果使用数据库或对象存储等外部服务，需要使用可直接访问的外部存储服务。
- 部署环境不能依赖 `docker-compose` 拉起额外服务，因此不要把数据库、向量库等作为同一个提交中的 compose 依赖。
- `data/ref_data/` 是标准科室、疾病和检查名称，不要修改；提交结果中的诊断和检查名称必须使用这里提供的标准名称。
- `outputs/` 是本地训练/测试运行产物目录，包含 `events.jsonl`、`final_results.jsonl`、`final_results_eval_report.json`、`run_summary.json` 和 `llm_prompts/`；这些内容适合用来分析错误模式，不建议手工改写。
- 如果你要进一步提升名称对齐效果，可以额外安装 `rapidfuzz`；项目会自动使用它增强模糊匹配，并在缺失时保持兼容。
- `Dockerfile` 一般不需要修改，以免影响平台部署和评测，默认已经包含部署入口和启动命令。
- `train.py` 是本地训练入口，可以按需修改；`test.py` 展示了启动 Agent 服务、调用 `/test`、批量评估结果的完整本地测试流程。


#### `workflow`

升级版新增的单例诊疗流程预算控制。`max_patient_minutes` 为常规收口目标；复杂病例可启用 `special_case_max_patient_minutes` 兜底，但最长不超过 4 分钟。问诊阶段优先保障最低轮次，离开问诊后用剩余时间推动检查和最终诊疗收口；LLM 调用次数与主循环迭代次数仍作为防死循环硬上限。

- `workflow.max_patient_minutes`：单例患者完整诊疗流程的时间软目标（分钟）。默认 `3`，系统会优先在该时限内收口。
- `workflow.special_case_max_patient_minutes`：复杂病例的兜底上限（分钟）。默认 `4`，仅在高复杂度病例触发。
- `workflow.min_doctor_turns` / `workflow.max_doctor_turns`：问诊轮次上下限，采用漏斗式提问；未达下限不允许进入诊断，达到上限则强制转入开检查或诊断。
- `workflow.max_exam_rounds`：开检查轮次上限；默认少量多次开具高价值检查，单项结果足以支持具体疾病时直接进入诊断，不足时再补开下一轮。
- `workflow.max_main_loop_iterations`：主循环迭代硬上限，防死循环。
- `workflow.max_llm_calls_per_patient`：单例患者 LLM 调用硬上限；达到后只走兜底逻辑。
- `workflow.llm_call_timeout_seconds`：单次 LLM 调用超时秒数；超时返回默认值并继续。
- `workflow.service_call_timeout_seconds`：问诊和检查等比赛服务调用超时秒数；远端服务长时间无响应时返回保守兜底并继续流程。
- `workflow.evaluation_call_timeout_seconds`：训练评估服务调用超时秒数；评估通常比问诊/检查慢，因此单独配置。
- `workflow.force_diagnosis_buffer_seconds`：剩余时间低于该值时提示进入诊断；代码会自动确保其小于总时长。

#### `memory`

升级版默认使用 `MarkdownMemory`：训练阶段按病例 upsert 反思块（含 `profile` / `diagnosis_reflection` / `examination_reflection` / `treatment_reflection` / `future_strategy`，以及 `general_diagnosis_rules` 等可迁移规则），运行时 `load_notes` 只读取 `general_*` 可迁移规则注入 prompt，不注入单个病例细节。

- `memory.md_path`：记忆文件路径，默认 `data/memory_data/memory.md`。
- `memory.max_notes`：注入 prompt 的可迁移规则最大条数。
- `memory.max_note_chars`：单条反思字段的最大字符数，超出自动截断。

python test.py
```

该脚本会自动启动 Agent 服务，调用 `POST /test` 生成 `final_results.jsonl`，再调用 `batch_evaluation` 进行批量评估并输出测试和评估结果。同时会生成 `diagnostic_metrics.json`，按病例统计 `CASE_START` 到 `CASE_END` 的耗时、LLM 调用次数及调用类型分布。

已有测试产物可直接分析，无需重新请求服务：

```bash
python3 test_metrics.py outputs/test/test_20260811_170448_320338
```

统计结果中的 `duration_seconds` 是该病例在测试运行中的实际墙钟耗时；`llm_calls` 优先读取最终结果中的运行时计数，旧产物则从 `llm_prompts` 追加记录回算。
