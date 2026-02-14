# 公众号内容模板

## 目录
- [文章结构](#文章结构)
- [HTML格式规范](#html格式规范)
- [内容示例](#内容示例)
- [排版建议](#排版建议)

## 概览
本文档提供微信公众号文章的标准格式模板，确保内容在公众号中显示美观、易读。

## 文章结构

### 标准结构
```
标题
├── 引导语（1-2段）
├── 核心观点（3-5段）
│   ├── 观点一 + 案例
│   ├── 观点二 + 数据
│   └── 观点三 + 分析
├── 图片（2-3张）
├── 总结升华（1-2段）
└── 互动引导（可选）
```

### 字数建议
- 短篇：800-1200字
- 中篇：1200-1800字
- 长篇：1800-2500字

## HTML格式规范

### 基础样式
```html
<section style="padding: 20px; background-color: #fff;">
  
  <!-- 段落 -->
  <p style="font-size: 16px; line-height: 1.8; color: #333; margin-bottom: 15px;">
    这里是段落内容...
  </p>
  
  <!-- 标题 -->
  <h2 style="font-size: 20px; color: #333; font-weight: bold; margin: 25px 0 15px;">
    二级标题
  </h2>
  
  <h3 style="font-size: 18px; color: #333; font-weight: bold; margin: 20px 0 10px;">
    三级标题
  </h3>
  
  <!-- 图片 -->
  <img src="图片URL" style="width: 100%; display: block; margin: 15px 0;" alt="图片描述">
  
  <!-- 引用 -->
  <div style="background-color: #f7f7f7; padding: 15px; margin: 15px 0; border-left: 4px solid #4CAF50;">
    <p style="font-size: 15px; line-height: 1.6; color: #666; margin: 0;">
      这里是引用内容...
    </p>
  </div>
  
</section>
```

## 内容示例

### AI技术文章模板

```html
<section style="padding: 20px;">
  <!-- 引导语 -->
  <p style="font-size: 16px; line-height: 1.8; color: #333; margin-bottom: 15px;">
    随着AI技术的快速发展，我们正处在一个前所未有的变革时代。从大模型的崛起，到各类AI应用的落地，这场技术革命正在深刻改变着我们的工作和生活方式。
  </p>
  
  <p style="font-size: 16px; line-height: 1.8; color: #333; margin-bottom: 15px;">
    今天，我们就来聊聊最近最火的AI话题，看看这些技术到底能给我们带来什么。
  </p>
  
  <!-- 核心观点1 -->
  <h2 style="font-size: 20px; color: #333; font-weight: bold; margin: 25px 0 15px;">
    一、技术突破：AI能力的新边界
  </h2>
  
  <p style="font-size: 16px; line-height: 1.8; color: #333; margin-bottom: 15px;">
    最近发布的GPT-5传闻再次引爆了整个AI领域。虽然官方尚未正式公布，但从各种泄露的信息来看，这次更新将会带来质的飞跃。
  </p>
  
  <!-- 配图 -->
  <img src="https://example.com/ai-image.jpg" style="width: 100%; display: block; margin: 15px 0;" alt="AI技术示意图">
  
  <p style="font-size: 16px; line-height: 1.8; color: #333; margin-bottom: 15px;">
    据业内人士透露，新模型在推理能力、多模态理解以及上下文记忆方面都有显著提升。这意味着AI将能够更好地理解复杂任务，提供更精准的解决方案。
  </p>
  
  <!-- 核心观点2 -->
  <h2 style="font-size: 20px; color: #333; font-weight: bold; margin: 25px 0 15px;">
    二、应用场景：从理论到实践
  </h2>
  
  <p style="font-size: 16px; line-height: 1.8; color: #333; margin-bottom: 15px;">
    技术的最终价值在于应用。目前，AI已经在多个领域展现出强大的实力：
  </p>
  
  <!-- 列表 -->
  <div style="background-color: #f9f9f9; padding: 15px; margin: 15px 0; border-radius: 5px;">
    <p style="font-size: 15px; line-height: 1.8; color: #666; margin: 0 0 10px;">
      🎯 <strong>编程辅助</strong>：AI编程助手可以大幅提升开发效率
    </p>
    <p style="font-size: 15px; line-height: 1.8; color: #666; margin: 0 0 10px;">
      📊 <strong>数据分析</strong>：智能分析工具让数据洞察更简单
    </p>
    <p style="font-size: 15px; line-height: 1.8; color: #666; margin: 0 0 10px;">
      ✍️ <strong>内容创作</strong>：AI写作助手帮助创作者突破瓶颈
    </p>
    <p style="font-size: 15px; line-height: 1.8; color: #666; margin: 0;">
      🤖 <strong>自动化</strong>：智能机器人接管重复性工作
    </p>
  </div>
  
  <!-- 核心观点3 -->
  <h2 style="font-size: 20px; color: #333; font-weight: bold; margin: 25px 0 15px;">
    三、未来展望：挑战与机遇并存
  </h2>
  
  <p style="font-size: 16px; line-height: 1.8; color: #333; margin-bottom: 15px;">
    尽管AI技术发展迅猛，但我们也不能忽视它带来的挑战。就业影响、数据安全、伦理问题等都需要我们认真思考和应对。
  </p>
  
  <div style="background-color: #fff3e0; padding: 15px; margin: 15px 0; border-left: 4px solid #ff9800;">
    <p style="font-size: 15px; line-height: 1.6; color: #666; margin: 0;">
      💡 <strong>小贴士</strong>：拥抱AI不是要被替代，而是要学会与AI协作，提升自己的核心竞争力。
    </p>
  </div>
  
  <p style="font-size: 16px; line-height: 1.8; color: #333; margin-bottom: 15px;">
    对于个人而言，最重要的是保持学习的心态，不断提升自己的技能，找到自己与AI的最佳结合点。
  </p>
  
  <!-- 总结 -->
  <h2 style="font-size: 20px; color: #333; font-weight: bold; margin: 25px 0 15px;">
    结语
  </h2>
  
  <p style="font-size: 16px; line-height: 1.8; color: #333; margin-bottom: 15px;">
    AI时代已经到来，无论是拥抱还是抗拒，变革都在发生。让我们以开放的心态迎接这个新时代，用智慧和勇气探索未知，创造属于自己的价值。
  </p>
  
  <p style="font-size: 16px; line-height: 1.8; color: #333; margin-bottom: 15px;">
    你对AI有什么看法？欢迎在评论区分享你的观点！
  </p>
  
  <!-- 分割线 -->
  <div style="border-top: 1px solid #e0e0e0; margin: 25px 0;"></div>
  
  <!-- 底部信息 -->
  <p style="font-size: 14px; color: #999; text-align: center;">
    本文原创，转载请注明出处
  </p>
</section>
```

### 商业财经文章模板

```html
<section style="padding: 20px;">
  <!-- 引导语 -->
  <p style="font-size: 16px; line-height: 1.8; color: #333; margin-bottom: 15px;">
    在当前的经济环境下，如何在不确定性中找到确定性，是每个投资者都在思考的问题。
  </p>
  
  <!-- 数据展示 -->
  <div style="background-color: #e3f2fd; padding: 15px; margin: 15px 0; border-radius: 5px;">
    <p style="font-size: 15px; line-height: 1.6; color: #1976d2; margin: 0; font-weight: bold;">
      📈 市场数据
    </p>
    <p style="font-size: 15px; line-height: 1.6; color: #666; margin: 5px 0 0;">
      某指数近3个月涨幅：+15.2%
    </p>
  </div>
  
  <!-- 核心分析 -->
  <h2 style="font-size: 20px; color: #333; font-weight: bold; margin: 25px 0 15px;">
    投资逻辑分析
  </h2>
  
  <p style="font-size: 16px; line-height: 1.8; color: #333; margin-bottom: 15px;">
    从基本面来看，该行业正处于快速发展期，多项指标显示其具有长期投资价值...
  </p>
  
  <!-- 风险提示 -->
  <div style="background-color: #ffebee; padding: 15px; margin: 15px 0; border-left: 4px solid #f44336;">
    <p style="font-size: 15px; line-height: 1.6; color: #c62828; margin: 0; font-weight: bold;">
      ⚠️ 风险提示
    </p>
    <p style="font-size: 15px; line-height: 1.6; color: #666; margin: 5px 0 0;">
      投资有风险，入市需谨慎。本文仅供参考，不构成投资建议。
    </p>
  </div>
</section>
```

## 排版建议

### 文字规范
- 正文字号：16px（微信最佳阅读体验）
- 标题字号：18-22px
- 行高：1.6-1.8
- 段落间距：15-20px

### 颜色建议
- 正文：#333333 或 #666666
- 标题：#333333
- 链接：#1AAD19（微信绿）
- 引用背景：#f7f7f7
- 重点标注：#ff6600

### 图片规范
- 宽度：100%（自适应）
- 格式：JPG、PNG
- 大小：建议每张图片小于2MB
- 位置：放在相关文字下方

### 互动引导
在文章末尾添加互动引导，提升读者参与度：
```html
<p style="font-size: 16px; line-height: 1.8; color: #333; margin-bottom: 15px;">
  💬 你对这个话题怎么看？欢迎在评论区分享你的观点！
</p>
```

### 版权声明
```html
<div style="border-top: 1px solid #e0e0e0; margin: 25px 0; padding-top: 15px;">
  <p style="font-size: 14px; color: #999; text-align: center; margin: 0;">
    本文原创，未经授权不得转载
  </p>
</div>
```

## 注意事项

1. **内容质量**：
   - 确保内容原创或有明确引用来源
   - 避免敏感话题和违规内容

2. **排版体验**：
   - 保持段落清晰，避免大段文字堆砌
   - 合理使用图片、引用、列表等元素

3. **移动端适配**：
   - 使用百分比宽度，确保在不同设备上正常显示
   - 避免固定宽度导致移动端显示异常

4. **加载速度**：
   - 图片大小适当，避免影响加载速度
   - 避免使用过多外部资源
