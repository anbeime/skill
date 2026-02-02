# -*- coding: utf-8 -*-
"""
数据存储和管理模块
"""

import os
import json
import logging
from typing import List, Dict, Optional
from datetime import datetime

from config import DATA_DIR, SKILLS_JSON_PATH, LAST_UPDATE_PATH


class DataManager:
    """数据管理类"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self._ensure_directories()
    
    def _ensure_directories(self):
        """确保必要的目录存在"""
        os.makedirs(DATA_DIR, exist_ok=True)
        self.logger.info(f"数据目录已准备: {DATA_DIR}")
    
    def save_skills(self, skills: List[Dict]) -> bool:
        """保存技能数据到 JSON 文件"""
        try:
            with open(SKILLS_JSON_PATH, 'w', encoding='utf-8') as f:
                json.dump({
                    'skills': skills,
                    'total': len(skills),
                    'updated_at': datetime.now().isoformat()
                }, f, ensure_ascii=False, indent=2)
            
            self.logger.info(f"技能数据已保存到: {SKILLS_JSON_PATH}")
            return True
        except Exception as e:
            self.logger.error(f"保存技能数据失败: {e}")
            return False
    
    def load_skills(self) -> Optional[List[Dict]]:
        """从 JSON 文件加载技能数据"""
        if not os.path.exists(SKILLS_JSON_PATH):
            self.logger.warning("技能数据文件不存在")
            return None
        
        try:
            with open(SKILLS_JSON_PATH, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            skills = data.get('skills', [])
            self.logger.info(f"已加载 {len(skills)} 个技能")
            return skills
        except Exception as e:
            self.logger.error(f"加载技能数据失败: {e}")
            return None
    
    def save_update_time(self):
        """保存最后更新时间"""
        try:
            with open(LAST_UPDATE_PATH, 'w', encoding='utf-8') as f:
                f.write(datetime.now().isoformat())
            self.logger.info("更新时间已记录")
        except Exception as e:
            self.logger.error(f"保存更新时间失败: {e}")
    
    def get_last_update_time(self) -> Optional[datetime]:
        """获取最后更新时间"""
        if not os.path.exists(LAST_UPDATE_PATH):
            return None
        
        try:
            with open(LAST_UPDATE_PATH, 'r', encoding='utf-8') as f:
                time_str = f.read().strip()
            return datetime.fromisoformat(time_str)
        except Exception as e:
            self.logger.error(f"读取更新时间失败: {e}")
            return None
    
    def compare_skills(self, old_skills: List[Dict], new_skills: List[Dict]) -> Dict:
        """比较新旧技能数据，返回变更统计"""
        old_names = {s['name'] for s in old_skills}
        new_names = {s['name'] for s in new_skills}
        
        added = new_names - old_names
        removed = old_names - new_names
        
        # 检查描述或链接变更
        old_dict = {s['name']: s for s in old_skills}
        new_dict = {s['name']: s for s in new_skills}
        
        modified = []
        for name in old_names & new_names:
            if (old_dict[name]['description'] != new_dict[name]['description'] or
                old_dict[name]['link'] != new_dict[name]['link']):
                modified.append(name)
        
        changes = {
            'added': list(added),
            'removed': list(removed),
            'modified': modified,
            'total_old': len(old_skills),
            'total_new': len(new_skills)
        }
        
        self.logger.info(f"变更统计: 新增 {len(added)}, 删除 {len(removed)}, 修改 {len(modified)}")
        return changes
    
    def export_to_csv(self, skills: List[Dict], output_path: str) -> bool:
        """导出技能数据为 CSV 格式"""
        try:
            import csv
            
            with open(output_path, 'w', newline='', encoding='utf-8-sig') as f:
                if not skills:
                    return False
                
                fieldnames = ['name', 'description', 'link', 'category', 'source']
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                
                writer.writeheader()
                for skill in skills:
                    writer.writerow({k: skill.get(k, '') for k in fieldnames})
            
            self.logger.info(f"CSV 导出成功: {output_path}")
            return True
        except Exception as e:
            self.logger.error(f"CSV 导出失败: {e}")
            return False
