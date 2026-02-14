# HTML排版完整指南

## 目录
- [排版原则](#排版原则)
- [基础结构](#基础结构)
- [标题与基础信息](#标题与基础信息)
- [文章结构分层](#文章结构分层)
- [关键内容局部划线](#关键内容局部划线)
- [颜色规范](#颜色规范)
- [图片插入](#图片插入)
- [标签与话题](#标签与话题)
- [秀米模板适配](#秀米模板适配)
- [完整示例](#完整示例)
- [常见问题](#常见问题)

## 排版原则

### 核心原则
1. **结构分层**：清晰的层级结构（一、二、三级）
2. **局部划线**：仅对关键短语/核心信息划线，不整句/整段高亮
3. **浅色调**：使用浅色背景，不遮挡文字，模拟手写划线质感
4. **重点突出**：划线内容不超过全文20%，确保清晰不花哨
5. **可预览可复制**：生成完整的HTML格式，可直接在浏览器预览和复制使用
6. **纯净输出**：不包含作者信息、制作信息等额外内容

### 模拟人工划线
- 划线对象：工具名、插件名、操作指令、核心功能、关键参数
- 不划线对象：整句、整段、过渡句、衔接性文字

### 输出要求
- HTML格式完整，可直接在浏览器中打开预览
- 可直接复制HTML代码到公众号后台使用
- 不包含作者名称、作者介绍
- 不包含"COZE制作"、"AI助手"等制作信息

## 基础结构

### HTML模板框架
```html
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        /* 基础样式 */
        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "PingFang SC", "Hiragino Sans GB", "Microsoft YaHei", sans-serif;
            line-height: 1.8;
            color: #333;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
        }
        
        /* 划线样式 */
        mark {
            padding: 2px 4px;
            border-radius: 3px;
            font-weight: 500;
        }
        
        /* 颜色规范（见下文） */
        .highlight-yellow { background-color: #fff3cd; }
        .highlight-green { background-color: #d4edda; }
        .highlight-red { background-color: #f8d7da; }
        .highlight-blue { background-color: #e8f4f8; }
        .highlight-purple { background-color: #f3e5f5; }
        .highlight-orange { background-color: #fff8e1; }
    </style>
</head>
<body>
    <!-- 文章内容 -->
</body>
</html>
```

## 标题与基础信息

### 主标题
```html
<h1 style="text-align: center; font-size: 28px; margin-bottom: 20px; color: #2c3e50;">
    文章标题
</h1>
```

### ⚠️ 不包含作者信息
**重要**：默认模式下**不包含**以下内容：
- 作者名称
- 作者介绍
- 发布日期
- 制作信息（如"COZE制作"、"AI助手"等）

### 摘要/引言（可选）
```html
<div style="background-color: #f8f9fa; padding: 20px; border-left: 4px solid #3498db; margin-bottom: 30px; border-radius: 4px;">
    <p style="margin: 0; color: #555;">这是文章的摘要或引言部分...</p>
</div>
```

**注意**：如果需要摘要，直接开始内容，不要添加"摘要"等字样。

## 文章结构分层

### 一级标题
```html
<h2 style="font-size: 24px; margin-top: 40px; margin-bottom: 20px; color: #2c3e50; border-bottom: 2px solid #3498db; padding-bottom: 10px;">
    一、章节标题
</h2>
```

### 二级标题
```html
<h3 style="font-size: 20px; margin-top: 30px; margin-bottom: 15px; color: #34495e;">
    1.1 子章节标题
</h3>
```

### 三级标题
```html
<h4 style="font-size: 18px; margin-top: 25px; margin-bottom: 12px; color: #57606f; font-weight: 600;">
    核心要点
</h4>
```

## 关键内容局部划线

### 划线原则
- ✅ 对象：专有名词、工具名、功能名、关键参数、核心观点
- ❌ 不划：整句、整段、过渡句、解释性文字

### 使用示例
```html
<p>
    使用 <mark class="highlight-yellow">ChatGPT</mark> 可以快速生成高质量内容，通过调整 <mark class="highlight-blue">temperature</mark> 参数控制输出的随机性。在 <mark class="highlight-green">prompt engineering</mark> 中，明确的指令是关键。
</p>
```

### 划线密度控制
- 全文划线不超过20%
- 每段最多2-3处划线
- 避免相邻文字连续划线

## 颜色规范

### 推荐配色
| 颜色 | class名 | 使用场景 | CSS值 |
|------|---------|----------|-------|
| 浅黄 | highlight-yellow | 默认高亮 | #fff3cd |
| 浅绿 | highlight-green | 成功、正面 | #d4edda |
| 浅红 | highlight-red | 警告、重要 | #f8d7da |
| 浅蓝 | highlight-blue | 信息、中性 | #e8f4f8 |
| 浅紫 | highlight-purple | 深度思考 | #f3e5f5 |
| 浅橙 | highlight-orange | 提示、补充 | #fff8e1 |

### 颜色CSS定义
```css
mark.highlight-yellow {
    background-color: #fff3cd;
    padding: 2px 4px;
    border-radius: 3px;
    font-weight: 500;
}

mark.highlight-green {
    background-color: #d4edda;
    padding: 2px 4px;
    border-radius: 3px;
    font-weight: 500;
}

mark.highlight-red {
    background-color: #f8d7da;
    padding: 2px 4px;
    border-radius: 3px;
    font-weight: 500;
}

mark.highlight-blue {
    background-color: #e8f4f8;
    padding: 2px 4px;
    border-radius: 3px;
    font-weight: 500;
}

mark.highlight-purple {
    background-color: #f3e5f5;
    padding: 2px 4px;
    border-radius: 3px;
    font-weight: 500;
}

mark.highlight-orange {
    background-color: #fff8e1;
    padding: 2px 4px;
    border-radius: 3px;
    font-weight: 500;
}
```

## 图片插入

### 单张图片
```html
<div style="text-align: center; margin: 30px 0;">
    <img src="图片URL" alt="图片描述" style="max-width: 100%; height: auto; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
    <p style="color: #7f8c8d; font-size: 14px; margin-top: 10px;">图1：图片说明</p>
</div>
```

### 多张图片并排
```html
<div style="display: flex; justify-content: space-between; gap: 20px; margin: 30px 0;">
    <div style="flex: 1; text-align: center;">
        <img src="图片1URL" alt="图片1" style="width: 100%; border-radius: 8px;">
        <p style="color: #7f8c8d; font-size: 14px; margin-top: 10px;">图1</p>
    </div>
    <div style="flex: 1; text-align: center;">
        <img src="图片2URL" alt="图片2" style="width: 100%; border-radius: 8px;">
        <p style="color: #7f8c8d; font-size: 14px; margin-top: 10px;">图2</p>
    </div>
</div>
```

## 标签与话题

### 话题标签
```html
<div style="margin-top: 40px; padding-top: 20px; border-top: 1px solid #e0e0e0;">
    <span style="display: inline-block; background-color: #3498db; color: white; padding: 5px 12px; border-radius: 15px; margin-right: 10px; font-size: 14px;">
        #人工智能
    </span>
    <span style="display: inline-block; background-color: #2ecc71; color: white; padding: 5px 12px; border-radius: 15px; margin-right: 10px; font-size: 14px;">
        #效率工具
    </span>
    <span style="display: inline-block; background-color: #e74c3c; color: white; padding: 5px 12px; border-radius: 15px; margin-right: 10px; font-size: 14px;">
        #AIGC
    </span>
</div>
```

## 秀米模板适配

### 使用秀米模板的优势
- 丰富的预设模板
- 专业的排版效果
- 易于编辑和调整

### 适配方式

#### 方式一：手动粘贴到秀米
1. 在秀米编辑器中选择合适的模板
2. 将生成的HTML内容复制粘贴
3. 微调样式和布局
4. 一键同步到公众号

#### 方式二：生成符合秀米结构的HTML
```html
<div style="background-color: #ffffff; padding: 20px;">
    <!-- 使用section块 -->
    <section style="margin-bottom: 30px;">
        <h2 style="font-size: 24px; color: #2c3e50; margin-bottom: 15px;">章节标题</h2>
        <p style="line-height: 1.8; color: #333;">
            这是段落内容，可以在秀米中进一步调整样式。
            <mark class="highlight-yellow">高亮文本</mark>
        </p>
    </section>
</div>
```

#### 方式三：使用秀米组件
```html
<!-- 引用组件 -->
<div style="background-color: #f0f4f8; border-left: 4px solid #3498db; padding: 15px; margin: 20px 0; border-radius: 4px;">
    <p style="margin: 0; color: #555;">
        <strong>💡 提示：</strong>这是提示框组件内容
    </p>
</div>

<!-- 重点卡片 -->
<div style="background-color: #fff3cd; border: 1px solid #ffeaa7; padding: 20px; margin: 20px 0; border-radius: 8px;">
    <h3 style="margin-top: 0; color: #d68910;">🎯 重点</h3>
    <p style="margin-bottom: 0; color: #7d6608;">这是重点卡片内容</p>
</div>
```

### 推荐的秀米模板类型
- 简约风格模板（适合技术类文章）
- 清新风格模板（适合生活类文章）
- 商务风格模板（适合行业分析）

## 完整示例

```html
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "PingFang SC", "Hiragino Sans GB", "Microsoft YaHei", sans-serif;
            line-height: 1.8;
            color: #333;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
        }
        
        h2 {
            font-size: 24px;
            margin-top: 40px;
            margin-bottom: 20px;
            color: #2c3e50;
            border-bottom: 2px solid #3498db;
            padding-bottom: 10px;
        }
        
        h3 {
            font-size: 20px;
            margin-top: 30px;
            margin-bottom: 15px;
            color: #34495e;
        }
        
        mark {
            padding: 2px 4px;
            border-radius: 3px;
            font-weight: 500;
        }
        
        .highlight-yellow { background-color: #fff3cd; }
        .highlight-green { background-color: #d4edda; }
        .highlight-red { background-color: #f8d7da; }
        .highlight-blue { background-color: #e8f4f8; }
        .highlight-purple { background-color: #f3e5f5; }
        .highlight-orange { background-color: #fff8e1; }
    </style>
</head>
<body>
    <h1 style="text-align: center; font-size: 28px; margin-bottom: 20px; color: #2c3e50;">
        如何使用AI提升写作效率
    </h1>
    
    <!-- 注意：不包含作者信息、日期等 -->
    
    <div style="background-color: #f8f9fa; padding: 20px; border-left: 4px solid #3498db; margin-bottom: 30px; border-radius: 4px;">
        <p style="margin: 0; color: #555;">
            在信息爆炸的时代，如何高效地创作内容成为每个创作者面临的重要挑战。本文将介绍如何利用AI工具提升写作效率。
        </p>
    </div>
    
    <h2>一、AI写作工具推荐</h2>
    
    <h3>1.1 ChatGPT</h3>
    <p>
        <mark class="highlight-yellow">ChatGPT</mark> 是目前最流行的AI写作工具之一。它可以根据用户的输入生成各种类型的内容，包括文章、邮件、代码等。通过调整 <mark class="highlight-blue">temperature</mark> 参数，可以控制输出的随机性和创造性。
    </p>
    
    <h3>1.2 Claude</h3>
    <p>
        <mark class="highlight-green">Claude</mark> 是另一款强大的AI助手，它在处理长文本和理解复杂指令方面表现出色。对于需要 <mark class="highlight-purple">深度分析</mark> 和 <mark class="highlight-red">逻辑推理</mark> 的任务，Claude可能是更好的选择。
    </p>
    
    <h2>二、写作技巧</h2>
    
    <div style="text-align: center; margin: 30px 0;">
        <img src="https://images.unsplash.com/photo-1455390582262-044cdead277a?w=800" alt="写作" style="max-width: 100%; height: auto; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
        <p style="color: #7f8c8d; font-size: 14px; margin-top: 10px;">图1：高效写作的关键</p>
    </div>
    
    <p>
        使用AI工具时，明确的目标和清晰的指令是关键。通过 <mark class="highlight-orange">Prompt Engineering</mark>，可以让AI生成更符合需求的内容。
    </p>
    
    <div style="margin-top: 40px; padding-top: 20px; border-top: 1px solid #e0e0e0;">
        <span style="display: inline-block; background-color: #3498db; color: white; padding: 5px 12px; border-radius: 15px; margin-right: 10px; font-size: 14px;">
            #AI写作
        </span>
        <span style="display: inline-block; background-color: #2ecc71; color: white; padding: 5px 12px; border-radius: 15px; margin-right: 10px; font-size: 14px;">
            #效率提升
        </span>
        <span style="display: inline-block; background-color: #e74c3c; color: white; padding: 5px 12px; border-radius: 15px; margin-right: 10px; font-size: 14px;">
            #ChatGPT
        </span>
    </div>
</body>
</html>
```

## 常见问题

### Q1: 如何确保划线不超过20%？
统计mark标签的数量和覆盖的字符数，确保不超过全文的20%。可以使用文本编辑器的查找功能统计mark数量。

### Q2: 颜色如何选择？
根据内容的重要性选择颜色：
- 黄色：默认高亮
- 绿色：正面、成功信息
- 红色：警告、重要信息
- 蓝色：中性信息
- 紫色：深度思考内容
- 橙色：补充说明

### Q3: 如何使用秀米模板？
1. 打开秀米编辑器
2. 选择合适的模板
3. 将生成的HTML复制粘贴
4. 微调样式和布局

### Q4: 图片如何处理？
- 使用Unsplash API搜索高质量图片
- 确保图片符合2.35:1的封面比例
- 在HTML中使用img标签插入

### Q5: 如何生成HTML？
可以使用智能体根据内容生成符合本指南规范的HTML代码，包括：
- 结构化标题
- 局部划线
- 图片插入
- 标签添加
