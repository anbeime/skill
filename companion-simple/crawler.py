# -*- coding: utf-8 -*-
"""
GitHub 技能仓库爬虫模块
"""

import re
import json
import time
import logging
from typing import List, Dict, Optional
from datetime import datetime

import requests
from bs4 import BeautifulSoup

from config import (
    GITHUB_RAW_README_URL,
    REQUEST_TIMEOUT,
    RETRY_TIMES,
    RETRY_DELAY
)


class SkillCrawler:
    """技能爬虫类"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    def fetch_readme(self) -> Optional[str]:
        """获取 README 内容"""
        for attempt in range(RETRY_TIMES):
            try:
                self.logger.info(f"正在获取 README 内容 (尝试 {attempt + 1}/{RETRY_TIMES})")
                response = self.session.get(
                    GITHUB_RAW_README_URL,
                    timeout=REQUEST_TIMEOUT
                )
                response.raise_for_status()
                response.encoding = 'utf-8'
                self.logger.info("成功获取 README 内容")
                return response.text
            except Exception as e:
                self.logger.error(f"获取 README 失败: {e}")
                if attempt < RETRY_TIMES - 1:
                    time.sleep(RETRY_DELAY)
        return None
    
    def parse_markdown_table(self, markdown_text: str) -> List[Dict]:
        """解析 Markdown 格式的技能列表"""
        skills = []
        current_category = None
        
        # 按行分割
        lines = markdown_text.split('\n')
        
        for i, line in enumerate(lines):
            line = line.strip()
            
            # 检测分类标题（## 或 ###）
            if line.startswith('###') or line.startswith('##'):
                current_category = line.lstrip('#').strip()
                self.logger.debug(f"发现分类: {current_category}")
                continue
            
            # 跳过非列表项
            if not line.startswith('-'):
                continue
            
            # 解析技能行
            # 格式1: - **[name](link)** - description
            # 格式2: - [name](link) - description
            # 移除开头的 "- " 和可能的 "**"
            line = line[1:].strip()  # 移除 "-"
            line = line.replace('**', '')  # 移除粗体标记
            
            # 提取链接和描述
            # 格式: [name](link) - description
            match = re.match(r'\[([^\]]+)\]\(([^\)]+)\)\s*[-–—]\s*(.+)', line)
            if match and current_category:
                name = match.group(1).strip()
                link = match.group(2).strip()
                description = match.group(3).strip()
                
                skill = {
                    'name': name,
                    'description': description,
                    'link': link,
                    'category': current_category,
                    'source': 'VoltAgent/awesome-agent-skills',
                    'crawled_at': datetime.now().isoformat()
                }
                skills.append(skill)
                self.logger.debug(f"解析技能: {name}")
        
        self.logger.info(f"共解析出 {len(skills)} 个技能")
        return skills
    
    def crawl(self) -> Optional[List[Dict]]:
        """执行爬取任务"""
        self.logger.info("开始爬取技能数据")
        
        # 获取 README
        readme_content = self.fetch_readme()
        if not readme_content:
            self.logger.error("无法获取 README 内容")
            return None
        
        # 解析技能列表
        skills = self.parse_markdown_table(readme_content)
        
        if not skills:
            self.logger.warning("未解析到任何技能数据")
            return None
        
        self.logger.info(f"爬取完成，共获取 {len(skills)} 个技能")
        return skills
    
    def validate_skill(self, skill: Dict) -> bool:
        """验证技能数据完整性"""
        required_fields = ['name', 'description', 'link', 'category']
        for field in required_fields:
            if not skill.get(field):
                self.logger.warning(f"技能数据缺少字段 {field}: {skill}")
                return False
        return True
    
    def filter_valid_skills(self, skills: List[Dict]) -> List[Dict]:
        """过滤有效的技能数据"""
        valid_skills = [s for s in skills if self.validate_skill(s)]
        self.logger.info(f"有效技能数: {len(valid_skills)}/{len(skills)}")
        return valid_skills
