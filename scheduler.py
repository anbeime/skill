# -*- coding: utf-8 -*-
"""
自动更新调度器模块
"""

import time
import logging
import schedule
from datetime import datetime, timedelta
from typing import Optional

from config import UPDATE_INTERVAL
from crawler import SkillCrawler
from data_manager import DataManager
from api_client import SkillStoreAPI


class UpdateScheduler:
    """自动更新调度器"""
    
    def __init__(self, enable_api_sync=False):
        self.logger = logging.getLogger(__name__)
        self.crawler = SkillCrawler()
        self.data_manager = DataManager()
        self.api_client = SkillStoreAPI() if enable_api_sync else None
        self.is_running = False
    
    def update_task(self) -> bool:
        """执行一次更新任务"""
        self.logger.info("=" * 60)
        self.logger.info(f"开始执行更新任务: {datetime.now()}")
        
        try:
            # 1. 爬取最新数据
            new_skills = self.crawler.crawl()
            if not new_skills:
                self.logger.error("爬取失败，本次更新终止")
                return False
            
            # 2. 验证数据
            valid_skills = self.crawler.filter_valid_skills(new_skills)
            if not valid_skills:
                self.logger.error("没有有效的技能数据")
                return False
            
            # 3. 比较变更
            old_skills = self.data_manager.load_skills()
            if old_skills:
                changes = self.data_manager.compare_skills(old_skills, valid_skills)
                self.logger.info(f"数据变更: {changes}")
            else:
                self.logger.info("首次更新，无历史数据对比")
            
            # 4. 保存数据
            if self.data_manager.save_skills(valid_skills):
                self.data_manager.save_update_time()
                self.logger.info("本地数据保存成功")
                
                # 5. 推送到技能商店 API（如果启用）
                if self.api_client:
                    self.logger.info("正在同步到技能商店...")
                    sync_result = self.api_client.sync_skills(valid_skills)
                    self.logger.info(f"API 同步结果: {sync_result}")
                
                self.logger.info("更新任务完成")
                return True
            else:
                self.logger.error("保存数据失败")
                return False
        
        except Exception as e:
            self.logger.error(f"更新任务异常: {e}", exc_info=True)
            return False
    
    def should_update(self) -> bool:
        """判断是否需要更新"""
        last_update = self.data_manager.get_last_update_time()
        if not last_update:
            self.logger.info("未找到上次更新记录，需要更新")
            return True
        
        elapsed = (datetime.now() - last_update).total_seconds()
        if elapsed >= UPDATE_INTERVAL:
            self.logger.info(f"距上次更新已过 {elapsed/3600:.1f} 小时，需要更新")
            return True
        
        self.logger.info(f"距上次更新仅 {elapsed/3600:.1f} 小时，暂不更新")
        return False
    
    def run_once(self):
        """立即执行一次更新"""
        self.logger.info("手动触发更新任务")
        self.update_task()
    
    def start_scheduled(self):
        """启动定时调度"""
        self.logger.info(f"启动定时调度器，更新间隔: {UPDATE_INTERVAL/3600} 小时")
        
        # 首次启动时立即检查更新
        if self.should_update():
            self.update_task()
        
        # 设置定时任务
        schedule.every(UPDATE_INTERVAL).seconds.do(self.update_task)
        
        self.is_running = True
        self.logger.info("调度器已启动，等待定时任务...")
        
        try:
            while self.is_running:
                schedule.run_pending()
                time.sleep(60)  # 每分钟检查一次
        except KeyboardInterrupt:
            self.logger.info("收到停止信号，调度器退出")
            self.is_running = False
    
    def stop(self):
        """停止调度器"""
        self.logger.info("正在停止调度器...")
        self.is_running = False
        schedule.clear()
