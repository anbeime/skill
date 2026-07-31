# 当前全部精选同步

只在用户明确要求拿到当前全部精选，或维护持久化精选镜像时读取本文件。普通资讯问答不要使用 snapshot。

## 首次建立镜像

snapshot 是分页的，一轮 bootstrap 需要多次请求。当前约 2900 条：`fields=minimal` 约 1.08MB（gzip 247KB），`fields=default` 约 3.1MB（gzip 1.05MB），且只增不减。

1. 选择字段模式：
   - 只维护 id、标题、站内链接和分类：`fields=minimal`（默认首选，省四倍流量）。
   - 需要摘要或第三方原文链接：`fields=default`。
2. 请求 `/api/v1/selected/snapshot?fields=<模式>&limit=500`。
3. 累积本页 `items`；记下响应里的 `cursor`（逐页恒定）。
4. 只要 `hasMore=true`，就带 `page=<上一响应的 nextPage>` 继续请求下一页，`fields` 不必也不能改。
5. `hasMore=false` 时本轮结束。把累积的完整集合与**第一页就拿到的那个 `cursor`** 作为一个原子状态写入；不能只保存其中一半，也不能中途保存半份镜像。

两个游标别搞混：`cursor` 是同步水位、翻页期间不变、翻完才用来调 changes；`nextPage` 只用于翻页。用 `nextPage` 去调 changes，或者翻页没翻完就开始调 changes，都会造成镜像缺条。

翻页期间条目可能被编辑或撤选。不用处理——翻完之后第一次 `changes` 会用同一个水位把这些变化补齐：改过的条目再来一次 `upsert`（幂等），撤选的条目来一次 `remove`（本地没有就是空操作）。

如果用户只想在对话里查看当前全部精选，不要翻完所有页：取第一页、报告 `count` 与 `hasMore`，再按用户指定数量展示。未指定数量时仍只先展示最重要的 3—8 条。

## 持续接收变化

1. 请求 `/api/v1/selected/changes?cursor=<原样回传>&limit=100`。
2. 完整应用本页每条 change：
   - `op=upsert`：按 id 新增或替换条目。
   - `op=remove`：按 id 删除条目。
3. 整页全部应用成功后，再原子保存响应中的新 cursor。
4. `hasMore=true` 时立即用新 cursor 继续排空积压；排空后再恢复正常轮询。
5. 健康轮询期间只调用 changes，不请求 snapshot、items 或 fingerprint。

## 恢复

changes 返回 `409` 且 Problem `code=snapshot_required` 时：

1. 停止重试旧 cursor。
2. 用原来的字段模式重新走一遍完整的 snapshot 分页流程（从无 `page` 的第一页开始）。
3. 原子替换本地完整集合与 cursor。
4. 后续恢复 changes 轮询。

snapshot 的 `page` 游标同样可能返回 `409 snapshot_required`（本轮快照已失效）。此时丢掉半份结果，从第一页重新开始，不要接着旧 `nextPage` 翻。

一次恢复仍失败时停止并报告；不要循环下载 snapshot。

## 不变量

- cursor 不透明且绑定字段模式、同步端点和服务端水位。
- 不解析、不递增、不修改、不跨端点复用 cursor。
- snapshot 的 `cursor`（同步水位）与 `nextPage`（翻页）是两个东西，互相解不开，任何一方都不能替代另一方。
- 镜像不完整（`hasMore=true` 还没翻完）时不要开始 changes 轮询，也不要对外声称已同步。
- `publishedAt` 和 `discoveredAt` 都不能表示编辑与撤选，不能充当完整同步水位。
- 不使用重叠时间窗替代 changes；时间窗无法可靠表达 remove。
- 不把 `/api/v1/items?mode=all` 当成“当前全部精选”。它是最近公开池，语义不同。
- 持久任务保存完整 URL 的 ETag，并在下次发送 `If-None-Match`；`304` 时保持本地状态和 cursor。
- 正常轮询至少间隔 60 秒；`hasMore=true` 的积压分页除外。
