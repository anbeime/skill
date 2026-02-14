# 自动化工作流配置说明

## 目录
- [概览](#概览)
- [n8n工作流设计](#n8n工作流设计)
- [工作流节点说明](#工作流节点说明)
- [配置示例](#配置示例)
- [部署指南](#部署指南)

## 概览

本文档说明如何基于本Skill的脚本构建n8n自动化工作流，实现从热点采集到多平台发布的完整自动化流程。

### 工作流优势
- **全自动化**：从选题到发布无需人工干预
- **多平台支持**：同时发布到微信、小红书、B站
- **智能决策**：基于评分系统筛选优质选题
- **安全可控**：支持草稿箱模式，人工审核后再发布

### 工作流架构
```
热点采集 → 选题筛选 → 内容生成 → 排版处理 → 素材上传 → 草稿发布 → 人工审核 → 正式发布
```

## n8n工作流设计

### 完整工作流图

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│  热点采集   │───▶│  选题筛选   │───▶│  内容生成   │───▶│  排版处理   │
└─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘
     │                 │                 │                 │
     ▼                 ▼                 ▼                 ▼
订阅源配置      filter_topics.py      AI智能体        HTML排版规范
     │                 │                 │                 │
     ▼                 ▼                 ▼                 ▼
定时触发            评分≥7分         标题+内容        结构+划线
                                          │                 │
                                          ▼                 ▼
                                    ┌─────────────┐    ┌─────────────┐
                                    │  图片搜索   │───▶│  素材上传   │
                                    └─────────────┘    └─────────────┘
                                          │                 │
                                          ▼                 ▼
                                    search_images.py   publish_wechat.py
                                                             │
                                                             ▼
                                                      ┌─────────────┐
                                                      │  草稿发布   │
                                                      └─────────────┘
                                                             │
                                                             ▼
                                                    ┌─────────────┐
                                                    │  人工审核   │
                                                    └─────────────┘
                                                             │
                                                  ┌──────────┘
                                                  │
                                             人工审核通过
                                                  │
                                                  ▼
                                            ┌─────────────┐
                                            │  正式发布   │
                                            └─────────────┘
```

## 工作流节点说明

### 节点1：定时触发器（Schedule Trigger）

**功能**：定期启动工作流

**配置**：
```json
{
  "mode": "cron",
  "cronExpression": "0 9,18 * * *",  // 每天9点和18点执行
  "timezone": "Asia/Shanghai"
}
```

### 节点2：热点采集（HTTP Request）

**功能**：从订阅源采集热点数据

**配置选项1：使用fetch_sources.py**
```bash
python scripts/fetch_sources.py --source "techcrunch" --keyword "AI"
```

**配置选项2：直接调用API**
```json
{
  "method": "GET",
  "url": "https://api.example.com/hot-topics",
  "headers": {
    "Authorization": "Bearer YOUR_TOKEN"
  }
}
```

### 节点3：选题筛选（Execute Command）

**功能**：调用filter_topics.py进行评分筛选

**命令**：
```bash
python scripts/filter_topics.py --topics "${topics}" --keyword "${keyword}"
```

**返回**：
```json
{
  "filtered_topics": [
    {
      "title": "OpenAI发布新模型",
      "score": 8.5,
      "breakdown": {
        "heat": 3.8,
        "controversy": 1.5,
        "value": 2.5,
        "relevance": 0.7
      }
    }
  ]
}
```

### 节点4：内容生成（HTTP Request to AI API）

**功能**：调用AI生成内容

**请求体**：
```json
{
  "model": "gpt-4",
  "messages": [
    {
      "role": "system",
      "content": "你是一个专业的自媒体内容创作者，擅长生成符合爆款风格的内容。"
    },
    {
      "role": "user",
      "content": "请根据以下热点生成一篇微信公众号文章：${selected_topic}"
    }
  ],
  "temperature": 0.7
}
```

### 节点5：图片搜索（Execute Command）

**功能**：搜索封面图和内文配图

**封面图搜索**：
```bash
python scripts/search_images.py --query "${cover_keyword}" --cover
```

**内文配图搜索**：
```bash
python scripts/search_images.py --query "${image_keyword}"
```

### 节点6：HTML排版（Execute Command / AI生成）

**功能**：生成符合规范的HTML排版

**使用AI生成**：
```json
{
  "model": "gpt-4",
  "messages": [
    {
      "role": "system",
      "content": "你是一个专业的HTML排版专家，严格遵循html-layout-guide.md中的规范。"
    },
    {
      "role": "user",
      "content": "请将以下内容转换为HTML格式：${content}"
    }
  ]
}
```

### 节点7：素材上传（Execute Command）

**功能**：上传封面图片到微信公众号

**命令**：
```bash
python scripts/publish_wechat.py --mode upload_cover --cover "${cover_url}"
```

**返回**：
```json
{
  "success": true,
  "media_id": "COVER_MEDIA_ID",
  "type": "thumb"
}
```

### 节点8：草稿发布（Execute Command）

**功能**：将文章保存到草稿箱

**命令**：
```bash
python scripts/publish_wechat.py --mode create_draft \
  --title "${title}" \
  --content "${html_content}" \
  --media-id "${cover_media_id}" \
  --author "${author}"
```

**返回**：
```json
{
  "success": true,
  "media_id": "DRAFT_MEDIA_ID"
}
```

### 节点9：人工审核（Wait）

**功能**：等待人工审核

**配置**：
```json
{
  "mode": "manual",
  "timeout": 86400,  // 24小时
  "message": "请在微信公众号后台审核草稿，确认无误后继续"
}
```

### 节点10：正式发布（HTTP Request）

**功能**：将草稿发布到正式文章

**API调用**：
```bash
curl -X POST "https://api.weixin.qq.com/cgi-bin/freepublish/submit?access_token=${access_token}" \
  -H "Content-Type: application/json" \
  -d '{
    "media_id": "${draft_media_id}"
  }'
```

## 配置示例

### 示例1：完整工作流JSON

```json
{
  "name": "微信公众号自动发布工作流",
  "nodes": [
    {
      "name": "定时触发器",
      "type": "n8n-nodes-base.scheduleTrigger",
      "parameters": {
        "mode": "cron",
        "cronExpression": "0 9,18 * * *",
        "timezone": "Asia/Shanghai"
      }
    },
    {
      "name": "热点采集",
      "type": "n8n-nodes-base.executeCommand",
      "parameters": {
        "command": "python /path/to/scripts/fetch_sources.py --source techcrunch --keyword AI"
      }
    },
    {
      "name": "选题筛选",
      "type": "n8n-nodes-base.executeCommand",
      "parameters": {
        "command": "python /path/to/scripts/filter_topics.py --topics \"{{ $json.topics }}\" --keyword AI"
      }
    },
    {
      "name": "内容生成",
      "type": "@n8n/n8n-nodes-langchain.openAi",
      "parameters": {
        "model": "gpt-4",
        "prompt": "请根据以下热点生成一篇微信公众号文章：{{ $json.title }}"
      }
    },
    {
      "name": "图片搜索",
      "type": "n8n-nodes-base.executeCommand",
      "parameters": {
        "command": "python /path/to/scripts/search_images.py --query \"{{ $json.cover_keyword }}\" --cover"
      }
    },
    {
      "name": "HTML排版",
      "type": "@n8n/n8n-nodes-langchain.openAi",
      "parameters": {
        "model": "gpt-4",
        "prompt": "请将以下内容转换为HTML格式，严格遵循html-layout-guide.md中的规范：{{ $json.content }}"
      }
    },
    {
      "name": "素材上传",
      "type": "n8n-nodes-base.executeCommand",
      "parameters": {
        "command": "python /path/to/scripts/publish_wechat.py --mode upload_cover --cover \"{{ $json.cover_url }}\""
      }
    },
    {
      "name": "草稿发布",
      "type": "n8n-nodes-base.executeCommand",
      "parameters": {
        "command": "python /path/to/scripts/publish_wechat.py --mode create_draft --title \"{{ $json.title }}\" --content \"{{ $json.html }}\" --media-id \"{{ $json.cover_media_id }}\""
      }
    }
  ],
  "connections": {
    "定时触发器": {
      "main": [[{"node": "热点采集", "type": "main", "index": 0}]]
    },
    "热点采集": {
      "main": [[{"node": "选题筛选", "type": "main", "index": 0}]]
    },
    "选题筛选": {
      "main": [[{"node": "内容生成", "type": "main", "index": 0}]]
    },
    "内容生成": {
      "main": [[{"node": "图片搜索", "type": "main", "index": 0}]]
    },
    "图片搜索": {
      "main": [[{"node": "HTML排版", "type": "main", "index": 0}]]
    },
    "HTML排版": {
      "main": [[{"node": "素材上传", "type": "main", "index": 0}]]
    },
    "素材上传": {
      "main": [[{"node": "草稿发布", "type": "main", "index": 0}]]
    }
  }
}
```

### 示例2：简化工作流（仅到草稿箱）

```json
{
  "name": "简化版工作流",
  "description": "仅保存到草稿箱，需要人工审核",
  "nodes": [
    {"name": "定时触发", "type": "scheduleTrigger"},
    {"name": "热点采集", "type": "executeCommand"},
    {"name": "选题筛选", "type": "executeCommand"},
    {"name": "内容生成", "type": "openAi"},
    {"name": "草稿发布", "type": "executeCommand"}
  ],
  "connections": [
    {"from": "定时触发", "to": "热点采集"},
    {"from": "热点采集", "to": "选题筛选"},
    {"from": "选题筛选", "to": "内容生成"},
    {"from": "内容生成", "to": "草稿发布"}
  ]
}
```

## 部署指南

### 前置要求

1. **n8n安装**
```bash
npm install -g n8n
n8n start
```

2. **Python环境**
```bash
python3 --version  # 需要 Python 3.9+
pip3 install requests
```

3. **Skill脚本**
```bash
cd /path/to/wechat-hotspot-publisher
# 确保所有脚本可执行
chmod +x scripts/*.py
```

4. **环境变量配置**
```bash
export COZE_WECHAT_OFFICIAL_ACCOUNT_7597373721971540014="your_access_token"
export OPENAI_API_KEY="your_openai_key"
```

### 部署步骤

**步骤1：导入工作流**
1. 打开n8n界面
2. 点击"Import Workflow"
3. 粘贴工作流JSON
4. 保存工作流

**步骤2：配置节点**
1. 定时触发器：设置执行时间
2. 热点采集：配置订阅源
3. 内容生成：配置AI API密钥
4. 微信发布：配置access_token

**步骤3：测试工作流**
1. 手动触发工作流
2. 检查每个节点的输出
3. 确认草稿箱中已生成内容

**步骤4：启用定时任务**
1. 确认测试无误
2. 启用工作流
3. 设置定时规则

**步骤5：监控和维护**
1. 定期检查工作流执行日志
2. 监控草稿箱内容质量
3. 根据反馈调整工作流

### 故障排查

**问题1：脚本执行失败**
- 检查Python环境是否正确
- 确认脚本路径是否正确
- 查看错误日志

**问题2：AI生成内容质量差**
- 调整AI的temperature参数
- 优化prompt提示词
- 增加内容审核节点

**问题3：微信API调用失败**
- 检查access_token是否有效
- 确认IP白名单配置
- 查看API返回的错误码

**问题4：图片上传失败**
- 检查图片URL是否有效
- 确认图片格式和大小
- 查看网络连接状态

### 优化建议

1. **增加质量检查节点**
   - 在草稿发布前增加内容质量评分
   - 低质量内容自动过滤

2. **支持多平台发布**
   - 添加小红书发布节点
   - 添加B站发布节点

3. **增加A/B测试**
   - 同一热点生成多个版本
   - 选择最佳版本发布

4. **数据分析**
   - 记录每篇文章的阅读量
   - 分析哪些选题表现更好
   - 优化选题筛选策略

## 常见问题

### Q1: 如何设置定时任务？
A: 在n8n的定时触发器节点中配置cron表达式，例如：
- `0 9 * * *`：每天9点
- `0 */6 * * *`：每6小时
- `0 9,18 * * *`：每天9点和18点

### Q2: 如何处理API调用失败？
A: 在节点配置中启用"Continue On Fail"选项，并添加错误处理节点：
```json
{
  "continueOnFail": true,
  "errorOutput": {
    "node": "错误处理",
    "type": "main"
  }
}
```

### Q3: 如何增加人工审核环节？
A: 在草稿发布节点和正式发布节点之间添加Wait节点：
```json
{
  "type": "n8n-nodes-base.wait",
  "parameters": {
    "mode": "manual",
    "timeout": 86400
  }
}
```

### Q4: 如何支持多平台发布？
A: 复制草稿发布节点，修改为对应平台的脚本：
- 小红书：`publish_xiaohongshu.py`
- B站：`publish_bilibili.py`

### Q5: 如何优化内容质量？
A: 
1. 调整AI的temperature参数（0.6-0.8）
2. 优化prompt提示词
3. 增加内容质量评分节点
4. 人工审核关键内容

## 总结

通过n8n自动化工作流，可以实现从热点采集到多平台发布的完整自动化流程。本Skill的脚本提供了完整的API支持，可以轻松集成到n8n中。

关键优势：
- 全自动化，无需人工干预
- 智能决策，基于评分筛选
- 安全可控，支持草稿箱模式
- 灵活扩展，支持多平台

开始构建你的自动化工作流吧！
