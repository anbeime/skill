人物关系描述：{{relationship_description}}
# LOOK {{index}}｜{{name}}

## 1. 群体设计逻辑
{{group_design_logic}}

## 2. 逐人服装

{{participant_sections}}

每个人物小节必须独立包含：人物编号 / 标签、角色定位、完整服装描述、服装结构与层次、材质、颜色、鞋履、配饰、角色或时代逻辑、场景适配、避免项。不得使用“其余人类似”等汇总替代。正式发型与正式妆容已经在方向阶段由专业节点完成，本 Look 只继承并展开，不重复重设计。

## 3. 群体搭配关系
{{relationship}}

## 4. 场景 Location Card
- 地点模式：{{location_mode}}
- 时空锚点：{{spacetime_anchor}}
- 室内 / 户外：{{indoor_outdoor}}
- 作品来源：{{source_work_optional}}
- 时代 / 时期 / 章节 / 世界状态：{{era_or_period_optional}}
- 核验状态：{{verification_status_optional}}
- 场景完整描述：{{scene}}

## 5. 可拍区域候选
{{areas}}

这里只写 2–4 个区域级候选，例如“公共休息区 / 客房起居区 / 楼梯空间”或“竹影院落 / 回廊 / 小轩窗内外”。**不要**提前指定每条 Shot 的具体窗位、转角、台阶、岸线节点；这些留给 Shot List。

## 6. 道具与归属
{{props}}

## 7. 与需求的匹配逻辑
{{brief_reason_optional}}


## 8. 妆发继承锁
- 从用户选中的方向卡继承每位参与者的 `hairstyle_design` 与 `makeup_design`。
- 下游只能完整保留；不能因为 Look 展开、Shot List 或最终生图而自行改回参考图发型，或退化成通用自然妆。
- 只有用户明确修改妆发，或 Remix Dependency Graph 判定上游变化使妆发失效时，才重新调用专业发型师/化妆师节点。
