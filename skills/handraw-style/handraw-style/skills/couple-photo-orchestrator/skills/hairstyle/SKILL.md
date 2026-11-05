---
name: editorial-hairstylist
description: Early professional hairstylist node that designs and locks formal shoot hair for each candidate direction before downstream Look expansion.
version: 2.24.26
language: zh-CN
---

# Editorial 专业发型师

## 定位
这是正式拍摄的**前置专业造型节点**。在方向卡已经有明确时空、场景与逐人服装草案后立即运行，用来生成该方向的正式发型；用户选中方向后，下游 Look / Shot / 生图只继承，不重复重新设计。

## 触发
- 自主模式：A/B/C 每个合法候选方向在展示给用户前，都先完成逐人发型设计。
- 抽卡模式：系统选定合法方向后，立即完成逐人发型设计，再进入 Look 展开。
- Remix：仅当上游变量根据依赖图使发型失效时重跑，例如换年代、换服装、换世界观，或地点环境发生会显著影响发型的变化。

## 参考图边界
- Canonical 真人参考图只提供人脸身份信息，不提供发型锁定。发长、直卷、刘海、分缝、体积、轮廓与发色质感均可重新设计。
- 不得因为原图中的头发清晰可见就默认沿用；除非用户明确要求保留原发型。

## 设计自由度 Hard Gate
除非用户明确锁定，原参考图和精修身份参考图的头发都不是限制。可自由改变：
- length：变长 / 变短；
- texture：直发 / 卷发 / 波浪；
- parting：中分 / 偏分 / 无明显分缝；
- fringe：保留原刘海 / 设计具体新刘海 / 露额；
- crown_volume：顶部体积；
- sides：两侧包裹、贴合、碎发；
- back：后区收束、盘发、披发、马尾等；
- silhouette：整体轮廓；
- ear_neck_exposure：是否露耳 / 露颈；
- hair_accessories：必要发饰；
- hair_color_feel：必要且与主题一致的发色质感。

**刘海策略必须显式决定，禁止无意识沿用参考图。**

## 设计依据
综合人物气质、脸型与五官重心、额头比例、头颈/肩部比例、逐人服装、领口与肩线、配饰、时代/作品世界、场景环境与摄影语言，直接设计最符合该方向气质的发型。

## 输出
每位参与者输出一个结构化 `hairstyle_design`：
- participant_id / label
- length
- texture
- parting
- fringe
- crown_volume
- sides
- back
- silhouette
- ear_neck_exposure
- hair_accessories
- hair_color_feel
- design_reason

不向用户再给 A/B/C 发型选项；方向卡直接显示定稿结果。用户明确要求改发型时才重跑本节点。
