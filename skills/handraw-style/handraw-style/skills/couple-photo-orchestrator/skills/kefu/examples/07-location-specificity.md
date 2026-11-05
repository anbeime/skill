> **REFERENCE-ONLY / NOT A CANDIDATE POOL**：本文件只演示需求解析结构，不得把其中题材、地点、作品或造型作为运行时推荐候选；正式推荐必须通过 `few_shot_exclusion_set`。

# Progressive Location Specificity Examples

这些示例强调：**需求确认只锁时空锚点，Group Look 只给可拍区域，Shot List 才决定微点位。**

## A. 现代现实室内｜巴黎

### 需求确认
- location_mode: real_world
- city: 巴黎
- district_or_area: Paris 6e / Saint-Germain-des-Prés
- street_or_route: Boulevard Raspail / Boulevard Saint-Germain（私人公寓概念方案至少锁到真实街道）
- named_place: Hôtel Lutetia Paris；或“Boulevard Saint-Germain 沿线的 Haussmann 公寓语境（conceptual_private_interior）”
- indoor_outdoor: indoor
- verification_status: known_public_place_needs_current_verification / conceptual_private_interior

此时不要写：哪一间套房、哪扇高窗、沙发旁哪个位置。

### Group Look 可拍区域
- 酒店公共沙龙
- 客房起居区
- 楼梯 / 过厅空间

### Shot List 才细化
- Shot 01：公共沙龙临高窗区域
- Shot 02：主楼梯转角
- Shot 03：客房起居区靠壁炉一侧

如果用户坚持私人公寓但没有真实房源，不得虚构门牌号并宣称是真实地址。

## B. 现代现实户外｜杭州西湖

### 需求确认
- location_mode: real_world
- city: 杭州
- district_or_area: 西湖风景名胜区·孤山 / 北山街一带
- indoor_outdoor: outdoor
- verification_status: known_public_place_needs_current_verification

不要只写“西湖边”，但也不要现在就锁某一棵树、某一段栏杆。

### Group Look 可拍区域
- 北山街梧桐街景
- 孤山临湖步道
- 湖岸石阶 / 小尺度停留空间

### Shot List 才细化
每条 Shot 根据构图和人物数量选择具体树影、栏杆、石阶或转角。

## C. 文学作品｜《红楼梦》

### 需求确认
- location_mode: source_work
- source_work: 《红楼梦》
- in_world_location: 大观园·潇湘馆
- era_or_period: 清代小说语境
- world_state_or_chapter: 大观园居住时期

这已经是合格的作品时空锚点。不要在此阶段强制写“竹影院落通向回廊的转角”。

### Group Look 可拍区域
- 竹影院落
- 回廊
- 小轩窗内外

### Shot List 才细化
根据每条 Shot 决定人物是在回廊折角、窗外竹影旁还是院落入口。

## D. 游戏作品｜《原神》

### 需求确认
- location_mode: source_work
- source_work: 《原神》
- in_world_location: 璃月港·玉京台
- era_or_period: 提瓦特当代世界状态
- world_state_or_chapter: 璃月主城稳定时期

不要只写“璃月 / 原神城市”，但也不要过早锁定某个栏杆角度。

### Group Look 可拍区域
- 玉京台主平台
- 台阶与飞檐层次
- 临栏观景区

### Shot List 才细化
由 Shot 的景别、参与人数和动作决定具体台阶、临栏位置与背景纵深。
