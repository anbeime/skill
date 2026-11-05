<!-- Generated from data/scenarios.json + data/projects.json. -->
[← 返回检索入口](../README.zh-CN.md#discovery)

# 自动操作网页与桌面

根据当前界面选择下一步动作，由程序实际执行。

**JEV 在哪一步**

观察界面与合法候选动作 → JEV 选择目标和动作 → 执行器操作

## 可以参考的项目

### [Jev Ultrafast](https://github.com/browser-use/jev-ultrafast)

用 JEV 一次选出浏览器动作与对应 DOM 元素，只在需要输入文本时再调用文本模型。

**值得参考什么:** 参考动作与 DOM 目标一起选择，以及与文本生成的分工。

[源码证据](https://github.com/browser-use/jev-ultrafast/blob/1231850a0bf1a0c0341fe408ef1668dbbfdfac46/jev_ultrafast/model.py)

### [Cua · JEV Use](https://github.com/trycua/cua)

把 Cua Driver 的观察与执行能力和 JEV 的有限动作选择结合起来。

**值得参考什么:** 参考界面观察如何转成有限动作 ID 的选择。

[源码证据](https://github.com/trycua/cua/blob/83f142c4290a0f7d9ed545ae8532858c6e4f8145/libs/cua-driver/examples/jev-use/python/jev_adapter.py#L11)

### [Agent Desktop · JEV Skill](https://github.com/lahfir/agent-desktop)

根据系统无障碍数据选择原生桌面控件与动作的可选 JEV Skill。

**值得参考什么:** 参考通过无障碍数据选择原生桌面控件。

[源码证据](https://github.com/lahfir/agent-desktop/blob/7a8e4a10281c7319733aa200fd79501f34529716/scripts/jev/act.mjs)

这些项目分别展示该模式的一部分，并非一套开箱即用的完整应用。源码核对不代表运行、性能或 BeatAPI 接入兼容性已经验证。

[试用免费 JEV API](https://docs.beatapi.io/decisions#free-calls) · [用 Agent 搜索](../docs/agent-search.zh.md)
