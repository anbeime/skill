# 图表生成与使用指南

## 目录
- [图表类型](#图表类型)
- [图表调用方法](#图表调用方法)
- [图表样式规范](#图表样式规范)
- [图表嵌入方式](#图表嵌入方式)
- [常见问题](#常见问题)

## 图表类型

### 1. 股价走势折线图 (Price Trend Chart)
**用途**：展示股票价格走势和移动平均线

**包含元素**：
- 收盘价折线
- MA5、MA20、MA60移动平均线
- 价格坐标轴
- 时间坐标轴
- 图例

**适用场景**：趋势分析、支撑阻力位判断

**示例**：
```bash
python scripts/chart_generator.py --symbol AAPL --market us --chart-type price --output-dir ./charts
```

### 2. K线图 (Candlestick Chart)
**用途**：展示价格的开盘、收盘、最高、最低信息

**包含元素**：
- K线（蜡烛图）：红色表示上涨，绿色表示下跌
- 影线：表示最高价和最低价
- 实体：表示开盘价和收盘价
- 成交量柱状图（下方）

**适用场景**：日内交易、波段操作

**示例**：
```bash
python scripts/chart_generator.py --symbol 600519.SH --market cn --chart-type candlestick --output-dir ./charts
```

### 3. MACD指标图 (MACD Chart)
**用途**：展示MACD指标及其金叉死叉信号

**包含元素**：
- DIF线（快线）
- DEA线（慢线）
- MACD柱状图（红柱表示上涨，绿柱表示下跌）
- 零轴参考线

**适用场景**：趋势转折判断、买卖时机把握

**示例**：
```bash
python scripts/chart_generator.py --symbol AAPL --market us --chart-type macd --output-dir ./charts
```

### 4. RSI指标图 (RSI Chart)
**用途**：展示RSI相对强弱指标和超买超卖信号

**包含元素**：
- RSI曲线
- 超买线（70）
- 超卖线（30）
- 中轴线（50）
- 超买超卖区域填充

**适用场景**：超买超卖判断、反转信号识别

**示例**：
```bash
python scripts/chart_generator.py --symbol 600519.SH --market cn --chart-type rsi --output-dir ./charts
```

### 5. 综合仪表盘 (Summary Dashboard)
**用途**：一次性生成所有关键图表

**包含图表**：
- 股价走势折线图
- K线图
- MACD指标图
- RSI指标图

**适用场景**：完整技术分析报告

**示例**：
```bash
python scripts/chart_generator.py --symbol AAPL --market us --chart-type all --output-dir ./charts
```

## 图表调用方法

### 基本语法
```bash
python scripts/chart_generator.py \
  --symbol <股票代码> \
  --market <市场类型> \
  --chart-type <图表类型> \
  --period <时间周期> \
  --output-dir <输出目录>
```

### 参数说明

| 参数 | 必填 | 说明 | 可选值 |
|------|------|------|--------|
| --symbol | 是 | 股票代码 | 如：600519.SH, AAPL |
| --market | 是 | 市场类型 | cn（A股）, us（美股） |
| --chart-type | 否 | 图表类型 | price, candlestick, macd, rsi, all |
| --period | 否 | 时间周期 | 1mo, 3mo, 6mo, 1y, 2y, 5y |
| --output-dir | 否 | 输出目录 | 默认为当前目录 |

### 使用示例

**示例1：生成贵州茅台的所有图表**
```bash
python scripts/chart_generator.py \
  --symbol 600519.SH \
  --market cn \
  --chart-type all \
  --period 1y \
  --output-dir ./charts/moutai
```

**示例2：生成苹果公司的K线图**
```bash
python scripts/chart_generator.py \
  --symbol AAPL \
  --market us \
  --chart-type candlestick \
  --period 6mo \
  --output-dir ./charts/apple
```

**示例3：生成特斯拉的MACD图**
```bash
python scripts/chart_generator.py \
  --symbol TSLA \
  --market us \
  --chart-type macd \
  --period 3mo \
  --output-dir ./charts/tesla
```

## 图表样式规范

### 配色方案
图表采用统一的专业配色：

| 元素 | 颜色（HEX） | 说明 |
|------|-------------|------|
| 收盘价 | #2E86AB | 主蓝色 |
| MA5 | #F18F01 | 橙色 |
| MA20 | #C73E1D | 红色 |
| MA60 | #3B1F2B | 深紫色 |
| 上涨K线 | #00C853 | 绿色 |
| 下跌K线 | #D50000 | 红色 |
| DIF线 | #2196F3 | 蓝色 |
| DEA线 | #FF9800 | 橙色 |
| RSI线 | #9C27B0 | 紫色 |
| 超买区域 | #D50000 | 红色半透明 |
| 超卖区域 | #00C853 | 绿色半透明 |

### 图表尺寸
- 单个图表：12x6 英寸
- K线图：12x10 英寸（含成交量）
- MACD/RSI图：12x10 英寸（双图）
- DPI：150（清晰度适中）

### 字体规范
- 标题字体大小：16（加粗）
- 坐标轴标签字体大小：12
- 图例字体大小：默认
- 字体族：DejaVu Sans, Arial Unicode MS

## 图表嵌入方式

### Markdown报告嵌入
```markdown
## 技术分析图表

### 股价走势图
![股价走势](./charts/600519.SH_price_chart.png)

### K线图与成交量
![K线图](./charts/600519.SH_candlestick.png)
```

### HTML报告嵌入
```html
<div class="chart-section">
  <h3>股价走势图</h3>
  <img src="./charts/600519.SH_price_chart.png" alt="股价走势" width="100%">
</div>
```

### 图片路径规范
- 相对路径：`./charts/<symbol>_<chart_type>.png`
- 绝对路径：`/path/to/charts/<symbol>_<chart_type>.png`
- URL路径：`https://example.com/charts/<symbol>_<chart_type>.png`

## 常见问题

### Q1: 如何修改图表配色？
A: 编辑 `scripts/chart_generator.py` 中的颜色代码。

### Q2: 如何调整图表尺寸？
A: 修改 `figsize` 参数，例如 `figsize=(14, 8)`。

### Q3: 图表生成失败怎么办？
A: 检查：
1. 股票代码是否正确
2. 网络连接是否正常
3. 依赖包是否安装完整

### Q4: 如何添加自定义技术指标？
A: 在 `chart_generator.py` 中添加新的绘图函数。

### Q5: 图表支持中文吗？
A: 目前使用英文字体，如需中文支持需要配置中文字体。

### Q6: 如何批量生成多只股票的图表？
A: 编写脚本循环调用：
```bash
for symbol in 600519.SH 000001.SZ AAPL TSLA; do
  python scripts/chart_generator.py --symbol $symbol --market cn --chart-type all --output-dir ./charts/$symbol
done
```

## 图表输出示例

生成的图表文件命名格式：
```
<symbol>_price_chart.png       # 股价走势图
<symbol>_candlestick.png       # K线图
<symbol>_macd.png              # MACD图
<symbol>_rsi.png               # RSI图
```

示例：
```
600519.SH_price_chart.png
600519.SH_candlestick.png
600519.SH_macd.png
600519.SH_rsi.png
```

**注意**：图表为PNG格式，分辨率150DPI，适合在网页和报告中展示。
