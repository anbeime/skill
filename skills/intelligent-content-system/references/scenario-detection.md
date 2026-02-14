# 场景识别规则

## 识别流程

```
用户输入
    ↓
提取关键信息（URL/关键词/文件/平台）
    ↓
识别动作意图（采集/配图/小红书/发布/热点）
    ↓
场景匹配（优先级规则）
    ↓
返回场景代码和参数
```

## 关键信息提取

### 1. URL提取
**正则表达式**：`https?://[^\s]+`

**示例**：
- "采集 https://example.com/article" → `https://example.com/article`
- "这篇文章 www.example.com 很好" → `https://www.example.com`（自动补全）

### 2. 关键词提取
**触发词**：热点、爆款、话题、趋势

**提取方式**：
- 直接提供："根据'AI工具'生成文章" → `AI工具`
- 询问获取："请提供关键词" → 用户回答

### 3. 文件路径提取
**模式**：
- 绝对路径：`D:\path\to\file.md`
- 相对路径：`./article.md`
- 文件名：`article.md`（当前目录）

**验证**：检查文件是否存在

### 4. 平台提取
**关键词映射**：
- "微信"、"公众号"、"wechat" → 微信公众号
- "小红书"、"XHS"、"RedNote" → 小红书
- "X"、"Twitter"、"推特" → X/Twitter
- "B站"、"哔哩哔哩"、"bilibili" → 哔哩哔哩

**多平台识别**：
- "微信和小红书" → [微信公众号, 小红书]
- "发布到所有平台" → [微信公众号, 小红书, X, B站]

## 动作意图识别

### 动作关键词表

| 动作 | 关键词 | 优先级 |
|------|--------|--------|
| 采集 | 采集、抓取、获取、爬取、保存网页、下载 | 高 |
| 配图 | 配图、插图、加图、生成图片、图文 | 高 |
| 小红书 | 小红书、XHS、RedNote、图文、种草 | 高 |
| 发布 | 发布、推送、上传、分享、post | 中 |
| 热点 | 热点、爆款、话题、趋势、热搜 | 高 |
| 优化 | 优化、格式化、美化、排版 | 低 |

### 组合动作识别

**规则**：
- "采集+发布" → 场景A1
- "采集+配图" → 场景A2
- "采集+小红书" → 场景A3
- "热点+文章" → 场景B1
- "热点+小红书" → 场景B2
- "热点+多平台" → 场景B3

## 场景匹配规则

### 优先级规则

1. **热点场景优先**（B类）
   - 如果包含"热点"关键词，优先匹配B类场景
   - B1 > B2 > B3（根据平台数量）

2. **采集场景次之**（A类）
   - 如果包含URL且有动作词，匹配A类场景
   - A1 > A2 > A3（根据后续动作）

3. **优化场景再次**（C类）
   - 如果包含文件路径且有动作词，匹配C类场景
   - C1 > C2 > C3（根据后续动作）

4. **单一功能最后**（D类）
   - 如果只有单一动作词，匹配D类场景
   - D1 > D2 > D3 > D4（根据动作优先级）

### 场景匹配决策树

```
输入分析
├── 包含"热点"关键词？
│   ├── 是 → 包含"小红书"？
│   │   ├── 是 → B2（热点图文生成）
│   │   └── 否 → 包含多个平台？
│   │       ├── 是 → B3（热点多平台发布）
│   │       └── 否 → B1（热点文章生成）
│   └── 否 → 继续
│
├── 包含URL？
│   ├── 是 → 包含"发布"？
│   │   ├── 是 → A1（采集并发布）
│   │   └── 否 → 包含"配图"？
│   │       ├── 是 → A2（采集并配图）
│   │       └── 否 → 包含"小红书"？
│   │           ├── 是 → A3（采集转小红书）
│   │           └── 否 → D1（仅采集网页）
│   └── 否 → 继续
│
├── 包含文件路径？
│   ├── 是 → 包含"配图"？
│   │   ├── 是 → C1（文章配图）
│   │   └── 否 → 包含"小红书"？
│   │       ├── 是 → C2（转小红书图文）
│   │       └── 否 → 包含"发布"？
│   │           ├── 是 → C3（多平台发布）
│   │           └── 否 → 询问用户意图
│   └── 否 → 继续
│
└── 单一动作词？
    ├── "配图" → D2（仅配图）
    ├── "小红书图文" → D3（仅小红书图文）
    ├── "发布" → D4（仅发布）
    └── 其他 → 询问用户意图
```

## 场景识别示例

### 示例1：明确的组合动作
**输入**："采集这篇文章并发布到微信公众号 https://example.com/article"

**识别过程**：
1. 提取URL：`https://example.com/article`
2. 识别动作：采集 + 发布
3. 提取平台：微信公众号
4. 匹配场景：A1（采集并发布）

**输出**：
```python
{
    'scenario': 'A1',
    'params': {
        'url': 'https://example.com/article',
        'platforms': ['微信公众号']
    }
}
```

### 示例2：热点内容创作
**输入**："根据AI热点生成一篇文章，发布到微信和小红书"

**识别过程**：
1. 识别动作：热点 + 发布
2. 提取平台：微信公众号、小红书
3. 匹配场景：B3（热点多平台发布）
4. 缺失参数：关键词（需询问）

**输出**：
```python
{
    'scenario': 'B3',
    'params': {
        'platforms': ['微信公众号', '小红书']
    },
    'missing': ['keyword']
}
```

### 示例3：文章配图
**输入**："给这篇文章配图 article.md"

**识别过程**：
1. 提取文件：`article.md`
2. 识别动作：配图
3. 匹配场景：C1（文章配图）

**输出**：
```python
{
    'scenario': 'C1',
    'params': {
        'file': 'article.md'
    }
}
```

### 示例4：模糊需求
**输入**："我想做内容创作"

**识别过程**：
1. 无明确动作词
2. 无URL/文件/关键词
3. 无法匹配场景

**输出**：
```python
{
    'scenario': 'UNKNOWN',
    'action': 'ask_user',
    'options': [
        'A1: 采集网页并发布',
        'B1: 热点文章生成',
        'C1: 文章配图',
        'C2: 转小红书图文',
        '其他: 请描述具体需求'
    ]
}
```

### 示例5：复杂需求
**输入**："采集这篇文章，先配图，再转小红书，最后发布到微信 https://example.com/article"

**识别过程**：
1. 提取URL：`https://example.com/article`
2. 识别动作：采集 + 配图 + 小红书 + 发布
3. 提取平台：微信公众号
4. 匹配场景：自定义工作流（A1的变体）

**输出**：
```python
{
    'scenario': 'CUSTOM',
    'workflow': [
        {'step': 'fetch', 'skill': 'baoyu-url-to-markdown'},
        {'step': 'illustrate', 'skill': 'article-illustrator'},
        {'step': 'xhs', 'skill': 'baoyu-xhs-images'},
        {'step': 'publish', 'skill': 'wechat-publisher'}
    ],
    'params': {
        'url': 'https://example.com/article',
        'platforms': ['微信公众号']
    }
}
```

## 参数验证规则

### URL验证
```python
def validate_url(url):
    """验证URL格式"""
    # 1. 检查协议
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url
    
    # 2. 检查格式
    pattern = r'^https?://[^\s]+$'
    if not re.match(pattern, url):
        return False, "URL格式不正确"
    
    # 3. 检查可访问性（可选）
    try:
        response = requests.head(url, timeout=5)
        if response.status_code >= 400:
            return False, f"URL无法访问（状态码：{response.status_code}）"
    except:
        pass  # 不强制要求可访问
    
    return True, url
```

### 文件路径验证
```python
def validate_file(file_path):
    """验证文件路径"""
    # 1. 检查文件是否存在
    if not os.path.exists(file_path):
        return False, f"文件不存在：{file_path}"
    
    # 2. 检查文件格式
    if not file_path.endswith('.md'):
        return False, "仅支持Markdown文件（.md）"
    
    # 3. 检查文件可读性
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            f.read(100)  # 读取前100字符测试
    except Exception as e:
        return False, f"文件无法读取：{str(e)}"
    
    return True, file_path
```

### 平台验证
```python
def validate_platforms(platforms):
    """验证平台列表"""
    supported = ['微信公众号', '小红书', 'X/Twitter', 'B站']
    
    invalid = [p for p in platforms if p not in supported]
    if invalid:
        return False, f"不支持的平台：{', '.join(invalid)}"
    
    return True, platforms
```

## 场景确认流程

### 高置信度（>80%）
直接执行，无需确认：
```
✓ 场景识别：A1 - 采集并发布
✓ 参数收集：URL已获取，平台已确定
→ 开始执行...
```

### 中置信度（50-80%）
简要确认：
```
场景识别：A1 - 采集并发布
确认参数：
- URL: https://example.com/article
- 平台: 微信公众号

是否正确？（是/否/调整）
```

### 低置信度（<50%）
详细确认：
```
无法确定场景，请选择：

1. A1: 采集网页并发布到平台
2. A2: 采集网页并配图
3. B1: 热点文章生成
4. C1: 文章配图
5. 其他（请描述）

请输入选项编号或描述需求：
```

## 错误处理

### 场景识别失败
```python
if scenario == 'UNKNOWN':
    # 1. 展示可用场景列表
    show_available_scenarios()
    
    # 2. 询问用户选择或描述
    user_choice = ask_user_choice()
    
    # 3. 重新识别或手动指定
    scenario = manual_select_scenario(user_choice)
```

### 参数缺失
```python
if has_missing_params(scenario, params):
    # 1. 列出缺失参数
    missing = get_missing_params(scenario, params)
    
    # 2. 逐个询问
    for param in missing:
        value = ask_user_param(param)
        params[param] = value
    
    # 3. 验证参数
    validate_all_params(params)
```

### 参数无效
```python
if not validate_params(params):
    # 1. 报告无效参数
    invalid = get_invalid_params(params)
    
    # 2. 说明错误原因
    explain_errors(invalid)
    
    # 3. 请求重新输入
    for param in invalid:
        value = ask_user_param(param)
        params[param] = value
```

## 智能体实现指南

### 场景识别代码框架
```python
def identify_scenario(user_input):
    """
    智能体场景识别主函数
    """
    # 1. 提取关键信息
    url = extract_url(user_input)
    keyword = extract_keyword(user_input)
    file_path = extract_file_path(user_input)
    platforms = extract_platforms(user_input)
    
    # 2. 识别动作意图
    actions = {
        '采集': any(word in user_input for word in ['采集', '抓取', '获取']),
        '配图': any(word in user_input for word in ['配图', '插图', '加图']),
        '小红书': any(word in user_input for word in ['小红书', 'XHS', 'RedNote']),
        '发布': any(word in user_input for word in ['发布', '推送', '上传']),
        '热点': any(word in user_input for word in ['热点', '爆款', '话题'])
    }
    
    # 3. 场景匹配（按优先级）
    # 热点场景
    if actions['热点']:
        if actions['小红书']:
            return 'B2', {'keyword': keyword}
        elif len(platforms) > 1:
            return 'B3', {'keyword': keyword, 'platforms': platforms}
        else:
            return 'B1', {'keyword': keyword}
    
    # 采集场景
    if url:
        if actions['发布']:
            return 'A1', {'url': url, 'platforms': platforms}
        elif actions['配图']:
            return 'A2', {'url': url}
        elif actions['小红书']:
            return 'A3', {'url': url}
        else:
            return 'D1', {'url': url}
    
    # 优化场景
    if file_path:
        if actions['配图']:
            return 'C1', {'file': file_path}
        elif actions['小红书']:
            return 'C2', {'file': file_path}
        elif actions['发布']:
            return 'C3', {'file': file_path, 'platforms': platforms}
    
    # 单一功能
    if actions['配图'] and not (url or file_path):
        return 'D2', {}
    if actions['小红书'] and not (url or file_path):
        return 'D3', {}
    if actions['发布'] and not (url or file_path):
        return 'D4', {'platforms': platforms}
    
    # 无法识别
    return 'UNKNOWN', {}
```

### 参数收集代码框架
```python
def collect_params(scenario, initial_params):
    """
    智能体参数收集主函数
    """
    # 1. 获取场景所需参数
    required_params = get_required_params(scenario)
    
    # 2. 检查缺失参数
    missing = [p for p in required_params if p not in initial_params]
    
    # 3. 逐个收集
    for param in missing:
        # 询问用户
        prompt = get_param_prompt(param)
        value = ask_user(prompt)
        
        # 验证参数
        valid, result = validate_param(param, value)
        if not valid:
            print(f"参数无效：{result}")
            continue
        
        initial_params[param] = result
    
    return initial_params
```

## 总结

场景识别是智能内容创作系统的核心功能，通过：
1. **关键信息提取**：URL、关键词、文件、平台
2. **动作意图识别**：采集、配图、小红书、发布、热点
3. **场景匹配规则**：优先级决策树
4. **参数验证**：确保参数有效性
5. **确认流程**：根据置信度决定是否确认

实现智能化的场景识别和参数收集，让用户用自然语言描述需求即可完成复杂任务。
