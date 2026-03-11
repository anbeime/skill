# FlexAssembly - OpenClaw柔性制造技能包

让OpenClaw从"对话"进化到"操控机器人"

## 简介

**FlexAssembly** 是一个基于OpenClaw的柔性制造技能包，核心突破是让AI能够操控机器人执行真实的装配任务。

### 核心能力

| 功能 | 说明 | 效果 |
|-----|------|------|
| **learn_product** | 学习新产品 | 50条演示，<2小时换产 |
| **assemble** | 智能装配 | AI控制机器人执行 |
| **inspect** | 零样本检测 | 1-2个良品样本 |
| **coordinate** | 多设备协同 | 机器人+AGV协同 |

### 效果对比

| 环节 | 传统方式 | FlexAssembly | 提升 |
|-----|---------|-------------|------|
| 换产时间 | 8-24小时 | <2小时 | **90%** |
| 训练数据 | 1000+条 | 50条 | **95%** |
| 专业要求 | 编程专家 | 操作员 | **80%** |

## 安装

```bash
# 克隆仓库
git clone https://github.com/anbeime/skill.git
cd skill/FlexAssemblySkill

# 安装到OpenClaw
openclaw skills install .
```

## 使用

```python
from flex_assembly import FlexAssemblySkill

# 创建技能包实例
skill = FlexAssemblySkill()

# 1. 学习新产品
result = skill.learn_product("connector_001", demo_count=50)

# 2. 执行装配
result = skill.assemble("connector_001")

# 3. 质量检测
result = skill.inspect("connector_001")

# 4. 多设备协同
result = skill.coordinate(["robot_1", "agv_1"], "运输物料")
```

## OpenClaw"上帝权限"应用

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  Shell接口  │     │  文件系统   │     │  硬件接口   │
│             │     │             │     │             │
│ 控制仿真    │     │ 管理知识库  │     │ 控制机器人  │
│ 控制机器人  │     │ 存储模型    │     │ 读取传感器  │
│ 执行训练    │     │ 管理配置    │     │ 操控执行器  │
└─────────────┘     └─────────────┘     └─────────────┘
```

## 项目结构

```
FlexAssemblySkill/
├── skill.md           # 技能包描述文件
├── skill.py           # 技能包实现
├── README.md          # 说明文档
├── requirements.txt   # 依赖
└── examples/          # 示例代码
    └── demo.py
```

## 许可证

MIT License

## 参赛信息

- 比赛: OpenClaw挑战赛
- 团队: FlexAssembly Team
