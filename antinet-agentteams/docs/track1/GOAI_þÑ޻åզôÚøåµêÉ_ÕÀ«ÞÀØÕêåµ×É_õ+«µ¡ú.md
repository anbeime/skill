# GOAI 赛道一 · 知识库集成差距分析（修正版）

> 生成：2026-08-16 13:00 | 分析人：项目总监（大湾区靓仔）
> 更正：上一版误判 `materials-agent` 为主体；**真正参赛主体是 `antinet-agentteams`**。
> 结论：接口契约正确、后端存活，断点在「主链路未闭合」。

---

## 一、文件夹关系（哪个有关）

| 文件夹 | 角色 | 是否参赛主体 |
|--------|------|--------------|
| `antinet-agentteams` | **八官署→AgentTeams(Hiclaw) 映射，复赛可执行代码包**：`core/`(八官署运行时)+`manifests/`(9 CR)+`skills/`(4 Skill)+`zhijia_client.py`(知识库客户端)+`docs/track1/`(简介/PPT/Identity/Skill映射) | ✅ **是（活体，最新 Aug11）** |
| `antinet-agentteams_submission` | 上述仓库的提交快照（diff taishige.py 完全一致，Aug12 冻结） | ✅ 提交用副本 |
| `agent-infra-materials` | manifest.yaml + skills/ + ppt/ + design/ + `_write_cards_*.py`：赛道一 manifest/Skill 模板素材 | 🟡 参考素材 |
| `AgentTeams` | AgentTeams(Hiclaw) 框架基座（controller/manager/copaw/qwenpaw/openclaw） | 🟡 平台，非作品 |
| `opspilot-zero-demo` | opspilot 独立 demo（agents/at/scenarios/skills/tools） | 🟡 补充 demo |
| `GOAI_track1_submission` | 含 `materials-agent`（**8/10 早期废弃变体**） | ❌ 已过时 |
| `materials-agent`(独立) | 同上早期变体，无 zhijia_client | ❌ 已过时 |

> 所以「结合整个知识库运行」要改的是 **`antinet-agentteams/core/`**（提交时以 `antinet-agentteams_submission/antinet-agentteams` 为源）。

---

## 二、知识库集成现状（实地核查）

`antinet-agentteams` 已内置 `zhijia_client.py`，直连本机 :8000 知易平台（= Antinet 后端）：
- `GET /api/pdf/status` → health
- `POST /api/knowledge/import/text` → 灌库（真实向量化）
- `POST /api/knowledge/search` → 检索
- `POST /api/pdf/extract/text` → 真实 PDF 解析

**实测后端（此刻在跑）契约全部对得上：**
| 接口 | 实测 | 结论 |
|------|------|------|
| `/api/pdf/status` | `{"available":true,...}` (200) | ✅ health 通过 |
| `/api/knowledge/import/text` | `{"success":true,"saved":1}` (200) | ✅ 灌库生效 |
| `/api/knowledge/search` | `[]` (200) | ✅ 接口通（当前无 SnSe 卡，故空） |

→ **集成不是假的，是契约正确 + 后端存活。断点在主链路逻辑。**

---

## 三、真正的断点（闭环未闭合）

### 🔴 P0-a — 太史阁.recall 读库「从不进主链路」
- `taishige.recall()` 已写好：优先 `zhijia.search()`（真实库），不可达才回退本地（证据：`core/memory/taishige.py:72-78`）。
- 但 `runtime.py` 的 `run_full()` 跑 PIPELINE（security-scan→doc-parse→extract→review→propose→verify→provenance），**全程不调用 `recall()`**（grep 证实 `runtime.py` 无 recall 调用）。
- 后果：通政司/监察院/丞相府**拿不到历史知识上下文**，"先读库再干活"（AGENTS.md 第4节）未实现 → recall 是死代码。

### 🔴 P0-b — 太史阁.writeback 回库「不灌生成的卡片」
- `writeback()` 只写本地 JSON + provenance md（`core/memory/taishige.py:48-70`），**不调 `zhijia.import_text()`**。
- 只有密卷房在解析时把「源文」灌库（`core/archive/mijuanfang.py:38-40` `zhijia.import_text(text)`）。
- 后果：生成的**四色卡片（蓝/绿/红）从不回流知识库** → 下一轮 recall 搜不到本轮结论 → 闭环断一半。

### 🟠 P1 — 密卷房真实 PDF 路径未启用
- `_parse_one()` 仅当 raw_dir 存在 `*.pdf` 才走 `zhijia.extract_pdf_text()`；当前 `examples/snse_survey/raw/` 只有预存 `.txt`，故走预存文本（诚实但非真解析）。
- health 显示 `text_plumber:true`，真实 PDF 抽取可用，缺的是真实 PDF 语料。

### 🟡 P2 — 检索返回结构喂给 recall 的字段对齐
- `zhijia.search` 返回 list[dict]，recall 取 `h.get('id')/h.get('title')`。需确认后端 search 返回含 `id`/`title`（实测未返回数据，待灌卡后验证）。

---

## 四、要「结合整个知识库运行起来」的最小改动（仅动 `antinet-agentteams/core/`）

1. **P0-a 接通读库**：在 `runtime.py run_full()`（及 `command/zhihuishi.py` 如有）的 `extract` 之前插入
   `kb_ctx = self.taishige.recall(topic)`，并把 `kb_ctx` 注入通政司/监察院/丞相府的抽取 prompt。
2. **P0-b 闭合回库**：在 `taishige.writeback()` 末尾，对每张卡片调用 `self.zhijia.import_text(card.content)`，
   让四色卡片真正入知识库（与密卷房灌源文对称）。
3. **P1 真解析**：放真实 PDF 到 `examples/snse_survey/raw/`，验证 `/api/pdf/extract/text` 命中。
4. 验证：`run_agentteams_local.py` 跑一次 → 日志出现「真实检索命中/平台知识库召回 N 条」+ 灌库 `saved:1`，
   且二次运行 recall 能命中首轮卡片。

> 不碰 `backend/`、不碰框架 `AgentTeams/`。改动局限在 `core/memory/taishige.py` 与 `core/runtime.py`，
> 零外部依赖，可独立跑通。

---

## 五、截止线事项（今天 23:59 初赛，与知识库无关但必须做）
- [ ] 推**公开仓库**（现仅 `gitee.com/anbeime/zhiyi` 私有，清单标注「待推送」）
- [ ] 官网 goaihz.com 用 `13632833907@qq.com` 提交：简介(`docs/track1/project_intro.md` 480字) + PPT(`Antinet_GOAI_track1.pptx`)
- [ ] 复赛（8/25–9/3）才需可运行 AgentTeams 代码包 + Demo 录屏（即上面 P0 闭环后的 `antinet-agentteams`）
