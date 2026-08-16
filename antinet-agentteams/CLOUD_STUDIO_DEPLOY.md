# 八官署 → AgentTeams 部署 SOP（双跑：本地免 Docker + 云端平台）

> 复赛窗口期（8/16–8/25）交付两种运行形态，**同一套代码**：
> - **形态 A · 本地免 Docker 跑**：用 `run_agentteams_local.py` 在任意装有 Python 的机器上直接跑通八官署主链路，
>   无需 Docker / MinIO / Matrix，评委一键复现（最稳保底）。
> - **形态 B · 云端平台跑**：在 **腾讯云 Cloud Studio · All in One** 容器里真实拉起 AgentTeams 平台，
>   apply 9 个 CR（1 Manager + 1 Team + 7 Worker），由 Manager/Team Leader 真实编排。
>
> **统一 LLM = 我们的 FreeLLM**（OpenAI 兼容）：
> - 本地：FreeLLM 在 `http://localhost:9000/v1/chat/completions`，用 `FREELLM_API_KEY` 注入 unified key；
>   若本机同时有 Genie(8910) 则 Genie 优先（同源本地模型）。
> - 云端：用 `ANTINET_LLM_BASE_URL` 把 Worker 主链路 LLM 指向**云端可达的 FreeLLM 端点**，
>   平台 Manager/Leader 用 `AGENTTEAMS_*` 指向同一个 FreeLLM。
>
> 本文件是「操作手册」，命令在对应环境终端执行。形态 A 在用户本机/任意 Linux 跑，形态 B 在 Cloud Studio 跑。

---

## 0. 前提与诚实声明（先读）

| 能力 | 本地形态 A | 云端形态 B（Cloud Studio） | 部署要点 |
|------|-----------|--------------------------|---------|
| **LLM（八官署 Worker / 平台）** | ✅ 本机 Genie(8910) 或 FreeLLM(9000) | ❌ 无本机服务 | 统一用 **FreeLLM**：本地 `FREELLM_API_KEY`；云端 `ANTINET_LLM_BASE_URL=<FreLLM可达/v1/chat/completions>` + `FREELLM_API_KEY`，平台装时 `AGENTTEAMS_OPENAI_BASE_URL=<FreLLM>` |
| **解析 / 向量（知易平台 8000）** | ⚠️ 本机无则诚实回退 | ❌ 云端无 | 走本地 txt 解析 + 本地分词，标注来源，**不冒充** |
| **MP 核验（Materials Project）** | ✅ 配 `MP_API_KEY` 即真实 | ✅ 云 API 天然可达 | 设 `MP_API_KEY` 即真实核验 |
| **AgentTeams 平台** | 不需要 | 需 Docker | 形态 B 才需要；形态 A 用 `run_agentteams_local.py` 等价于同套代码 |

**一句话**：两套形态都真实跑通八官署主链路；LLM 走 FreeLLM 即真实在环；解析/向量诚实回退；
MP 核验真实。验收标准（拉起角色 + 跑通任务 + 结构化产出）在形态 B 满足，形态 A 满足"可执行代码包真实可运行"。

---

## 1. 代码入云（二选一）

### 方案 A：GitHub clone（推荐，最干净）
```bash
# 在 Cloud Studio 终端
git clone <你的仓库地址> antinet-agentteams
cd antinet-agentteams
```
> 若仓库尚未推送 GitHub，本地执行 `git push` 后再 clone。需要我帮你推，告诉我账号即可。

### 方案 B：上传提交包
把 `antinet-agentteams_submission.zip`（根目录为 `antinet-agentteams/`）上传到 Cloud Studio，
解压后 `cd antinet-agentteams`。

---

## 2. Docker 校验（All in One 可能已含，确认一下）

```bash
docker version            # 需 Server 段存在（Docker daemon 在跑）
docker compose version    # 安装脚本用得到
```
- **若 docker 可用** → 跳到步骤 3。
- **若提示 command not found / daemon 未启动**：在 Cloud Studio 的「设置 / 环境」里开启 Docker，
  或按官方文档安装 Docker 引擎后再继续。**没有 Docker，AgentTeams 装不起来。**

---

## 3. 安装 AgentTeams 平台（一步到位，非交互）

```bash
# 平台 LLM：统一用我们的 FreeLLM（OpenAI 兼容），Manager/Leader 用它
export AGENTTEAMS_NON_INTERACTIVE=1
export AGENTTEAMS_TIMEZONE=Asia/Shanghai
export AGENTTEAMS_LLM_PROVIDER=openai-compat
export AGENTTEAMS_OPENAI_BASE_URL=<FreeLLM 可达 base url, 如 https://freellm.xxx/v1>
export AGENTTEAMS_DEFAULT_MODEL=<模型名>
export AGENTTEAMS_LLM_API_KEY=<FreeLLM unified key>
export AGENTTEAMS_ADMIN_USER=admin
export AGENTTEAMS_ADMIN_PASSWORD=<自定义密码>
export AGENTTEAMS_DASHBOARD=1

bash <(curl -sSL https://raw.githubusercontent.com/agentscope-ai/AgentTeams/main/install/agentteams-install.sh)
```
- 镜像从 `higress-registry.cn-hangzhou.cr.aliyuncs.com`（杭州源）拉取，国内可达。
- 安装完会拉起 `agentteams-manager` 等容器。验证：
```bash
docker ps --filter name=agentteams-manager --format '{{.Names}}\t{{.Status}}'
```

---

## 4. apply 9 个 CR（关键：先把 Worker 包拷进容器）

> ⚠️ **必读**：`agentteams-apply.sh` 只把 manifest.yaml 拷进容器（`/tmp/import/`），
> 不会拷 `worker_packages/`。而 manifest 里 `package: file://./worker_packages/X.zip`
> 是**相对 manifest 所在目录**解析的，所以必须先把包目录拷进容器，否则 apply 必失败。

```bash
# 4.1 把 worker_packages 拷进容器，使 file://./worker_packages/ 可解析
docker cp worker_packages agentteams-manager:/tmp/import/worker_packages

# 4.2 声明式 apply 全部 9 个 CR（1 Manager + 1 Team + 7 Worker）
#     install/ 目录下有官方脚本；若不在当前目录，先 git clone AgentTeams 或单独取该脚本
bash AgentTeams/install/agentteams-apply.sh -f manifests/manifest.yaml
```
- 成功标志：无报错，且 `docker exec agentteams-manager agt get workers` 列出 7 个 Worker。
- 若 `file://` 仍解析失败，改用显式导入兜底（逐个 Worker）：
```bash
for w in junsicha chengxiangfu jinyiwei mijuanfang tongzhengsi jianchayuan taishige; do
  bash AgentTeams/install/agentteams-import.sh worker --name $w --zip worker_packages/$w.zip --runtime copaw
done
bash AgentTeams/install/agentteams-apply.sh -f <(awk '/^---/{c++} c>=1' manifests/manifest.yaml)  # 仅 apply Manager+Team
```

---

## 5. 验证 8 官署角色已拉起

```bash
docker exec agentteams-manager agt get workers          # 应见 7 个 Worker = Running
docker exec agentteams-manager agt get teams            # 应见 antinet 团队
docker exec agentteams-manager agt get managers         # 应见 zhihuiling
```
- 在 Element Web（安装时一并部署的 Dashboard）里应能看到每个 Worker 的专属房间。
- 任一 Worker 未 Running → `docker logs agentteams-worker-<name>` 看原因（多半是包/镜像问题）。

---

## 6. 跑通最小可执行闭环（真实端到端）

闭环有三条触发路径，**形态 A 用 ①，形态 B 用 ②/③**：

### 路径 ①：本地免 Docker 跑（形态 A，最稳保底，评委一键复现）
```bash
cd antinet-agentteams
# 统一 LLM = FreeLLM（本机 9000；若本机有 Genie:8910 则 Genie 优先）
export FREELLM_API_KEY=<你的 FreeLLM unified key>      # 不设则回退 Genie/规则
export MP_API_KEY=<可选：Materials Project key>         # 设了即真实 MP 核验

python run_agentteams_local.py --topic "SnSe 空位工程导热"
# 输出：9 个 CR 拓扑 + 7 阶段主链路派发追踪 + 四色卡片统计 + LLM 在环标记
# 产物：examples/snse_survey/{blue,green,red,yellow}_cards.json, survey_report.json, provenance/
```
> 这条路径**无需 Docker**，直接证明「复赛 · 可执行 AgentTeams 代码包」真实可运行；
> 与形态 B 共用 `core/runtime.py` 同一套八官署代码，零外部依赖、可完全离线（LLM/MP 不可达时如实降级）。

### 路径 ②：本地内核 + 平台 TaskFlow 桥（形态 B 快速验证）
```bash
# Worker 主链路 LLM 指向云端可达的 FreeLLM
export ANTINET_LLM_BASE_URL=<FreeLLM可达 /v1/chat/completions>
export ANTINET_LLM_MODEL=<模型名>
export ANTINET_LLM_API_KEY=<FreeLLM key>
export MP_API_KEY=<可选：Materials Project key>

python taskflow_bridge.py "SnSe 空位工程导热"
# 输出：① 平台 TaskFlow DAG 计划 ② dry-run 真实主链路（蓝/绿/黄/红卡 + LLM 在环标记）
```
> 这条路径证明「意图图→平台 TaskFlow」桥接与真实执行一致，**无需等平台全链路**，是形态 B 演示的保底。

### 路径 ③：平台内由 Manager 派发（形态 B 完整 AgentTeams 编排）
在 Element Web 里以 Admin 身份给 `zhihuiling`（指挥使）下发任务：
```
@zhihuiling 请处理「SnSe 空位工程导热」相关文献，按八官署流程产出四色卡片
```
指挥使 → 军机处(Team Leader) → 各 Worker 按 `taskflow_bridge.py` 生成的计划顺序执行 → 回流太史阁。
验收：每条消息带 provenance，最终产出结构化四色卡片 JSON/JSONL。

---

## 7. 排错清单（云端最常见 5 坑）

| 现象 | 原因 | 解决 |
|------|------|------|
| `agentteams-manager container is not running` | 平台没装起来 | 回步骤 3 重装；`docker ps -a` 看容器是否 exited |
| Worker 卡在异常 / `file://...zip not found` | apply 没拷 worker_packages | 重做步骤 4.1 的 `docker cp` |
| `agt apply` 报 `WorkerPackage manifest invalid` | 包内 manifest.json 结构不符 | 已对齐 `version/source/worker`，重跑 `python build_worker_packages.py` |
| Worker 内 LLM 全回退规则（卡片标注 `llm_involved=False`） | 云端无 Genie / 未设 FreeLLM | 本地设 `FREELLM_API_KEY`；云端设 `ANTINET_LLM_BASE_URL`+`FREELLM_API_KEY`（步骤 6） |
| MP 核验标注 `MP_API=off` | 没设 key | 设 `MP_API_KEY` 环境变量（云 API 天然可达） |

---

## 8. 提交物核对（复赛交什么）

- `antinet-agentteams/` 整个目录（含 `manifests/manifest.yaml`、7 个 `worker_packages/*.zip`、
  `taskflow_bridge.py`、`skills/`、`core/`）。
- `README.md` / `SUBMISSION.md`（已写明「真实服务接入 / 云端部署」）。
- 本 SOP（`CLOUD_STUDIO_DEPLOY.md`）。
- 演示用：路径 ① 的 `taskflow_bridge.py` 输出 + 路径 ② 的 Element Web 截图 / provenance 日志。

---

## 附：本次迁移相对初版的改动

1. **manifest.yaml**：删除 2 个 `example.com` 占位 `mcpServers`（通政司/太史阁）——MP 与向量均走 Python 直连，不依赖平台 MCP，不删 apply 必失败。
2. **build_worker_packages.py**：Worker 包 `manifest.json` 补齐平台解析所需的 `version/source/worker{base_image,runtime,model}`。
3. **taskflow_bridge.py（新增）**：意图图 → AgentTeams TaskFlow 适配桥，含 dry-run 一致性验证。
4. **core/common/llm_client.py**：新增 `ANTINET_LLM_BASE_URL/MODEL/API_KEY` 环境变量覆盖（云端指向可达 FreeLLM）；
   另新增 `FREELLM_BASE_URL` / `FREELLM_API_KEY` 环境变量，把我们的 FreeLLM 作为一等备用 LLM，
   本地不设则回退本机 Genie(8910)（无回归）。
5. **junji_chu.py（先前已完成）**：MP 核验接真实 `api.materialsproject.org`（根路径 + 浏览器 UA + is_stable 过滤器），7/11 已实测点亮。
