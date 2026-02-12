# -*- coding: utf-8 -*-
"""
技能商店自动更新主程序
"""

import os
import sys
import logging
import argparse
from datetime import datetime

# 添加当前目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import LOG_DIR, LOG_FILE
from scheduler import UpdateScheduler
from data_manager import DataManager


def setup_logging(verbose: bool = False):
    """配置日志系统"""
    os.makedirs(LOG_DIR, exist_ok=True)
    
    log_level = logging.DEBUG if verbose else logging.INFO
    
    # 配置日志格式
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # 文件处理器
    file_handler = logging.FileHandler(LOG_FILE, encoding='utf-8')
    file_handler.setLevel(log_level)
    file_handler.setFormatter(formatter)
    
    # 控制台处理器
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)
    
    # 根日志器
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)
    
    return root_logger


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description='技能商店自动更新工具',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  # 立即执行一次更新
  python main.py --once
  
  # 启动定时自动更新（后台运行）
  python main.py --daemon
  
  # 查看当前数据统计
  python main.py --stats
  
  # 导出技能数据为 CSV
  python main.py --export skills.csv
        """
    )
    
    parser.add_argument(
        '--once',
        action='store_true',
        help='立即执行一次更新任务'
    )
    
    parser.add_argument(
        '--daemon',
        action='store_true',
        help='启动定时自动更新（持续运行）'
    )
    
    parser.add_argument(
        '--stats',
        action='store_true',
        help='显示当前技能数据统计'
    )
    
    parser.add_argument(
        '--export',
        metavar='FILE',
        help='导出技能数据为 CSV 文件'
    )
    
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='显示详细日志'
    )
    
    parser.add_argument(
        '--api-sync',
        action='store_true',
        help='启用 API 同步（需配置 API URL 和 Key）'
    )
    
    args = parser.parse_args()
    
    # 配置日志
    logger = setup_logging(args.verbose)
    logger.info("技能商店自动更新工具启动")
    
    # 创建调度器和数据管理器（根据参数决定是否启用 API 同步）
    scheduler = UpdateScheduler(enable_api_sync=args.api_sync)
    data_manager = DataManager()
    
    try:
        if args.once:
            # 立即执行一次更新
            logger.info("执行模式: 单次更新")
            scheduler.run_once()
        
        elif args.daemon:
            # 启动定时调度
            logger.info("执行模式: 定时自动更新")
            scheduler.start_scheduled()
        
        elif args.stats:
            # 显示统计信息
            logger.info("执行模式: 数据统计")
            skills = data_manager.load_skills()
            if skills:
                categories = {}
                for skill in skills:
                    cat = skill.get('category', '未分类')
                    categories[cat] = categories.get(cat, 0) + 1
                
                print(f"\n技能数据统计:")
                print(f"总计: {len(skills)} 个技能")
                print(f"分类数: {len(categories)}")
                print(f"\n各分类技能数:")
                for cat, count in sorted(categories.items(), key=lambda x: x[1], reverse=True):
                    print(f"  {cat}: {count}")
                
                last_update = data_manager.get_last_update_time()
                if last_update:
                    print(f"\n最后更新: {last_update.strftime('%Y-%m-%d %H:%M:%S')}")
            else:
                print("暂无技能数据")
        
        elif args.export:
            # 导出数据
            logger.info(f"执行模式: 导出数据到 {args.export}")
            skills = data_manager.load_skills()
            if skills:
                if data_manager.export_to_csv(skills, args.export):
                    print(f"成功导出 {len(skills)} 个技能到: {args.export}")
                else:
                    print("导出失败")
            else:
                print("暂无技能数据可导出")
        
        else:
            # 默认显示帮助
            parser.print_help()
    
    except KeyboardInterrupt:
        logger.info("收到中断信号，程序退出")
    except Exception as e:
        logger.error(f"程序异常: {e}", exc_info=True)
        sys.exit(1)


if __name__ == '__main__':
    main()
