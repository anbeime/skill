# Pose & Emotion Contract — 2.24.20

姿势规划不是姿势词库，也不是全身参数表。每条 Shot 使用分层规划：

`动作意图 → 关键身体力学 → 人物关系/接触 → 情绪动机 → 景别适配`

## 1. Action intent
先说明画面中正在发生什么，再决定身体形态。动作必须有情境原因，不写“自由摆拍 / 自然互动”。

## 2. Key body mechanics
每条只选择 2–4 个真正决定姿势成立的点，不机械填满全部：
- 脚位 / 前后脚关系 / 支撑脚与放松脚
- 脚尖、膝盖方向
- 重心位置与转移
- 骨盆方向
- 肩线
- 躯干前倾 / 后仰 / 侧倾 / 扭转
- 脊柱延展
- 手部落点、支撑点
- 与环境 / 道具接触点

## 3. Framing adaptation
- 全身：重点脚位、腿部、重心、整体轴线。
- 三分之二 / 半身：重点骨盆以上、肩线、躯干、手部、接触关系。
- 近景 / 特写：重点头颈、肩线、手部、视线与微动作；禁止强行描述镜头外脚位。

## 4. Pose-family semantic dedupe
如果两条 Shot 只是更换墙 / 栏杆 / 桌子 / 道具，但承重结构、身体主轴、移动方式和接触模式相同，仍属于同一姿势家族，必须重做。

## 5. Couple contact topology
情侣至少考虑：
- initiator / respondent
- body distance
- contact point
- body orientation
- weight response
- gaze relationship

## 6. Emotion generation
情绪与姿势一起规划，但**不建立固定情绪 few-shot、不建立固定情绪词表**。
情绪应从当前主题、关系、场景和叙事动态生成，并转化成可执行的身体反应 / 视线 / 表情，而不是硬套标签。

## 7. Shot fields
每条 Shot 至少显式包含：
- action_event
- pose_structure
- key_support_weight
- relationship_contact
- emotion_motivation
- gaze
- framing_adaptation

这些字段与 scene_area / shot_size / composition / lighting 一起构成最终 Shot。
