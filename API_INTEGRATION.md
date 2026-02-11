# API 集成指南

## 概述

本系统支持将爬取的技能数据自动推送到技能商店 API。

## 配置 API

编辑 `config.py` 文件：

```python
# 技能商店 API 配置
SKILL_STORE_API_URL = "https://your-api-server.com/api/skills"
SKILL_STORE_API_KEY = "your_api_key_here"
```

## API 接口规范

### 1. 批量推送技能

**端点**: `POST /api/skills/batch`

**请求体**:
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
  ]
}
```

**响应**:
```json
{
  "success": true,
  "added": 182,
  "message": "Skills imported successfully"
}
```

### 2. 获取技能列表

**端点**: `GET /api/skills`

**响应**:
```json
{
  "skills": [
    {
      "name": "anthropics/docx",
      "description": "...",
      "link": "...",
      "category": "..."
    }
  ],
  "total": 182
}
```

### 3. 更新单个技能

**端点**: `PUT /api/skills/{skill_name}`

**请求体**:
```json
{
  "name": "anthropics/docx",
  "description": "Updated description",
  "link": "...",
  "category": "..."
}
```

### 4. 删除技能

**端点**: `DELETE /api/skills/{skill_name}`

## 启用 API 同步

修改 `main.py`，在创建调度器时启用 API 同步：

```python
# 启用 API 同步
scheduler = UpdateScheduler(enable_api_sync=True)
```

## 示例：Flask API 服务器

创建一个简单的 Flask API 服务器接收技能数据：

```python
# api_server.py
from flask import Flask, request, jsonify
import json
import os

app = Flask(__name__)
SKILLS_FILE = 'skills_store.json'

def load_skills():
    if os.path.exists(SKILLS_FILE):
        with open(SKILLS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {'skills': []}

def save_skills(data):
    with open(SKILLS_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

@app.route('/api/skills', methods=['GET'])
def get_skills():
    data = load_skills()
    return jsonify(data)

@app.route('/api/skills/batch', methods=['POST'])
def batch_import():
    data = request.json
    skills = data.get('skills', [])
    
    store = load_skills()
    store['skills'] = skills
    store['total'] = len(skills)
    save_skills(store)
    
    return jsonify({
        'success': True,
        'added': len(skills),
        'message': 'Skills imported successfully'
    })

@app.route('/api/skills/<skill_name>', methods=['PUT'])
def update_skill(skill_name):
    skill_data = request.json
    store = load_skills()
    
    # 查找并更新
    for i, skill in enumerate(store['skills']):
        if skill['name'] == skill_name:
            store['skills'][i] = skill_data
            save_skills(store)
            return jsonify({'success': True})
    
    # 不存在则添加
    store['skills'].append(skill_data)
    save_skills(store)
    return jsonify({'success': True, 'created': True})

@app.route('/api/skills/<skill_name>', methods=['DELETE'])
def delete_skill(skill_name):
    store = load_skills()
    store['skills'] = [s for s in store['skills'] if s['name'] != skill_name]
    save_skills(store)
    return jsonify({'success': True})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000)
```

运行服务器：
```bash
pip install flask
python api_server.py
```

## 测试 API 集成

```bash
# 1. 启动 API 服务器
python api_server.py

# 2. 配置 config.py
SKILL_STORE_API_URL = "http://localhost:8000/api/skills"

# 3. 运行更新（启用 API 同步）
python main.py --once --api-sync
```

## 安全建议

1. **使用 HTTPS**: 生产环境必须使用 HTTPS
2. **API 密钥认证**: 在请求头中添加 `Authorization: Bearer YOUR_API_KEY`
3. **速率限制**: 实现 API 速率限制防止滥用
4. **数据验证**: 服务器端验证所有输入数据
5. **日志记录**: 记录所有 API 请求用于审计

## 故障处理

### API 连接失败
- 检查 API URL 配置
- 验证网络连接
- 查看日志文件 `logs/updater.log`

### 认证失败
- 确认 API Key 正确
- 检查 API Key 权限

### 数据同步不一致
- 手动触发完整同步
- 检查数据格式是否匹配
