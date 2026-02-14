#!/usr/bin/env python3
"""
共享记忆库实现
支持实时同步、版本控制、创作沉淀
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Any, Optional


class SharedMemory:
    """共享记忆库"""

    def __init__(self, project_id: str = None):
        """初始化"""
        self.project_id = project_id or datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # 三大模块
        self.base_materials = BaseMaterials()
        self.project_library = ProjectLibrary(self.project_id)
        self.creation_rules = CreationRules()
    
    def get(self, key: str) -> Any:
        """获取数据"""
        # 先从项目库中查找
        value = self.project_library.get(key)
        if value is not None:
            return value
        
        # 再从基础素材库中查找
        return self.base_materials.get(key)
    
    def set(self, key: str, value: Any, module: str = 'project'):
        """设置数据"""
        if module == 'base':
            self.base_materials.set(key, value)
        else:
            self.project_library.set(key, value)
    
    def get_version(self, key: str) -> Optional[int]:
        """获取数据版本"""
        return self.project_library.get_version(key)


class BaseMaterials:
    """基础素材库"""
    
    def __init__(self):
        """初始化"""
        self.data = {
            'characters': {},  # 历史人物结构化档案
            'memes': {},       # 全网热梗动态库
            'assets': {}       # 无版权素材库
        }
    
    def get(self, key: str) -> Optional[Any]:
        """获取数据"""
        parts = key.split('.')
        
        if parts[0] == 'characters' and len(parts) == 2:
            return self.data['characters'].get(parts[1])
        elif parts[0] == 'memes' and len(parts) == 2:
            return self.data['memes'].get(parts[1])
        elif parts[0] == 'assets' and len(parts) >= 2:
            # 支持嵌套访问，如 assets.visual.fonts
            value = self.data['assets']
            for part in parts[1:]:
                value = value.get(part, {})
                if value == {}:
                    return None
            return value if value != {} else None
        
        return None
    
    def set(self, key: str, value: Any):
        """设置数据"""
        parts = key.split('.')
        
        if parts[0] == 'characters' and len(parts) == 2:
            self.data['characters'][parts[1]] = value
        elif parts[0] == 'memes' and len(parts) == 2:
            self.data['memes'][parts[1]] = value
        elif parts[0] == 'assets':
            # 支持嵌套设置，如 assets.visual.fonts.roboto
            if len(parts) == 1:
                self.data['assets'] = value
            else:
                value = self.data['assets']
                for part in parts[1:-1]:
                    if part not in value:
                        value[part] = {}
                    value = value[part]
                value[parts[-1]] = value


class ProjectLibrary:
    """项目创作库"""
    
    def __init__(self, project_id: str):
        """初始化"""
        self.project_id = project_id
        self.data = {
            'user_requirements': {},  # 用户需求
            'meme_schemes': {},       # 人梗融合方案
            'scripts': {},            # 定稿文案
            'storyboards': {},        # 分镜表
            'visual_designs': {},     # 视觉设计提示词
            'audio_schemes': {},      # 音频方案
            'qc_reports': {},         # 质量检测报告
            'revision_logs': {},      # 修改记录
        }
        self.versions = {}  # 版本控制
    
    def get(self, key: str) -> Optional[Any]:
        """获取数据"""
        parts = key.split('.')
        
        if len(parts) == 1:
            # 直接查询，如 'script' -> 返回最新的脚本
            return self._get_latest(parts[0])
        elif len(parts) == 2:
            # 查询特定类型的数据，如 'scripts.draft' -> 返回名为draft的脚本
            return self.data.get(parts[0], {}).get(parts[1])
        
        return None
    
    def _get_latest(self, data_type: str) -> Optional[Any]:
        """获取最新版本的数据"""
        if data_type not in self.versions:
            return None
        
        latest_key = self.versions[data_type]['latest']
        return self.data.get(data_type, {}).get(latest_key)
    
    def set(self, key: str, value: Any, version: int = None):
        """设置数据"""
        parts = key.split('.')
        
        if len(parts) == 1:
            # 直接设置，自动生成key
            data_type = parts[0]
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            data_key = f"{data_type}_{timestamp}"
            
            if data_type not in self.data:
                self.data[data_type] = {}
            
            self.data[data_type][data_key] = value
            
            # 更新版本
            if version is None:
                if data_type not in self.versions:
                    self.versions[data_type] = {'latest': None, 'version': 0}
                version = self.versions[data_type]['version'] + 1
            
            self.versions[data_type] = {
                'latest': data_key,
                'version': version,
                'timestamp': datetime.now().isoformat()
            }
        
        elif len(parts) == 2:
            # 设置特定类型的数据
            data_type, data_key = parts
            
            if data_type not in self.data:
                self.data[data_type] = {}
            
            self.data[data_type][data_key] = value
            
            # 更新版本
            if version is None:
                if data_type not in self.versions:
                    self.versions[data_type] = {'latest': None, 'version': 0}
                version = self.versions[data_type]['version'] + 1
            
            self.versions[data_type] = {
                'latest': data_key,
                'version': version,
                'timestamp': datetime.now().isoformat()
            }
    
    def get_version(self, key: str) -> Optional[int]:
        """获取数据版本"""
        parts = key.split('.')
        
        if len(parts) == 1:
            data_type = parts[0]
            if data_type in self.versions:
                return self.versions[data_type]['version']
        
        return None
    
    def get_all_versions(self, data_type: str) -> List[Dict]:
        """获取某个类型的所有版本"""
        if data_type not in self.data:
            return []
        
        versions = []
        for data_key, data_value in self.data[data_type].items():
            # 查找对应的版本信息
            version_info = None
            if data_type in self.versions and self.versions[data_type]['latest'] == data_key:
                version_info = self.versions[data_type]
            
            versions.append({
                'key': data_key,
                'value': data_value,
                'version': version_info['version'] if version_info else None,
                'timestamp': version_info['timestamp'] if version_info else None
            })
        
        return versions


class CreationRules:
    """创作规则库"""
    
    def __init__(self):
        """初始化"""
        self.data = {
            'platform_rules': {   # 平台创作规则
                '抖音': {
                    'duration': {'min': 15, 'max': 30},
                    'aspect_ratio': '9:16',
                    'hook': '黄金3秒钩子前置',
                    'topics': {'min': 3, 'max': 5}
                },
                'B站': {
                    'duration': {'min': 45, 'max': 90},
                    'aspect_ratio': '16:9',
                    'hook': '细节玩梗，增加弹幕互动',
                    'topics': {'min': 2, 'max': 4}
                },
                '快手': {
                    'duration': {'min': 15, 'max': 30},
                    'aspect_ratio': '9:16',
                    'hook': '笑点前置，节奏更快',
                    'topics': {'min': 3, 'max': 5}
                }
            },
            'qc_standards': {      # 质量量化评分标准
                'dimensions': {
                    'historical_accuracy': {'weight': 0.30, 'description': '历史准确性'},
                    'meme_naturalness': {'weight': 0.25, 'description': '梗点自然度'},
                    'internet_sense': {'weight': 0.20, 'description': '网感'},
                    'visual_appeal': {'weight': 0.15, 'description': '画面感'},
                    'platform_fit': {'weight': 0.10, 'description': '平台适配性'}
                },
                'pass_score': 80.0
            },
            'taboos': {},          # 历史人物创作禁忌清单
            'best_practices': {}   # 爆款文案/视频沉淀
        }
        
        # 加载默认数据
        self._load_default_data()
    
    def get(self, key: str) -> Optional[Any]:
        """获取数据"""
        parts = key.split('.')
        
        if parts[0] == 'platform_rules' and len(parts) == 2:
            return self.data['platform_rules'].get(parts[1])
        elif parts[0] == 'qc_standards' and len(parts) == 2:
            return self.data['qc_standards'].get(parts[1])
        elif parts[0] == 'taboos' and len(parts) >= 2:
            if len(parts) == 2:
                return self.data['taboos'].get(parts[1])
            else:
                # 支持嵌套访问
                value = self.data['taboos'].get(parts[1], {})
                for part in parts[2:]:
                    value = value.get(part, {})
                    if value == {}:
                        return None
                return value if value != {} else None
        elif parts[0] == 'best_practices' and len(parts) >= 2:
            if len(parts) == 2:
                return self.data['best_practices'].get(parts[1])
            else:
                value = self.data['best_practices'].get(parts[1], {})
                for part in parts[2:]:
                    value = value.get(part, {})
                    if value == {}:
                        return None
                return value if value != {} else None
        
        return None
    
    def set(self, key: str, value: Any):
        """设置数据"""
        parts = key.split('.')
        
        if parts[0] == 'taboos' or parts[0] == 'best_practices':
            # 支持嵌套设置
            if len(parts) == 1:
                self.data[parts[0]] = value
            else:
                if parts[1] not in self.data[parts[0]]:
                    self.data[parts[0]][parts[1]] = {}
                value = self.data[parts[0]][parts[1]]
                for part in parts[2:-1]:
                    if part not in value:
                        value[part] = {}
                    value = value[part]
                value[parts[-1]] = value
    
    def _load_default_data(self):
        """加载默认数据"""
        # 历史人物创作禁忌清单
        self.data['taboos'] = {
            '李白': {
                'core_image': '浪漫主义诗人，豪放不羁',
                'must_respect': ['诗歌成就', '爱国情怀', '艺术才华'],
                'can_tease': ['饮酒习惯', '漫游天下', '与杜甫的友谊'],
                'forbidden': ['歪曲历史事实', '恶意贬低', '政治隐喻']
            },
            '李清照': {
                'core_image': '婉约派词人，才女气质',
                'must_respect': ['文学成就', '爱国情怀', '女性地位'],
                'can_tease': ['好赌', '好酒', '情感经历'],
                'forbidden': ['歪曲历史事实', '恶意贬低', '性别歧视']
            },
            '乾隆': {
                'core_image': '清朝皇帝，文化繁荣',
                'must_respect': ['政治成就', '文化贡献', '国家统一'],
                'can_tease': ['盖章狂魔', '下江南', '写诗'],
                'forbidden': ['歪曲历史事实', '恶意贬低', '政治隐喻']
            }
        }
