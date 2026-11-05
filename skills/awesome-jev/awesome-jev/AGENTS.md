# awesome-jev

JEV 项目证据目录，使用 Node.js ESM 脚本维护。

data/: 项目事实、原文及三语编辑摘要。
scripts/: 目录维护、验证、README 生成及 BeatAPI 导出；导出要求目标站点已安装依赖并编译 Paraglide。

BeatAPI 导出命令：`node scripts/export-website-data.mjs <beatapi-root>/src/lib/jev-projects.ts`。生成事实 TS、messages/marketing/jev-projects 三语 JSON 与静态消息适配器；禁止在目标站点手改这些生成结果。

[PROTOCOL]: 变更时更新此头部，然后检查 AGENTS.md
