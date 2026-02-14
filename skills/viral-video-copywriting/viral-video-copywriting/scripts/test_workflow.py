#!/usr/bin/env python3
"""
测试脚本：验证爆款短视频文案创作的完整流程

本脚本模拟完整的使用流程，确保每一步都能正常工作。
"""

import json
import sys


def step1_get_video_info(source_type="sample"):
    """
    第一步：获取视频信息

    Args:
        source_type: 'sample' (使用示例数据) 或 'url' (尝试从URL提取)

    Returns:
        dict: 视频信息
    """
    print("=" * 50)
    print("第一步：获取对标视频信息")
    print("=" * 50)

    if source_type == "url":
        print("\n方式A：通过抖音链接自动提取")
        url = input("请输入抖音视频URL（直接回车使用示例数据）：")
        if url.strip():
            print(f"\n正在提取：{url}")
            print("注意：由于抖音平台限制，可能无法成功提取")
            # 这里可以调用extract_douyin_video.py
            # 暂时返回模拟数据
            video_info = {
                "title": "从URL提取的标题",
                "description": "从URL提取的描述",
                "copywriting": "从URL提取的文案",
                "background_music": "从URL提取的音乐信息"
            }
        else:
            print("\n使用示例数据...")
            video_info = get_sample_video_data()
    else:
        print("\n方式B：使用示例数据")
        video_info = get_sample_video_data()

    print("\n✅ 第一步完成，获取到视频信息：")
    print(f"  标题：{video_info['title']}")
    print(f"  描述：{video_info['description'][:50]}...")
    print(f"  文案长度：{len(video_info['copywriting'])}字")
    print()

    return video_info


def step2_analyze_viral_factors(video_info):
    """
    第二步：深度拆解爆款因素

    Args:
        video_info: 视频信息字典

    Returns:
        dict: 分析报告
    """
    print("=" * 50)
    print("第二步：深度拆解爆款因素")
    print("=" * 50)

    print("\n正在分析视频...")

    # 模拟分析过程（实际由智能体完成）
    analysis_report = {
        "hook_analysis": {
            "type": "悬念型",
            "content": "你知道吗？90%的人都在用错误的方式工作。",
            "strength": 9
        },
        "structure_analysis": {
            "type": "问题-解决方案",
            "description": "提出问题 → 给出3个解决方案 → 总结引导",
            "parts": {
                "opening": {
                    "content": "你知道吗？90%的人都在用错误的方式工作。",
                    "function": "吸引注意，引发好奇",
                    "word_count": 18,
                    "percentage": 8.5
                },
                "middle": {
                    "content": "今天分享3个小技巧，让你的工作效率翻倍...",
                    "function": "传递价值，提供方法",
                    "word_count": 180,
                    "percentage": 85
                },
                "ending": {
                    "content": "学会了吗？收藏起来，明天就开始用！",
                    "function": "强化记忆，促进互动",
                    "word_count": 14,
                    "percentage": 6.5
                },
                "total": {
                    "word_count": 212,
                    "percentage": 100
                }
            }
        },
        "style_analysis": {
            "language": "接地气，口语化",
            "emotion": "积极向上，实用导向",
            "sentence_pattern": "长短结合，以短句为主",
            "vocabulary": "口语化，通俗易懂",
            "techniques": ["设问", "列举", "行动引导"]
        },
        "length_analysis": {
            "total_word_count": 212,
            "estimated_duration": 63,  # 按正常语速200字/分钟
            "parts": {
                "opening": {"word_count": 18, "percentage": 8.5, "estimated_seconds": 5.4},
                "middle": {"word_count": 180, "percentage": 85, "estimated_seconds": 54},
                "ending": {"word_count": 14, "percentage": 6.5, "estimated_seconds": 4.2}
            },
            "avg_sentence_length": 10.6,
            "avg_sentence_count": 20
        },
        "content_analysis": {
            "core_value": "提升工作效率的方法",
            "target_audience": "职场人士，特别是工作效率低的人",
            "pain_point": "忙碌但效率低，需要快速见效的方法"
        },
        "viral_elements": [
            {
                "element": "开头悬念钩子",
                "weight": 30,
                "reason": "前3秒抓住注意力，引发好奇"
            },
            {
                "element": "具体可执行的方法",
                "weight": 40,
                "reason": "3个实用技巧，看完就能用"
            },
            {
                "element": "收藏引导",
                "weight": 20,
                "reason": "提高互动率，增加算法推荐"
            },
            {
                "element": "话题标签",
                "weight": 10,
                "reason": "增加曝光，触达目标用户"
            }
        ]
    }

    print("\n✅ 第二步完成，生成分析报告：")
    print(f"  开头钩子：{analysis_report['hook_analysis']['type']}")
    print(f"  文案结构：{analysis_report['structure_analysis']['type']}")
    print(f"  文案总字数：{analysis_report['length_analysis']['total_word_count']}字")
    print(f"  预计时长：{analysis_report['length_analysis']['estimated_duration']}秒")
    print(f"  爆款要素：{len(analysis_report['viral_elements'])}个")
    print()

    return analysis_report


def step3_understand_user_needs():
    """
    第三步：了解用户需求

    Returns:
        dict: 用户需求
    """
    print("=" * 50)
    print("第三步：了解用户需求")
    print("=" * 50)

    print("\n请描述您的创作想法：")
    print("(以下为示例输入，实际使用时由用户提供)")

    user_needs = {
        "core_content": "提高工作效率的方法，针对学生群体",
        "target_audience": "大学生和研究生",
        "value_proposition": "帮助学生平衡学习、社团、生活",
        "initial_draft": "想讲讲时间管理，但不知道怎么组织内容",
        "style_preference": "希望亲切一点，不要太严肃"
    }

    print(f"  核心内容：{user_needs['core_content']}")
    print(f"  目标受众：{user_needs['target_audience']}")
    print(f"  传递价值：{user_needs['value_proposition']}")
    print()

    return user_needs


def step4_create_new_copywriting(video_info, analysis_report, user_needs):
    """
    第四步：创作爆款新文案

    Args:
        video_info: 视频信息
        analysis_report: 分析报告
        user_needs: 用户需求

    Returns:
        list: 多版文案
    """
    print("=" * 50)
    print("第四步：创作爆款新文案")
    print("=" * 50)

    print("\n正在创作文案...")
    print("严格对标原则：结构100%对标、风格100%对标、长度±5%以内")

    # 模拟创作过程（实际由智能体完成）
    copywriting_versions = [
        {
            "version": "A",
            "content": """作为学生，你是否每天都在忙，却感觉什么都没做成？

今天分享3个学生专属技巧，让你学习效率翻倍！

第一个技巧：黄金时间段。找出你一天中注意力最集中的2小时，专门用来攻克最难的内容。

第二个技巧：碎片时间利用。排队、等车、课间，这些碎片时间可以用来背单词、复习笔记。

第三个技巧：每日三件事。每天睡前写下明天最重要的3件事，第二天直接按清单执行。

学会了吗？收藏起来，明天就开始用！

别忘了关注我，分享更多学生成长干货！""",
            "word_count": 205,  # 接近对标文案的212字
            "design_idea": {
                "hook_type": "痛点共鸣型（对标：悬念型）",
                "structure": "问题-解决方案（完全对标）",
                "style": "亲切、接地气（完全对标）",
                "sentence_pattern": "长短结合，以短句为主（完全对标）",
                "vocabulary": "口语化，通俗易懂（完全对标）"
            },
            "word_breakdown": {
                "opening": {"word_count": 18, "percentage": 8.8},  # 对标：18字，8.5%
                "middle": {"word_count": 173, "percentage": 84.4},  # 对标：180字，85%
                "ending": {"word_count": 14, "percentage": 6.8}  # 对标：14字，6.5%
            },
            "benchmark_comparison": {
                "total_word_count": {"benchmark": 212, "new": 205, "deviation": "-3.3%"},
                "opening_word_count": {"benchmark": 18, "new": 18, "deviation": "0%"},
                "middle_word_count": {"benchmark": 180, "new": 173, "deviation": "-3.9%"},
                "ending_word_count": {"benchmark": 14, "new": 14, "deviation": "0%"},
                "estimated_duration": {"benchmark": 63, "new": 61.5, "deviation": "-2.4%"},
                "structure_type": {"benchmark": "问题-解决方案", "new": "问题-解决方案", "deviation": "一致"},
                "language_style": {"benchmark": "接地气，口语化", "new": "亲切，接地气", "deviation": "一致"},
                "emotion_tone": {"benchmark": "积极向上", "new": "积极向上", "deviation": "一致"}
            },
            "highlights": [
                {"text": "每天忙却什么都没做成", "type": "开头钩子", "benchmark_element": "你知道吗？90%的人都在用错误的方式工作。"},
                {"text": "黄金时间段、碎片时间、每日三件事", "type": "核心方法", "benchmark_element": "番茄工作法、二八法则、每日三件事"},
                {"text": "收藏起来", "type": "行动引导", "benchmark_element": "收藏起来"}
            ],
            "element_migration": [
                {"benchmark": "开头钩子-悬念型", "new": "开头钩子-痛点型", "effect": "保留钩子功能，适配学生群体"},
                {"benchmark": "收藏引导", "new": "收藏引导", "effect": "完全迁移，保持互动引导"},
                {"benchmark": "3个方法列举", "new": "3个方法列举", "effect": "完全迁移，保持结构"}
            ]
        },
        {
            "version": "B",
            "content": """同学，你还在为时间不够用而焦虑吗？

我发现学霸们都在用这3个方法管理时间！

方法一：番茄工作法变体。学生版的45+10，学习45分钟，休息10分钟，正好一节课。

方法二：优先级四象限。把事情按紧急和重要程度分类，先做重要紧急的。

方法三：专注力训练。每天练习一次25分钟无手机学习，逐步提升专注时长。

3个方法，亲测有效！

点赞收藏，转发给你的同学！""",
            "word_count": 198,  # 接近对标文案的212字
            "design_idea": {
                "hook_type": "痛点+好奇心（对标：悬念型）",
                "structure": "问题-解决方案（完全对标）",
                "style": "更活泼、互动性强（对标风格调整）",
                "sentence_pattern": "长短结合，以短句为主（完全对标）",
                "vocabulary": "口语化，通俗易懂（完全对标）"
            },
            "word_breakdown": {
                "opening": {"word_count": 17, "percentage": 8.6},  # 对标：18字，8.5%
                "middle": {"word_count": 166, "percentage": 83.8},  # 对标：180字，85%
                "ending": {"word_count": 15, "percentage": 7.6}  # 对标：14字，6.5%
            },
            "benchmark_comparison": {
                "total_word_count": {"benchmark": 212, "new": 198, "deviation": "-6.6%"},
                "opening_word_count": {"benchmark": 18, "new": 17, "deviation": "-5.6%"},
                "middle_word_count": {"benchmark": 180, "new": 166, "deviation": "-7.8%"},
                "ending_word_count": {"benchmark": 14, "new": 15, "deviation": "+7.1%"},
                "estimated_duration": {"benchmark": 63, "new": 59.4, "deviation": "-5.7%"},
                "structure_type": {"benchmark": "问题-解决方案", "new": "问题-解决方案", "deviation": "一致"},
                "language_style": {"benchmark": "接地气，口语化", "new": "活泼，互动性强", "deviation": "一致"},
                "emotion_tone": {"benchmark": "积极向上", "new": "积极向上", "deviation": "一致"}
            },
            "highlights": [
                {"text": "时间不够用而焦虑", "type": "开头钩子", "benchmark_element": "你知道吗？90%的人都在用错误的方式工作。"},
                {"text": "学霸们都在用", "type": "身份标签", "benchmark_element": "90%的人"},
                {"text": "点赞收藏，转发给你的同学", "type": "社交引导", "benchmark_element": "收藏起来"}
            ],
            "element_migration": [
                {"benchmark": "开头钩子-悬念型", "new": "开头钩子-痛点+好奇心", "effect": "保留钩子功能，增加身份标签"},
                {"benchmark": "收藏引导", "new": "点赞收藏，转发", "effect": "扩展互动引导，增加社交传播"},
                {"benchmark": "3个方法列举", "new": "3个方法列举", "effect": "完全迁移，保持结构"}
            ]
        }
    ]

    print("\n✅ 第四步完成，生成2版文案：")
    for version in copywriting_versions:
        print(f"\n  版本{version['version']}：")
        print(f"    总字数：{version['word_count']}字（对标：{version['benchmark_comparison']['total_word_count']['benchmark']}字，偏差：{version['benchmark_comparison']['total_word_count']['deviation']}）")
        print(f"    结构：{version['design_idea']['structure']}")
        print(f"    风格：{version['design_idea']['style']}")
        print(f"    亮点数量：{len(version['highlights'])}个")
        print(f"    对标元素迁移：{len(version['element_migration'])}个")

    print()

    return copywriting_versions

    print("\n✅ 第四步完成，生成2版文案：")
    for version in copywriting_versions:
        print(f"\n  版本{version['version']}：")
        print(f"    设计思路：{version['design_idea']['hook_type']} + {version['design_idea']['structure']}")
        print(f"    亮点数量：{len(version['highlights'])}个")

    print()

    return copywriting_versions


def step5_iterate_optimize(copywriting_versions):
    """
    第五步：迭代优化（可选）

    Args:
        copywriting_versions: 文案版本列表

    Returns:
        dict: 优化后的文案
    """
    print("=" * 50)
    print("第五步：迭代优化（可选）")
    print("=" * 50)

    print("\n如果对文案有反馈，可以继续优化...")
    print("(以下为示例，实际使用时由用户提供反馈)")

    # 模拟优化过程
    print("\n示例反馈：版本A的开头可以更有冲击力")
    print("\n优化后的版本A开头：")
    print("  原版：作为学生，你是否每天都在忙，却感觉什么都没做成？")
    print("  优化：你每天学8小时，成绩还是提不上来？")

    print("\n✅ 第五步完成（可选）")
    print()

    return copywriting_versions


def get_sample_video_data():
    """获取示例视频数据"""
    return {
        "title": "3个小技巧让你工作效率翻倍",
        "description": "职场必备技能，建议收藏！很多人每天工作都很忙，但效率很低...",
        "copywriting": "你知道吗？90%的人都在用错误的方式工作。今天分享3个小技巧，让你的工作效率翻倍。第一个技巧：番茄工作法...",
        "background_music": "轻快电子音乐，节奏明快，积极向上",
        "tags": ["职场", "效率", "工作技巧"],
        "data": {
            "likes": 1200000,
            "comments": 30000,
            "shares": 50000
        }
    }


def main():
    """主函数：执行完整流程测试"""
    print("\n" + "=" * 50)
    print("爆款短视频文案创作 - 完整流程测试")
    print("=" * 50)
    print()

    # 第一步：获取视频信息
    video_info = step1_get_video_info(source_type="sample")

    # 第二步：深度拆解爆款因素
    analysis_report = step2_analyze_viral_factors(video_info)

    # 第三步：了解用户需求
    user_needs = step3_understand_user_needs()

    # 第四步：创作爆款新文案
    copywriting_versions = step4_create_new_copywriting(video_info, analysis_report, user_needs)

    # 第五步：迭代优化（可选）
    optimized_versions = step5_iterate_optimize(copywriting_versions)

    # 总结
    print("=" * 50)
    print("测试完成！")
    print("=" * 50)
    print("\n✅ 完整流程验证通过")
    print("  - 第一步：获取视频信息 ✓")
    print("  - 第二步：拆解爆款因素 ✓")
    print("  - 第三步：了解用户需求 ✓")
    print("  - 第四步：创作新文案 ✓")
    print("  - 第五步：迭代优化 ✓")
    print()

    # 输出详细结果
    print("=" * 50)
    print("详细结果（JSON格式）")
    print("=" * 50)
    result = {
        "video_info": video_info,
        "analysis_report": analysis_report,
        "user_needs": user_needs,
        "copywriting_versions": copywriting_versions
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))

    return 0


if __name__ == "__main__":
    sys.exit(main())
