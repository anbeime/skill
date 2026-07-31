# 国内搜索引擎深度搜索指南

## 🔍 百度 (Baidu)

### 特色功能

| 功能 | 说明 | URL |
|------|------|-----|
| **中文优化** | 中文内容索引最全 | `https://www.baidu.com/s?wd={keyword}` |
| **百度学术** | 学术资源搜索 | `https://xueshu.baidu.com/s?wd={keyword}` |
| **百度新闻** | 新闻聚合 | `https://news.baidu.com/` |

### 搜索示例

```javascript
// 1. 基础搜索
web_fetch({"url": "https://www.baidu.com/s?wd=Python教程"})

// 2. 站内搜索
web_fetch({"url": "https://www.baidu.com/s?wd=site:github.com+python"})

// 3. 文件类型搜索
web_fetch({"url": "https://www.baidu.com/s?wd=机器学习+filetype:pdf"})

// 4. 学术搜索
web_fetch({"url": "https://xueshu.baidu.com/s?wd=深度学习+图像识别"})
```

---

## 🔎 必应中国版 (Bing CN/INT)

### 特色功能

| 功能 | 说明 | URL |
|------|------|-----|
| **中文优化** | `ensearch=0` 中文结果 | `https://cn.bing.com/search?q={keyword}&ensearch=0` |
| **国际版** | `ensearch=1` 英文结果 | `https://cn.bing.com/search?q={keyword}&ensearch=1` |
| **学术搜索** | 学术资源 | `https://cn.bing.com/academic/search?q={keyword}` |

### 搜索示例

```javascript
// 1. 中文搜索结果
web_fetch({"url": "https://cn.bing.com/search?q=人工智能技术&ensearch=0"})

// 2. 英文搜索结果（使用中国服务器）
web_fetch({"url": "https://cn.bing.com/search?q=artificial+intelligence&ensearch=1"})

// 3. 学术搜索
web_fetch({"url": "https://cn.bing.com/academic/search?q=机器学习算法"})
```

---

## 🔍 360搜索

### 特色功能

| 功能 | 说明 | URL |
|------|------|-----|
| **安全搜索** | 内置安全防护 | 默认开启 |
| **基础搜索** | 网页搜索 | `https://www.so.com/s?q={keyword}` |

### 搜索示例

```javascript
// 1. 基础搜索
web_fetch({"url": "https://www.so.com/s?q=网络安全"})

// 2. 站内搜索
web_fetch({"url": "https://www.so.com/s?q=site:zhihu.com+python"})
```

---

## 🔍 搜狗 (Sogou) + 微信搜索

### 特色功能

| 功能 | 说明 | URL |
|------|------|-----|
| **网页搜索** | 通用搜索 | `https://sogou.com/web?query={keyword}` |
| **微信公众号** | 搜公众号文章（唯一渠道） | `https://wx.sogou.com/weixin?type=2&query={keyword}` |
| **知乎优化** | 知乎内容索引好 | `site:zhihu.com` 配合使用 |

### 搜索示例

```javascript
// 1. 网页搜索
web_fetch({"url": "https://sogou.com/web?query=python教程"})

// 2. 微信公众号文章搜索
web_fetch({"url": "https://wx.sogou.com/weixin?type=2&query=Python编程"})

// 3. 搜索特定公众号
web_fetch({"url": "https://wx.sogou.com/weixin?type=2&query=公众号:机器之心"})

// 4. 知乎内容搜索
web_fetch({"url": "https://www.sogou.com/web?query=site:zhihu.com+机器学习"})
```

---

## 📱 神马搜索 (Shenma)

### 特色功能

| 功能 | 说明 | URL |
|------|------|-----|
| **移动优化** | 专注移动端搜索 | `https://m.sm.cn/s?q={keyword}` |
| **阿里生态** | 整合阿里系内容 | UC浏览器默认搜索 |

### 搜索示例

```javascript
// 1. 移动端搜索
web_fetch({"url": "https://m.sm.cn/s?q=python入门教程"})

// 2. 移动网站点搜索
web_fetch({"url": "https://m.sm.cn/s?q=site:zhuanlan.zhihu.com+AI"})
```

---

## 🌍 国内搜索策略

### 按搜索目标选择引擎

| 搜索目标 | 首选引擎 | 原因 |
|---------|---------|------|
| **综合中文内容** | 百度 | 中文索引最全 |
| **微信公众号** | 搜狗微信 | 唯一支持公众号搜索 |
| **知乎内容** | 搜狗 | 知乎优化好 |
| **移动端内容** | 神马 | 移动端优化 |
| **学术资源** | 必应学术 | 学术索引 |
| **中英文双语** | 必应中国/国际版 | enswitch切换 |
| **新闻资讯** | 百度新闻 | 新闻聚合 |

---

## 📚 参考资料

- [百度搜索高级语法](https://baike.baidu.com/item/搜索语法)
- [必应搜索技巧](https://cn.bing.com/tips)
- [搜狗搜索帮助](https://help.sogou.com/)
