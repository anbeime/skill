# 微信公众号API参考

## 目录
- [草稿箱发布API](#草稿箱发布api)
- [接口地址](#接口地址)
- [请求参数](#请求参数)
- [响应参数](#响应参数)
- [错误码](#错误码)
- [完整示例](#完整示例)

## 概览
本文档说明如何使用微信公众号素材管理API，将文章发布到草稿箱。

## 草稿箱发布API

### 接口地址
```
POST https://api.weixin.qq.com/cgi-bin/draft/add?access_token=ACCESS_TOKEN
```

### 请求参数

#### JSON Body结构
```json
{
  "articles": [
    {
      "title": "文章标题",
      "author": "作者名称",
      "digest": "摘要",
      "content": "文章内容（HTML格式）",
      "content_source_url": "原文链接",
      "thumb_media_id": "封面图素材ID",
      "show_cover_pic": 1,
      "need_open_comment": 1,
      "only_fans_can_comment": 0
    }
  ]
}
```

#### 参数说明

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| title | string | 是 | 文章标题 |
| author | string | 否 | 作者名称 |
| digest | string | 否 | 摘要（会显示在图文消息列表中） |
| content | string | 是 | 文章内容，HTML格式 |
| content_source_url | string | 否 | 原文链接，点击"阅读原文"跳转 |
| thumb_media_id | string | 是 | 封面图素材ID |
| show_cover_pic | int | 否 | 是否显示封面图，0-不显示，1-显示（默认0） |
| need_open_comment | int | 否 | 是否打开评论，0-不打开，1-打开 |
| only_fans_can_comment | int | 否 | 是否只有粉丝可评论，0-所有人，1-仅粉丝 |

### 响应参数

#### 成功响应
```json
{
  "errcode": 0,
  "errmsg": "ok",
  "media_id": "MEDIA_ID"
}
```

#### 参数说明
- `errcode`: 错误码，0表示成功
- `errmsg`: 错误信息
- `media_id`: 素材ID，可用于后续操作

### 错误码

| 错误码 | 说明 |
|--------|------|
| 40001 | AppSecret错误或AppSecret不属于这个公众号 |
| 40003 | 不合法的媒体文件类型 |
| 40004 | 不合法的媒体文件ID |
| 40007 | 不合法的媒体文件ID |
| 41001 | 缺少access_token参数 |
| 42001 | access_token超时 |
| 40002 | 不合法的凭证类型 |
| 40003 | 不合法的OpenID |
| 40164 | IP地址不在白名单中 |

## 完整示例

### Python调用示例

```python
import requests
import json

def publish_draft(access_token, title, content, thumb_media_id, author=None, digest=None):
    """
    发布文章到草稿箱
    
    Args:
        access_token: 公众号access_token
        title: 文章标题
        content: 文章内容（HTML格式）
        thumb_media_id: 封面图素材ID
        author: 作者名称（可选）
        digest: 摘要（可选）
    
    Returns:
        dict: 包含media_id的响应数据
    """
    url = f"https://api.weixin.qq.com/cgi-bin/draft/add?access_token={access_token}"
    
    data = {
        "articles": [
            {
                "title": title,
                "content": content,
                "thumb_media_id": thumb_media_id,
                "show_cover_pic": 1,
                "need_open_comment": 1,
                "only_fans_can_comment": 0
            }
        ]
    }
    
    if author:
        data["articles"][0]["author"] = author
    if digest:
        data["articles"][0]["digest"] = digest
    
    response = requests.post(url, json=data)
    result = response.json()
    
    if result.get("errcode") == 0:
        return {
            "success": True,
            "media_id": result.get("media_id"),
            "message": "发布成功"
        }
    else:
        return {
            "success": False,
            "error_code": result.get("errcode"),
            "message": result.get("errmsg")
        }
```

### HTML内容格式示例

```html
<section style="margin: 20px;">
  <h2 style="font-size: 18px; color: #333; margin-bottom: 15px;">文章标题</h2>
  
  <p style="line-height: 1.8; color: #666; margin-bottom: 10px;">
    这是文章的第一段内容，建议保持简洁明了。
  </p>
  
  <p style="line-height: 1.8; color: #666; margin-bottom: 10px;">
    这是文章的第二段内容。
  </p>
  
  <img src="https://example.com/image.jpg" style="width: 100%; margin: 15px 0;" alt="配图">
  
  <h3 style="font-size: 16px; color: #333; margin: 20px 0 10px;">小标题</h3>
  
  <p style="line-height: 1.8; color: #666;">
    继续阐述观点...
  </p>
</section>
```

## 注意事项

1. **Access Token获取**：
   - 使用AppID和AppSecret获取access_token
   - access_token有效期为2小时
   - 建议缓存access_token，避免频繁获取

2. **图片上传**：
   - 封面图需要先上传到微信公众号素材库
   - 使用 `/cgi-bin/media/upload` 接口上传
   - 上传成功后返回的media_id作为thumb_media_id使用

3. **HTML格式要求**：
   - 使用内联样式，不推荐外部CSS
   - 图片宽度建议使用百分比或固定宽度
   - 避免使用JavaScript和外部链接

4. **调用频率限制**：
   - 草稿箱接口有调用频率限制
   - 建议控制调用频率，避免超过限制
