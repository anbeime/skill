# CLAUDE.md

本仓库是 Agent Skill「cy-carousel」：把一个 AI 概念、论文或产品做成封面＋内页（1440×1920）的手排图文轮播，连同标题、正文、置顶评论和来源清单一起交付。仓库根目录就是 Skill 本体，用户直接 clone 到 Skills 目录使用。

## 目录

- `SKILL.md`：Agent 使用说明（红线、版式、流程、常见坑）；`references/排字细节.md`：排字数值与原理。
- `scripts/`：Skill 脚本。
  - `手排.py`：手排入口（`headline` / `body` / `big` / `sticker` / `strip` / `page` …）。
  - `render.py`：渲染；`check_all.py`：红线和技术检查；`package.py`：打包成品；`对照.py`：参照页对照。
  - `build.py`、`layouts_v2.py` 等：底层库，不作为排版入口。
  - `*.swift`：macOS Vision / AppKit 工具，只在 macOS 上可用。
- `assets/fonts/`：随包字体（SIL OFL 1.1），许可证和 SHA256 记在 `来源与许可证.json`。
- `examples/`：样板（全套预览、文案、制作脚本）。
- `tools/`：维护用脚本（`validate_repo.py` 仓库检查、`submit_feedback.py` 登记反馈），不属于 Skill 流程。
- `tests/`：`unittest` 测试。
- `.github/`：CI 与 Agent 工作流，见 `docs/agent-workflow.md`。

## 不可违背的原则

`SKILL.md` 的红线：事实可回溯；只用开放授权素材；图上不写出处；不改原文；不用 `build.py` 自动版式排页面；脚本只出文件、不发布；参照图不外传。代码改动不能放宽 `check_all.py` 对这些红线的检查。

## 开发约定

- Python 3.10+，依赖见 `requirements.txt`（`jieba` 只有源码包，装不上时先 `pip install -U setuptools wheel`）。
- 提交前必须通过：

  ```bash
  python tools/validate_repo.py
  python -m unittest discover -s tests
  ```

- 行为改动配测试；测试只用仓库自带字体，不依赖 macOS 系统字体和 Swift 工具。
- 改默认渲染效果（字号、配色、断行、图层顺序）要附改动前后的样张。
- 用户可见变化同步 `SKILL.md`、`README.md`，排字相关同步 `references/排字细节.md`。
- 新增字体必须是开放许可，并把字体、许可证和 SHA256 登记进 `assets/fonts/来源与许可证.json`。
- 提交信息使用 `fix:` / `feat:` / `docs:` / `test:` / `ci:` 前缀，简体中文描述。
