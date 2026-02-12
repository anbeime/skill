# -*- coding: utf-8 -*-
"""
技能商店 API 集成模块
"""

import logging
import requests
from typing import List, Dict, Optional

from config import SKILL_STORE_API_URL, SKILL_STORE_API_KEY, REQUEST_TIMEOUT


class SkillStoreAPI:
    """技能商店 API 客户端"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.api_url = SKILL_STORE_API_URL
        self.api_key = SKILL_STORE_API_KEY
        self.session = requests.Session()
        
        # 设置认证头
        if self.api_key:
            self.session.headers.update({
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json'
            })
    
    def push_skills(self, skills: List[Dict]) -> bool:
        """
        推送技能数据到技能商店
        
        Args:
            skills: 技能列表
            
        Returns:
            bool: 是否成功
        """
        if not self.api_url or self.api_url == "http://localhost:8000/api/skills":
            self.logger.warning("API URL 未配置或使用默认值，跳过推送")
            return False
        
        try:
            self.logger.info(f"正在推送 {len(skills)} 个技能到技能商店...")
            
            # 批量推送
            response = self.session.post(
                f"{self.api_url}/batch",
                json={'skills': skills},
                timeout=REQUEST_TIMEOUT
            )
            
            response.raise_for_status()
            result = response.json()
            
            self.logger.info(f"推送成功: {result}")
            return True
        
        except requests.exceptions.RequestException as e:
            self.logger.error(f"推送失败: {e}")
            return False
    
    def update_skill(self, skill: Dict) -> bool:
        """
        更新单个技能
        
        Args:
            skill: 技能数据
            
        Returns:
            bool: 是否成功
        """
        if not self.api_url or self.api_url == "http://localhost:8000/api/skills":
            return False
        
        try:
            skill_id = skill.get('name')
            response = self.session.put(
                f"{self.api_url}/{skill_id}",
                json=skill,
                timeout=REQUEST_TIMEOUT
            )
            
            response.raise_for_status()
            return True
        
        except requests.exceptions.RequestException as e:
            self.logger.error(f"更新技能 {skill.get('name')} 失败: {e}")
            return False
    
    def delete_skill(self, skill_name: str) -> bool:
        """
        删除技能
        
        Args:
            skill_name: 技能名称
            
        Returns:
            bool: 是否成功
        """
        if not self.api_url or self.api_url == "http://localhost:8000/api/skills":
            return False
        
        try:
            response = self.session.delete(
                f"{self.api_url}/{skill_name}",
                timeout=REQUEST_TIMEOUT
            )
            
            response.raise_for_status()
            return True
        
        except requests.exceptions.RequestException as e:
            self.logger.error(f"删除技能 {skill_name} 失败: {e}")
            return False
    
    def sync_skills(self, local_skills: List[Dict]) -> Dict:
        """
        同步技能到技能商店
        
        Args:
            local_skills: 本地技能列表
            
        Returns:
            Dict: 同步统计信息
        """
        if not self.api_url or self.api_url == "http://localhost:8000/api/skills":
            self.logger.warning("API 未配置，跳过同步")
            return {'synced': False, 'reason': 'API not configured'}
        
        try:
            # 获取远程技能列表
            response = self.session.get(
                self.api_url,
                timeout=REQUEST_TIMEOUT
            )
            response.raise_for_status()
            remote_skills = response.json().get('skills', [])
            
            # 比较差异
            local_names = {s['name'] for s in local_skills}
            remote_names = {s['name'] for s in remote_skills}
            
            to_add = local_names - remote_names
            to_remove = remote_names - local_names
            to_update = local_names & remote_names
            
            stats = {
                'added': 0,
                'updated': 0,
                'deleted': 0,
                'failed': 0
            }
            
            # 添加新技能
            for skill in local_skills:
                if skill['name'] in to_add:
                    if self.update_skill(skill):
                        stats['added'] += 1
                    else:
                        stats['failed'] += 1
            
            # 更新现有技能
            for skill in local_skills:
                if skill['name'] in to_update:
                    if self.update_skill(skill):
                        stats['updated'] += 1
                    else:
                        stats['failed'] += 1
            
            # 删除已移除的技能
            for name in to_remove:
                if self.delete_skill(name):
                    stats['deleted'] += 1
                else:
                    stats['failed'] += 1
            
            self.logger.info(f"同步完成: {stats}")
            return stats
        
        except Exception as e:
            self.logger.error(f"同步失败: {e}")
            return {'synced': False, 'error': str(e)}
