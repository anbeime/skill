# 部署检查清单

## ✅ 部署前检查

### 1. 环境准备
- [ ] Python 3.7+ 已安装
- [ ] pip 可用
- [ ] 网络连接正常
- [ ] 磁盘空间充足（至少 100MB）

### 2. 依赖安装
```bash
cd C:\D\StepFun\skill_store_updater
pip install -r requirements.txt
```

检查项：
- [ ] requests 已安装
- [ ] beautifulsoup4 已安装
- [ ] schedule 已安装
- [ ] lxml 已安装

### 3. 配置检查

编辑 `config.py`：

```python
# 必须配置项
- [ ] GITHUB_RAW_README_URL 正确
- [ ] DATA_DIR 路径存在
- [ ] LOG_DIR 路径存在

# 可选配置项（API 集成时需要）
- [ ] SKILL_STORE_API_URL 已配置
- [ ] SKILL_STORE_API_KEY 已配置
- [ ] UPDATE_INTERVAL 符合需求
```

### 4. 功能测试

```bash
# 测试 1: 单次爬取
python main.py --once
- [ ] 成功爬取数据
- [ ] 生成 data/skills.json
- [ ] 生成 logs/updater.log
- [ ] 无错误信息

# 测试 2: 查看统计
python main.py --stats
- [ ] 显示技能总数
- [ ] 显示分类统计
- [ ] 显示更新时间

# 测试 3: 导出 CSV
python main.py --export test.csv
- [ ] 成功生成 CSV 文件
- [ ] 数据完整
- [ ] 编码正确（UTF-8）

# 测试 4: 详细日志
python main.py --once -v
- [ ] 显示详细日志
- [ ] 无异常错误
```

## 🔧 自动化部署

### Windows 任务计划程序

#### 方法 1: PowerShell 脚本（推荐）

```powershell
# 以管理员身份运行
.\setup_scheduled_task.ps1
```

检查项：
- [ ] 任务创建成功
- [ ] 触发时间正确（每天凌晨2点）
- [ ] 程序路径正确
- [ ] 工作目录正确

#### 方法 2: 批处理脚本

```bash
# 测试单次运行
run_once.bat
- [ ] 脚本正常执行
- [ ] 显示更新进度
- [ ] 无错误提示

# 测试后台运行
start_daemon.bat
- [ ] 服务启动成功
- [ ] 持续运行中
- [ ] 日志正常记录
```

#### 方法 3: 手动配置

1. 打开"任务计划程序"
2. 创建基本任务
   - [ ] 名称: SkillStoreAutoUpdate
   - [ ] 描述: 自动更新技能商店数据
3. 触发器
   - [ ] 类型: 每天
   - [ ] 时间: 凌晨 2:00
   - [ ] 启用: 是
4. 操作
   - [ ] 程序: python
   - [ ] 参数: C:\D\StepFun\skill_store_updater\main.py --once
   - [ ] 起始于: C:\D\StepFun\skill_store_updater
5. 条件
   - [ ] 只有在网络可用时才启动
   - [ ] 如果错过计划，立即启动
6. 设置
   - [ ] 允许按需运行任务
   - [ ] 如果任务失败，每隔 10 分钟重新启动

## 🌐 API 集成部署（可选）

### 1. API 服务器部署

```bash
# 安装额外依赖
pip install flask flask-cors

# 启动测试服务器
python api_server_example.py
```

检查项：
- [ ] 服务器启动成功
- [ ] 端口 8000 可访问
- [ ] 健康检查通过: http://localhost:8000/health

### 2. API 配置

编辑 `config.py`:

```python
SKILL_STORE_API_URL = "http://your-server:8000/api/skills"
SKILL_STORE_API_KEY = "your_secure_api_key"
```

检查项：
- [ ] API URL 可访问
- [ ] API Key 正确
- [ ] 网络连接正常

### 3. API 同步测试

```bash
python main.py --once --api-sync
```

检查项：
- [ ] 数据成功推送
- [ ] API 响应正常
- [ ] 日志无错误

## 📊 监控设置

### 1. 日志监控

```bash
# 查看最新日志
type logs\updater.log

# 实时监控
Get-Content logs\updater.log -Wait
```

检查项：
- [ ] 日志文件存在
- [ ] 日志正常记录
- [ ] 无错误信息

### 2. 数据验证

```bash
# 检查数据文件
python -c "import json; data=json.load(open('data/skills.json', encoding='utf-8')); print(f'Total: {data[\"total\"]} skills')"
```

检查项：
- [ ] 数据文件存在
- [ ] JSON 格式正确
- [ ] 技能数量合理（180+）

### 3. 定期检查

建议每周检查：
- [ ] 日志文件大小
- [ ] 数据更新时间
- [ ] 任务执行状态
- [ ] 磁盘空间

## 🔒 安全检查

### 1. 文件权限
- [ ] 配置文件只读
- [ ] 日志目录可写
- [ ] 数据目录可写

### 2. API 安全（如使用）
- [ ] 使用 HTTPS
- [ ] API Key 安全存储
- [ ] 不在日志中暴露密钥

### 3. 网络安全
- [ ] 防火墙规则正确
- [ ] 代理配置（如需要）
- [ ] SSL 证书有效（HTTPS）

## 📝 文档检查

确保以下文档可访问：
- [ ] README.md - 完整文档
- [ ] QUICKSTART.md - 快速开始
- [ ] API_INTEGRATION.md - API 集成
- [ ] PROJECT_SUMMARY.md - 项目总结

## 🎯 部署完成验证

### 最终测试清单

```bash
# 1. 完整更新流程
python main.py --once -v
- [ ] 爬取成功
- [ ] 数据保存
- [ ] 日志记录

# 2. 统计信息
python main.py --stats
- [ ] 显示正确

# 3. 数据导出
python main.py --export final_test.csv
- [ ] 导出成功

# 4. 定时任务（如配置）
schtasks /query /tn SkillStoreAutoUpdate
- [ ] 任务存在
- [ ] 状态正常

# 5. API 同步（如配置）
python main.py --once --api-sync
- [ ] 同步成功
```

## ✅ 部署成功标准

所有以下条件满足即为部署成功：

1. ✅ 依赖安装完成
2. ✅ 配置文件正确
3. ✅ 单次更新成功
4. ✅ 数据文件生成
5. ✅ 日志正常记录
6. ✅ 统计功能正常
7. ✅ 导出功能正常
8. ✅ 定时任务配置（可选）
9. ✅ API 集成测试（可选）
10. ✅ 文档完整可用

## 🆘 故障排查

如遇问题，按顺序检查：

1. **爬取失败**
   - 检查网络连接
   - 查看详细日志: `python main.py --once -v`
   - 检查 GitHub 仓库是否可访问

2. **数据解析错误**
   - 查看日志文件
   - 检查 README 格式是否变更
   - 更新解析规则

3. **API 同步失败**
   - 检查 API 配置
   - 测试 API 连接
   - 查看 API 服务器日志

4. **定时任务不执行**
   - 检查任务计划程序状态
   - 查看任务历史记录
   - 验证程序路径

## 📞 支持资源

- 日志文件: `logs/updater.log`
- 配置文件: `config.py`
- 文档目录: 项目根目录
- 测试命令: `python main.py --once -v`

---

**部署完成后，请保存此清单作为运维参考！**
