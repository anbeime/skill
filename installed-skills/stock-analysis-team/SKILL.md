---
name: stock-analysis-team
description: 提供股票多维度分析团队协同研究能力；当用户需要股票分析、投资决策支持、风险评估、市场复盘或回测验证时使用
dependency:
  python:
    - yfinance>=0.2.28
    - pandas>=2.0.0
    - numpy>=1.24.0
    - ta>=0.11.0
    - matplotlib>=3.7.0
    - requests>=2.31.0
    - beautifulsoup4>=4.12.0
    - jinja2>=3.1.0
    - plotly>=5.18.0
---

# 股票分析团队

## 任务目标
- 本 Skill 用于：通过多角色团队协同完成股票的深度分析和投资决策支持
- 能力包含：基本面分析、技术分析、情绪分析、新闻分析、风险评估、市场策略制定、回测验证
- 触发条件：用户提供股票代码、上传股票截图、请求市场复盘、需要投资建议或风险评估时

## 前置准备
- 依赖说明：脚本所需的依赖包及版本
  ```
  yfinance>=0.2.28
  pandas>=2.0.0
  numpy>=1.24.0
  ta>=0.11.0
  ```
- 非标准文件/文件夹准备：无

## 操作步骤
- 标准流程：
  1. 股票代码识别
     - 如果用户提供图片：智能体使用图像识别能力提取股票代码
     - 如果用户提供文本：智能体识别股票代码（支持A股如 600519.SH，美股如 AAPL）
  2. 调用数据获取脚本
     - 执行 `python scripts/market_data_fetcher.py --symbol <股票代码> --market <cn|us>` 获取实时行情、技术指标和历史数据
  3. 分析师团队协同工作
     - 基本面分析师：根据 [analysis-framework.md](references/analysis-framework.md) 中的基本面分析框架，评估财务健康状况
     - 情绪分析师：分析市场情绪和舆情，给出情绪评分
     - 新闻分析师：分析相关新闻和宏观经济影响
     - 技术分析师：根据技术指标（MA、MACD、RSI）判断趋势和买卖点
  4. 研究员团队辩论
     - 看多研究员：基于分析师报告列举上涨理由
     - 看空研究员：基于分析师报告列举下跌风险
     - 通过结构化辩论，平衡收益与风险
  5. 交易员团队决策
     - 综合分析师和研究员报告，制定交易计划
     - 确定买入/卖出/观望建议
     - 给出具体的价格点位和仓位建议
  6. 风控与执行团队评估
     - 根据 [risk-scoring-criteria.md](references/risk-scoring-criteria.md) 评估投资风险等级（1-10分）
     - 1-3分：低风险；4-6分：中等风险；7-10分：高风险
     - 投资组合经理批准或拒绝交易提议
  7. 市场策略制定
     - 如果是A股：根据 [market-strategy.md](references/market-strategy.md) 中的三段式复盘策略，输出进攻/均衡/防守计划
     - 如果是美股：根据 Regime Strategy，输出 risk-on/neutral/risk-off 计划
  8. 生成HTML格式研究报告
     - 调用图表生成脚本：`python scripts/chart_generator.py --symbol <股票代码> --market <cn|us> --chart-type all --output-dir ./charts`
     - 智能体组织报告数据，生成JSON格式数据文件
     - 调用HTML报告生成脚本：`python scripts/html_report_generator.py --data report_data.json --charts-dir ./charts --output report.html`
     - 生成的HTML报告包含以下内容：
       - **报告封面**：渐变背景 + 公司名称 + 股票代码 + 分析日期 + 风险等级徽章
       - **核心结论**：渐变卡片 + 投资建议 + 预期收益 + 最大风险
       - **公司概览**：信息卡片 + 财务指标表格 + 业务亮点
       - **技术分析图表**：响应式网格布局 + 4种技术图表（股价走势、K线、MACD、RSI）
       - **基本面分析**：财务健康度评分表 + 财务数据对比表
       - **情绪与新闻分析**：情绪指标表 + 情绪趋势
       - **风险评估**：风险评分进度条 + 各维度评分卡片
       - **投资建议**：买卖点位表格（带颜色标识）
       - **免责声明**：黄色警告框
  9. AI回测验证（可选）
     - 如果用户要求验证历史准确率：根据 [backtesting-guidelines.md](references/backtesting-guidelines.md) 的方法，评估方向胜率和止盈止损命中率

- 可选分支：
  - 当用户请求市场复盘：执行步骤1-7，跳过个股分析，提供大盘概览和板块分析
  - 当用户上传股票截图：执行步骤1识别代码，然后进入标准流程
  - 当用户选择 cn/us/both：根据选择分析对应市场的股票

## 资源索引
- 必要脚本：
  - 见 [scripts/market_data_fetcher.py](scripts/market_data_fetcher.py)（用途与参数：获取股票行情数据、技术指标和历史数据）
  - 见 [scripts/chart_generator.py](scripts/chart_generator.py)（用途与参数：生成股价走势图、K线图、MACD图、RSI图等静态可视化图表）
  - 见 [scripts/image_fetcher.py](scripts/image_fetcher.py)（用途与参数：获取公司Logo、产品图片等视觉素材）
  - 见 [scripts/html_report_generator.py](scripts/html_report_generator.py)（用途与参数：生成基础HTML格式报告）
  - 见 [scripts/enhanced_html_report_generator.py](scripts/enhanced_html_report_generator.py)（用途与参数：生成增强版HTML报告，包含交互式图表、图片展示、趋势图等）
- 领域参考：
  - 见 [references/analysis-framework.md](references/analysis-framework.md)（何时读取：分析师团队执行分析时）
  - 见 [references/market-strategy.md](references/market-strategy.md)（何时读取：制定市场策略时）
  - 见 [references/risk-scoring-criteria.md](references/risk-scoring-criteria.md)（何时读取：风控团队评估风险时）
  - 见 [references/backtesting-guidelines.md](references/backtesting-guidelines.md)（何时读取：执行回测验证时）
  - 见 [references/chart-guide.md](references/chart-guide.md)（何时读取：生成和使用图表时）
  - 见 [references/html-template.html](references/html-template.html)（何时读取：生成HTML报告时作为参考）

## 注意事项
- 所有投资建议仅供研究参考，不构成投资建议，必须在报告中明确标注免责声明
- 风险评分必须基于多维度综合判断，避免单一指标主导
- 市场策略制定需要考虑市场周期和宏观经济环境
- 回测验证需要足够的历史数据支持，避免过拟合

## 使用示例

### 示例1：单只股票深度分析
```bash
# 用户输入：分析贵州茅台 600519.SH
# 智能体执行：
# 1. 识别股票代码 600519.SH
# 2. 调用脚本获取数据
python scripts/market_data_fetcher.py --symbol 600519.SH --market cn
# 3. 组织各团队协同分析
# 4. 生成包含风险评分的研究报告
```

### 示例2：图片识别+分析
```bash
# 用户上传股票截图
# 智能体执行：
# 1. 使用图像识别提取股票代码（如 AAPL）
# 2. 调用脚本获取数据
python scripts/market_data_fetcher.py --symbol AAPL --market us
# 3. 执行完整分析流程
# 4. 输出研究报告
```

### 示例3：A股市场复盘
```bash
# 用户输入：今天A股市场如何？给个复盘
# 智能体执行：
# 1. 调用脚本获取大盘数据
python scripts/market_data_fetcher.py --symbol 000001.SH --market cn
# 2. 分析市场整体表现和板块涨跌
# 3. 根据三段式复盘策略输出：进攻/均衡/防守计划
# 4. 提供市场操作建议
```
