# 小红书发布API参考

## 目录
- [概述](#概述)
- [发布接口说明](#发布接口说明)
- [授权方式](#授权方式)
- [参数说明](#参数说明)
- [内容规范](#内容规范)
- [错误处理](#错误处理)
- [完整示例](#完整示例)

## 概述
本文档说明如何使用小红书API发布图文笔记。

**注意**：小红书没有官方公开的发布API，实际使用时需要通过抓包分析Web端请求，或使用自动化工具（如Puppeteer）模拟发布。

## 发布接口说明

### 端点
```
POST https://edith.xiaohongshu.com/api/sns/web/v1/note/publish
```

### 请求头
```
Cookie: <你的Cookie>
Content-Type: application/json
User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36
x-s: <签名>
a1: <设备标识>
```

## 授权方式

### Cookie获取
1. 登录小红书网页版：https://www.xiaohongshu.com
2. 打开浏览器开发者工具（F12）
3. 切换到Network标签
4. 刷新页面或进行任意操作
5. 找到任意请求，复制Request Headers中的Cookie
6. 提取关键参数：
   - `a1`: 设备唯一标识
   - `x-s`: 请求签名（需要算法生成）
   - `web_session`: 会话ID

### Cookie有效期
- Web端Cookie通常有效期为30天
- 需要定期更新，避免过期
- 建议保存在安全的地方，避免泄露

## 参数说明

### 请求体示例
```json
{
  "type": "normal",
  "title": "笔记标题",
  "desc": "笔记内容",
  "at_uid_list": [],
  "image_list": [
    "http://example.com/image1.jpg",
    "http://example.com/image2.jpg"
  ],
  "tag_list": [
    {"name": "AI"},
    {"name": "技术"}
  ],
  "poi_id": "",
  "post_time": 0,
  "share_text": ""
}
```

### 字段说明

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| type | string | 是 | 笔记类型：normal-普通, video-视频 |
| title | string | 是 | 标题，最多20字 |
| desc | string | 是 | 内容，支持Markdown和HTML |
| image_list | array | 否 | 图片URL列表 |
| tag_list | array | 否 | 标签列表，最多5个 |
| at_uid_list | array | 否 | @的用户ID列表 |
| poi_id | string | 否 | 地点ID |
| post_time | number | 否 | 发布时间戳，0为立即发布 |
| share_text | string | 否 | 分享时的描述文字 |

## 内容规范

### 标题规范
- 长度：1-20个字符
- 风格：吸引眼球，可以使用emoji
- 示例：
  - "AI绘画神器！5分钟生成惊艳作品✨"
  - "程序员必看！这3个工具提升10倍效率🚀"

### 内容规范
- 长度：建议800-1500字
- 风格：口语化，分段清晰
- 排版：
  - 使用emoji点缀
  - 重要内容加粗
  - 使用分隔线分段
  - 适当使用列表

### 标签规范
- 数量：1-5个标签
- 格式：#标签名
- 建议：
  - 1-2个核心标签
  - 2-3个长尾标签
- 示例：
  - #AI绘画
  - #Midjourney
  - #设计师

### 图片规范
- 数量：1-9张
- 比例：3:4或1:1
- 大小：每张不超过10MB
- 格式：JPG、PNG

## 错误处理

### 常见错误码

| 错误码 | 说明 | 解决方案 |
|--------|------|----------|
| 401 | 未登录 | 重新获取Cookie |
| 403 | 禁止访问 | 检查IP和账号状态 |
| 10001 | 参数错误 | 检查请求参数格式 |
| 10002 | 内容违规 | 修改内容后重试 |
| 10003 | 图片上传失败 | 检查图片URL和格式 |

### 错误响应示例
```json
{
  "success": false,
  "code": 401,
  "msg": "未登录",
  "data": null
}
```

## 完整示例

### Python发布示例

```python
import requests
import json

def publish_xiaohongshu_note(title, content, cookie):
    """
    发布图文笔记到小红书
    
    Args:
        title: 笔记标题
        content: 笔记内容
        cookie: 小红书Cookie
    
    Returns:
        发布结果
    """
    url = "https://edith.xiaohongshu.com/api/sns/web/v1/note/publish"
    
    headers = {
        'Cookie': cookie,
        'Content-Type': 'application/json',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    data = {
        'type': 'normal',
        'title': title,
        'desc': content,
        'tag_list': [
            {'name': 'AI'},
            {'name': '技术'}
        ],
        'post_time': 0
    }
    
    response = requests.post(url, headers=headers, json=data)
    result = response.json()
    
    if result.get('success'):
        return {
            'success': True,
            'note_id': result['data']['note_id']
        }
    else:
        return {
            'success': False,
            'error': result.get('msg', '未知错误')
        }

# 使用示例
if __name__ == "__main__":
    title = "AI绘画神器推荐！5分钟生成惊艳作品✨"
    content = """
    今天给大家推荐几个超好用的AI绘画工具！
    
    1. Midjourney：效果最惊艳，适合专业创作
    2. Stable Diffusion：开源免费，可本地部署
    3. DALL-E 3：GPT-4集成，操作简单
    
    每个都有自己的特色，看你需要什么～
    
    #AI绘画 #Midjourney #设计
    """
    
    cookie = "你的Cookie"
    result = publish_xiaohongshu_note(title, content, cookie)
    print(json.dumps(result, ensure_ascii=False, indent=2))
```

### 小红书内容格式示例

```markdown
# 标题

## 开头（吸引眼球）
✨ 5分钟学会AI绘画，零基础也能出大片！

## 核心内容（分段清晰）
今天给大家分享3个超好用的AI绘画工具：

### 1️⃣ Midjourney
- 优点：效果最惊艳，细节丰富
- 适合：专业创作、商业设计
- 难度：★★★★☆

### 2️⃣ Stable Diffusion
- 优点：开源免费，可定制
- 适合：开发者、设计师
- 难度：★★★☆☆

### 3️⃣ DALL-E 3
- 优点：GPT-4集成，操作简单
- 适合：新手、快速出图
- 难度：★★☆☆☆

---

💡 小贴士：
- 新手推荐从DALL-E 3开始
- 想要更多自由度试试SD
- 追求极致效果选Midjourney

---

📌 记得点赞收藏哦！有问题评论区见～

#AI绘画 #Midjourney #设计 #教程
```

## 注意事项

1. **API限制**：
   - 小红书没有公开API，以上接口可能随时变动
   - 建议定期抓包分析最新接口
   - 考虑使用官方开放平台（如有）

2. **签名生成**：
   - 请求签名（x-s）需要复杂的算法
   - 需要逆向分析JS代码
   - 建议使用抓包获取的签名

3. **账号安全**：
   - 不要频繁发布，避免被限流
   - 避免发布违规内容
   - 妥善保管Cookie

4. **替代方案**：
   - 使用Selenium/Puppeteer模拟浏览器操作
   - 使用第三方服务（如RPA工具）
   - 手动发布（最稳定）
