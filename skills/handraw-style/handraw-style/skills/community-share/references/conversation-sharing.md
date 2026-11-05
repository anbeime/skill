# 出图后的“分享到网站”

适用于 Codex / Claude 调用本包任何 Skill 后交付的用户生成图片。此流程把**生成图片 + 用户最初的创作指令 + 实际画风/图型编号备注**分享到网站**作品广场**，不使用二阶段设计参数或完整生图提示词，也不以论坛发帖替代作品发布。

## 作品广场接口

- `GET /api/boot` 验证当前账号可用；使用现有个人 API Key（`Api-Key` 请求头），无需另建网站账号系统。
- 图片先走 `POST /api/uploads`（JSON body：`{"dataUrl": "data:image/png;base64,...", "nameZh": "..."}`），返回站内 `/uploads/...` 地址；首图为 `entry.images[0]`，其余为附图。每件作品最多封面加8张附图，超过则拆分，不能静默丢图。
- `POST /api/entries` 请求体为 `{"entry": {...}}`，设置 `title`、`prompt`、`originalRequest`、`images`、`styleIds`、`layoutId`、`requestId`。作品即时发布，不经审核。
- `styleIds` 传实际使用的画风编号数组（如 `["FA-013"]`），`layoutId` 传图型编号（如 `SC-001`）。每件作品最多两个不同画风、一个图型；不使用的类别不传关联。**正文编号备注与正式关联都要保存**，不能只靠文字识别。
- 接口返回 `{"ok": true, "id": "<UUID>", "kind": "work", "url": "/forum/?view=resource&kind=work&id=<UUID>"}`。`kind` 必须为 `"work"`。禁止用论坛主题链接作为作品成功回执。
- `requestId` 是幂等键：同一请求重复提交返回同一作品，不会重复发布。
- 这个客户端不直接调用论坛发帖接口。网站内部是否同步预览话题由网站实现处理，不影响发布目标为原生作品。

## 编号备注

原始消息逐字保留在 `original_request`，作品与预览使用相同文本：原文后换行，仅追加实际使用的编号标签：

```text
我要做一张适合发小红书的图片。你帮我设计下
【画风：FA-013 】
```

- 编号来自实际解析并采用的方案，使用当前索引中的规范编号，不从图片反推；多个编号全部记录，超出单件作品关联上限时拆分作品。
- `--style FA-013` 与 `--layout IG-038` 可重复；明确未使用某类时传 `--no-style` / `--no-layout`。新的草稿应明确传入两类选择。
- 实际使用图型时才追加 `【图型：IG-038 】`，多个编号用顿号分隔。未使用保存为空列表、历史缺失保存为 `null`；两者都不输出空标签或说明。禁止追加“备注（实际使用编号）：”、“画风编号：”、“图型编号：未使用”等冗余文字。
- 原始消息及其哈希保持不变，编号另存并校验；发布时同时传正式 `assets` 关联，发布后核验，不能仅凭本地备注宣称已关联。缺少真实编号时先补全；明确未使用则传空列表。

## 捕获原始指令

1. 在提炼主题、编译提示词或进入子 Skill 之前，把当前创作任务的第一条用户创作请求逐字保存为 UTF-8 文件 `original-request.txt`，包含原有标点、空格和换行。不得从 `prompt.txt`、主题摘要或最终生图请求反推。
2. 用户回复 A/B/C、出图、继续、放大第几张时，继承该创作任务的原始请求；修改后的操作要求可以另存内部元数据，但不能替换最初请求。用户明确开启新主题或替换创作要求时建立新任务。
3. 只捕获对应的创作消息正文，不收集环境上下文、整段聊天、API Key、账号绑定消息或其他个人信息。原始请求确实缺失时不伪造；先恢复原文，再提供分享入口。

## 出图后准备分享草稿

图片已保存到真实路径并完成检查后，使用安装包中的脚本准备本地草稿。脚本路径从**安装包根目录**解析，不能从 `.agents/skills/` 的扁平发现入口推断包根目录。

```bash
python -X utf8 skills/community-share/scripts/conversation_share.py prepare --draft /absolute/output/.handraw-share.json --original-request-file /absolute/output/original-request.txt --image /absolute/output/01.png --image /absolute/output/02.png --title "作品标题" --style FA-013 --no-layout --host codex
```

- 一批组图提供一个分享链接，草稿仅包含本批交付的图片；选格放大则为本次放大图片另建草稿。文件顺序就是封面与附图顺序。
- `prepare` 保存本地草稿和校验摘要，并启动或复用仅监听 `127.0.0.1:18763` 的后台分享服务，**不上传、不发布作品**。不得在生成完成后直接调用 `publish`。
- 草稿目录属于用户本地输出，不打进公开 Skill 包；个人密钥由每个用户单独绑定，绝不预置作者密钥。
- Codex / Claude 本地客户端：把命令输出的 `[分享到网站](http://127.0.0.1:18763/share/...)` 原样作为最终回复中的 Markdown 链接输出，不能包进代码块。链接打开图片与原始指令预览，页面内有真实 HTML 发布按钮。不得把 `:codex-followup` 当成已验证的可点击按钮。
- 本机服务在电脑重启后需要重新启动；对已有草稿执行下列 `link` 命令可恢复相同链接。链接只能在运行服务的电脑上使用。无法运行本地服务的云端客户端，只显示“回复分享到网站”的文字触发，并明确它不是按钮。
- 分享入口放在图片交付说明之后、画廊传送门之前。仅输出提示词、参考图、内部过程图，或生成失败时不显示分享按钮。

```bash
python -X utf8 skills/community-share/scripts/conversation_share_ui.py link --draft /absolute/output/.handraw-share.json
```

已有待发布草稿可补充/修改编号，并保留同一分享链接。此命令不上传、不发帖，不覆盖已经发布或发布结果未确认的记录：

```bash
python -X utf8 skills/community-share/scripts/conversation_share.py annotate --draft /absolute/output/.handraw-share.json --style FA-013 --no-layout
```

## 用户点击后发布

打开分享链接只预览，不授权发布。用户点击预览页的“分享到作品广场”按钮，页面通过同源 POST 请求发布**该草稿中的图片与原始创作指令及编号备注**，成功后展示真实广场作品链接。不要代用户点击发布按钮来测试真实草稿。

用户在对话中明确回复“分享到网站”时，也授权发布当前草稿；直接执行，不再问一遍确认：

```bash
python -X utf8 skills/community-share/scripts/conversation_share.py publish --draft /absolute/output/.handraw-share.json
```

- 先校验编号与图片，再确认账号及作品发布权限，依次上传图片，创建一件免费作品；原始指令后仅附编号，不添加二阶段提示词、内部设计推理或整个聊天记录。
- 回传真实广场作品链接；区分创建成功、内容回读和资产关联核验。相同草稿再次点击返回原链接，不重复创建作品。
- 上传失败只补失败项。作品创建请求结果不明时停止自动重发，先核对作品广场，避免重复投稿；不得仅凭发起请求就报告成功。
- 不登录时先引导当前用户绑定自己的个人 API Key。只读验证不会发帖；绑定完成后继续原草稿。
- 旧版已发布论坛帖保留原回执，不删除、覆盖或谎称已进入作品广场。需要继续分享到广场时，另建 `.handraw-work-share.json` 草稿和分享链接；可复用同账号且摘要匹配的上传记录，仍须用户在新草稿点击发布。

## 绑定账号

```bash
python -X utf8 skills/community-share/scripts/conversation_share.py bind
```

密钥从标准输入传入，不作为命令行参数、按钮参数、分享正文或公开 Skill 内容。支持 `HANDRAW_COMMUNITY_API_KEY` 环境变量；默认本地绑定文件为安装包 `client/cache/conversation_share.auth.json`（被 Git 忽略）。已有用户级 community-share 凭据也可读取。输出只包含账号名与用户 ID，不回显密钥。

API 依据：[手绘风个人 API Key 与图文帖子接口](https://handraw-style.com/t/topic/29)。只向固定官方 HTTPS 域名发送 `Api-Key`；不附加 `Api-Username`，不跟随携带凭据的重定向。
