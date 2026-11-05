<!-- Generated from data/scenarios.json + data/projects.json. -->
[← 返回检索入口](../README.zh-CN.md#discovery)

# 筛选新闻与内容

从信息流中保留相关内容，过滤不需要的信息。

**JEV 在哪一步**

已获取的内容 → JEV 判断相关性或类别 → 程序筛选或分流

## 可以参考的项目

### [NewsJack](https://github.com/elvisun/newsjack)

从实时新闻流中筛选品牌可跟进话题的开源 PR 工作流。

**值得参考什么:** 参考新闻初筛如何衔接后续品牌话题处理。

[源码证据](https://github.com/elvisun/newsjack/tree/092d882fc69912622f620c50eb493afe625f99dc/demos/news-desk-dealer)

### [Bluenoise](https://github.com/rokcso/bluenoise)

为 X/Twitter 过滤帖子与回复的浏览器扩展；默认用本地规则，可选择用 Jev 检查未匹配的回复。

**值得参考什么:** 参考本地规则先过滤、JEV 补充判断未命中回复的分工。

[源码证据](https://github.com/rokcso/bluenoise/blob/ef81ea7a7c3677501d6de8f9235a4d6a866b573a/entrypoints/background.ts)

### [Youtube Sponsor Detection](https://github.com/trungdq88/youtube-sponsor-detection)

结合实时音频与字幕由 Jev 驱动的 YouTube 视频赞助广告片段检测与自动跳过扩展。

**值得参考什么:** 参考字幕片段分类如何衔接播放器跳过广告的操作。

[源码证据](https://github.com/trungdq88/youtube-sponsor-detection/blob/de01f0568d043035889a296a61ce21e0accc8b16/extension/lib/jev.js#L1-L541)

这些项目分别展示该模式的一部分，并非一套开箱即用的完整应用。源码核对不代表运行、性能或 BeatAPI 接入兼容性已经验证。

[试用免费 JEV API](https://docs.beatapi.io/decisions#free-calls) · [用 Agent 搜索](../docs/agent-search.zh.md)
