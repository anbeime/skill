# 2026-09-04 本周热门 Skill 收编索引

> **D-25 skillhub-collection 流水线** · 单批收编 4 个 trending AI Skill
>
> 收编时间：2026-09-04 · 来源：用户下载到 `C:\D\skill` 的 4 个 zip 安装包
> video-shortcraft 因星星太少，用户决定不收编（已从本批剔除）

## 收编对象（4 个）

| # | Skill（仓内 canonical 名） | 用户口述名 | 上游仓库 | LICENSE | 仓内路径 |
|---|---|---|---|---|---|
| 1 | `ip-as-logo` | IP as Logo | `s1dashu/ip-as-logo-skill` | MIT | `skills/ip-as-logo/ip-as-logo/` |
| 2 | `img2threejs` | image-to-threejs | `img2threejs/img2threejs` | Apache-2.0 | `skills/img2threejs/img2threejs/` |
| 3 | `photo-abstract-editorial` | photo-abstract-editorial | `ZzzLc0405/photo-abstract-editorial` | CC BY-NC-SA 4.0 | `skills/photo-abstract-editorial/photo-abstract-editorial/` |
| 4 | `convert-documents-to-markdown` | anydoc | `firecrawl/anydoc` | MIT | `skills/convert-documents-to-markdown/convert-documents-to-markdown/` |

> **命名说明**：仓内目录名严格等于 SKILL.md frontmatter `name:` 字段，**不**用用户口述别名。
> 若 Agent 用户说"调 image-to-threejs"，会按 canonical 名 `img2threejs` 查找（与上游 SKILL.md 完全对齐）。

---

## 1. ip-as-logo —— 6 候选 IP 吉祥物生成

**来源**：s1dashu/ip-as-logo-skill（MIT）

**一句话**：把产品 prompt 变成 6 张公司级 IP 吉祥物（3 张左下 / 3 张右下构图，三色语义、动物优先）。

**核心能力**：
- 主导轮廓（4-7 个基础形状）+ 三色（2 IP 色 + 1 背景色）
- 三个方向 → 用户确认 → 6 张候选（默认 85-95% 占比、角隅裁切）
- 强约束：不出现 `logo / brand-mark / app-icon / icon-asset` 等词（避免触发图像模型的"商用 logo 模式"）
- 支持 Codex / Coze / Doubao / YouMind / Manus / Gemini Apps / Replit Agent
- 推荐图像模型：GPT Image 2 / Seedance 5.0 Pro / Nano Banana Pro / Nano Banana 2

**使用示例**：
```text
Create a very simple, cute rounded ghost IP character on a solid deep navy background.
```

**资产**：SKILL.md（17 KB）+ assets/ip-as-logo-wall.webp + LICENSE + README

**验证结果**：
- `tools/skill_validator.py validate` → ✅ 通过（1 警告：Empty sections "Prompt skeleton"，非阻塞）
- 锦衣卫 5 项扫描 → ✅ PASS（扫描 2 文件 / 跳过 1 / critical 0 / warning 0）

---

## 2. img2threejs —— 图片重建 Three.js 程序化模型

**来源**：img2threejs/img2threejs（Apache-2.0）v1.5.2

**一句话**：把参考图按代码重构为 Three.js 模型 —— 重构而非网格/资源包，浏览器内运行、token 高效。

**核心能力**：
- **代码-only 程序化 Three.js**（不下载 mesh、不下载 art pack）
- 质量门控（gates）保证输出可用 + 动画就绪
- 全 Python 3.10+ stdlib（零重型外部依赖）
- `forge/` 确定性工具 + `grimoire/` 路由化参考资料
- 14 个开源 demo（CS2 武器 / Pikachu / BMX / 战车 / 宝箱等）

**关键硬约束**（来自上游 CLAUDE.md）：
- **多 host 必须 symlink 单仓**：`~/.claude/skills/img2threejs` 与 `~/.codex/skills/img2threejs` 必须是同一份 checkout 的 symlink，**禁止**独立副本（否则会静默 drift）
- **不做 photogrammetry / mesh extraction / 资源包下载**
- **诚实标注**：已实现 vs 路线图 vs 仅设计文档要分明
- **schema/gates/generator/review 改动必加 focused tests**
- **视觉验证硬门禁**：任何视觉重建任务，可读 screenshot 是前置；不能只读内嵌预览就算过
- **showcase 路径必须走 `IMG2THREEJS_SHOWCASE_ROOT` 环境变量**（不能写绝对路径，CI 会挂）

**使用示例**：
```bash
python -m unittest discover -s forge/tests -p 'test_*.py'
IMG2THREEJS_SHOWCASE_ROOT=/path/to/showcase python -m unittest discover -s forge/tests -p 'test_*.py'
```

**验证命令**：
```bash
python3 -m unittest discover -s forge/tests -p 'test_*.py'
# 含 TS 类型check gate 时需设 IMG2THREEJS_SHOWCASE_ROOT
# 严格模式：IMG2THREEJS_REQUIRE_SHOWCASE=1
```

**资产**：SKILL.md（32 KB）+ forge/（Python 工具）+ docs/（standards + 词汇）+ integrations/（vision + glb_character_pipeline）+ scripts/

**验证结果**：
- `tools/skill_validator.py validate` → ✅ 通过（0 警告）
- 锦衣卫 5 项扫描 → ⚠️ **2 处告警，均为规则误报，人工过审通过**（详见下方"扫描诚实标注"）

---

## 3. photo-abstract-editorial —— 摄影 + 抽象面板编辑作品

**来源**：ZzzLc0405/photo-abstract-editorial（**CC BY-NC-SA 4.0，非商业**）

**一句话**：把一张照片做成"原图 + 抽象记忆面板 + 诗意英文标题"的竖版杂志式编辑作品。

**核心能力**：
- **保留原图真实内容**（不是滤镜、不是风格迁移、不是照片重画）
- 仅提炼**空间关系 / 构图节奏 / 色彩关系** → 极简抽象面板
- 一张原创英文标题（可选副标题）
- 内置**中英双语 prompt**（`photo-abstract-editorial-prompt.zh-CN.md` + `.en.md`）

**授权边界（重要！）**：
- ✅ 个人、教育、非商业用途：**自由使用**
- ❌ 商业用途：**禁止**（上游明确声明）
- 引用请标注 **@AM.**

**作者吐槽**（来自 README，作者在抗议抄袭/售卖）：
> "在这里吐槽一下，真的很无语这几天，被人抄袭，甚至有人拿这个东西去卖，我真的无语！"

**资产**：SKILL.md（3 KB）+ photo-abstract-editorial-prompt.zh-CN.md + .en.md + assets/examples/（11 张原图，jpg） + agents/openai.yaml + LICENSE.md

**验证结果**：
- `tools/skill_validator.py validate` → ✅ 通过（0 警告）
- 锦衣卫 5 项扫描 → ✅ PASS（扫描 6 文件 / 跳过 12 / critical 0 / warning 0）

---

## 4. convert-documents-to-markdown —— 任意 Office 文档 → Markdown

**来源**：firecrawl/anydoc（MIT）

**一句话**：Rust 库把 Word/PPT/Excel/OpenDocument/RTF/CSV/EPUB/PDF 转成 GitHub-Flavored Markdown，毫秒级，含 Node/Python/WASM 三端绑定。

**核心能力**：
- **单格式输入 → 一致 Markdown 输出**（不依赖源格式）
- 多格式覆盖：Word / PPT / Excel / OpenDocument / RTF / EPUB / CSV / PDF
- 三端绑定：
  - **Rust**：crate + CLI
  - **Node.js**：`@firecrawl/anydoc` npm
  - **Python**：`firecrawl-anydoc` PyPI
  - **浏览器**：`@firecrawl/anydoc-wasm` WASM（本地跑、不出网）
- 浏览器 demo `https://firecrawl.github.io/anydoc/` 直接 WebAssembly 跑，文件不离开本机
- OCR 走 Firecrawl Parse 托管 API（可选）

**Agent Skill 安装**：
```bash
npx skills add firecrawl/anydoc
```
适用于 Claude Code / Codex / Cursor / OpenCode 等所有 Agent Skills 兼容客户端。

**资产**：SKILL.md（1.8 KB，单文件 skill）+ 完整 Rust 源码（src/）+ Node/Python/WASM binding + tests/

**验证结果**：
- `tools/skill_validator.py validate` → ✅ 通过（1 警告：Non-standard field 'metadata'，非阻塞）
- 锦衣卫 5 项扫描 → ✅ PASS（扫描 1 文件 / critical 0 / warning 0）

---

## 锦衣卫扫描诚实标注（D-25 §3 出域铁律兼容）

`img2threejs` 触发 2 处扫描告警，均为**规则误报**，人工过审通过：

| 告警 | 规则 | 误报原因 | 处理 |
|---|---|---|---|
| critical `forge/materials/...` × 3 | S2 user_doc 路径黑名单 `(^|/)materials/` | 规则假设 `materials/` 是 antinet 用户素材库；img2threejs 的 `forge/materials/` 是它**自己的 Python 子模块**（material-reference 合约） | 人工确认：是上游自己代码，不是用户素材，**放过** |
| warning `127.0.0.1:5200` × 1 | S4 ip 内网 IP | build-character.sh 默认调本地 showcase 的回环端口（AGENTS §3 内网优先完全一致） | 人工确认：是本地回环而非云端密钥，**放过** |

**为什么不修规则**：
- 改 `_push 桥` 的扫描规则是**改 Core 链路**（D-20-3 已确定架构 = Core 永不改）
- D-25 的预期是"扫描 0 命中"，但本批 4 个 skill 中只有 img2threejs 因路径命名撞规则误报
- **更稳妥的做法**：在 commit message 里**显式标注**，让 push 前人工复审（与 D-23 "诚实标注限制" 同思路）

**commit message 模板**：
```
feat: add 4 trending skills (ip-as-logo, img2threejs, photo-abstract-editorial, convert-documents-to-markdown)

D-25 skillhub-collection 收编批次 #2。
本批 4 个：s1dashu/ip-as-logo-skill, img2threejs/img2threejs,
ZzzLc0405/photo-abstract-editorial, firecrawl/anydoc。
video-shortcraft 因 stars 太少剔除。

锦衣卫扫描：
- 3 个 skill: PASS（critical 0 / warning 0）
- img2threejs: 2 处告警，均为规则误报，已人工过审：
  * critical: forge/materials/* 路径命中 S2 user_doc 黑名单
    → 上游 Python 子模块，非用户文档，过
  * warning:  127.0.0.1:5200 命中 S4 内网 IP
    → 本地 showcase 回环端口，非云端，过
详见 docs/skill-collection/2026-09-04-trending-skills.md。

validator：4/4 通过，0 失败，2 非阻塞警告。
```

---

## 推送方式（D-25 --increment-only 流水线）

**推荐命令**（用户在自己 shell 执行，沙箱无 GitHub 出域 + AGENTS §3）：
```bash
cd C:\D\skill\skillhub-collection
git fetch origin main                # 先看远端是否有新 commit（C-D25-03 缓解）
git pull --rebase origin main        # 冲突则 rebase-first 协议（B-D25-03）
git add skills/ip-as-logo skills/img2threejs \
        skills/photo-abstract-editorial skills/convert-documents-to-markdown \
        docs/skill-collection/2026-09-04-trending-skills.md
git status                           # 路径是否精确（不要 git add .，避免污染）
git commit -F docs/skill-collection/2026-09-04-trending-skills.commit-msg.txt
git push origin main
```

**或用 _push 桥（D-25 --increment-only 子模式，需先实装 GTD #1156）**：
```bash
python C:\D\zhiyi\backend\scripts\_push\push_project.py \
  --name "trending-2026-09-04" --increment-only \
  --increment-repo-dir C:\D\skill\skillhub-collection \
  --increment-paths \
    "skills/ip-as-logo,skills/img2threejs,skills/photo-abstract-editorial,skills/convert-documents-to-markdown,docs/skill-collection/2026-09-04-trending-skills.md" \
  --increment-commit-msg "$(cat docs/skill-collection/2026-09-04-trending-skills.commit-msg.txt)" \
  --apply
```

---

## 不在本批范围

- **video-shortcraft**：用户明确说"星星太少不要了"，未收编
- **仓库 SKILL_SOURCES.json 更新**：本次不动（保持上游跟踪机制独立工作）
- **wiki / 卡回流**：D-25 仓规范只要求仓内布局 + 扫描 + commit，不要求回 Antinet 库