# 快速开始指南

## 🚀 5分钟快速部署

### 1. 安装依赖

```bash
cd C:\D\StepFun\skill_store_updater
pip install -r requirements.txt
```

### 2. 立即运行一次

```bash
python main.py --once
```

这将：
- 从 GitHub 爬取最新的 182+ 个技能
- 保存到 `data/skills.json`
- 生成日志到 `logs/updater.log`

### 3. 查看结果

```bash
# 查看统计
python main.py --stats

# 导出为 CSV
python main.py --export skills.csv
```

## 📋 完整功能

### 基础使用

```bash
# 单次更新
python main.py --once

# 后台持续运行（每24小时自动更新）
python main.py --daemon

# 查看统计
python main.py --stats

# 导出 CSV
python main.py --export output.csv

# 详细日志
python main.py --once -v
```

### 高级功能：API 同步

#### 步骤 1: 配置 API

编辑 `config.py`:

```python
SKILL_STORE_API_URL = "https://your-api.com/api/skills"
SKILL_STORE_API_KEY = "your_api_key"
```

#### 步骤 2: 启用 API 同步

```bash
python main.py --once --api-sync
```

#### 步骤 3: 测试 API（可选）

启动示例 API 服务器：

```bash
pip install flask flask-cors
python api_server_example.py
```

然后在另一个终端：

```bash
python main.py --once --api-sync
```

## 🔄 自动化部署

### Windows 任务计划程序

#### 方法 1: 使用 PowerShell 脚本

以管理员身份运行 PowerShell：

```powershell
.\setup_scheduled_task.ps1
```

#### 方法 2: 手动创建

1. 打开"任务计划程序"
2. 创建基本任务
3. 名称: `SkillStoreAutoUpdate`
4. 触发器: 每天凌晨 2:00
5. 操作: 启动程序
   - 程序: `python`
   - 参数: `C:\D\StepFun\skill_store_updater\main.py --once`
   - 起始于: `C:\D\StepFun\skill_store_updater`

### 使用批处理脚本

双击运行：

```bash
# 单次更新
run_once.bat

# 后台持续运行
start_daemon.bat
```

## 📊 数据格式

### JSON 输出

`data/skills.json`:

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
  "total": 182,
  "updated_at": "2026-02-02T10:30:00"
}
```

### CSV 导出

```csv
name,description,link,category,source
anthropics/docx,Create edit and analyze Word documents,https://...,Document Creation,VoltAgent/awesome-agent-skills
```

## 🔧 配置选项

### `config.py` 主要配置

```python
# 更新频率（秒）
UPDATE_INTERVAL = 3600 * 24  # 24小时

# GitHub 仓库
GITHUB_RAW_README_URL = "https://raw.githubusercontent.com/..."

# 数据存储
DATA_DIR = "C:\\D\\StepFun\\skill_store_updater\\data"

# API 配置
SKILL_STORE_API_URL = "http://localhost:8000/api/skills"
SKILL_STORE_API_KEY = "your_api_key_here"
```

## 🐛 故障排查

### 问题 1: 爬取失败

```bash
# 检查网络连接
ping github.com

# 查看详细日志
python main.py --once -v
```

### 问题 2: 解析错误

```bash
# 查看日志
type logs\updater.log
```

### 问题 3: API 同步失败

```bash
# 测试 API 连接
curl http://localhost:8000/health

# 检查 API 配置
python -c "from config import SKILL_STORE_API_URL; print(SKILL_STORE_API_URL)"
```

## 📈 监控和维护

### 查看日志

```bash
# Windows
type logs\updater.log

# 实时监控
Get-Content logs\updater.log -Wait
```

### 数据备份

```bash
# 备份数据
copy data\skills.json data\skills_backup_%date:~0,10%.json
```

### 清理旧日志

```bash
# 删除 30 天前的日志
forfiles /p logs /s /m *.log /d -30 /c "cmd /c del @path"
```

## 🎯 使用场景

### 场景 1: 个人使用

```bash
# 每天手动更新一次
python main.py --once
```

### 场景 2: 团队共享

```bash
# 启动 API 服务器
python api_server_example.py

# 配置定时任务每天自动更新
.\setup_scheduled_task.ps1
```

### 场景 3: CI/CD 集成

```yaml
# .github/workflows/update-skills.yml
name: Update Skills
on:
  schedule:
    - cron: '0 2 * * *'  # 每天凌晨2点
jobs:
  update:
    runs-on: windows-latest
    steps:
      - uses: actions/checkout@v2
      - name: Setup Python
        uses: actions/setup-python@v2
      - name: Install dependencies
        run: pip install -r requirements.txt
      - name: Update skills
        run: python main.py --once --api-sync
```

## 📚 更多文档

- [完整 README](README.md)
- [API 集成指南](API_INTEGRATION.md)
- [配置文件说明](config.py)

## 💡 提示

1. **首次运行**: 建议先运行 `python main.py --once -v` 查看详细过程
2. **定期备份**: 定期备份 `data/skills.json`
3. **监控日志**: 定期检查 `logs/updater.log` 确保正常运行
4. **API 测试**: 集成 API 前先用示例服务器测试
5. **网络问题**: 如遇网络问题，可调整 `RETRY_TIMES` 和 `RETRY_DELAY`
