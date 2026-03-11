"""
FlexAssembly 技能包演示示例
"""

from skill import FlexAssemblySkill


def main():
    """演示FlexAssembly技能包的核心功能"""
    
    print("\n" + "="*60)
    print("   FlexAssembly - OpenClaw柔性制造技能包演示")
    print("="*60)
    
    # 创建技能包实例
    skill = FlexAssemblySkill()
    
    # ========== 1. 学习新产品 ==========
    print("\n" + "-"*60)
    print("【功能1】学习新产品 - 快速换产")
    print("-"*60)
    
    product_id = "connector_001"
    print(f"\n用户: 帮我学习产品 {product_id}")
    print("OpenClaw: 好的，正在学习产品...\n")
    
    result = skill.learn_product(product_id, demo_count=50)
    
    print(f"\n学习结果:")
    print(f"  - 状态: {result['status']}")
    print(f"  - 产品ID: {result['product_id']}")
    print(f"  - 演示数量: {result['demo_count']}条")
    print(f"  - 训练时间: {result['train_time']}")
    print(f"  - 换产时间: {result['switch_time']}")
    print(f"\n对比传统方案: 8-24小时 → <2小时")
    
    # ========== 2. 执行装配 ==========
    print("\n" + "-"*60)
    print("【功能2】执行装配 - AI控制机器人")
    print("-"*60)
    
    print(f"\n用户: 执行 {product_id} 的装配")
    print("OpenClaw: 开始执行装配任务...\n")
    
    result = skill.assemble(product_id)
    
    print(f"\n装配结果:")
    print(f"  - 状态: {result['status']}")
    print(f"  - 执行时间: {result['execution_time']}")
    print(f"  - 动作步数: {result['action_count']}步")
    print(f"  - 质量评分: {result['quality_score']}")
    
    # ========== 3. 质量检测 ==========
    print("\n" + "-"*60)
    print("【功能3】质量检测 - 零样本检测")
    print("-"*60)
    
    print(f"\n用户: 检测 {product_id} 的质量")
    print("OpenClaw: 执行零样本质量检测...\n")
    
    result = skill.inspect(product_id)
    
    print(f"\n检测结果:")
    print(f"  - 状态: {result['status']}")
    print(f"  - 是否缺陷: {'是' if result['is_defect'] else '否'}")
    print(f"  - 置信度: {result['confidence']}")
    print(f"  - 备注: {result['note']}")
    
    # ========== 4. 多设备协调 ==========
    print("\n" + "-"*60)
    print("【功能4】多设备协调 - 协同工作")
    print("-"*60)
    
    devices = ["robot_1", "agv_1"]
    task = "运输物料到装配工位"
    
    print(f"\n用户: 协调 {devices} 执行任务: {task}")
    print("OpenClaw: 开始协调设备...\n")
    
    result = skill.coordinate(devices, task)
    
    print(f"\n协调结果:")
    print(f"  - 状态: {result['status']}")
    print(f"  - 设备: {result['devices']}")
    print(f"  - 任务: {result['task']}")
    for r in result['results']:
        print(f"    - {r['device']}: {r['status']}")
    
    # ========== 5. 状态查询 ==========
    print("\n" + "-"*60)
    print("【功能5】状态查询 - 产品管理")
    print("-"*60)
    
    print(f"\n用户: 查看所有产品状态")
    
    result = skill.status()
    
    print(f"\n状态结果:")
    print(f"  - 产品数量: {result['count']}")
    for product in result['products']:
        print(f"    - {product['product_id']}: {product['status']}")
    
    # ========== 总结 ==========
    print("\n" + "="*60)
    print("   演示完成！")
    print("="*60)
    
    print("""
效果对比总结:
┌─────────────┬──────────────┬──────────────────┐
│   环节      │    传统      │   FlexAssembly   │
├─────────────┼──────────────┼──────────────────┤
│ 换产时间    │  8-24小时    │   < 2小时        │
│ 训练数据    │  1000+条     │   50条           │
│ 专业要求    │  编程专家    │   操作员即可     │
│ 质检样本    │  大量缺陷    │   1-2个良品      │
└─────────────┴──────────────┴──────────────────┘

OpenClaw "上帝权限" 应用:
- Shell接口: 控制仿真环境、机器人
- 文件系统: 管理知识库、配置、模型
- 硬件接口: 控制真实设备
""")


if __name__ == "__main__":
    main()
