---
name: ecommerce-full-pipeline
description: 电商运营在开展跨境电商或闲鱼捡漏业务时，若需解决选品难、上架繁琐等痛点，必用此技能！一键打通“爆品挖掘→1688采集→多平台上架→推广文案→短视频生成”全自动流水线，轻松实现端到端自动化，让开店运营效率翻倍。
version: 1.0.0
author: anbeime
tags:
  - ecommerce
  - scraping
  - marketing
  - video
  - automation
  - bargain
  - xianyu
  - 1688
  - trend
  - pipeline
---

# 跨境电商全链路自动化工具

## 任务目标

- 本技能用于：跨境电商从选品到推广的全流程自动化
- 能力包含：
  1. **1688 商品采集**：关键词搜索、详情抓取、图片下载、反爬回退（Mock 数据兜底）
  2. **智能数据清洗**：自动翻译标题、价格标准化、供应商评分、利润率计算、批量过滤
  3. **多平台上架**：一键生成微信小店/Shopify/TikTok 上架模板，支持 CSV/Excel/JSON 导出
  4. **推广方案生成**：自动关键词生成、竞品分析、广告文案撰写、预算规划
  5. **短视频创作**：基于商品图片自动生成竖屏推广视频（MoviePy + Ken Burns 特效）
  6. **一键代发**：1688 源头直接下单，支持无痕发货备注、Playwright 浏览器自动化
  7. **爆品趋势挖掘**：多源趋势聚合（Google Trends）、6 维爆品评分、自动触发后续流水线
  8. **闲鱼选品捡漏**：二手商品搜索、品牌识别、虚标过滤、6 维捡漏评分、价格监控、智能推荐
  9. **全自动流水线**：爆品挖掘→采集→清洗→上架→推广→视频，一键端到端执行
- 触发条件：用户需要开展跨境电商业务，包括选品、上架、推广、视频创作或二手选品捡漏时

## 前置准备

- Python 3.8+
- 依赖包安装：

```bash
pip install requests beautifulsoup4 lxml pyyaml pytrends moviepy pillow
```

- 1688 / 闲鱼需要登录态才能完整采集，建议在已登录的浏览器环境中使用
- 推广视频生成需要 ffmpeg（MoviePy 依赖）

## 操作步骤

### 流程一：全链路自动化（推荐）

```bash
# 自动挖掘爆品 → 采集 → 清洗 → 上架 → 推广 → 视频生成
python main.py auto-pipeline --seed-keywords "收纳盒,蓝牙耳机" --top-n 5 --product-limit 3 --platform all
```

### 流程二：1688 采集 → 上架 → 推广

```bash
# Step 1: 采集
python main.py scrape --keyword "蓝牙耳机" --pages 2 --detail --download-images

# Step 2: 清洗（过滤毛利率低于20%、供应商评分低于60分的商品）
python main.py clean --input data/raw_products.json --min-margin 0.20 --min-score 60

# Step 3: 上架（生成多平台模板）
python main.py publish --input data/cleaned_products.json --platform all --export all

# Step 4: 推广（关键词+竞品分析+广告文案+预算）
python main.py promote --input data/cleaned_products.json --limit 10 --daily-budget 50

# Step 5: 生成推广短视频
python main.py video --input data/cleaned_products.json --limit 5 --duration 15
```

### 流程三：爆品挖掘

```bash
# 自动挖掘趋势爆品
python main.py trend --categories electronics,home --top-n 10

# 指定种子词挖掘
python main.py trend --seed-keywords "充电宝,手机壳" --top-n 10
```

### 流程四：闲鱼选品捡漏

```bash
# 闲鱼搜索
python main.py xianyu --keyword "投影仪" --price-max 999 --pages 3 --condition 9成新

# 捡漏搜索（带参数需求）
python main.py hunt --keyword "投影仪 4K 云台" --budget 999 \
  --min-lumens 1000 --require-4k --require-gimbal --require-wall

# 智能推荐（多关键词综合）
python main.py recommend --keywords "投影仪,家用投影,4K投影" --budget 999 \
  --min-lumens 1000 --require-4k --require-gimbal

# 价格监控
python main.py monitor --keywords "投影仪,坚果投影" --budget 999
```

### 流程五：一键代发

```bash
python main.py fulfill --source-url "https://detail.1688.com/offer/xxx.html" \
  --receiver-name "张三" --receiver-phone "13800138000" \
  --receiver-address "北京市朝阳区xxx" --sku-spec "白色/大号" --quantity 1
```

## 核心逻辑

### 爆品挖掘评分模型

爆品评分 = 趋势速度 × 35% + (1-竞争度) × 25% + 利润潜力 × 25% + 供应稳定 × 15%

| 维度 | 权重 | 评分逻辑 |
|------|------|---------|
| 趋势速度 | 35% | Google Trends 搜索量变化率，近期涨幅越高分越高 |
| 竞争度 | 25% | 市场竞争强度反向指标，竞争越低分越高 |
| 利润潜力 | 25% | 1688 供货价与预估售价的利润率 |
| 供应稳定 | 15% | 供应商数量和供货稳定性 |

### 闲鱼捡漏评分模型

评分公式：价格优势(30分) + 性价比(20分) + 成色(15分) + 卖家信誉(15分) + 参数匹配(20分) - 风险扣分

| 维度 | 分值 | 评分逻辑 |
|------|------|---------|
| 价格优势 | 0-30 | 实际价/合理二手价的比值越低分越高，降价幅度加分 |
| 性价比 | 0-20 | 相对全新价的折扣率，折扣越大分越高 |
| 成色 | 0-15 | 全新15分 > 几乎全新13 > 99新12 > 9成新10 > 正常使用7 |
| 卖家信誉 | 0-15 | 百分百好评+10，想要人数加分 |
| 参数匹配 | 0-20 | 按用户需求参数（亮度/4K/云台等）的匹配度 |
| 风险扣分 | 0-30 | 低价高参数虚标、无品牌、商家批量出货等风险因素 |

### 品牌识别与虚标过滤

- 内置 30+ 品牌识别词典（投影仪/手机/笔记本/平板等品类）
- 虚标检测：低价高参数异常（如 ¥200 声称 3000+ 流明）
- 黑名单过滤：已知虚标品牌关键词、商家批量出货识别

### 数据清洗规则

- 自动翻译标题为英文（上架 Shopify/TikTok）
- 价格标准化（统一为 USD）
- 利润率 = (预估售价 - 供货价) / 预估售价
- 供应商评分过滤、起订量筛选

### 推广视频生成

- 基于 MoviePy 自动生成竖屏短视频（9:16）
- Ken Burns 慢推拉特效
- 商品图片轮播 + 标题叠加
- 时长可配置（默认 15 秒）

## 项目结构

```
ecommerce-tool/
├── main.py                  # CLI 入口（13 个子命令）
├── config.yaml              # 配置文件
├── requirements.txt         # 依赖
├── ecommerce_tool/
│   ├── scraper.py           # 1688 采集模块
│   ├── cleaner.py           # 数据清洗模块
│   ├── publisher.py          # 多平台上架模块
│   ├── promoter.py           # 推广方案模块
│   ├── video_generator.py    # 短视频生成模块
│   ├── fulfillment.py        # 一键代发模块
│   ├── trend_detector.py     # 爆品挖掘模块
│   ├── xianyu_scraper.py     # 闲鱼采集模块
│   ├── bargain_hunter.py     # 捡漏分析模块
│   └── utils.py              # 工具函数
```

## CLI 命令一览

| 命令 | 说明 |
|------|------|
| `scrape` | 从 1688 采集商品 |
| `clean` | 清洗商品数据 |
| `publish` | 生成上架模板（微信小店/Shopify/TikTok） |
| `promote` | 生成推广方案（关键词/竞品/文案/预算） |
| `video` | 生成推广短视频 |
| `fulfill` | 一键代发下单 |
| `pipeline` | 全流程自动化（采集→清洗→上架→推广→视频） |
| `trend` | 自动挖掘爆品趋势 |
| `auto-pipeline` | 全自动爆品流水线（挖掘→采集→上架→推广→视频） |
| `xianyu` | 闲鱼商品搜索 |
| `hunt` | 闲鱼捡漏搜索 |
| `recommend` | 智能推荐（多关键词综合） |
| `monitor` | 价格监控 |

## Python API 调用

```python
from ecommerce_tool.scraper import Scraper1688
from ecommerce_tool.cleaner import DataCleaner
from ecommerce_tool.publisher import Publisher
from ecommerce_tool.promoter import Promoter
from ecommerce_tool.video_generator import VideoGenerator
from ecommerce_tool.fulfillment import FulfillmentEngine
from ecommerce_tool.trend_detector import TrendDetector
from ecommerce_tool.xianyu_scraper import XianyuScraper
from ecommerce_tool.bargain_hunter import BargainHunter

# 1688 采集
scraper = Scraper1688(config, logger)
products = scraper.search("蓝牙耳机", pages=2)

# 爆品挖掘
detector = TrendDetector(config, logger)
candidates = detector.discover(categories=["electronics"], top_n=10)

# 闲鱼捡漏
hunter = BargainHunter(config, logger)
results = hunter.hunt(
    keyword="投影仪",
    price_max=999,
    spec_requirements={
        "min_lumens": 1000,
        "support_4k": True,
        "has_gimbal": True,
        "support_wall": True,
    },
)
print(hunter.display_results(results))
```

## 注意事项

- 1688 / 闲鱼有反爬机制，建议设置合理请求间隔（1.5-3.5 秒）
- 网络不可用时自动回退 Mock 数据（开发调试用）
- 视频生成需要 ffmpeg 环境
- 推广文案和关键词为 AI 生成参考，实际投放需人工审核
- 闲鱼捡漏评分仅供选品参考，不构成交易建议
- 虚标过滤不能 100% 消除假货，购买前请仔细核实

## 相关链接

- 源码仓库: https://gitee.com/anbeime/ebay
