# 样片《RAG 与知识库》（2026-09-06，4′35″，8246 帧）

质量标尺。看 `frames/overview_1..6.jpg` 通览，`frames/ref_*.jpg` 看单帧细节。

| 文件 | 说明 |
|---|---|
| `research.md` | 调研文档（7900 字，105 个来源，§7 数字与比喻清单） |
| `narration.txt` | 解说词（44 句、4 章、竖线切字幕块） |
| `timeline.md` | 配音后的时间轴（句/块帧号） |
| `storyboard_src.md` / `分镜表.md` | 分镜源（令牌）与填帧后的成品 |
| `AGENT_RAG_BUILD_RULES.md` / `AGENT_RAG_QC_RULES.md` | 本片实际使用的构建/QC 协议（含 §8 闪烁白名单实例） |
| `qc/` | v1 四章 QC 报告 + v3 终检报告（可看问题长什么样、怎么量化） |
| `shots_src/G1..G8/` | 44 个镜头源码 + 各组 BUILD_NOTES（参数、偏离、QC 修复记录）。import 路径是原工程的（`../../ui`、`../../common`），与模板一致可直接参考 |
| `ui_rag.tsx` | 本片图元库（模板 `src/ui.tsx` 即由此演化） |
| `交付说明.md` | 交付文档范例 |
