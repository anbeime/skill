# 哔哩哔哩发布API参考

## 目录
- [概述](#概述)
- [发布接口说明](#发布接口说明)
- [授权方式](#授权方式)
- [参数说明](#参数说明)
- [内容规范](#内容规范)
- [错误处理](#错误处理)
- [完整示例](#完整示例)

## 概览
本文档说明如何使用B站API发布专栏文章。

## 发布接口说明

### 专栏分类ID
| 分类ID | 名称 |
|--------|------|
| 122 | 技术 |
| 124 | 游戏 |
| 125 | 动画 |
| 126 | 影视 |
| 127 | 生活 |
| 128 | 动漫 |
| 129 | 音乐 |
| 130 | 舞蹈 |
| 131 | 娱乐 |
| 132 | 资讯 |

### 保存草稿接口
```
POST https://api.bilibili.com/x/article/drafts
```

### 发布接口
```
POST https://api.bilibili.com/x/article/publish?csrf={bili_jct}
```

## 授权方式

### Cookie获取
1. 登录B站：https://www.bilibili.com
2. 打开浏览器开发者工具（F12）
3. 切换到Application标签
4. 展开Cookies → https://www.bilibili.com
5. 找到并复制以下Cookie：
   - `SESSDATA`: 会话凭证
   - `bili_jct`: CSRF Token（必需）
   - `DedeUserID`: 用户ID

### Cookie有效期
- SESSDATA通常有效期为30天
- 需要定期更新
- 建议保存在安全的地方

## 参数说明

### 保存草稿请求体
```json
{
  "title": "文章标题",
  "content": "文章内容（Markdown或HTML）",
  "category_id": 122,
  "summary": "文章摘要",
  "list": [],
  "reprint": 0,
  "original": 1,
  "top_video": "",
  "spoiler": 0,
  "words": 1200,
  "media_id": 0,
  "dynamic": ""
}
```

### 字段说明

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| title | string | 是 | 标题，最多100字 |
| content | string | 是 | 文章内容，支持Markdown |
| category_id | number | 是 | 专栏分类ID |
| summary | string | 否 | 摘要，最多200字 |
| list | array | 否 | 图片列表 |
| reprint | number | 是 | 0-原创, 1-转载 |
| original | number | 是 | 是否原创，0-否, 1-是 |
| top_video | string | 否 | 顶部视频BV号 |
| spoiler | number | 否 | 是否剧透，0-否, 1-是 |
| words | number | 是 | 文章字数 |
| media_id | number | 否 | 媒体ID |
| dynamic | string | 否 | 同步动态的内容 |

### 发布请求体
```json
{
  "id": "草稿ID"
}
```

## 内容规范

### 标题规范
- 长度：1-100个字符
- 风格：清晰、有吸引力
- 示例：
  - "深度解析：AI大模型的未来发展方向"
  - "2024年程序员必学的5个新技术"

### 内容规范
- 长度：建议1000-3000字
- 格式：支持Markdown
- 结构：
  - 引言
  - 核心内容（分章节）
  - 案例或数据
  - 总结
  - 参考资料

### Markdown示例
```markdown
# 深度解析：AI大模型的未来发展方向

## 引言
随着GPT-4的发布，AI大模型技术...

## 1. 模型规模持续扩大
近年来，大模型的参数量呈指数级增长...

## 2. 多模态能力提升
除了文本，图像、音频等多模态能力...

## 3. 推理能力优化
大模型在复杂推理任务上的表现...

## 总结
AI大模型正在快速发展，未来可期...

## 参考资料
1. OpenAI官网
2. Google AI Blog
```

## 错误处理

### 常见错误码

| 错误码 | 说明 | 解决方案 |
|--------|------|----------|
| -101 | 账号未登录 | 检查Cookie中的SESSDATA |
| -111 | CSRF校验失败 | 检查Cookie中的bili_jct |
| -400 | 请求错误 | 检查参数格式 |
| -402 | 内容违规 | 修改内容后重试 |
| -404 | 草稿不存在 | 检查草稿ID |

### 错误响应示例
```json
{
  "code": -101,
  "message": "账号未登录",
  "data": null
}
```

## 完整示例

### Python发布示例

```python
import requests
import json

def publish_bilibili_article(title, content, cookie):
    """
    发布专栏文章到B站
    
    Args:
        title: 文章标题
        content: 文章内容（Markdown）
        cookie: B站Cookie
    
    Returns:
        发布结果
    """
    # 提取CSRF Token
    csrf_token = None
    for item in cookie.split(';'):
        item = item.strip()
        if 'bili_jct=' in item:
            csrf_token = item.split('=')[1]
            break
    
    if not csrf_token:
        raise ValueError("Cookie中缺少bili_jct")
    
    headers = {
        'Cookie': cookie,
        'Content-Type': 'application/json',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Referer': 'https://member.bilibili.com'
    }
    
    # 1. 保存草稿
    draft_url = "https://api.bilibili.com/x/article/drafts"
    draft_data = {
        'title': title,
        'content': content,
        'category_id': 122,  # 技术
        'summary': content[:100],
        'reprint': 0,
        'original': 1,
        'words': len(content),
        'media_id': 0,
        'spoiler': 0,
        'dynamic': ''
    }
    
    response = requests.post(draft_url, headers=headers, json=draft_data)
    result = response.json()
    
    if result['code'] != 0:
        return {
            'success': False,
            'error': result.get('message', '保存草稿失败')
        }
    
    draft_id = result['data']['id']
    
    # 2. 发布草稿
    publish_url = f"https://api.bilibili.com/x/article/publish?csrf={csrf_token}"
    publish_data = {'id': draft_id}
    
    response = requests.post(publish_url, headers=headers, json=publish_data)
    result = response.json()
    
    if result['code'] == 0:
        article_id = result['data']['id']
        return {
            'success': True,
            'article_id': article_id,
            'url': f"https://www.bilibili.com/read/cv{article_id}"
        }
    else:
        return {
            'success': False,
            'error': result.get('message', '发布失败')
        }

# 使用示例
if __name__ == "__main__":
    title = "深度解析：AI大模型的未来发展方向"
    content = """
# 深度解析：AI大模型的未来发展方向

## 引言
随着GPT-4的发布，AI大模型技术...

## 1. 模型规模持续扩大
近年来，大模型的参数量呈指数级增长...

## 总结
AI大模型正在快速发展，未来可期...
    """
    
    cookie = "你的Cookie"
    result = publish_bilibili_article(title, content, cookie)
    print(json.dumps(result, ensure_ascii=False, indent=2))
```

## 注意事项

1. **发布限制**：
   - 普通用户每日可发布多篇专栏
   - 避免短时间内连续发布
   - 建议间隔至少30分钟

2. **内容审核**：
   - 发布后需要审核
   - 违规内容会被删除或屏蔽
   - 遵守B站社区规范

3. **账号安全**：
   - 妥善保管Cookie
   - 不要在公开平台分享Cookie
   - 定期更换密码

4. **原创声明**：
   - 转载内容必须标注
   - 原创内容会获得更多推荐
   - 抄袭可能导致封号

5. **图片上传**：
   - 专栏支持插入图片
   - 需要先上传图片获取URL
   - 使用B站图片上传API

### 图片上传接口
```
GET https://api.bilibili.com/x/archive/oss/upload
```

返回示例：
```json
{
  "code": 0,
  "message": "0",
  "ttl": 1,
  "data": {
    "url": "https://upos-sz-mirrorcos.bilivideo.com/xxx",
    "biz_id": "xxxxx"
  }
}
```
