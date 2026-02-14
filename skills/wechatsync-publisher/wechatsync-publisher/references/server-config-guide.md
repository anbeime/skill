# 服务器端接口配置指南

## 目录
- [接口架构](#接口架构)
- [各平台接口配置](#各平台接口配置)
- [认证信息配置](#认证信息配置)
- [部署步骤](#部署步骤)
- [测试方法](#测试方法)

---

## 接口架构

### 基础URL
```
http://39.108.254.228:8002
```

### 接口列表
| 平台 | 接口路径 | 认证方式 | 状态 |
|------|---------|---------|------|
| 微信公众号 | `/publish-draft` | AppID + AppSecret | ✅ 已配置 |
| 知乎 | `/publish-zhihu` | Cookie / OAuth | ⏳ 待配置 |
| 微博 | `/publish-weibo` | AppKey + AppSecret + AccessToken | ⏳ 待配置 |
| 掘金 | `/publish-juejin` | Cookie | ⏳ 待配置 |
| CSDN | `/publish-csdn` | Cookie | ⏳ 待配置 |
| 简书 | `/publish-jianshu` | Cookie | ⏳ 待配置 |
| 头条号 | `/publish-toutiao` | AppKey + AppSecret | ⏳ 待配置 |
| B站专栏 | `/publish-bilibili` | Cookie / OAuth | ⏳ 待配置 |
| 雪球 | `/publish-xueqiu` | Cookie | ⏳ 待配置 |
| 大鱼号 | `/publish-dayu` | AppKey + AppSecret | ⏳ 待配置 |
| 小红书 | `/publish-xiaohongshu` | Cookie / API Key | ⏳ 待配置 |
| X (Twitter) | `/publish-x` | API Key + Token | ⏳ 待配置 |
| WordPress | `/publish-wordpress` | REST API + Token | ⏳ 待配置 |

### 通用请求格式
```json
{
  "title": "文章标题",
  "content": "文章内容",
  "cover": "封面图URL（可选）",
  "digest": "摘要/标签（可选）"
}
```

### 通用返回格式
```json
{
  "success": true,
  "message": "发布成功",
  "data": {
    "url": "文章链接",
    "id": "文章ID"
  }
}
```

---

## 各平台接口配置

### 1. 微信公众号 ✅ 已配置

**接口路径**：`POST /publish-draft`

**认证方式**：AppID + AppSecret

**配置示例**（Node.js）：
```javascript
app.post('/publish-draft', async (req, res) => {
  const { title, content, cover } = req.body;

  // 微信公众号配置
  const appId = process.env.WECHAT_APPID;
  const appSecret = process.env.WECHAT_APPSECRET;

  // 1. 获取access_token
  const tokenUrl = `https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid=${appId}&secret=${appSecret}`;
  const tokenResponse = await axios.get(tokenUrl);
  const accessToken = tokenResponse.data.access_token;

  // 2. 发布草稿
  const publishUrl = `https://api.weixin.qq.com/cgi-bin/draft/add?access_token=${accessToken}`;
  const publishData = {
    articles: [{
      title: title,
      content: content,
      thumb_media_id: cover,  // 需要先上传图片获取media_id
      author: "",
      digest: "",
      content_source_url: "",
      need_open_comment: 1,
      only_fans_can_comment: 0
    }]
  };

  const publishResponse = await axios.post(publishUrl, publishData);

  res.json({
    success: true,
    message: "发布成功",
    data: publishResponse.data
  });
});
```

---

### 2. 知乎 ⏳ 待配置

**接口路径**：`POST /publish-zhihu`

**认证方式**：Cookie

**获取Cookie**：
1. 登录知乎网站
2. 打开浏览器开发者工具（F12）
3. 切换到 Network 标签
4. 刷新页面，找到任意请求
5. 复制 Request Headers 中的 Cookie

**配置示例**（Node.js）：
```javascript
app.post('/publish-zhihu', async (req, res) => {
  const { title, content, cover } = req.body;

  // 知乎Cookie配置
  const cookie = process.env.ZHIHU_COOKIE;

  // 调用知乎API发布文章
  const publishUrl = "https://zhuanlan.zhihu.com/api/articles";

  const publishData = {
    title: title,
    content: content,
    column: "",  // 专栏ID，可选
    commentPermission: "anyone",  // 评论权限
    syncToWeibo: false  // 是否同步到微博
  };

  const publishResponse = await axios.post(publishUrl, publishData, {
    headers: {
      'Cookie': cookie,
      'Content-Type': 'application/json'
    }
  });

  res.json({
    success: true,
    message: "发布成功",
    data: {
      url: publishResponse.data.url,
      id: publishResponse.data.id
    }
  });
});
```

---

### 3. 微博 ⏳ 待配置

**接口路径**：`POST /publish-weibo`

**认证方式**：AppKey + AppSecret + AccessToken

**获取认证信息**：
1. 登录微博开放平台：https://open.weibo.com/
2. 创建应用，获取 AppKey 和 AppSecret
3. 使用 OAuth2.0 授权获取 AccessToken

**配置示例**（Node.js）：
```javascript
app.post('/publish-weibo', async (req, res) => {
  const { title, content, cover } = req.body;

  // 微博认证配置
  const appKey = process.env.WEIBO_APPKEY;
  const accessToken = process.env.WEIBO_ACCESS_TOKEN;

  // 调用微博API发布微博
  const publishUrl = `https://api.weibo.com/2/statuses/update.json?access_token=${accessToken}`;

  const publishData = {
    status: `${title}\n\n${content}`,
    visible: 0  // 可见性：0公开
  };

  const publishResponse = await axios.post(publishUrl, querystring.stringify(publishData), {
    headers: {
      'Content-Type': 'application/x-www-form-urlencoded'
    }
  });

  res.json({
    success: true,
    message: "发布成功",
    data: {
      url: publishResponse.data.url,
      id: publishResponse.data.id
    }
  });
});
```

---

### 4. 掘金 ⏳ 待配置

**接口路径**：`POST /publish-juejin`

**认证方式**：Cookie

**获取Cookie**：
1. 登录掘金网站
2. 打开浏览器开发者工具（F12）
3. 切换到 Network 标签
4. 刷新页面，找到任意请求
5. 复制 Request Headers 中的 Cookie

**配置示例**（Node.js）：
```javascript
app.post('/publish-juejin', async (req, res) => {
  const { title, content, tags } = req.body;

  // 掘金Cookie配置
  const cookie = process.env.JUEJIN_COOKIE;

  // 调用掘金API发布文章
  const publishUrl = "https://api.juejin.cn/content_api/article/create_draft";

  const publishData = {
    title: title,
    brief: content.substring(0, 100),  // 摘要
    content: content,
    mark_content: content,  // Markdown内容
    category_id: "",  // 分类ID
    tags: tags || [],  // 标签列表
    cover_image: "",  // 封面图URL
    edit_type: 1  // 0=草稿，1=发布
  };

  const publishResponse = await axios.post(publishUrl, publishData, {
    headers: {
      'Cookie': cookie,
      'Content-Type': 'application/json'
    }
  });

  res.json({
    success: true,
    message: "发布成功",
    data: {
      url: publishResponse.data.data.article_url,
      id: publishResponse.data.data.article_id
    }
  });
});
```

---

### 5. CSDN ⏳ 待配置

**接口路径**：`POST /publish-csdn`

**认证方式**：Cookie

**获取Cookie**：
1. 登录CSDN网站
2. 打开浏览器开发者工具（F12）
3. 切换到 Network 标签
4. 刷新页面，找到任意请求
5. 复制 Request Headers 中的 Cookie

**配置示例**（Node.js）：
```javascript
app.post('/publish-csdn', async (req, res) => {
  const { title, content, tags } = req.body;

  // CSDN Cookie配置
  const cookie = process.env.CSDN_COOKIE;

  // 调用CSDN API发布文章
  const publishUrl = "https://mp.csdn.net/mp_api/article/post";

  const publishData = {
    title: title,
    markdowncontent: content,
    content: "",  // HTML内容，可选
    tags: tags || [],
    categories: "",  // 分类
    type: "original",  # 原创
    status: 1,  # 0=草稿，1=发布
    cover_image: ""  # 封面图URL
  };

  const publishResponse = await axios.post(publishUrl, publishData, {
    headers: {
      'Cookie': cookie,
      'Content-Type': 'application/json'
    }
  });

  res.json({
    success: true,
    message: "发布成功",
    data: {
      url: publishResponse.data.url,
      id: publishResponse.data.id
    }
  });
});
```

---

### 6. 其他平台（简书、头条号、B站、雪球、大鱼、小红书、X、WordPress）

配置方式类似，参考各平台官方API文档。

---

## 认证信息配置

### 环境变量配置（推荐）

创建 `.env` 文件：
```bash
# 微信公众号
WECHAT_APPID=your_appid
WECHAT_APPSECRET=your_appsecret

# 知乎
ZHIHU_COOKIE=your_cookie

# 微博
WEIBO_APPKEY=your_appkey
WEIBO_APPSECRET=your_appsecret
WEIBO_ACCESS_TOKEN=your_token

# 掘金
JUEJIN_COOKIE=your_cookie

# CSDN
CSDN_COOKIE=your_cookie

# ... 其他平台
```

### 代码中读取环境变量
```javascript
require('dotenv').config();

const wechatAppId = process.env.WECHAT_APPID;
const wechatAppSecret = process.env.WECHAT_APPSECRET;
```

---

## 部署步骤

### 1. 准备服务器环境
```bash
# 安装Node.js
curl -fsSL https://deb.nodesource.com/setup_18.x | bash -
apt-get install -y nodejs

# 安装依赖
npm init -y
npm install express axios dotenv body-parser
```

### 2. 创建服务器代码
```javascript
const express = require('express');
const axios = require('axios');
const bodyParser = require('body-parser');
require('dotenv').config();

const app = express();
app.use(bodyParser.json());

// 各平台接口（见上文配置）

app.listen(8002, () => {
  console.log('Server running on http://39.108.254.228:8002');
});
```

### 3. 配置环境变量
```bash
# 编辑 .env 文件
nano .env

# 添加各平台的认证信息
```

### 4. 启动服务
```bash
node server.js
```

### 5. 使用PM2守护进程（推荐）
```bash
# 安装PM2
npm install -g pm2

# 启动服务
pm2 start server.js --name wechatsync

# 查看日志
pm2 logs wechatsync

# 设置开机自启
pm2 startup
pm2 save
```

---

## 测试方法

### 测试微信接口（已配置）
```bash
curl -X POST http://39.108.254.228:8002/publish-draft \
  -H "Content-Type: application/json" \
  -d '{
    "title": "测试文章",
    "content": "<h1>测试</h1><p>内容</p>"
  }'
```

### 测试知乎接口（配置后）
```bash
curl -X POST http://39.108.254.228:8002/publish-zhihu \
  -H "Content-Type: application/json" \
  -d '{
    "title": "测试文章",
    "content": "# 测试\n\n内容"
  }'
```

### 测试微博接口（配置后）
```bash
curl -X POST http://39.108.254.228:8002/publish-weibo \
  -H "Content-Type: application/json" \
  -d '{
    "title": "测试",
    "content": "测试内容"
  }'
```

---

## 注意事项

1. **安全性**：
   - 不要将 `.env` 文件提交到Git
   - 定期更新Cookie和Token
   - 使用HTTPS（生产环境）

2. **稳定性**：
   - 使用PM2守护进程
   - 配置日志记录
   - 监控服务状态

3. **合规性**：
   - 遵守各平台的使用规范
   - 不要频繁发布，避免被封禁
   - 内容要符合各平台的审核标准

4. **错误处理**：
   - 捕获异常并返回统一格式
   - 记录错误日志
   - 提供友好的错误提示

---

## 逐步部署建议

### 第一阶段：测试微信
- ✅ 已完成
- 继续使用 `/publish-draft` 接口

### 第二阶段：添加知乎
1. 获取知乎Cookie
2. 配置 `/publish-zhihu` 接口
3. 测试发布

### 第三阶段：添加微博
1. 注册微博开放平台账号
2. 创建应用获取AppKey和AppSecret
3. 配置 `/publish-weibo` 接口
4. 测试发布

### 第四阶段：逐个添加其他平台
- 掘金
- CSDN
- 简书
- 头条号
- B站
- 雪球
- 大鱼号
- 小红书
- X
- WordPress

---

## 总结

- ✅ 每个平台独立的接口
- ✅ 每个平台独立的认证配置
- ✅ 统一的请求和返回格式
- ✅ 支持逐步部署和测试
- ✅ 安全、稳定、可维护

您可以逐步添加各个平台的接口，配置完成后即可使用Skill实现多平台一键发布！
