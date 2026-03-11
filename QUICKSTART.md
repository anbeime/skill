# FlexAssemblySkill

OpenClaw柔性制造技能包 - 让AI操控机器人

## 安装

```bash
# 安装到OpenClaw
openclaw skills install .
```

## 使用

```python
from skill import FlexAssemblySkill

skill = FlexAssemblySkill()

# 学习新产品
skill.learn_product("product_001", demo_count=50)

# 执行装配
skill.assemble("product_001")

# 质量检测
skill.inspect("product_001")

# 多设备协调
skill.coordinate(["robot_1", "agv_1"], "运输物料")
```

## 运行演示

```bash
python examples/demo.py
```
