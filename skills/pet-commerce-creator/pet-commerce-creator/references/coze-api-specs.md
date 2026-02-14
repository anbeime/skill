# COZE视频大模型API规范文档

## 目录
- API概览
- 认证方式
- 接口列表
- 素材上传规范
- 视频合成规范
- 字幕配置规范
- 错误处理
- 最佳实践

## API概览

COZE视频大模型API提供端到端的视频合成服务，支持图片、音频、字幕等多素材整合，实现音画精准同步。

**基础信息**：
- API地址：https://api.coze.cn/v1
- 认证方式：Bearer Token（API Key）
- 数据格式：JSON
- 字符编码：UTF-8

**核心功能**：
1. 素材上传：支持图片（JPG/PNG）、音频（MP3）
2. 视频合成：多素材整合、音画同步、转场效果
3. 状态查询：实时查询合成任务状态
4. 视频下载：获取成品视频下载链接

## 认证方式

### 获取API Key
1. 登录COZE开放平台
2. 创建应用并获取API Key
3. 将API Key配置为环境变量

### 请求头设置
所有API请求需在HTTP Header中携带认证信息：

```
Authorization: Bearer {api_key}
Content-Type: application/json
```

## 接口列表

### 1. 上传素材
**接口**：POST /material/upload

**功能**：上传图片或音频素材

**请求参数**：
- Content-Type：multipart/form-data
- file：文件对象

**支持格式**：
- 图片：JPG、JPEG、PNG（推荐JPG）
- 音频：MP3（推荐）

**响应示例**：
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "material_id": "mat_1234567890abcdef",
    "url": "https://cdn.coze.cn/materials/xxx.jpg"
  }
}
```

### 2. 创建视频合成任务
**接口**：POST /video/create

**功能**：创建视频合成任务

**请求参数**：
```json
{
  "duration": 15,
  "resolution": "1080P",
  "aspect_ratio": "9:16",
  "transition": {
    "type": "fade",
    "duration": 0.2
  },
  "materials": {
    "images": [
      {"material_id": "mat_xxx1"},
      {"material_id": "mat_xxx2"}
    ],
    "audios": [
      {"material_id": "aud_xxx1"},
      {"material_id": "aud_xxx2"}
    ]
  },
  "subtitles": {
    "tracks": [
      {
        "text": "这是一条字幕",
        "start_time": 0,
        "end_time": 3,
        "font": "sans-serif",
        "font_size": 28,
        "color": "#FFFFFF",
        "position": {
          "x": "center",
          "y": "bottom",
          "margin_bottom": 30
        }
      }
    ]
  },
  "sync_mode": "precise",
  "quality": {
    "denoise": true,
    "sharpen": "low"
  }
}
```

**参数说明**：
- `duration`：视频总时长（秒），推荐15/20/30秒
- `resolution`：分辨率，支持1080P/720P
- `aspect_ratio`：画面比例，支持9:16（竖屏）/16:9（横屏）
- `transition.type`：转场类型，支持fade（柔焦渐变）/none（无转场）
- `transition.duration`：转场时长（秒），推荐0.2-0.3秒
- `sync_mode`：音画同步模式，precise（精准同步）
- `quality.denoise`：是否开启高清降噪
- `quality.sharpen`：锐化强度，支持low（轻度）/medium（中度）/high（重度）

**响应示例**：
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "task_id": "task_1234567890abcdef"
  }
}
```

### 3. 查询任务状态
**接口**：GET /video/status

**功能**：查询视频合成任务状态

**请求参数**：
- task_id：任务ID

**响应示例（处理中）**：
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "task_id": "task_xxx",
    "status": "processing",
    "progress": 60
  }
}
```

**响应示例（完成）**：
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "task_id": "task_xxx",
    "status": "completed",
    "progress": 100,
    "download_url": "https://cdn.coze.cn/videos/xxx.mp4",
    "duration": 15,
    "size": "5.2MB"
  }
}
```

**状态说明**：
- `processing`：处理中
- `completed`：已完成
- `failed`：失败（error字段包含错误信息）

### 4. 下载视频
**接口**：GET（直接访问download_url）

**功能**：下载合成完成的视频

**使用方式**：
1. 从任务状态接口获取download_url
2. 直接访问该URL下载视频文件

## 素材上传规范

### 图片素材
**格式要求**：
- 格式：JPG、PNG（推荐JPG）
- 分辨率：不低于1080x1920（1080P竖屏）
- 文件大小：单张不超过10MB
- 命名规范：镜头序号_场景名称.jpg（如01_猫咪蜷睡.jpg）

**质量要求**：
- 无模糊、噪点
- 色彩饱满，对比度适中
- 角色清晰可见，无遮挡
- 商品卖点区域突出

**命名示例**：
```
01_猫咪扒粮袋_流量.jpg
02_猫咪吃粮特写_带货.jpg
03_猫咪满足舔嘴_萌点.jpg
```

### 音频素材
**格式要求**：
- 格式：MP3（仅支持MP3）
- 采样率：44.1kHz或48kHz
- 比特率：128kbps-320kbps
- 文件大小：单个不超过20MB
- 命名规范：类型_用途.mp3（如bgm_轻快.mp3）

**质量要求**：
- 无杂音、爆音
- 音量适中（推荐-6dB至-3dB）
- 背景音乐无版权问题
- 口播清晰响亮

**命名示例**：
```
bgm_轻快软萌.mp3
sfx_猫叫.mp3
voice_口播带货.mp3
```

## 视频合成规范

### 基础参数
**时长配置**：
- 总时长：15秒（短平快）/20秒（中等）/30秒（完整）
- 单镜头时长：2-5秒（普通镜头）/4-5秒（高潮镜头）
- 转场时长：0.2-0.3秒（柔焦渐变）

**分辨率配置**：
- 1080P竖屏：1920x1080（推荐）
- 720P竖屏：1280x720（备选）

### 转场配置
**柔焦渐变（推荐）**：
```json
{
  "type": "fade",
  "duration": 0.2
}
```

**无转场**：
```json
{
  "type": "none",
  "duration": 0
}
```

### 画质配置
**高清降噪+轻微锐化（推荐）**：
```json
{
  "denoise": true,
  "sharpen": "low"
}
```

**重度锐化（不推荐，可能过锐）**：
```json
{
  "denoise": true,
  "sharpen": "high"
}
```

## 字幕配置规范

### 标准字幕格式
```json
{
  "tracks": [
    {
      "text": "字幕文本内容",
      "start_time": 0,
      "end_time": 3,
      "font": "sans-serif",
      "font_size": 28,
      "color": "#FFFFFF",
      "outline_color": "#8B4513",
      "outline_width": 1,
      "position": {
        "x": "center",
        "y": "bottom",
        "margin_bottom": 30,
        "margin_left": 20,
        "margin_right": 20
      },
      "effect": "none"
    }
  ]
}
```

### 参数说明
- `text`：字幕文本，单句3-8字（1080P竖屏适配）
- `start_time`：开始时间（秒），从0开始
- `end_time`：结束时间（秒）
- `font`：字体，推荐sans-serif（无衬线体）
- `font_size`：字号，26-28号（1080P竖屏）
- `color`：字体颜色，奶白色#FFFFFF、浅黄色#FFFACD
- `outline_color`：描边颜色，浅棕色#8B4513、浅粉色#FFB6C1
- `outline_width`：描边宽度，1px
- `position.x`：水平位置，left/center/right
- `position.y`：垂直位置，top/center/bottom
- `position.margin_bottom`：距底边距（像素），30px
- `position.margin_left`：距左边距（像素），20px
- `position.margin_right`：距右边距（像素），20px
- `effect`：特效，none（无）/sparkle（火花）/sweat（汗珠）

### 带货字幕配置示例
**卖点字幕（醒目样式）**：
```json
{
  "text": "配方干净无添加",
  "start_time": 5,
  "end_time": 8,
  "font_size": 28,
  "color": "#FFD700",  金黄色，醒目
  "outline_color": "#FF0000",  红色描边，突出
  "outline_width": 2,
  "effect": "sparkle"  小火花特效
}
```

**关注引导字幕（固定位置）**：
```json
{
  "text": "关注领优惠券",
  "start_time": 12,
  "end_time": 15,
  "font_size": 28,
  "color": "#FFFFFF",
  "outline_color": "#FFB6C1",
  "position": {
    "x": "center",
    "y": "bottom",
    "margin_bottom": 30
  }
}
```

### 字幕同步规则
1. 与画面动作同步：字幕显示时间与画面关键动作匹配
2. 与音效同步：字幕出现时间与音效触发时间对齐
3. 与口播同步：口播字幕与旁白/对话音频精准同步
4. 无遮挡原则：字幕不得遮挡宠物主体、商品卖点区域

## 错误处理

### 错误码列表
| 错误码 | 说明 | 解决方案 |
|--------|------|----------|
| 0 | 成功 | - |
| 1001 | API Key无效 | 检查凭证配置 |
| 1002 | 参数错误 | 检查请求参数格式 |
| 2001 | 素材格式不支持 | 转换为JPG/PNG/MP3格式 |
| 2002 | 素材大小超限 | 压缩文件大小 |
| 3001 | 合成任务失败 | 重试任务或调整素材 |
| 3002 | 素材上传失败 | 检查网络连接 |
| 4001 | 任务超时 | 检查素材数量和时长 |

### 重试策略
- 素材上传失败：立即重试，最多3次
- 合成任务失败：等待2秒后重试，最多3次
- 任务超时（>180秒）：放弃任务，检查素材

## 最佳实践

### 1. 素材准备
- 图片：统一分辨率1080x1920，格式JPG
- 音频：统一格式MP3，采样率44.1kHz
- 命名：按镜头序号排序，便于管理

### 2. 合成参数
- 时长：严格控制15-30秒，适配平台推荐逻辑
- 转场：统一柔焦渐变0.2秒，保持视觉柔和
- 字幕：底部居中，距底30px，无遮挡

### 3. 质量控制
- 图片：无模糊、噪点、黑边
- 音频：无杂音、爆音
- 字幕：无错别字，与音画同步

### 4. 性能优化
- 批量上传素材，减少网络请求
- 轮询间隔2秒，避免频繁查询
- 任务完成后立即下载，释放资源

### 5. 异常处理
- 捕获所有API异常，提供友好错误提示
- 记录失败日志，便于问题排查
- 提供人工介入通道，避免任务卡死

## 附录：完整示例

### 完整视频合成请求示例
```json
{
  "duration": 15,
  "resolution": "1080P",
  "aspect_ratio": "9:16",
  "transition": {
    "type": "fade",
    "duration": 0.2
  },
  "materials": {
    "images": [
      {"material_id": "mat_xxx1"},
      {"material_id": "mat_xxx2"},
      {"material_id": "mat_xxx3"},
      {"material_id": "mat_xxx4"}
    ],
    "audios": [
      {"material_id": "aud_bgm"},
      {"material_id": "aud_voice"}
    ]
  },
  "subtitles": {
    "tracks": [
      {
        "text": "这款猫粮超好吃",
        "start_time": 0,
        "end_time": 3,
        "font_size": 28,
        "color": "#FFFFFF",
        "outline_color": "#8B4513",
        "position": {
          "x": "center",
          "y": "bottom",
          "margin_bottom": 30
        }
      },
      {
        "text": "关注领优惠券",
        "start_time": 12,
        "end_time": 15,
        "font_size": 28,
        "color": "#FFD700",
        "outline_color": "#FF0000",
        "effect": "sparkle"
      }
    ]
  },
  "sync_mode": "precise",
  "quality": {
    "denoise": true,
    "sharpen": "low"
  }
}
```
