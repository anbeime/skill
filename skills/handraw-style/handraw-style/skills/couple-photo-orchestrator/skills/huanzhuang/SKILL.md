---
name: couple-photo-wardrobe-board
description: Design numbered six-look wardrobe boards for one or any number of participants inside a confirmed portrait theme, preserving full per-person outfit detail.
version: 2.24.26
---

# 任意人数换装 6 宫格

当用户说“换装”“换衣服”“重新搭配”“服装不满意”“再来一版”等，并且当前人物摄影项目已有明确主题时，使用本 Skill。

情侣只是两人预设；本 Skill 的标准数据结构是 `participants[]`，人数可为 1 或任意多人。

## Detail Floor

每一套候选必须逐人写完整服装，不得压缩：
- P01 一条完整 outfit
- P02 一条完整 outfit
- ...直到所有人

禁止“其他人类似”“其余成员同款”“大家统一穿……”作为人物服装描述。允许先说明共享母题，但之后仍要逐人给最终穿着。

## 流程

1. 继承已确认的主题、地点语境、人物 roster、人物关系、身份参考和避免项。主题未确认时退回 `kefu`。
2. 设计 6 套在至少两项上明显不同的群体服装组合。
3. 每套 JSON 必须包含：
   - `name`
   - `participants`: 每人包含 `participant_id`、`label`、`outfit`
   - `group_relationship`
   - `scene`
   - `props`
4. 六套必须包含完全相同的人物 ID，顺序一致；不得在某套里漏人或增人。
5. 展示完整文字板卡，等待用户确认出图。
6. 用户明确授权后，将 6 套完整逐人服装编译成一次生成的一张无编号自适应 6 宫格。每格必须出现该候选的完整人物 roster。
   - 生成 6 宫格时不指定单格比例、单格尺寸或整板比例。
   - 6 宫格不规定列数/行数；AI 可自由排布，只要恰好 6 格、每格清晰独立、整体可读。
7. `register-grid` 只叠加准确数字编号；模型不得生成文字或数字。
8. 用户说“再来一版”时，创建 6 套全新组合并延续编号。
9. 用户可选一个或多个编号；`select` 把所选方案升级为 confirmed Look，并在具备结构化地点时写入 schema v3 的 `participant_looks`、`visual_lock.participant_outfits` 与 `location_lock`，再回到 `paishe`。

## 新 JSON 示例

```json
[
  {
    "name": "LOOK A",
    "participants": [
      {"participant_id": "P01", "label": "姐姐", "outfit": "完整服装描述……"},
      {"participant_id": "P02", "label": "弟弟", "outfit": "完整服装描述……"},
      {"participant_id": "P03", "label": "母亲", "outfit": "完整服装描述……"}
    ],
    "group_relationship": "三人共享米白与灰蓝，但材质与廓形按年龄和角色区分……",
    "scene": "……",
    "props": "……"
  }
]
```

旧的 `female / male / couple` 双人 JSON 仍可读取，并自动转换为 P01/P02；新项目不要再写旧格式。

## 状态与边界

- `WARDROBE_TEXT_REVIEW`：文字候选审阅
- `WARDROBE_GRID_REVIEW`：带编号宫格审阅
- 新板卡归档受影响的旧 handoff / 拍摄方案 / Shot 板，不删除历史图
- 编号单调递增
- 主题改变后旧主题候选不可直接选入新流程

## 命令

```powershell
python skills/huanzhuang/scripts/wardrobe_board.py create <项目目录> --theme "<confirmed theme>" --options-file <draft.json> --theme-id THEME-001
python skills/huanzhuang/scripts/wardrobe_board.py prepare-grid <项目目录> BOARD-001 --theme-id THEME-001
python skills/huanzhuang/scripts/wardrobe_board.py register-grid <项目目录> BOARD-001 --image <六宫格.png> --theme-id THEME-001
python skills/huanzhuang/scripts/wardrobe_board.py select <项目目录> --ids 1,3 --theme-id THEME-001
```


## 跨 Session / 重开主题 / 换装不降质

换装是服装分支，不是“简化模式”。无论新 session、重开 Theme 还是“再来一版”，每个候选仍必须完整写出所有人物，不得把后面的人压缩成“其他人类似”。

场景必须保持已确认的**时空锚点**：候选中的 `scene` 不能把真实地点或作品内地点缩写成“酒店 / 街头 / 庭院 / 城市”。换装阶段只需要保留地点锚点，并可给区域级候选；不要提前锁定 Shot 级的窗位、回廊转角、台阶或岸线节点。

### 现实室内地点
现实室内换装方案不能只写城市或街区。优先保留真实具名酒店/建筑；私人公寓概念至少保留真实街道/路线锚点，并标记为 `conceptual_private_interior`。不得虚构门牌或房号。


## 2.24.20 发型边界
- Wardrobe Board 只负责服装/整体造型预览，不锁正式拍摄发型。
- 若用户真正选择了新的换装方案，该“换服装”动作按 Remix Dependency Graph 使原正式发型/妆容失效；系统应立即重新运行 Editorial 发型师 → Editorial 化妆师，再锁定新 Look。换装预览本身的临时妆发不直接成为正式结果。


## 2.24.20 妆容边界
- Wardrobe Board 中的妆容只用于视觉完整性/找感觉，不锁正式拍摄妆面。
- 新换装一旦确认，立即重算正式妆发；之后下游只继承新锁。
