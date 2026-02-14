---
name: historical-science-video-prod
description: 自动化生成历史科学类3分钟科普短视频的全流程素材包，包含口播文案、分镜脚本、Veo2提示词、人物形象规范等，适配即梦平台视频生成。
dependency:
  python:
    - langchain-core>=0.1.0
    - langchain-openai>=0.0.5
---

# 历史科学类科普短视频自动化生成 Skill

## 任务目标
- 本 Skill 用于：自动化生成历史科学类3分钟科普短视频的全流程素材
- 能力包含：口播文案创作、分镜脚本规划、Veo2提示词生成、人物形象设计
- 触发条件：用户需要制作历史科学类科普视频，希望快速获得完整的素材包

## 前置准备
- 依赖说明：无需额外安装，依赖包已在 dependency 字段中声明
- 输入要求：用户提供科普主题、年代背景、核心科学结论

## 操作步骤
- 标准流程：
  1. **准备输入信息**
     - 确定科普主题（如"蝴蝶效应的起源"、"青霉素的发现"）
     - 明确年代背景（如"1961年"、"1928年"）
     - 提炼核心科学结论（如"初始条件的敏感性"）
  
  2. **执行生成脚本**
     - 调用 `scripts/generate_video_materials.py` 处理...
     - 传入参数：--theme、--era、--core_conclusion、--output_dir
  
  3. **查看输出素材**
     - `output/script.txt` - 3分钟口播文案（约900-1100字）
     - `output/storyboard.md` - 分镜脚本表（30-35个分镜）
     - `output/veo2_prompts.txt` - Veo2提示词清单
     - `output/character_design.md` - 人物形象规范

- 可选分支：
  - 当 需要调整风格：在 references/style-guide.md 中修改复古风格参数
  - 当 需要优化文案结构：在 references/script-structure.md 中调整时间分配

## 资源索引
- 必要脚本：见 [scripts/generate_video_materials.py](scripts/generate_video_materials.py)（用途与参数：生成全流程素材包，接收主题、年代、核心结论参数）
- 领域参考：见 [references/multi-agent-architecture.md](references/multi-agent-architecture.md)（何时读取：了解多智能体协作体系架构）
- 领域参考：见 [references/style-guide.md](references/style-guide.md)（何时读取：调整复古风格参数时）
- 领域参考：见 [references/veo2-prompt-template.md](references/veo2-prompt-template.md)（何时读取：了解Veo2提示词标准格式）
- 领域参考：见 [references/script-structure.md](references/script-structure.md)（何时读取：了解文案结构和时间分配）

## 注意事项
- 脚本会自动调用大模型生成内容，生成时间约1-2分钟
- 输出文件将保存到指定的 output_dir 目录
- 确保提供的核心科学结论准确无误，脚本会基于此生成文案
- 生成的分镜脚本严格遵循3分钟时长，每镜4-6秒

## 使用示例
- 功能说明：生成"蝴蝶效应的起源"主题的视频素材包
- 执行方式：脚本自动调用大模型生成
- 关键参数或指导要点：主题、年代、核心结论
- 简单示例代码或命令：
```bash
python scripts/generate_video_materials.py \
  --theme "蝴蝶效应的起源" \
  --era "1961年" \
  --core_conclusion "初始条件的微小变化会导致巨大差异，无法长期预测天气" \
  --output_dir "./output"
```
