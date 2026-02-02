# 技能商店自动更新系统

自动从 [VoltAgent/awesome-agent-skills](https://github.com/VoltAgent/awesome-agent-skills) 仓库爬取并更新技能数据。

## 功能特性

- ✅ 自动爬取 GitHub 仓库中的技能列表
- ✅ 支持定时自动更新（默认每24小时）
- ✅ 数据变更检测（新增/删除/修改）
- ✅ JSON 格式存储，支持 CSV 导出
- ✅ 完整的日志记录
- ✅ 命令行工具，支持多种运行模式

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 运行方式

#### 立即执行一次更新
```bash
python main.py --once
```

#### 启动定时自动更新（后台持续运行）
```bash
python main.py --daemon
```

#### 查看当前数据统计
```bash
python main.py --stats
```

#### 导出数据为 CSV
```bash
python main.py --export skills.csv
```

#### 显示详细日志
```bash
python main.py --once -v
```

## 目录结构

```
skill_store_updater/
├── main.py              # 主程序入口
├── config.py            # 配置文件
├── crawler.py           # 爬虫模块
├── data_manager.py      # 数据管理模块
├── scheduler.py         # 定时调度模块
├── requirements.txt     # 依赖包列表
├── data/                # 数据存储目录
│   ├── skills.json      # 技能数据（自动生成）
│   └── last_update.txt  # 更新时间记录
└── logs/                # 日志目录
    └── updater.log      # 运行日志
```

## 配置说明

在 `config.py` 中可以修改以下配置：

- `UPDATE_INTERVAL`: 更新间隔（秒），默认 86400（24小时）
- `GITHUB_RAW_README_URL`: GitHub 仓库 README 地址
- `DATA_DIR`: 数据存储目录
- `LOG_DIR`: 日志存储目录

## 数据格式

### JSON 输出格式

```json
{
  "skills": [
    {
      "name": "anthropics/docx",
      "description": "Create, edit, and analyze Word documents",
      "link": "https://github.com/anthropics/skills/tree/main/skills/docx",
      "category": "Document Creation",
      "source": "VoltAgent/awesome-agent-skills",
      "crawled_at": "2026-02-02T10:30:00"
    }
  ],
  "total": 200,
  "updated_at": "2026-02-02T10:30:00"
}
```

## Windows 定时任务设置

### 方法1: 使用任务计划程序

1. 打开"任务计划程序"
2. 创建基本任务
3. 触发器: 每天
4. 操作: 启动程序
   - 程序: `python`
   - 参数: `C:\D\StepFun\skill_store_updater\main.py --once`
   - 起始于: `C:\D\StepFun\skill_store_updater`

### 方法2: 使用 daemon 模式

创建 `start_updater.bat`:

```batch
@echo off
cd /d C:\D\StepFun\skill_store_updater
python main.py --daemon
```

将此批处理文件添加到启动项，实现开机自启。

## 集成到技能商店

修改 `config.py` 中的 API 配置：

```python
SKILL_STORE_API_URL = "http://your-api-server/api/skills"
SKILL_STORE_API_KEY = "your_api_key"
```

然后在 `scheduler.py` 的 `update_task()` 方法中添加 API 推送逻辑。

## 故障排查

### 爬取失败
- 检查网络连接
- 确认 GitHub 仓库地址正确
- 查看日志文件 `logs/updater.log`

### 数据解析错误
- 检查 GitHub 仓库 README 格式是否变更
- 查看详细日志 `python main.py --once -v`

## 许可证

MIT License
