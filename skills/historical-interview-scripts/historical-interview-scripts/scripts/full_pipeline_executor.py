#!/usr/bin/env python3
"""
全流程执行模块

实现9智能体协作的端到端视频生成流程
"""

import os
from typing import Dict, List, Any
from config.settings import Config
from memory.shared_memory import SharedMemory
from agents.historian_agent import HistorianAgent
from agents.meme_analyst_agent import MemeAnalystAgent
from agents.scriptwriter_agent import ScriptwriterAgent
from agents.qc_optimizer_agent import QCOptimizerAgent
from agents.visual_design_agent import VisualDesignAgent
from agents.storyboard_agent import StoryboardAgent
from agents.audio_matcher_agent import AudioMatcherAgent
from tools.external_tools import ExternalToolsManager


class FullPipeline:
    """全流程执行器"""
    
    def __init__(self, config: Config):
        """
        初始化全流程
        
        Args:
            config: 配置对象
        """
        self.config = config
        self.memory = SharedMemory()
        self.llm_client = None  # 实际使用时替换为真实的LLM客户端
        
        # 初始化智能体
        self.agents = {
            'historian': HistorianAgent('historian', self.llm_client, self.memory),
            'meme_analyst': MemeAnalystAgent('meme_analyst', self.llm_client, self.memory),
            'scriptwriter': ScriptwriterAgent('scriptwriter', self.llm_client, self.memory),
            'qc_optimizer': QCOptimizerAgent('qc_optimizer', self.llm_client, self.memory),
            'visual_design': VisualDesignAgent('visual_design', self.llm_client, self.memory),
            'storyboard': StoryboardAgent('storyboard', self.llm_client, self.memory),
            'audio_matcher': AudioMatcherAgent('audio_matcher', self.llm_client, self.memory)
        }
        
        # 初始化外部工具管理器
        self.tools = ExternalToolsManager(self.llm_client, self.memory)
        
        # 创建输出目录
        self._create_output_dirs()
    
    def _create_output_dirs(self):
        """创建输出目录"""
        dirs = ['./output/images', './output/audio', './output/videos', './output/scripts']
        for dir_path in dirs:
            os.makedirs(dir_path, exist_ok=True)
    
    def execute(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行全流程
        
        Args:
            request: 创作请求
                - characters: 历史人物列表
                - theme: 访谈主题
                - platform: 目标平台
                - style: 视觉风格
                - duration: 视频时长
        
        Returns:
            dict: 执行结果
        """
        print("=" * 60)
        print("全流程执行开始")
        print("=" * 60)
        
        # 阶段1：人物档案研究
        print("\n【阶段1】人物档案研究")
        print("-" * 60)
        characters_data = self.agents['historian'].execute(
            characters=request['characters'],
            research_depth='basic'
        )
        
        # 阶段2：网络热梗分析
        print("\n【阶段2】网络热梗分析")
        print("-" * 60)
        memes = self.agents['meme_analyst'].execute(
            theme=request['theme'],
            platform=request['platform']
        )
        
        # 阶段3：文案创作
        print("\n【阶段3】文案创作")
        print("-" * 60)
        draft_script = self.agents['scriptwriter'].execute(
            characters=request['characters'],
            memes=memes,
            theme=request['theme']
        )
        
        # 阶段4：质量审查
        print("\n【阶段4】质量审查")
        print("-" * 60)
        qc_report = self.agents['qc_optimizer'].execute(
            draft_script=draft_script,
            characters_data=characters_data,
            platform=request['platform']
        )
        
        # 循环优化（如果需要）
        optimization_round = 1
        while not qc_report['passed'] and optimization_round <= 3:
            print(f"\n【优化轮次 {optimization_round}】")
            print("-" * 60)
            
            # 根据质量报告进行优化
            for revision in qc_report['revisions']:
                target_agent = revision['target_agent']
                if target_agent == 'meme_analyst':
                    print(f"  - 热梗分析师优化：{revision['issue']}")
                    memes = self.agents['meme_analyst'].execute(
                        theme=request['theme'],
                        platform=request['platform'],
                        suggestions=revision['suggestions']
                    )
                elif target_agent == 'scriptwriter':
                    print(f"  - 文案师优化：{revision['issue']}")
                    draft_script = self.agents['scriptwriter'].execute(
                        characters=request['characters'],
                        memes=memes,
                        theme=request['theme'],
                        suggestions=revision['suggestions']
                    )
            
            # 重新质量审查
            qc_report = self.agents['qc_optimizer'].execute(
                draft_script=draft_script,
                characters_data=characters_data,
                platform=request['platform']
            )
            
            optimization_round += 1
        
        # 阶段5：视觉设计
        print("\n【阶段5】视觉设计")
        print("-" * 60)
        visual_prompts = self.agents['visual_design'].execute(
            characters=request['characters'],
            theme=request['theme'],
            style=request.get('style', 'cartoon')
        )
        
        # 阶段6：分镜策划
        print("\n【阶段6】分镜策划")
        print("-" * 60)
        storyboards = self.agents['storyboard'].execute(
            script=draft_script,
            visual_prompts=visual_prompts,
            duration=request.get('duration', 60)
        )
        
        # 阶段7：音频匹配
        print("\n【阶段7】音频匹配")
        print("-" * 60)
        audio_configs = self.agents['audio_matcher'].execute(
            storyboards=storyboards,
            characters_data=characters_data
        )
        
        # 阶段8：素材生成
        print("\n【阶段8】素材生成")
        print("-" * 60)
        
        # 生成图片
        image_paths = []
        for i, storyboard in enumerate(storyboards):
            image_path = self.tools.generate_image(
                prompt=storyboard['visual_prompt'].get('keyframe', ''),
                style=request.get('style', 'cartoon'),
                output_path=f"./output/images/scene_{i+1}.png"
            )
            image_paths.append(image_path)
        
        # 生成音频
        audio_paths = []
        for i, audio_config in enumerate(audio_configs):
            audio_path = self.tools.generate_audio(
                text=audio_config['dialogue_audio']['text'],
                voice_config=audio_config['dialogue_audio']['voice'],
                output_path=f"./output/audio/scene_{i+1}.mp3"
            )
            audio_paths.append(audio_path)
        
        # 阶段9：视频剪辑
        print("\n【阶段9】视频剪辑")
        print("-" * 60)
        final_video = self.tools.edit_video(
            storyboards=storyboards,
            audio_configs=audio_configs,
            output_path=f"./output/videos/final_video.mp4"
        )
        
        # 保存文案
        script_path = f"./output/scripts/final_script.txt"
        with open(script_path, 'w', encoding='utf-8') as f:
            f.write(draft_script)
        
        print("\n" + "=" * 60)
        print("全流程执行完成")
        print("=" * 60)
        print(f"\n📄 文案路径：{script_path}")
        print(f"🖼️ 图片数量：{len(image_paths)}")
        print(f"🎵 音频数量：{len(audio_paths)}")
        print(f"🎬 视频路径：{final_video}")
        
        return {
            'script': draft_script,
            'script_path': script_path,
            'images': image_paths,
            'audios': audio_paths,
            'video': final_video,
            'qc_report': qc_report,
            'storyboards': storyboards,
            'audio_configs': audio_configs
        }


if __name__ == '__main__':
    # 示例配置
    config = Config()
    
    # 创建全流程执行器
    pipeline = FullPipeline(config)
    
    # 执行请求
    request = {
        'characters': ['qin_shihuang', 'li_bai'],
        'theme': '现代职场',
        'platform': 'douyin',
        'style': 'cartoon',
        'duration': 60
    }
    
    # 执行全流程
    result = pipeline.execute(request)
    
    print("\n✓ 全流程执行成功！")
