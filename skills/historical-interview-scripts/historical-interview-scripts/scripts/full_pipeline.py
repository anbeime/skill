#!/usr/bin/env python3
"""
历史名人访谈短视频 - 端到端全流程生成主入口
"""

import os
import sys
import argparse
import json
from datetime import datetime

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from agents.historian_agent import HistorianAgent
from agents.meme_analyst_agent import MemeAnalystAgent
from agents.scriptwriter_agent import ScriptwriterAgent
from agents.qc_optimizer_agent import QCOptimizerAgent
from agents.visual_design_agent import VisualDesignAgent
from agents.storyboard_agent import StoryboardAgent
from agents.audio_matcher_agent import AudioMatcherAgent
from memory.shared_memory import SharedMemory
from config.settings import load_config


class FullPipeline:
    """端到端全流程生成器"""

    def __init__(self, config_path=None):
        """初始化"""
        self.config = load_config(config_path)
        self.memory = SharedMemory()
        self.project_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.output_dir = os.path.join(self.config.get('output_dir', './output'), f"project_{self.project_id}")
        os.makedirs(self.output_dir, exist_ok=True)

        # 初始化智能体
        self.agents = {
            'historian': HistorianAgent(self.memory, self.config),
            'meme_analyst': MemeAnalystAgent(self.memory, self.config),
            'scriptwriter': ScriptwriterAgent(self.memory, self.config),
            'qc_optimizer': QCOptimizerAgent(self.memory, self.config),
            'visual_design': VisualDesignAgent(self.memory, self.config),
            'storyboard': StoryboardAgent(self.memory, self.config),
            'audio_matcher': AudioMatcherAgent(self.memory, self.config),
        }

    def run_basic_mode(self, characters, theme, style, platform):
        """
        运行基础模式（4智能体：文案创作）
        
        Args:
            characters: 历史人物列表，如 ["李白", "李清照", "乾隆"]
            theme: 访谈主题，如 "古代名人的现代职场生存"
            style: 创作风格，如 "轻松调侃" / "吐槽" / "互怼"
            platform: 目标平台，如 "抖音" / "B站" / "快手"
        
        Returns:
            dict: 包含定稿文案的字典
        """
        print(f"\n{'='*60}")
        print(f"启动基础模式：文案创作（4智能体）")
        print(f"{'='*60}\n")

        # 阶段1：并行素材准备
        print(f"【阶段1】并行素材准备...")
        
        # 历史考据
        print(f"  - 历史考据智能体：分析人物档案...")
        characters_data = self.agents['historian'].analyze_characters(characters)
        print(f"    ✓ 完成：生成{len(characters)}个人物档案")
        
        # 热梗融合
        print(f"  - 热梗融合智能体：匹配网络热梗...")
        meme_schemes = self.agents['meme_analyst'].match_memes(characters_data, platform)
        print(f"    ✓ 完成：生成人梗融合方案")
        
        # 阶段2：剧本创作
        print(f"\n【阶段2】剧本创作...")
        print(f"  - 剧本创作智能体：生成访谈文案...")
        draft_script = self.agents['scriptwriter'].generate_script(
            characters_data, 
            meme_schemes, 
            theme, 
            style, 
            platform
        )
        print(f"    ✓ 完成：生成初版文案")
        
        # 阶段3：质量审查
        print(f"\n【阶段3】质量审查...")
        print(f"  - 质量审查智能体：评估文案质量...")
        qc_report = self.agents['qc_optimizer'].evaluate_script(draft_script, characters_data, platform)
        
        if qc_report['total_score'] >= 80:
            print(f"    ✓ 质量达标（{qc_report['total_score']:.1f}分），通过审核")
            final_script = qc_report.get('optimized_script', draft_script)
        else:
            print(f"    ✗ 质量不达标（{qc_report['total_score']:.1f}分），触发回改...")
            # 自动回改逻辑
            final_script = self._auto_revision(draft_script, qc_report, characters_data, platform)
        
        # 保存结果
        output_file = os.path.join(self.output_dir, "script.md")
        self._save_script(final_script, output_file)
        print(f"\n✓ 文案已保存到：{output_file}")
        
        return {
            'project_id': self.project_id,
            'characters': characters,
            'theme': theme,
            'style': style,
            'platform': platform,
            'script': final_script,
            'qc_score': qc_report['total_score'],
            'output_file': output_file
        }

    def run_full_mode(self, characters, theme, style, platform, enable_video_generation=False):
        """
        运行完整模式（7智能体：文案创作 + 视觉设计 + 音频匹配）
        
        注意：视频生成（画面生成+剪辑）需要配置外部工具，默认禁用
        
        Args:
            enable_video_generation: 是否启用视频生成（需要配置外部工具）
        
        Returns:
            dict: 包含完整创作结果的字典
        """
        print(f"\n{'='*60}")
        print(f"启动完整模式：端到端创作（7智能体）")
        print(f"{'='*60}\n")

        # 阶段1：文案创作（复用基础模式）
        print(f"【阶段1】文案创作（4智能体）...")
        script_result = self.run_basic_mode(characters, theme, style, platform)
        final_script = script_result['script']
        
        # 阶段2：视觉设计
        print(f"\n【阶段2】视觉设计（2智能体）...")
        
        # 人物形象设计
        print(f"  - 人物形象设计智能体：生成视觉提示词...")
        visual_prompts = self.agents['visual_design'].generate_visual_prompts(
            characters, 
            theme, 
            self.config.get('visual_style', 'cartoon')
        )
        print(f"    ✓ 完成：生成{len(characters)}个人物视觉提示词")
        
        # 分镜设计
        print(f"  - 分镜设计智能体：生成分镜表...")
        storyboard = self.agents['storyboard'].generate_storyboard(
            final_script, 
            visual_prompts, 
            platform
        )
        print(f"    ✓ 完成：生成分镜表（{len(storyboard['shots'])}个镜头）")
        
        # 阶段3：音频匹配
        print(f"\n【阶段3】音频匹配（1智能体）...")
        print(f"  - 音频匹配智能体：生成音频方案...")
        audio_scheme = self.agents['audio_matcher'].generate_audio_scheme(
            final_script, 
            storyboard
        )
        print(f"    ✓ 完成：生成音频制作方案")
        
        # 阶段4：视频生成（可选，需要配置外部工具）
        video_result = {}
        if enable_video_generation:
            print(f"\n【阶段4】视频生成（需要外部工具）...")
            print(f"  ⚠️  注意：视频生成需要配置AI绘画工具、音频工具和视频剪辑工具")
            print(f"  ⚠️  当前未配置，跳过视频生成")
            print(f"  💡 提示：请参考 scripts/tools/ 目录下的工具封装，配置您的API凭证")
            video_result = {
                'enabled': False,
                'reason': '外部工具未配置'
            }
        else:
            print(f"\n【阶段4】视频生成（已禁用）...")
            print(f"  💡 提示：如需生成视频，请设置 --enable-video 参数并配置外部工具")
            video_result = {
                'enabled': False,
                'reason': '用户未启用'
            }
        
        # 保存所有结果
        self._save_all_outputs(
            final_script, 
            visual_prompts, 
            storyboard, 
            audio_scheme, 
            video_result
        )
        
        return {
            'project_id': self.project_id,
            'characters': characters,
            'theme': theme,
            'style': style,
            'platform': platform,
            'script': final_script,
            'visual_prompts': visual_prompts,
            'storyboard': storyboard,
            'audio_scheme': audio_scheme,
            'video_result': video_result,
            'output_dir': self.output_dir
        }

    def _auto_revision(self, draft_script, qc_report, characters_data, platform):
        """自动回改逻辑"""
        print(f"\n  → 执行自动回改...")
        
        # 根据QC报告的具体问题，触发对应智能体重新生成
        revisions = qc_report.get('revisions', [])
        
        for revision in revisions:
            print(f"    - {revision['issue']}：触发{revision['target_agent']}重新生成...")
            
            # 这里可以根据具体问题调用不同的智能体
            if revision['target_agent'] == 'meme_analyst':
                # 重新匹配热梗
                meme_schemes = self.agents['meme_analyst'].match_memes(characters_data, platform, revision.get('suggestions'))
                # 重新生成文案
                draft_script = self.agents['scriptwriter'].generate_script(
                    characters_data, 
                    meme_schemes, 
                    "auto_revision", 
                    "轻松调侃", 
                    platform
                )
            
            elif revision['target_agent'] == 'scriptwriter':
                # 重新生成文案
                draft_script = self.agents['scriptwriter'].generate_script(
                    characters_data, 
                    None, 
                    "auto_revision", 
                    "轻松调侃", 
                    platform,
                    suggestions=revision.get('suggestions')
                )
        
        # 再次审查
        print(f"    → 再次审查...")
        qc_report = self.agents['qc_optimizer'].evaluate_script(draft_script, characters_data, platform)
        
        if qc_report['total_score'] >= 80:
            print(f"    ✓ 回改成功（{qc_report['total_score']:.1f}分）")
            return qc_report.get('optimized_script', draft_script)
        else:
            print(f"    ✗ 回改后仍不达标（{qc_report['total_score']:.1f}分），使用原稿")
            return draft_script

    def _save_script(self, script, filepath):
        """保存文案"""
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(script)

    def _save_all_outputs(self, script, visual_prompts, storyboard, audio_scheme, video_result):
        """保存所有输出"""
        # 保存文案
        self._save_script(script, os.path.join(self.output_dir, "script.md"))
        
        # 保存视觉提示词
        with open(os.path.join(self.output_dir, "visual_prompts.json"), 'w', encoding='utf-8') as f:
            json.dump(visual_prompts, f, ensure_ascii=False, indent=2)
        
        # 保存分镜表
        with open(os.path.join(self.output_dir, "storyboard.json"), 'w', encoding='utf-8') as f:
            json.dump(storyboard, f, ensure_ascii=False, indent=2)
        
        # 保存音频方案
        with open(os.path.join(self.output_dir, "audio_scheme.json"), 'w', encoding='utf-8') as f:
            json.dump(audio_scheme, f, ensure_ascii=False, indent=2)
        
        # 保存视频结果
        with open(os.path.join(self.output_dir, "video_result.json"), 'w', encoding='utf-8') as f:
            json.dump(video_result, f, ensure_ascii=False, indent=2)
        
        # 保存项目元数据
        metadata = {
            'project_id': self.project_id,
            'created_at': datetime.now().isoformat(),
            'outputs': {
                'script': 'script.md',
                'visual_prompts': 'visual_prompts.json',
                'storyboard': 'storyboard.json',
                'audio_scheme': 'audio_scheme.json',
                'video_result': 'video_result.json'
            }
        }
        with open(os.path.join(self.output_dir, "metadata.json"), 'w', encoding='utf-8') as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='历史名人访谈短视频生成器')
    parser.add_argument('--characters', type=str, required=True,
                        help='历史人物列表，用逗号分隔，如 "李白,李清照,乾隆"')
    parser.add_argument('--theme', type=str, default='古代名人的现代访谈',
                        help='访谈主题')
    parser.add_argument('--style', type=str, default='轻松调侃',
                        choices=['轻松调侃', '吐槽', '互怼', '脑洞大开'],
                        help='创作风格')
    parser.add_argument('--platform', type=str, default='B站',
                        choices=['抖音', 'B站', '快手'],
                        help='目标平台')
    parser.add_argument('--mode', type=str, default='basic',
                        choices=['basic', 'full'],
                        help='运行模式：basic（仅文案）或 full（文案+视觉+音频）')
    parser.add_argument('--enable-video', action='store_true',
                        help='启用视频生成（需要配置外部工具）')
    parser.add_argument('--config', type=str,
                        help='配置文件路径')
    
    args = parser.parse_args()
    
    # 解析历史人物列表
    characters = [c.strip() for c in args.characters.split(',')]
    
    # 创建流水线
    pipeline = FullPipeline(args.config)
    
    # 运行
    try:
        if args.mode == 'basic':
            result = pipeline.run_basic_mode(
                characters=characters,
                theme=args.theme,
                style=args.style,
                platform=args.platform
            )
        else:
            result = pipeline.run_full_mode(
                characters=characters,
                theme=args.theme,
                style=args.style,
                platform=args.platform,
                enable_video_generation=args.enable_video
            )
        
        print(f"\n{'='*60}")
        print(f"✓ 创作完成！")
        print(f"{'='*60}")
        print(f"项目ID：{result['project_id']}")
        print(f"历史人物：{', '.join(result['characters'])}")
        print(f"访谈主题：{result['theme']}")
        print(f"创作风格：{result['style']}")
        print(f"目标平台：{result['platform']}")
        if 'qc_score' in result:
            print(f"文案质量：{result['qc_score']:.1f}分")
        print(f"输出目录：{result.get('output_dir', result['output_file'])}")
        print(f"{'='*60}\n")
        
    except Exception as e:
        print(f"\n✗ 错误：{str(e)}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
