# Editorial Makeup Artist Plan

为每位人物输出：
- participant_id / label
- skin_optimization
- base_makeup
- brows_eyes
- cheeks_lips
- highlight_contour
- theme_fit

Hard Gate：
- 本节点前移到方向阶段：先完成该方向的逐人服装草案与 Editorial 发型，再生成 `makeup_design`。
- 女性默认 `skin_optimization`：**白皙柔焦影楼精修，同时具有明显淡化斑点/泛红/肤色不均、去黑眼圈、轻微磨皮、柔和柔焦光晕、均匀偏白皙的健康肤色**。
- 非女性按人物与题材做专业、克制、上镜的肤质与气色整理。
- 用户选中方向后，下游继承本结果；除非依赖图失效或用户明确改妆，不重复设计。
