---
name: financial-analysis
description: 获取财经新闻和股票数据，生成热门财经趋势分析和个股深度评估报告；适用于市场分析、投资研究和个股跟踪
dependency:
  python:
    - tushare>=1.2.0
    - pandas>=2.0.0
---

# 财经数据分析

## 任务目标
- 本 Skill 用于：财经数据获取与投资分析
- 能力包含：热门新闻收集、宏观形势总结、个股深度分析、报告生成
- 触发条件：用户询问财经热点、股票分析、市场趋势等

## 前置准备

### 依赖说明
scripts脚本所需的依赖包及版本
```
tushare>=1.2.0
pandas>=2.0.0
```

### TuShare Token配置

**获取Token：**
1. 访问TuShare官网：https://tushare.pro/
2. 注册账号并登录
3. 在"个人中心" → "接口TOKEN"页面获取token

**使用方式：**
- 命令行参数：`--token "your_token_here"`
- 推荐使用命令行参数，避免环境变量配置问题

**注意：** TuShare需要token认证，但免费用户也能获取每日一定额度的数据。

## 操作步骤

### 1. 获取热门新闻
调用 `scripts/fetch_news.py` 获取前100条热门财经新闻：
```bash
python3 scripts/fetch_news.py --limit 100 --token "your_tushare_token"
```
脚本返回JSON格式的新闻列表，包含标题、内容、时间等字段。

### 2. 新闻分析与总结
基于获取的新闻数据，智能体执行：
- 提取宏观形势特点（政策导向、经济指标、行业趋势）
- 识别热门个股特点（频繁提及的公司、热点概念）
- 参见 [references/news-analysis-guide.md](references/news-analysis-guide.md) 了解分析维度

### 3. 个股深度分析
对于新闻中提及的热门个股或用户指定的个股：

#### 3.1 获取股票数据
调用 `scripts/fetch_stock_data.py` 获取最近一周的行情数据：
```bash
python3 scripts/fetch_stock_data.py --stock_code 000001 --days 7 --token "your_tushare_token"
```

#### 3.2 综合分析
智能体基于新闻数据和股票行情进行多维度分析：
- 盈利能力：财报数据、净利润率、ROE等
- 自身潜力：技术面、成长性、竞争优势
- 行业潜力：行业景气度、政策支持、市场规模
- 主要形势：当前价格趋势、市场情绪、风险因素
- 价值与购买代价：估值水平、安全边际、配置建议

参考 [references/stock-analysis-guide.md](references/stock-analysis-guide.md) 的分析框架

### 4. 生成分析报告
使用 [assets/report-template.md](assets/report-template.md) 模板，将分析结果整理为结构化的Markdown报告。

## 资源索引
- 必要脚本：
  - [scripts/fetch_news.py](scripts/fetch_news.py)（获取热门新闻，参数：limit=新闻数量，token=TuShare token）
  - [scripts/fetch_stock_data.py](scripts/fetch_stock_data.py)（获取股票历史数据，参数：stock_code=股票代码，days=天数，token=TuShare token）
- 领域参考：
  - [references/news-analysis-guide.md](references/news-analysis-guide.md)（新闻分析维度与方法）
  - [references/stock-analysis-guide.md](references/stock-analysis-guide.md)（个股分析框架）
- 输出资产：
  - [assets/report-template.md](assets/report-template.md)（报告格式模板）

## 注意事项
- 数据获取依赖网络环境，需确保网络连接正常
- TuShare需要token认证，免费用户有每日调用次数限制
- 股票代码格式：A股使用6位数字（如000001），支持沪市（600xxx/688xxx）和深市（000xxx/002xxx/300xxx）
- 分析过程中结合新闻时效性和数据准确性进行判断
- 报告生成时保持客观中立，提供充分的数据支撑
- 推荐使用命令行参数传入token，避免环境变量配置问题

## 使用示例

### 示例1：市场热点分析
```bash
# 获取热门新闻
python3 scripts/fetch_news.py --limit 100 --token "your_token_here"
# 智能体分析宏观趋势和热门板块
```

### 示例2：个股深度分析
```bash
# 获取个股数据
python3 scripts/fetch_stock_data.py --stock_code 600519 --days 7 --token "your_token_here"
# 智能体结合新闻进行多维度分析
```

### 示例3：综合报告生成
获取新闻和个股数据后，智能体按照report-template.md生成完整的分析报告，包含宏观、板块、个股三个层面的内容。

## 可选：使用AKShare

如果您AKShare可以访问，可以使用 `--use_akshare` 参数：
```bash
python3 scripts/fetch_stock_data.py --stock_code 600519 --days 7 --use_akshare
```

**注意：** AKShare在国内可能无法访问，推荐使用TuShare。
