---
name: content-creation-publisher
description: 内容创作与发布全流程技能，整合网页采集、Markdown格式化、智能配图、多平台发布（微信公众号、X/Twitter）功能，实现从内容获取到发布的一站式解决方案
dependency:
  python:
    - requests>=2.28.0
    - pillow>=10.0.0
  system:
    - Node.js环境（用于baoyu技能）
    - Chrome浏览器（用于CDP功能）
---

# 内容创作与发布全流程

## 任务目标
- 本技能用于：从内容采集到发布的完整工作流
- 能力包含：
  - 网页内容提取转Markdown
  - Markdown格式化和排版优化
  - 智能文章配图
  - 多平台自动发布（微信公众号、X/Twitter）
- 触发条件：用户需要采集、编辑、配图、发布内容

## 核心功能模块

### 模块1：内容采集（baoyu-url-to-markdown）
**功能**：将任意网页转换为干净的Markdown格式

**使用场景**：
- 采集文章、论文、新闻
- 提取知识库内容
- 保存网页内容

**操作步骤**：
1. 提供网页URL
2. 选择捕获模式：
   - 自动模式：页面加载后立即捕获
   - 等待模式：需要登录或交互的页面
3. 自动提取并转换为Markdown

**技术实现**：
- 使用Chrome CDP技术
- 智能清理HTML标签
- 保留文章结构和格式

---

### 模块2：格式优化（baoyu-format-markdown）
**功能**：格式化和优化Markdown文档

**核心特性**：
1. **自动格式化**
   - 添加frontmatter（标题、日期、标签）
   - 调整标题层级
   - 优化列表和代码块

2. **排版优化**
   - 修复中文标点符号导致的**加粗bug
   - 自动在中文和英文之间添加空格
   - ASCII标点转全角引号
   - CJK字符间距优化

3. **内容增强**
   - 自动生成摘要
   - 添加目录
   - 优化段落结构

**使用场景**：
- 优化采集的内容
- 格式化原创文章
- 统一文档风格

---

### 模块3：智能配图（article-illustrator）
**功能**：分析文章内容，在需要视觉辅助的位置生成插图

**配图类型**：
- 信息补充型：数据可视化、流程图
- 概念具象化：抽象概念的视觉表达
- 引导想象型：场景描绘、氛围营造

**配图风格**（6种类型 × 8种风格）：
- **类型**：infographic、scene、flowchart、comparison、framework、timeline
- **风格**：notion、elegant、warm、minimal、blueprint、watercolor、editorial、scientific

**操作步骤**：
1. 分析文章结构，识别需要配图的位置
2. 为每个位置生成配图计划和提示词
3. 使用图像生成能力创建插图
4. 将图片插入到文章对应位置

---

### 模块4：多平台发布

#### 4.1 微信公众号发布（baoyu-post-to-wechat）
**功能**：自动发布内容到微信公众号

**发布模式**：
1. **图文模式**
   - 适合带图片的文章
   - 支持多图文
   - 自动处理图片上传

2. **文章模式**
   - 适合长文
   - 保留Markdown格式
   - 自动转换为公众号格式

**操作方式**：
- **浏览器模式**（推荐）：使用Chrome自动化
- **API模式**：需配置WECHAT_APP_ID和WECHAT_APP_SECRET

**操作步骤**：
1. 准备Markdown内容和图片
2. 选择发布模式（图文/文章）
3. 自动打开浏览器并登录
4. 自动填充内容并发布

---

#### 4.2 X/Twitter发布（baoyu-post-to-x）
**功能**：自动发布内容到X（Twitter）

**发布类型**：
1. **普通推文**
   - 支持文本 + 图片
   - 自动处理字数限制
   - 支持话题标签

2. **X Articles（长文）**
   - 支持Markdown格式
   - 适合深度内容
   - 保留格式和排版

**技术特点**：
- 使用真实Chrome + CDP
- 绕过反自动化检测
- 支持多图上传

**操作步骤**：
1. 准备内容（文本/Markdown）
2. 选择发布类型（推文/Articles）
3. 自动打开浏览器并登录
4. 自动发布内容

---

## 完整工作流

### 工作流1：网页文章采集与发布
```
1. 网页URL
   ↓
2. baoyu-url-to-markdown（提取内容）
   ↓
3. baoyu-format-markdown（格式优化）
   ↓
4. article-illustrator（智能配图）
   ↓
5a. baoyu-post-to-wechat（发布到微信）
   ↓
5b. baoyu-post-to-x（发布到X）
```

### 工作流2：原创内容创作与发布
```
1. 创作Markdown文章
   ↓
2. baoyu-format-markdown（格式优化）
   ↓
3. article-illustrator（智能配图）
   ↓
4. 多平台发布
```

### 工作流3：学术内容处理
```
1. 论文网页URL
   ↓
2. baoyu-url-to-markdown（提取内容）
   ↓
3. paper-analysis-assistant（论文分析）
   ↓
4. baoyu-format-markdown（格式优化）
   ↓
5. ppt-generator（生成PPT）
   ↓
6. baoyu-post-to-wechat（发布解读）
```

### 工作流4：电商内容营销
```
1. product-marketing-copywriter（生成文案）
   ↓
2. baoyu-format-markdown（格式优化）
   ↓
3. pop-up-book-illustration（3D插图）
   ↓
4. baoyu-post-to-x（推广发布）
```

---

## 协同技能组合

### 与现有技能的协同

#### 内容提取组
- **baoyu-url-to-markdown** + paper-analysis-assistant
- **baoyu-url-to-markdown** + stock-analysis
- **baoyu-url-to-markdown** + web-design-analyzer

#### 格式优化组
- **baoyu-format-markdown** + article-illustrator
- **baoyu-format-markdown** + poetry-music-visual
- **baoyu-format-markdown** + ppt-generator

#### 内容创作组
- ecommerce-copywriter + **baoyu-format-markdown** + **baoyu-post-to-x**
- product-marketing-copywriter + **baoyu-format-markdown** + **baoyu-post-to-wechat**
- xiaohongshu-makeup + **baoyu-format-markdown** + 多平台发布

#### 视频内容组
- viral-video-copywriting + **baoyu-format-markdown** + **baoyu-post-to-x**
- pet-commerce-creator + **baoyu-format-markdown** + 多平台发布

---

## 前置准备

### 环境依赖
```bash
# 检查Node.js
node --version

# 检查Chrome
chrome --version

# 安装依赖（如需要）
npm install
```

### 账号准备
1. **微信公众号**
   - 已注册的公众号账号
   - 或配置API（WECHAT_APP_ID、WECHAT_APP_SECRET）

2. **X/Twitter账号**
   - 已注册的X账号
   - 浏览器中保持登录状态

### 配置文件（可选）
```bash
# 创建配置文件
~/.baoyu-skills/.env

# 配置内容（可选）
WECHAT_APP_ID=your_app_id
WECHAT_APP_SECRET=your_app_secret
```

---

## 使用示例

### 示例1：采集文章并发布到微信
```
用户："采集这篇文章并发布到微信公众号"
URL: https://example.com/article

执行流程：
1. baoyu-url-to-markdown 提取内容
2. baoyu-format-markdown 格式优化
3. article-illustrator 智能配图
4. baoyu-post-to-wechat 发布到微信
```

### 示例2：优化文章并多平台发布
```
用户："优化这篇文章并发布到微信和X"
输入：article.md

执行流程：
1. baoyu-format-markdown 格式优化
2. article-illustrator 智能配图
3. baoyu-post-to-wechat 发布到微信
4. baoyu-post-to-x 发布到X
```

### 示例3：采集论文并生成PPT
```
用户："采集这篇论文并生成PPT"
URL: https://arxiv.org/abs/xxxxx

执行流程：
1. baoyu-url-to-markdown 提取内容
2. paper-analysis-assistant 论文分析
3. baoyu-format-markdown 格式优化
4. ppt-generator 生成PPT
5. baoyu-post-to-wechat 发布解读
```

---

## 资源索引

### 核心脚本
- **内容采集**：[baoyu-url-to-markdown/scripts/main.ts](baoyu-url-to-markdown/scripts/main.ts)
- **格式优化**：[baoyu-format-markdown/scripts/main.ts](baoyu-format-markdown/scripts/main.ts)
- **智能配图**：[article-illustrator/SKILL.md](../article-illustrator/SKILL.md)
- **微信发布**：[baoyu-post-to-wechat/scripts/wechat-browser.ts](baoyu-post-to-wechat/scripts/wechat-browser.ts)
- **X发布**：[baoyu-post-to-x/scripts/x-browser.ts](baoyu-post-to-x/scripts/x-browser.ts)

### 参考文档
- **URL转Markdown**：[baoyu-url-to-markdown/SKILL.md](baoyu-url-to-markdown/SKILL.md)
- **格式化指南**：[baoyu-format-markdown/SKILL.md](baoyu-format-markdown/SKILL.md)
- **微信发布指南**：[baoyu-post-to-wechat/references/](baoyu-post-to-wechat/references/)
- **X发布指南**：[baoyu-post-to-x/references/](baoyu-post-to-x/references/)

### 协同技能
- paper-analysis-assistant - 论文分析
- stock-analysis - 股票分析
- ppt-generator - PPT生成
- ecommerce-copywriter - 电商文案
- product-marketing-copywriter - 产品文案
- xiaohongshu-makeup - 小红书内容
- viral-video-copywriting - 爆款视频文案

---

## 注意事项

### 1. Chrome依赖
- 3个模块需要Chrome浏览器
- 确保Chrome已安装并可访问
- 首次使用可能需要手动登录账号

### 2. 账号安全
- 使用浏览器模式时，账号信息保存在本地
- 建议使用专用账号进行自动化发布
- 定期检查发布内容

### 3. 内容审核
- 发布前建议人工审核内容
- 确保符合平台规范
- 注意版权和原创性

### 4. 频率限制
- 避免频繁发布导致账号异常
- 建议设置发布间隔
- 遵守平台规则

### 5. 技术限制
- CDP功能依赖Chrome稳定性
- 网络环境可能影响采集和发布
- 部分网站可能有反爬虫机制

---

## 高级功能

### 批量处理
```
批量采集多个URL
  ↓
批量格式优化
  ↓
批量智能配图
  ↓
定时发布到多平台
```

### 自定义工作流
用户可以根据需求组合不同模块：
- 仅采集 + 格式化
- 仅配图 + 发布
- 完整流程自动化

### 模板系统
- 预设多种内容模板
- 自定义格式化规则
- 保存常用工作流

---

## 故障排查

### 问题1：Chrome无法启动
**解决方案**：
- 检查Chrome是否安装
- 更新Chrome到最新版本
- 检查系统权限

### 问题2：网页采集失败
**解决方案**：
- 检查网络连接
- 尝试等待模式
- 手动登录后再采集

### 问题3：发布失败
**解决方案**：
- 检查账号登录状态
- 确认内容符合平台规范
- 检查图片大小和格式

### 问题4：格式化异常
**解决方案**：
- 检查Markdown语法
- 手动调整特殊格式
- 使用预设模板

---

## 更新日志

### v1.0.0（2026-02-09）
- ✅ 整合4个baoyu技能
- ✅ 整合article-illustrator
- ✅ 创建完整工作流
- ✅ 支持多平台发布
- ✅ 添加协同技能组合

---

## 技能组成

本技能整合了以下子技能：

1. **baoyu-url-to-markdown** - 网页转Markdown
2. **baoyu-format-markdown** - Markdown格式化
3. **baoyu-post-to-wechat** - 微信公众号发布
4. **baoyu-post-to-x** - X/Twitter发布
5. **article-illustrator** - 智能文章配图

以及可协同的44个现有技能。

---

**🚀 一站式内容创作与发布解决方案！**
