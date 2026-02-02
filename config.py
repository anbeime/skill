# -*- coding: utf-8 -*-
"""
技能商店自动更新配置文件
"""

# GitHub 仓库配置
GITHUB_REPO_URL = "https://github.com/VoltAgent/awesome-agent-skills"
GITHUB_RAW_README_URL = "https://raw.githubusercontent.com/VoltAgent/awesome-agent-skills/main/README.md"

# 更新频率配置（秒）
UPDATE_INTERVAL = 3600 * 24  # 每24小时更新一次

# 数据存储路径
DATA_DIR = "C:\\D\\StepFun\\skill_store_updater\\data"
SKILLS_JSON_PATH = f"{DATA_DIR}\\skills.json"
LAST_UPDATE_PATH = f"{DATA_DIR}\\last_update.txt"

# 日志配置
LOG_DIR = "C:\\D\\StepFun\\skill_store_updater\\logs"
LOG_FILE = f"{LOG_DIR}\\updater.log"

# 技能商店 API 配置（根据实际情况修改）
SKILL_STORE_API_URL = "http://localhost:8000/api/skills"
SKILL_STORE_API_KEY = "your_api_key_here"

# 爬取配置
REQUEST_TIMEOUT = 30
RETRY_TIMES = 3
RETRY_DELAY = 5
