---
name: flex_assembly
version: 1.0.0
description: 柔性制造技能包 - 让OpenClaw操控机器人
author: FlexAssembly Team
license: MIT
tags:
  - manufacturing
  - robotics
  - assembly
  - quality-inspection
commands:
  - name: learn_product
    description: 学习新产品，实现快速换产
    params:
      - name: product_id
        type: string
        required: true
        description: 产品ID
      - name: demo_count
        type: integer
        default: 50
        description: 演示数据数量
  - name: assemble
    description: 执行装配任务
    params:
      - name: product_id
        type: string
        required: true
      - name: robot_id
        type: string
        default: "robot_1"
  - name: inspect
    description: 零样本质量检测
    params:
      - name: product_id
        type: string
        required: true
      - name: image_path
        type: string
        required: false
  - name: coordinate
    description: 协调多设备
    params:
      - name: devices
        type: array
        required: true
      - name: task
        type: string
        required: true
  - name: status
    description: 获取产品状态
    params:
      - name: product_id
        type: string
        required: false
---

# FlexAssembly - 柔性制造技能包

## 功能概述

FlexAssembly让OpenClaw从"对话"进化到"操控机器人"，实现AI控制真实产线。

### 核心能力

1. **快速换产**: 仅需50条演示，2小时内完成换产（传统需要8-24小时）
2. **智能装配**: AI控制机器人执行装配任务
3. **零样本检测**: 仅需1-2个良品样本即可检测未知缺陷
4. **多设备协同**: 协调机器人、AGV等多设备协同工作

### OpenClaw"上帝权限"的应用

| OpenClaw能力 | FlexAssembly实现 | 效果 |
|-------------|-----------------|------|
| Shell接口 | 控制仿真环境/机器人 | AI操控物理设备 |
| 文件系统 | 管理知识库/模型 | AI自主管理知识 |
| 硬件接口 | 控制双臂机器人 | AI直接控制产线 |

## 使用示例

### 学习新产品

```
用户: 帮我学习产品connector_001
OpenClaw: 好的，正在学习产品connector_001...
[FlexAssembly] 启动仿真环境...
[FlexAssembly] 采集演示数据 (50条)...
[FlexAssembly] 训练策略模型...
产品 connector_001 学习完成，换产时间: < 2小时
```

### 执行装配

```
用户: 执行connector_001的装配
OpenClaw: 开始执行装配任务...
[感知] 产品位置: (x=0.52, y=0.31, z=0.08)
[规划] 生成动作序列: 16步
[协调] 调度机器人执行...
装配完成，耗时: 45秒
```

### 质量检测

```
用户: 检测connector_001的质量
OpenClaw: 执行零样本检测...
检测结果: 合格
置信度: 0.98
```

## 应用价值

| 场景 | 传统成本 | FlexAssembly成本 | 年节省 |
|-----|---------|-----------------|-------|
| 换产停机 | 8小时/次 | 2小时/次 | 600小时 |
| 专家费用 | 30万/年 | 0 | 30万/年 |
| 数据采集 | 10万/产品 | 1万/产品 | 90万/年 |

## 技术原理

### 多智能体协同

```
感知 → 规划 → 执行

视觉感知小龙虾 → 任务规划小龙虾 → 协调调度小龙虾
    ↓                  ↓                  ↓
 产品识别          动作序列          设备调度
 质量检测          路径规划          故障恢复
```

### 少样本学习

- 使用模仿学习 + 强化学习
- 域自适应技术
- 元学习框架

### 零样本检测

- CLIP/DINO特征提取
- 异常检测算法
- 对比学习方法
