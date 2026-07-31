# 错误与重试

请求失败时读取本文件。先保护用户问题的原意，再考虑重试；不得靠放宽参数或换数据源伪装成功。

## v1 应用错误

请求到达 v1 应用后，标准错误使用 `application/problem+json`，至少包含：

```json
{
  "type": "/problems/invalid-request",
  "title": "Invalid request",
  "status": 400,
  "detail": "Human-readable explanation",
  "code": "invalid_request",
  "requestId": "req_123"
}
```

按稳定 `code` 分支，不解析 `detail` 人话：

- `invalid_request`：修正明确参数；不要自动改成另一个问题。
- `invalid_cursor`：书签已失效（cursor 不能跨窗口、端点或查询条件，服务端演进也可能让旧书签作废）。恢复方式是**显式从第一页重新发起同一查询**，并如实说明列表已从头开始；禁止的是静默回退——把新第一页悄悄当成上次的续页拼下去。
- `snapshot_required`：仅 selected changes 按 [sync.md](sync.md) 重建一次。
- `rate_limited`：遵守 `Retry-After`，串行重试。
- `temporarily_unavailable`：有限退避后告诉用户暂不可用。

未知 code 按 HTTP status 保守处理，并保留 `requestId` 供反馈。

CDN 安全层可能在请求到达应用前返回 566／567 极小 JSON，不保证 Problem 格式或 CORS 头。这不改变 v1 的匿名访问合同，也不要求自定义 User-Agent。保留响应中的 `requestId` 和 `help`，正常退避后最多重试一次；仍失败就停止并反馈。不得循环换 UA、伪装 Mozilla／Chrome，或申请长期 IP 白名单。

## 重试

- `400／409`：除明确的 selected snapshot 恢复外，不盲目重试。
- `404`：普通资源不重试；日报 latest／指定日期按 [API 参考](api.md) 只查一次有界索引，不猜日期。
- `429`：按 `Retry-After` 等待；没有该头时等待 60 秒。不要增加并发。
- `5xx` 或超时：最多重试 2 次，采用指数退避。
- 仍失败：说明 AI HOT 暂不可用，并提供 `https://aihot.virxact.com/feedback`；不得用训练记忆冒充实时数据。
- 浏览器跨域错误：说明浏览器没有读到响应，不把它误报为用户账号或 IP 被封。

持久轮询使用条件请求：

```text
If-None-Match: <上次同一完整 URL 的 ETag>
```

`304` 表示内容未变化。保留已有数据与 cursor，不把它当空响应。
