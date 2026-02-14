#!/usr/bin/env python3
"""
配置管理
"""

import os
import json
from typing import Dict, Any


# 默认配置
DEFAULT_CONFIG = {
    # LLM配置
    'llm': {
        'provider': 'openai',  # openai, anthropic, zhipu, etc.
        'api_key': '',  # 请在此处填写您的API密钥
        'model': 'gpt-4',
        'temperature': 0.7,
        'max_tokens': 2000
    },
    
    # 输出配置
    'output_dir': './output',
    
    # 视觉风格
    'visual_style': 'cartoon',  # cartoon, q_style, realistic
    
    # 外部工具配置（视频生成需要）
    'tools': {
        # AI绘画工具
        'image_generator': {
            'enabled': False,
            'provider': 'openai',  # openai (DALL-E), midjourney, stability
            'api_key': '',
            'model': 'dall-e-3',
            'size': '1024x1024'
        },
        
        # 音频生成工具
        'audio_generator': {
            'enabled': False,
            'tts_provider': 'azure',  # azure, google, aws, openai
            'api_key': '',
            'region': 'eastus',
            'voice': 'zh-CN-XiaoxiaoNeural'
        },
        
        # 视频剪辑工具
        'video_editor': {
            'enabled': False,
            'provider': 'moviepy',  # moviepy, ffmpeg
            'output_format': 'mp4',
            'resolution': '1080p'
        }
    },
    
    # 平台配置
    'platforms': {
        '抖音': {
            'duration_limit': 30,
            'aspect_ratio': '9:16',
            'resolution': '1080x1920'
        },
        'B站': {
            'duration_limit': 60,
            'aspect_ratio': '16:9',
            'resolution': '1920x1080'
        },
        '快手': {
            'duration_limit': 30,
            'aspect_ratio': '9:16',
            'resolution': '1080x1920'
        }
    }
}


def load_config(config_path: str = None) -> Dict[str, Any]:
    """
    加载配置文件
    
    Args:
        config_path: 配置文件路径，如果为None则使用默认配置
    
    Returns:
        dict: 配置字典
    """
    config = DEFAULT_CONFIG.copy()
    
    if config_path and os.path.exists(config_path):
        with open(config_path, 'r', encoding='utf-8') as f:
            user_config = json.load(f)
        
        # 合并配置
        config = _merge_config(config, user_config)
    
    # 检查环境变量
    config = _load_from_env(config)
    
    return config


def _merge_config(base: Dict, override: Dict) -> Dict:
    """递归合并配置"""
    for key, value in override.items():
        if key in base and isinstance(base[key], dict) and isinstance(value, dict):
            base[key] = _merge_config(base[key], value)
        else:
            base[key] = value
    return base


def _load_from_env(config: Dict) -> Dict:
    """从环境变量加载配置"""
    # LLM API密钥
    if 'LLM_API_KEY' in os.environ:
        config['llm']['api_key'] = os.environ['LLM_API_KEY']
    
    # 图像生成API密钥
    if 'IMAGE_API_KEY' in os.environ:
        config['tools']['image_generator']['api_key'] = os.environ['IMAGE_API_KEY']
    
    # 音频生成API密钥
    if 'AUDIO_API_KEY' in os.environ:
        config['tools']['audio_generator']['api_key'] = os.environ['AUDIO_API_KEY']
    
    return config


def save_config_template(output_path: str = 'config_template.json'):
    """保存配置模板"""
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(DEFAULT_CONFIG, f, ensure_ascii=False, indent=2)
    
    print(f"✓ 配置模板已保存到：{output_path}")
    print(f"  请修改配置模板中的API密钥，然后使用 --config 参数指定配置文件路径")
