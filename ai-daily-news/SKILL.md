---
name: ai-daily-news
description: 聚合AI领域最新新闻和论文，智能筛选生成图文并茂深度文章；支持HackerNews、ArXiv及自定义源多源数据采集，自动下载配图，支持使用豆包Doubao等LLM辅助生成
dependency:
  python:
    - requests>=2.28.0
    - feedparser>=6.0.10
    - beautifulsoup4>=4.12.0
    - openai>=1.0.0
  system: []
---

# AI Daily News 生成器

## 任务目标
本 Skill 用于：
- 自动获取AI领域最热门的新闻和论文
- 智能筛选出最有价值的内容
- 生成包含标题、正文和配图的高质量文章

能力包含：
- 聚合多个来源的AI内容（Hacker News + ArXiv + 国内新闻源 + 自定义源）
- ArXiv论文自动提取架构图和流程图
- Hacker News文章自动提取OG图片
- 支持国内新闻源（36氪等）
- 按指定日期筛选内容
- 自动下载相关图片
- 格式化输出结构化文章

触发条件：
- "生成今天AI热点文章"
- "整理昨天的AI新闻"
- "获取最新的AI论文和新闻"
- "写一篇AI领域的日报"

## 前置准备

### 依赖安装
确保已安装以下 Python 依赖包：
```bash
pip install requests feedparser beautifulsoup4 openai
```

### 目录准备
无需额外准备目录，脚本会自动创建输出目录。

### LLM配置（可选）
如果需要使用LLM辅助生成文章，请配置环境变量：

```bash
# 设置API密钥（火山引擎豆包或其他兼容OpenAI API的服务）
export ARK_API_KEY="your-api-key-here"
# 或
export OPENAI_API_KEY="your-api-key-here"
```

支持的LLM服务：
- **豆包 Doubao**（火山引擎ARK）：需要配置对应的API密钥
- **OpenAI**：需要配置 `OPENAI_API_KEY`
- **其他兼容OpenAI API的服务**：配置对应的API密钥环境变量

## 操作步骤

### 步骤 1：获取AI热点数据

调用脚本获取热门内容：

**方式A：获取最新内容**
```bash
python scripts/fetch_ai_daily.py \
  --hn-limit 5 \
  --arxiv-limit 5 \
  --output ./ai_daily_data.json
```

**方式B：获取指定日期的内容（YYYY-MM-DD格式）**
```bash
python scripts/fetch_ai_daily.py \
  --date 2025-02-07 \
  --hn-limit 5 \
  --arxiv-limit 5 \
  --output ./ai_daily_data.json
```

**方式C：使用国内新闻源（推荐国内用户）**
```bash
python scripts/fetch_ai_daily.py \
  --no-hacker-news \
  --no-arxiv \
  --domestic-source 36kr-ai \
  --domestic-limit 8 \
  --output ./ai_daily_data.json
```

**方式D：混合多个数据源**
```bash
python scripts/fetch_ai_daily.py \
  --hn-limit 3 \
  --arxiv-limit 2 \
  --domestic-source 36kr-ai \
  --domestic-limit 5 \
  --output ./ai_daily_data.json
```

**方式E：添加自定义新闻源（RSS/Atom feed 或 JSON API）**
```bash
python scripts/fetch_ai_daily.py \
  --custom-url "https://api.example.com/news" \
  --custom-source "MyNews" \
  --hn-limit 5 \
  --arxiv-limit 5 \
  --output ./ai_daily_data.json
```

参数说明：
- `--date`: 指定日期，格式：YYYY-MM-DD（仅用于ArXiv日期过滤）
- `--custom-url`: 自定义新闻源URL（支持JSON API和RSS/Atom feed）
- `--custom-source`: 自定义新闻源名称（默认：custom）
- `--domestic-source`: 使用预设的国内新闻源（36kr-ai, sina-tech, zhihu-daily）
- `--domestic-limit`: 国内新闻源获取数量（默认：5）
- `--no-hacker-news`: 不获取Hacker News数据
- `--no-arxiv`: 不获取ArXiv数据
- `--hn-limit`: Hacker News获取数量（默认8）
- `--arxiv-limit`: ArXiv论文获取数量（默认2）
- `--output`: 输出JSON文件路径（默认：ai_daily_news.json）
- `--download-images`: 自动下载所有图片到本地
- `--image-output-dir`: 图片保存目录（默认：./images）
- `--no-article`: 不生成文章，仅输出JSON数据
- `--model`: 使用的LLM模型（默认：doubao-seed-1-8-251228）
- `--base-url`: LLM API的base_url

预设的国内新闻源：
- `36kr-ai`: 36氪AI专栏
- `sina-tech`: 新浪科技
- `zhihu-daily`: 知乎日报

脚本将返回包含以下信息的JSON数据：
- Hacker News热门讨论（含OG图片，最近6个月内）
- ArXiv最新AI论文（含架构图、流程图等多张图片，最近一个月内）
- 国内新闻源AI相关内容（标题、链接等）
- 每条内容的标题、摘要、链接、发布时间、图片URL等

### 步骤 2：下载图片

**方式A：获取数据时自动下载（推荐）**
```bash
python scripts/fetch_ai_daily.py \
  --download-images \
  --image-output-dir ./ai_daily_articles/images \
  --output ./ai_daily_data.json
```

**方式B：批量下载（从已有的JSON数据）**
```bash
python scripts/download_batch_images.py \
  --input ./ai_daily_data.json \
  --output ./ai_daily_articles/images
```

参数说明：
- `--input`: 输入JSON文件路径
- `--output`: 图片保存目录
- `--date`: 日期字符串（可选，用于文件命名）

图片下载特点：
- ArXiv论文：自动提取架构图、流程图、实验结果图等
- Hacker News文章：自动提取OG图片
- 自动过滤公式图、小图标和无效URL
- 统一的命名格式：`{source}_{type}_{index}.{ext}`（如：`hacker_news_news_01.jpg`、`arxiv_paper_02.png`）

### 步骤 3：生成文章

**方案A：使用LLM自动生成（推荐）**

使用 `--article` 参数（默认启用）自动生成文章：

```bash
python scripts/fetch_ai_daily.py \
  --hn-limit 5 \
  --arxiv-limit 5 \
  --base-url "https://ark.cn-beijing.volces.com/api/v3" \
  --model "doubao-seed-1-8-251228" \
  --output ./ai_daily_data.json
```

文章将自动保存为 `{output文件名}_article.md`

**方案B：使用外部LLM生成文章**

根据JSON数据手动调用LLM生成文章，参考以下提示：

```
你是一位专业的AI领域科技记者，擅长撰写深度、通俗易懂、富有洞见的AI资讯文章。

请根据以下AI相关内容，生成一篇高质量的AI日报文章。

文章格式要求：
1. **标题**：吸引人且概括性强的标题
2. **导语**：简要介绍当天AI领域亮点（100-200字）
3. **正文**：精选内容，每条包含：
   - 子标题
   - 主要内容描述（150-300字）
   - 图片（如果有，使用格式：![图片描述](./images/xxx.jpg)）
   - 原文链接
4. **结语**：总结性观点或展望（100-200字）

内容编写原则：
- 准确性：基于数据生成，不编造事实
- 可读性：用通俗易懂的语言解释技术概念
- 连贯性：在条目间加入过渡，增强文章流畅性
- 价值性：每条内容都要说明"为什么值得关注"

请直接输出Markdown格式的文章，不要添加其他说明。

以下是待生成的内容：
[插入JSON数据]
```

## 完整示例

### 示例1：生成今天的热点文章（含图片）
```bash
# 获取最新数据，自动下载图片，生成文章
python scripts/fetch_ai_daily.py \
  --hn-limit 5 \
  --arxiv-limit 5 \
  --download-images \
  --image-output-dir ./images \
  --output ai_daily_$(date +%Y-%m-%d).json

# 输出文件：
# - ai_daily_2025-02-08.json: 原始数据
# - ai_daily_2025-02-08_article.md: 生成的文章
# - images/: 图片目录
```

### 示例2：生成指定日期的文章
```bash
# 获取2025年1月15日的数据
python scripts/fetch_ai_daily.py \
  --date 2025-01-15 \
  --hn-limit 5 \
  --arxiv-limit 5 \
  --download-images \
  --output ai_daily_2025-01-15.json
```

### 示例3：使用国内新闻源（推荐国内用户）
```bash
# 只使用国内新闻源
python scripts/fetch_ai_daily.py \
  --no-hacker-news \
  --no-arxiv \
  --domestic-source 36kr-ai \
  --domestic-limit 8 \
  --download-images \
  --output ai_daily_domestic.json
```

### 示例4：混合多个数据源（国内外结合）
```bash
# 结合国内外多个数据源
python scripts/fetch_ai_daily.py \
  --hn-limit 3 \
  --arxiv-limit 2 \
  --domestic-source 36kr-ai \
  --domestic-limit 5 \
  --download-images \
  --output ai_daily_mixed.json
```

### 示例5：使用自定义新闻源
```bash
# 添加自定义RSS feed作为数据源
python scripts/fetch_ai_daily.py \
  --custom-url "https://techcrunch.com/category/artificial-intelligence/feed/" \
  --custom-source "TechCrunch" \
  --hn-limit 3 \
  --arxiv-limit 3 \
  --custom-limit 5 \
  --download-images \
  --output ai_daily_with_custom.json
```

## 资源索引

### 必要脚本
- [scripts/fetch_ai_daily.py](scripts/fetch_ai_daily.py)
  - 用途：主脚本，获取Hacker News、ArXiv和自定义源的内容，可选生成文章
  - 关键参数：`--date`, `--custom-url`, `--download-images`, `--no-article`
  - 输出：JSON数据文件和可选的Markdown文章

- [scripts/download_batch_images.py](scripts/download_batch_images.py)
  - 用途：从JSON数据文件中批量下载所有图片
  - 参数：`--input`, `--output`, `--date`
  - 输出：多个图片文件

- [scripts/download_image.py](scripts/download_image.py)
  - 用途：下载指定URL的单张图片到本地
  - 参数：`--url`, `--output`
  - 输出：本地图片文件

## 注意事项

### 数据获取
- Hacker News API可能会有访问限制，建议控制请求频率
- ArXiv API返回的是最新论文，不保证有每天的新论文
- 自定义新闻源需要提供有效的JSON API或RSS/Atom feed

### 图片下载
- ArXiv论文图片会自动过滤公式图和小图标
- 部分图片可能因网络问题下载失败，脚本会自动跳过
- base64编码的图片URL会被自动跳过

### 文章生成
- LLM生成的内容需要人工审核，确保准确性
- 图片路径需要根据实际下载的文件名进行调整
- 建议在使用前查看原始JSON数据，了解内容质量

### 性能优化
- 图片下载可以单独进行，与数据获取分离
- 批量下载比单个下载效率更高
- 可以使用 `--no-article` 参数先获取数据，再单独生成文章

## 使用场景扩展

### 1. 定时任务
可以设置cron定时任务，每天自动生成AI日报：
```bash
# 每天早上9点生成
0 9 * * * cd /path/to/ai-daily-news && python scripts/fetch_ai_daily.py --download-images --output ai_daily_$(date +\%Y-\%m-\%d).json
```

### 2. 多源聚合
通过组合多个自定义源，实现更全面的信息聚合：
```bash
python scripts/fetch_ai_daily.py \
  --custom-url "https://source1.com/feed" \
  --custom-source "Source1" \
  --custom-url2 "https://source2.com/api" \
  --custom-source2 "Source2" \
  # （需要多次运行或修改脚本支持多个自定义源）
```

### 3. 自定义筛选
可以基于JSON数据编写自己的筛选逻辑：
```python
import json

with open('ai_daily_data.json', 'r') as f:
    data = json.load(f)

# 筛选特定的关键词
selected = [e for e in data['entries'] if 'LLM' in e['title'] or 'GPT' in e['title']]

# 保存筛选结果
with open('selected.json', 'w') as f:
    json.dump(selected, f, indent=2)
```
