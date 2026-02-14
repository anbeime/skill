#!/usr/bin/env python3
"""
音频匹配智能体
"""

from typing import Dict, List, Any
from .base_agent import BaseAgent


class AudioMatcherAgent(BaseAgent):
    """音频匹配智能体"""
    
    def execute(self, storyboards: List[Dict], characters_data: Dict[str, Dict]) -> List[Dict]:
        """
        匹配音效和音乐
        
        Args:
            storyboards: 分镜列表
            characters_data: 人物档案
        
        Returns:
            list: 音频配置列表
        """
        self.log(f"开始匹配音效和音乐...")
        
        audio_configs = []
        
        for storyboard in storyboards:
            audio_config = self._generate_audio_config(storyboard, characters_data)
            audio_configs.append(audio_config)
        
        self.log(f"✓ 完成：匹配{len(audio_configs)}个分镜的音频")
        
        return audio_configs
    
    def _generate_audio_config(self, storyboard: Dict, characters_data: Dict) -> Dict:
        """
        生成音频配置
        
        Args:
            storyboard: 分镜信息
            characters_data: 人物档案
        
        Returns:
            dict: 音频配置
        """
        speaker = storyboard['speaker']
        character_data = characters_data.get(speaker, {})
        
        # 音色配置
        voice_config = {
            'name': character_data.get('name', speaker),
            'gender': character_data.get('gender', 'male'),
            'age': character_data.get('age', 40),
            'style': character_data.get('style', 'serious'),
            'tone': character_data.get('tone', 'calm')
        }
        
        # BGM配置
        bgm_config = {
            'type': 'interview' if storyboard['scene_type'] == 'dialogue' else 'opening',
            'mood': 'energetic' if storyboard['scene_type'] == 'introduction' else 'calm',
            'volume': 0.3
        }
        
        # 音效配置
        sfx_config = []
        if storyboard['scene_type'] == 'introduction':
            sfx_config.append({
                'type': 'applause',
                'timing': '0s',
                'duration': '2s'
            })
        elif storyboard['scene_type'] == 'punchline':
            sfx_config.append({
                'type': 'laugh_track',
                'timing': '1s',
                'duration': '3s'
            })
        
        return {
            'scene_index': storyboard['scene_index'],
            'dialogue_audio': {
                'voice': voice_config,
                'text': storyboard['dialogue']
            },
            'background_music': bgm_config,
            'sound_effects': sfx_config
        }
