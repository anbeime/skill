# A/B/C 时空方向卡

> A/B/C 只代表方向，不代表模式。第一步环节必须完整保留并输出三张方案卡供用户挑选，严禁系统或 AI 自动选定，严禁跳过选向直接出图；若全家福/其他多人缺少总人数、性别构成或关系结构，先一次性补齐缺失项再输出。

## A｜{{direction_name}}
```text
时空坐标：{{spacetime_anchor}}
人物身份：{{participant_identities}}
人物关系描述：{{relationship_description}}
核心场景：{{core_scenes}}
{{per_participant_wardrobe_fields}}
{{per_participant_styling_fields}}
色彩 / 光线：{{palette_lighting}}
人物状态：{{human_state}}
通用摄影关键词：高级摄影师风格，创意构图，强烈的戏剧张力
摄影语言：{{photographic_language}}
出8宫格图片。
```

## B｜{{direction_name}}
```text
时空坐标：{{spacetime_anchor}}
人物身份：{{participant_identities}}
人物关系描述：{{relationship_description}}
核心场景：{{core_scenes}}
{{per_participant_wardrobe_fields}}
{{per_participant_styling_fields}}
色彩 / 光线：{{palette_lighting}}
人物状态：{{human_state}}
通用摄影关键词：高级摄影师风格，创意构图，强烈的戏剧张力
摄影语言：{{photographic_language}}
出8宫格图片。
```

## C｜{{direction_name}}
```text
时空坐标：{{spacetime_anchor}}
人物身份：{{participant_identities}}
人物关系描述：{{relationship_description}}
核心场景：{{core_scenes}}
{{per_participant_wardrobe_fields}}
{{per_participant_styling_fields}}
色彩 / 光线：{{palette_lighting}}
人物状态：{{human_state}}
通用摄影关键词：高级摄影师风格，创意构图，强烈的戏剧张力
摄影语言：{{photographic_language}}
出8宫格图片。
```

`per_participant_wardrobe_fields` HARD RULE：
- 情侣默认输出两行：`女方服装：...` 与 `男方服装：...`。
- 多人按已确认角色名或 P01/P02/... 每人一行：`P01｜角色服装：...`。
- 禁止输出单一合并 `服装造型` 字段替代逐人服装。
- 即使共享色盘/材质逻辑，也要逐人写具体服装与差异。

`per_participant_styling_fields` HARD RULE：
- 每个候选方向在展示前先运行 `skills/hairstyle`，再运行 `skills/makeup`。
- 每位人物至少输出两行：`Pxx 发型定稿：...` 与 `Pxx 妆容定稿：...`；情侣可用“女方/男方”。
- 发型与妆容是该方向的正式结果，不是占位词；用户选中方向后下游生图继承，不重复设计。
- 女性妆容默认采用白皙柔焦影楼精修硬组合；用户明确要求时覆盖。

`代码片段与出8宫格关键词附加` HARD RULE：
- A / B / C 三个候选方案的提示词内容必须完整放在独立的代码片段（```text ... ```）中，方便用户一键点击复制。
- 8宫格出图要求不是单独的 key-value 字段，而是直接在方案内容末尾附加一句出图关键词：`出8宫格图片。`。
- 第一步环节必须完整保留并出齐 3 个候选方案供用户挑选，严禁系统或 AI 自动选定；只有用户明确回复“抽卡”时才允许由 AI 随机选择一个方向。
- 极简流程：用户可直接点击代码块一键复制任意方案去出图；若用户回复 A / B / C，AI 直接基于该方案生成 8 宫格图片，不再输出冗长的方案计划文档。

`人物关系描述` HARD RULE：
- 情侣与所有多人拍摄必填。
- 描述关系结构、角色层级与互动基础；不得只写“情侣 / 家人 / 朋友”。
- 不使用固定关系 few-shot，按当前主题动态生成。

Hard Gates：
- A/B：两个现代现实世界著名真实地点，彼此地域/空间差异明显。
- C：古代 / 未来现实地标未来化 / 已知作品+明确地点。
- 三张卡全部通过 `few_shot_exclusion_set`。
- 禁止泛风格卡代替时空锚点。

结尾：
`可直接点击上方任意方案代码块一键复制提示词自行出图；或回复 A / B / C，我直接为你生成该方案的 8 宫格图片；也可以回复“抽卡”。`
