# CLAUDE.md

本仓库是 Agent Skill「原生字幕拼图」：把视频真实帧做成保留原字幕（原生模式）或绘制已审核台词（脚本模式）的长图。

## 目录

- `skills/native-subtitle-quote-image/`：Skill 本体，发布时打包的就是这个目录。
  - `SKILL.md`：Agent 使用说明；`references/`：详细流程文档。
  - `scripts/native_subtitle_stitch.py`：渲染 CLI（`sample` / `render` / `render-script`）。
  - `scripts/check_environment.py`、`scripts/check_update.py`：环境与版本检查。
  - `VERSION`：Skill 版本。
- `scripts/validate_repo.py`：打包不变量检查；`scripts/bump_version.py`：发版改版本号。
- `tests/`：`unittest` 测试。
- `README.md` / `README_EN.md` / `README_KO.md`：三语 README，内容需保持同步。
- `.github/`：CI 与 Agent 工作流，见 `docs/agent-workflow.md`。

## 不可违背的原则

- 原生字幕模式只裁切画面里已有的字幕，不 OCR、不重绘、不翻译、不覆盖。
- 脚本字幕模式必须明确标注为后期绘制，不得冒充原字幕或人物逐字引语。
- 不帮助绕过 DRM 或平台访问控制。

## 开发约定

- Python 3.10+，依赖见 `skills/native-subtitle-quote-image/requirements.txt`。
- 提交前必须通过：

  ```bash
  python scripts/validate_repo.py
  python -m unittest discover -s tests
  ```

- 行为改动配测试；用户可见变化同步 `SKILL.md` 与三语 README。
- 版本号只在发版时由 `scripts/bump_version.py` 修改，功能 PR 不要动。
- 提交信息使用 `fix:` / `feat:` / `docs:` / `test:` / `ci:` 前缀，简体中文描述。
