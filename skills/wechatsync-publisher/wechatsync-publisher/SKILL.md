---
name: wechatsync-publisher
description: 多平台内容发布助手，支持智能选题筛选、AI生成优质内容、一键发布到微信公众号等平台；支持内容格式自动适配（HTML/Markdown/纯文本）
---

# 多平台内容发布助手

## 任务目标
- 本Skill用于：高效实现多平台内容发布，从选题、创作到一键推送的全流程自动化
- 能力包含：
  - 智能选题筛选（10分制打分系统）
  - AI生成优质内容（热点评论、技术解析、干货教程、故事洞察等）
  - 多平台一键发布（微信、知乎、掘金、CSDN、B站、小红书）
  - 内容格式自动适配（HTML、Markdown、纯文本）
- 触发条件：
  - "发布到微信公众号"
  - "多平台发布文章"
  - "一键推送内容"
  - "生成并发布文章"

## 前置准备

### 依赖说明
本Skill使用Python标准库，无额外依赖。

### 环境准备
无需特殊环境准备，确保网络连接即可。

### 接口配置
- **服务器地址**：`http://39.108.254.228:8002`（您自建的服务）
- **微信公众号**：已配置接口 `/publish-draft` ✅
- **其他平台**：需要逐步配置独立接口
  - 知乎：`/publish-zhihu`（需配置知乎Cookie）
  - 微博：`/publish-weibo`（需配置微博AppKey/Token）
  - 掘金：`/publish-juejin`（需配置掘金Cookie）
  - CSDN：`/publish-csdn`（需配置CSDN Cookie）
  - 其他平台：详见 `references/server-config-guide.md`

**接口架构**：
- 每个平台独立的发布接口
- 每个平台独立的认证配置
- 统一的请求和返回格式

**详细配置指南**：
- 参考文档：`references/server-config-guide.md`
- 包含：各平台接口配置示例、认证信息获取方式、部署步骤、测试方法

## 操作步骤

### 标准流程

#### 步骤一：选题筛选（可选）

如果您有多个选题候选，可使用选题筛选功能进行打分排序：

```bash
python scripts/filter_topics.py --topics "AI技术:8,2,3,1,AI伦理:7,2,4,1,人工智能:6,1,3,1" --threshold 7
```

**参数说明**：
- `--topics`：选题列表，格式为 `选题名:热度,争议性,价值,相关性`
- `--threshold`：分数阈值，≥7分进入推荐池

**智能体处理**：
如果由智能体处理选题，智能体会根据热度、争议性、价值、相关性四个维度进行评分，并筛选出优质选题。

#### 步骤二：差异化内容生成

根据平台特性生成差异化的内容，确保每个平台的内容都符合平台风格和用户习惯。

**核心原则**：
- 同一主题，多版本适配
- 保持核心信息一致
- 优化表达方式和侧重点
- 符合平台格式要求

**生成内容**：

1. **了解平台特性**：参考 [references/content-adaptation-guide.md](references/content-adaptation-guide.md)
   - 深度阅读类：微信、WordPress（1500-3000字，HTML格式）
   - 知识问答类：知乎（1000-2000字，Markdown格式）
   - 短内容类：微博、X（140-280字，纯文本）
   - 技术社区类：掘金、CSDN（800-1500字，Markdown+代码）
   - 图文社区类：小红书（300-800字，纯文本+emoji）

2. **生成主内容**（建议以微信公众号为主）：
   - 选择内容风格：参考 [references/viral-content-templates.md](references/viral-content-templates.md)
   - 生成HTML格式内容：遵循 [references/html-layout-guide.md](references/html-layout-guide.md)
   - 排版规范：结构分层+局部划线，不超过20%

3. **适配其他平台**：
   - 知乎：转换为问答式结构，Markdown格式
   - 微博/X：提取核心观点，纯文本+话题标签
   - 小红书：使用emoji+短段落，纯文本+标签
   - 掘金/CSDN：添加代码示例，Markdown格式

4. **搜索封面图**：
```bash
python scripts/search_images.py --keyword "AI技术" --count 1 --size 1600x680
```

**智能体处理**：
智能体会根据目标平台自动：
- 调整内容长度（微信3000字 vs 小红书600字）
- 选择内容格式（HTML/Markdown/纯文本）
- 优化标题风格（悬念式 vs 技术向 vs 吸睛短标题）
- 调整封面比例（2.35:1 vs 16:9 vs 3:4）
- 适配标签格式（#话题# vs #标签）
- 确保纯净输出（无作者信息、制作信息）

#### 步骤三：一键发布

调用发布脚本，将内容推送到目标平台：

```bash
# 发布到微信公众号（已可用）
python scripts/publish.py --platform wechat --title "文章标题" --content "HTML内容" --cover-image "封面图URL" --tags "标签1,标签2"

# 发布到知乎（需配置统一接口）
python scripts/publish.py --platform zhihu --title "文章标题" --content "Markdown内容"

# 发布到微博（需配置统一接口）
python scripts/publish.py --platform weibo --title "文章标题" --content "纯文本内容"

# 发布到掘金（需配置统一接口）
python scripts/publish.py --platform juejin --title "文章标题" --content "Markdown内容" --tags "AI,技术"

# 发布到小红书（需配置统一接口）
python scripts/publish.py --platform xiaohongshu --title "文章标题" --content "纯文本内容" --cover-image "封面图URL"
```

**支持的平台**：
- 深度阅读类：wechat、wordpress
- 知识问答类：zhihu
- 短内容类：weibo、x
- 技术社区类：juejin、csdn
- 文艺社区类：jianshu
- 流量分发类：toutiao、dayu
- 视频配套类：bilibili
- 财经投资类：xueqiu
- 图文社区类：xiaohongshu

### 可选分支

#### 分支A：快速发布模式（推荐）

无特殊要求时，自动执行以下流程：

1. **自动选题**：智能体根据当前热点和目标受众生成选题
2. **生成内容**：默认生成图文并茂的公众号爆款文
3. **搜索封面**：根据标题关键词自动搜索封面图
4. **一键推送**：发布到微信公众号草稿箱

**示例请求**：
- "发布一篇关于AI技术的文章"
- "生成并发布热点评论"
- "快速推送一篇技术解析"

#### 分支B：多平台差异化发布（推荐）

需要同时发布到多个平台时，智能体会为每个平台生成差异化的内容：

1. **生成主内容**：以微信公众号为主，生成深度内容（1500-3000字，HTML格式）
2. **差异化适配**：
   - **知乎**：转换为问答式结构（1000-2000字，Markdown格式）
   - **微博**：提取核心观点（140-280字，纯文本+话题标签）
   - **小红书**：使用emoji+短段落（300-800字，纯文本+标签）
   - **掘金/CSDN**：添加代码示例（800-1500字，Markdown格式）
   - **X**：简洁有力（140-280字，纯文本+话题标签）
3. **批量推送**：依次发布到各平台

**注意**：除微信外，其他平台需要先配置统一接口。

**示例请求**：
- "发布'AI技术革命'到微信、知乎、微博、小红书、掘金"
- "多平台分发这篇文章"
- "批量发布到所有平台"

**差异化要点**：
- 内容长度：微信3000字 vs 小红书600字 vs 微博200字
- 内容格式：HTML vs Markdown vs 纯文本
- 标题风格：悬念式 vs 问题式 vs 吸睛短标题
- 封面比例：2.35:1 vs 16:9 vs 3:4

#### 分支C：手动审核模式

需要人工审核后发布：

1. **生成内容**：智能体生成内容
2. **预览审核**：用户提供审核意见
3. **调整优化**：根据反馈调整内容
4. **最终发布**：发布到目标平台

## 资源索引

### 必要脚本
- [scripts/publish.py](scripts/publish.py)：多平台发布脚本，支持微信公众号（已配置）、知乎、掘金、CSDN、B站、小红书（需配置接口）
- [scripts/search_images.py](scripts/search_images.py)：Unsplash图片搜索脚本，支持关键词和尺寸筛选
- [scripts/filter_topics.py](scripts/filter_topics.py)：选题筛选脚本，10分制打分系统

### 领域参考
- [references/server-config-guide.md](references/server-config-guide.md)：服务器端接口配置完整指南
  - 何时读取：需要了解如何在服务器上配置各平台接口和认证信息时
- [references/platform-requirements.md](references/platform-requirements.md)：各平台发布格式要求
  - 何时读取：需要了解目标平台的内容格式和发布规范时
- [references/html-layout-guide.md](references/html-layout-guide.md)：HTML排版完整指南
  - 何时读取：为微信公众号生成HTML内容时
- [references/viral-content-templates.md](references/viral-content-templates.md)：爆款内容模板
  - 何时读取：需要生成高质量内容时参考
- [references/content-adaptation-guide.md](references/content-adaptation-guide.md)：差异化内容生成指南
  - 何时读取：需要为多平台生成差异化内容时
- [references/xiaohongshu-creation-guide.md](references/xiaohongshu-creation-guide.md)：小红书创作完整指南
  - 何时读取：需要为小红书创作精美内容和图片卡片时

## 注意事项

### 发布规范
1. **纯净输出**：不包含作者信息、制作信息（如"COZE制作"、"AI助手"等）
2. **排版质量**：
   - 微信：严格遵循HTML排版指南，划线密度不超过20%
   - 其他平台：符合各平台格式要求
3. **封面规范**：
   - 微信：2.35:1比例（推荐1600x680px）
   - 小红书：3:4竖屏
   - 其他平台：16:9比例

### 内容质量
1. **原创性**：确保内容原创或注明出处
2. **准确性**：数据和引用需准确可靠
3. **价值性**：提供有价值的信息和见解

### 平台限制
1. **微信公众号**：已配置接口，可直接使用
2. **其他平台**：需在 `scripts/publish.py` 中配置接口地址，参考：
   ```python
   def publish_zhihu(title, content, cover_image=None, tags=None):
       api_url = "YOUR_ZHIHU_API_URL"  # 替换为实际接口
       # 实现发布逻辑
   ```

## 使用示例

### 示例一：快速发布微信文章（推荐）

**功能说明**：自动生成图文并茂的公众号爆款文并发布到草稿箱

**执行方式**：智能体+脚本混合

**关键步骤**：
1. 智能体生成选题和内容
2. 调用 `scripts/search_images.py` 搜索封面图
3. 调用 `scripts/publish.py` 发布到微信草稿箱

**示例**：
```bash
# 智能体生成内容
# 脚本搜索封面图
python scripts/search_images.py --keyword "AI技术" --count 1

# 脚本发布内容
python scripts/publish.py --platform wechat --title "AI如何改变未来" --content "HTML内容" --cover-image "https://source.unsplash.com/1600x680/?AI"
```

---

### 示例二：选题筛选+内容生成+发布

**功能说明**：从多个候选选题中筛选最佳选题，生成内容并发布

**执行方式**：脚本+智能体+脚本混合

**关键步骤**：
1. 调用 `scripts/filter_topics.py` 筛选选题
2. 智能体根据筛选结果生成内容
3. 调用 `scripts/publish.py` 发布

**示例**：
```bash
# 筛选选题
python scripts/filter_topics.py --topics "AI技术:8,2,3,1,AI伦理:7,2,4,1" --threshold 7

# 智能体生成内容
# 脚本发布
python scripts/publish.py --platform wechat --title "AI伦理" --content "HTML内容"
```

---

### 示例三：多平台批量发布

**功能说明**：同时发布到多个平台（需配置接口）

**执行方式**：智能体+脚本混合

**关键步骤**：
1. 智能体生成主内容（HTML格式）
2. 智能体转换为各平台格式（Markdown/纯文本）
3. 依次调用 `scripts/publish.py` 发布到各平台

**示例**：
```bash
# 发布到微信（已配置）
python scripts/publish.py --platform wechat --title "标题" --content "HTML内容"

# 发布到知乎（需配置接口）
python scripts/publish.py --platform zhihu --title "标题" --content "Markdown内容"

# 发布到掘金（需配置接口）
python scripts/publish.py --platform juejin --title "标题" --content "Markdown内容" --tags "AI,技术"
```

---

## 高级功能

### 自动化工作流

结合定时任务和自动化工具（如n8n、Zapier）可以实现完全自动化的内容发布流程：

1. **定时选题**：每日自动抓取热点并筛选选题
2. **AI生成内容**：根据选题自动生成内容
3. **自动发布**：一键推送到多平台

### 接口扩展

支持自定义接口扩展，在 `scripts/publish.py` 中添加新的平台发布方法：

```python
def publish_custom(title, content, cover_image=None, tags=None):
    """
    自定义平台发布
    """
    api_url = "YOUR_CUSTOM_API_URL"
    # 实现发布逻辑
```

### 内容模板

支持自定义内容模板，在 `references/viral-content-templates.md` 中添加新的模板类型。

---

## 故障排除

### 常见问题

**问题1：微信发布失败**
- 检查网络连接
- 确认接口地址正确：`http://39.108.254.228:8002/publish-draft`
- 查看返回错误信息

**问题2：其他平台发布功能待实现**
- 在 `scripts/publish.py` 中配置相应平台的接口地址
- 参考各平台官方文档了解接口规范

**问题3：图片搜索失败**
- 检查网络连接
- 确认Unsplash服务可用

---

## 更新日志

### v1.0.0 (2024)
- 初始版本发布
- 支持微信公众号一键发布
- 支持图片搜索
- 支持选题筛选
- 提供多平台发布框架
