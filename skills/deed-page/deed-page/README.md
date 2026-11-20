# deed.page

把 Agent 生成的 HTML 文件或构建输出目录（如 `dist/`、`build/`、`out/`）发布到公开的 `https://<slug>.deed.page/` 链接。无需注册账号或 API Key，一次 `curl` 请求即可上线。

## 适用场景

- 用户说"发布 / 部署 / 托管 / 给我一个链接"时，把生成的报告、仪表盘、幻灯片、落地页、原型或小游戏放到线上
- 更新或删除之前发布的站点（使用首次发布返回的 owner token）

## 安全规则

1. 只说"做一个网页"时只在本地生成草稿，先展示文件，用户确认后才上传。
2. 其他情况上传前展示目标地址（公开可访问）和完整文件列表，并等待用户明确确认。
3. 只发布干净的输出目录；`scripts/publish.sh` 会自动跳过 `.env`、`.git`、`node_modules`、密钥文件等。
4. owner token 保存在 `~/.config/deed-page/token`（权限 600），不打印、不写进页面、提交或日志。

## 快速示例

```bash
# 预览将要上传的文件（不上传）
scripts/publish.sh ./dist --dry-run

# 用户确认后发布，最后一行输出为公开链接
scripts/publish.sh ./dist
```

依赖：`curl`、`tar`；超过约 4 MB 的目录需要 Node 18+（`scripts/publish-large.mjs`）。

上游仓库：https://github.com/f-o-x11/deed-page-skill（MIT）· 文档：https://deed.page/docs
