# AI HOT v1 API 参考

只在需要完整参数、字段、分页或构建客户端时读取本文件。普通资讯问答优先遵循 `SKILL.md` 的默认路由。

## 共同合同

- Base URL：`https://aihot.virxact.com`
- 匿名只读，不需要 API Key，不发送 cookie。
- OpenAPI：`https://aihot.virxact.com/openapi-v1.json`
- 所有 cursor 都是不透明书签：只原样回传给产生它的同一端点和同一查询，不解析、不修改、不跨查询复用。
- 未知参数、无效参数、损坏或跨查询 cursor 都返回明确的 Problem JSON，不会静默回到第一页。
- 对同一完整 URL 保存响应 `ETag`；下次发送 `If-None-Match`。`304` 表示内容未变化。
- items cursor 没有按时间自动失效，但 24 小时／7 天是滚动窗口，较老条目可能在两次翻页之间自然离开窗口；需要精确镜像时改用 selected snapshot + changes。

## 操作

### 最近资讯、分类与搜索

`GET /api/v1/items`

| 参数 | 合同 |
|---|---|
| `mode` | `selected` 或 `all`；默认 `selected` |
| `window` | `24h` 或 `7d`；默认 `7d` |
| `by` | `timeline` 或 `published`；默认 `timeline`（见下方「时间口径」） |
| `category` | `ai-models`、`ai-products`、`industry`、`paper`、`tip` |
| `q` | 2—200 字；使用服务端搜索 |
| `limit` | 1—100；默认 50。只需要头几条时显式调小，别默认拉满 50 |
| `cursor` | 原样回传上一页的 `page.nextCursor` |

#### 时间口径

`window` 从哪个时间点往回算、结果按哪个时间排序，由 `by` 决定。两个原始时间戳恒定随每条返回，可自行判断。

- `by=timeline`（默认）：与 aihot.virxact.com 网页看到的顺序和集合一致。规则是——原文发布后 72 小时内被收录，按收录时间；超过 72 小时才收录的历史回填，归位到原文发布日。所以官方博客、公众号、HuggingFace Daily 这类「原文两三天前发、今天才抓到」的慢推信源，仍会出现在 `window=24h` 里，同时旧文回填不会冒充最近。
- `by=published`：只按第三方原文发布时间。慢推信源会掉出短窗口——同一时刻 `window=24h` 下它比默认口径少约两成条目。需要严格按原文时间线对账时才用。

切换 `by` 会让已持有的 cursor 失效并返回 `invalid_cursor`，这是有意的：换了口径继续用旧书签会串页。重新从第一页开始即可。

响应外层：

```json
{
  "schemaVersion": 1,
  "query": {
    "mode": "selected",
    "category": null,
    "q": null,
    "window": "24h",
    "by": "timeline",
    "ordering": "timelineDesc"
  },
  "items": [],
  "page": {
    "count": 0,
    "hasMore": false,
    "nextCursor": null
  }
}
```

每个 item 必有以下键：

- `id`
- `title`
- `originalTitle`
- `summary`
- `source.name`
- `links.aihot`
- `links.original`
- `publishedAt`
- `discoveredAt`
- `category`
- `score`
- `selected`

其中 `originalTitle`、`summary`、`publishedAt`、`category` 和 `score` 的键始终存在，但值可以是 `null`；展示前必须判空。`id`、`title`、`source.name`、`links.aihot`、`links.original`、`discoveredAt` 和 `selected` 为非空值。响应还可能带可选的 `attribution`，客户端不得依赖它一定存在，也不得因未来新增未知字段而报错。`page.count` 是本页条数，不是全库总数。

示例：

```text
GET /api/v1/items?mode=selected&window=24h&limit=8
GET /api/v1/items?mode=selected&window=7d&category=paper&limit=20
GET /api/v1/items?mode=selected&window=7d&q=OpenAI&limit=20
GET /api/v1/items?mode=all&window=24h&limit=50
```

### 当前热点

`GET /api/v1/hot-topics`

响应为 `{schemaVersion, count, items}`，不是可续页集合。保持 API 热度顺序。item 包含 `sourceCount`、`signalCount`、`sourceNames`、`latestAt`，并可能包含可选的 `links.story`（给人阅读的 HTML 事件页）；其中 `sourceCount` 是独立信源数。热点与普通资讯字段不同，不得把两种响应强行混成同一列表协议。

### 事件详情

`GET /api/v1/stories/{publicId}`

publicId 只取自实际返回的 hot-topics `links.story`，或另一个 story 响应里 storyline／related 的引用。对于 `links.story`，先确认 URL 属于 `https://aihot.virxact.com/story/{publicId}`，只提取路径末段的实际 `publicId`，再调用本 API；不得直接请求该 HTML 网页 URL，也不得把网页响应当 API 数据。字段缺失或 URL 格式不符时不得猜测 id，改用 items 关键词查询。响应为 `{schemaVersion, story}`：`story.reports` 是逆序报道时间线（每条含站内 `links.aihot`）；`story.digest` 是随事件演化增量更新的 AI 综述（与旧结论矛盾处会显式标注），`story.latest` 是最新进展一句话；`storyline`／`related` 是关联事件引用（含 `links.api` 可直接续跳）。事件被合并时返回 308，跟随 Location 即可；404 表示事件层或该事件当前不可用，回落到 items。`status` 为 `settled` 表示事件已收束（超过 48 小时无新报道）。

### 日报

```text
GET /api/v1/dailies?limit=7
GET /api/v1/dailies/latest
GET /api/v1/dailies/2026-07-24
```

- 索引响应为 `{schemaVersion, count, items}`，不是可续页集合。
- 最新或指定日报响应为 `{schemaVersion, report}`。
- 保留 report 的 `lead`、`sections` 与 `flashes` 结构，不把日报重排成普通 items。
- 日报索引项和 report 顶层的 `links.aihot` 必有。sections／flashes 中 `links.aihot` 可能为 `null`；此时使用必有的 `links.original`，不要再寻找旧字段 `permalink` 或 `sourceUrl`。
- 最新日报或指定日期返回 404 时，索引只查一次有界的 `/api/v1/dailies?limit=7`。索引有结果时，从中选择实际返回的最近日期，再请求一次对应的 `/api/v1/dailies/{date}` 取得完整日报并如实说明日期；索引为空就报告当前没有可用日报。绝不猜“昨天”或自行拼接日期。

### 正文与周期报告边界

- `items` 只返回标题、摘要、来源、时间、评分和链接，不返回正文，也没有 `/api/v1/items/{id}`。用户要深入阅读时提供 `links.aihot` 和 `links.original`，不要抓网页或全文 RSS 冒充单篇正文 API。
- AI HOT 编辑成品周报与月报目前只有 `/weekly` 和 `/monthly` 网页，没有 v1、Skill 或 RSS 端点。“最近一周精选”仍是滚动 7 天 items 查询，不得称为正式周报。

### 完整精选同步

```text
GET /api/v1/selected/snapshot?fields=minimal&limit=500
GET /api/v1/selected/snapshot?fields=minimal&limit=500&page=<opaque>
GET /api/v1/selected/changes?cursor=<opaque>&limit=100
```

只有用户明确要求当前全部精选或持久镜像时才使用。完整算法见 [sync.md](sync.md)；不要仅凭本文件实现同步状态机。

snapshot 是**分页**的，一次请求拿不到全部：

| 参数 | 合同 |
|---|---|
| `fields` | `default` 或 `minimal`；默认 `default`。`minimal` 去掉摘要与原文链接，体积约为 default 的四分之一 |
| `limit` | 1—1000；默认 500 |
| `page` | 原样回传上一响应的 `nextPage`；续页的 `fields` 由游标锁定，传不同值无效 |

响应里有两个不同的游标，**不要混用**：

- `cursor`：同步游标，逐页恒定，指向第一页取到的水位。**翻完所有页之后**才拿它调 `changes`。
- `nextPage`：翻页游标，只在本轮快照内有效。`hasMore=true` 时必须继续翻，否则镜像不完整。

规模参考：当前约 2900 条，`fields=default` 全量约 3.1MB（gzip 1.05MB），`fields=minimal` 约 1.08MB（gzip 247KB）。条目只增不减，会逐年变大——不确定就用 `minimal`，需要摘要时再取 `default`。

## 分页

1. 处理当前页全部 items。
2. `page.hasMore=true` 时，原样回传 `page.nextCursor` 请求下一页。
3. 达到用户指定数量即可停止；无需为了“完整”耗尽所有页。
4. `page.hasMore=false` 时结束。
5. cursor 报错就报告或按对应恢复合同处理，绝不删掉 cursor 后假装翻页成功。
6. 普通 items 分页不是一致性快照；新条目不会造成已翻页内容重复，但滚动窗口内的编辑、撤选和自然过期可能改变后续页。完整、可恢复同步只使用 selected snapshot + changes。

## 字段语义

- `links.aihot`：AI HOT 站内中文阅读页，默认主链接。
- `links.original`：第三方原文，仅在用户要出处时附加。
- `originalTitle`：来源原标题，可能不是英文。
- `publishedAt`：第三方原文发布时间。展示前把 ISO 时间转换到 `Asia/Shanghai`。
- `discoveredAt`：AI HOT 首次收到时间。`publishedAt` 为空时可回退使用，但必须标为“AI HOT 收录时间”。
- `score`：0—100 总分，可能为空，不表示当前响应按它排序。
- `selected`：是否属于当前精选。
- `category`：允许未来增加新值；不要把未知值当成响应损坏。

## 时间范围

v1 只承诺 `24h` 和 `7d` 两个服务端窗口：

- 今天、过去 24 小时：用 `24h`。
- 最近、最近一周：用 `7d`。
- 用户要 2 天、3 天等其它七天内范围：取 `7d` 后本地收窄。**收窄用的字段必须与请求的 `by` 口径一致**，否则会切掉服务端本来算在窗口内的条目：
  - 默认 `by=timeline`：用时间轴值——`publishedAt` 为空取 `discoveredAt`；`discoveredAt - publishedAt > 72 小时`（历史回填）取 `publishedAt`；其余取 `discoveredAt`。
  - 显式 `by=published`：才直接用 `publishedAt`。
  - 拿 `publishedAt` 去收窄默认口径，会把官方博客、公众号、HuggingFace Daily 这类慢推信源整批误删（见上方「时间口径」）。
- 超过 7 天的普通公开池不承诺可用；不要用 selected snapshot 冒充历史搜索。
