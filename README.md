# ai-tracking-skill-set

一组用于"追踪信息 → 拉取数据 →（可选）调用 LLM → 生成结构化输出"的 Python 小工具/Skill 集合。

目前包含五类主题：
- 📰 **AI 领域日报**（新闻 + 论文 + 配图 + 可选自动成文）
- 📈 **财经新闻与个股数据获取**（TuShare / 可选 AKShare）
- 🔥 **GitHub 热门仓库搜索与 README 抓取**
- 📝 **微信公众号发布**（服务号 API 自动发布）
- 📄 **飞书文档归档**（自动创建日报/周报文档）

## 目录结构

- [ai-daily-news/](ai-daily-news/)：AI 热点聚合与文章生成
	- 说明文档：[ai-daily-news/SKILL.md](ai-daily-news/SKILL.md)
	- 入口脚本：[ai-daily-news/scripts/fetch_ai_daily.py](ai-daily-news/scripts/fetch_ai_daily.py)
	- 图片下载：[ai-daily-news/scripts/download_batch_images.py](ai-daily-news/scripts/download_batch_images.py)
- [financial-analysis/](financial-analysis/)：财经新闻与个股数据
	- 说明文档：[financial-analysis/SKILL.md](financial-analysis/SKILL.md)
	- 获取新闻：[financial-analysis/scripts/fetch_news.py](financial-analysis/scripts/fetch_news.py)
	- 获取行情：[financial-analysis/scripts/fetch_stock_data.py](financial-analysis/scripts/fetch_stock_data.py)
- [github_hot_repo_collect_analysis/](github_hot_repo_collect_analysis/)：GitHub 热门仓库搜索
	- 说明文档：[github_hot_repo_collect_analysis/github-hot-repos/SKILL.md](github_hot_repo_collect_analysis/github-hot-repos/SKILL.md)
	- 入口脚本：[github_hot_repo_collect_analysis/github-hot-repos/scripts/search_github_repos.py](github_hot_repo_collect_analysis/github-hot-repos/scripts/search_github_repos.py)
- [wechat-official-publish/](wechat-official-publish/)：✨ 微信公众号发布
	- 说明文档：[wechat-official-publish/SKILL.md](wechat-official-publish/SKILL.md)
	- 发布脚本：[wechat-official-publish/scripts/wechat_publish.py](wechat-official-publish/scripts/wechat_publish.py)
	- 功能：获取 token、上传图片、创建草稿、正式发布、发送预览
- [feishu-content-archive/](feishu-content-archive/)：✨ 飞书文档归档
	- 说明文档：[feishu-content-archive/SKILL.md](feishu-content-archive/SKILL.md)
	- 归档脚本：[feishu-content-archive/scripts/archive_to_feishu.py](feishu-content-archive/scripts/archive_to_feishu.py)
	- 功能：将 AI 日报/GitHub 周报自动归档到飞书文档（独立文档，按日期命名）

## 环境要求

- Python 3（建议 3.10+）
- macOS / Linux / Windows 均可（脚本主要依赖网络访问）

## 安装依赖

仓库根目录提供了一个较"全量"的依赖清单（适合直接一次装齐）：

```bash
python -m venv .venv
source .venv/bin/activate

pip install -r requirements.txt
```

如果你只想跑某一个子项目，也可以参考各自的 SKILL 文档（例如 [ai-daily-news/SKILL.md](ai-daily-news/SKILL.md)）按需安装更小的依赖集合。

## 配置（可选/按需）

### 1) AI 日报的 LLM Key（可选）

若你希望脚本自动生成文章（默认会生成，除非加 `--no-article`），需要配置任意一种兼容 OpenAI SDK 的 Key：

```bash
# 火山引擎 ARK / 豆包（示例）
export ARK_API_KEY="your-api-key"

# 或 OpenAI
export OPENAI_API_KEY="your-api-key"
```

如需自定义模型服务地址，可在运行时传 `--base-url`。

### 2) TuShare Token（财经脚本必需）

财经脚本默认使用 TuShare，需要在命令行通过 `--token` 传入。

### 3) GitHub PAT（GitHub 热门仓库脚本必需）

脚本从环境变量读取 GitHub Token（注意变量名是固定的）：

```bash
export COZE_GITHUB_PAT_7606697694219796480="your_github_pat"
```

Token 可在 https://github.com/settings/tokens 创建。脚本说明中建议 public_repo 权限（仅抓取公开仓库通常不需要额外权限，但 Token 可提升速率限制）。

### 4) 微信公众号 API 凭证（发布到公众号必需）

**注意**：必须是**服务号**（订阅号无发布 API 权限），且已完成微信认证。

```bash
export WECHAT_APPID="your_appid"
export WECHAT_APPSECRET="your_appsecret"
```

获取方式：
1. 登录 [微信公众平台](https://mp.weixin.qq.com/)
2. 开发 → 基本配置
3. 获取 AppID 和 AppSecret
4. 添加服务器 IP 到白名单

详见：[wechat-official-publish/SKILL.md](wechat-official-publish/SKILL.md)

### 5) 飞书文档配置（飞书归档必需）

飞书归档技能需要 OpenClaw 的 `feishu_doc` 工具支持，无需额外配置 API 凭证。

文档会自动创建到飞书文档根目录，命名规范：
- AI 日报：`AI 日报-YYYY-MM-DD`
- GitHub 周报：`GitHub 周报-YYYY-MM-DD`

详见：[feishu-content-archive/SKILL.md](feishu-content-archive/SKILL.md)

## 使用示例

### AI Daily News：抓取热点 + 下载图片 +（可选）生成文章

```bash
python ai-daily-news/scripts/fetch_ai_daily.py \
	--hn-limit 5 \
	--arxiv-limit 5 \
	--download-images \
	--image-output-dir ai-daily-news/output/images \
	--output ai-daily-news/output/ai_daily_data.json
```

常用参数：
- 指定日期（仅用于 ArXiv 过滤）：`--date 2025-02-07`
- 只用国内源：`--no-hacker-news --no-arxiv --domestic-source 36kr-ai --domestic-limit 8`
- 不生成文章：`--no-article`

### 财经：获取新闻

```bash
python financial-analysis/scripts/fetch_news.py \
	--limit 100 \
	--token "your_tushare_token" \
	--output financial-analysis/output/news.json
```

### 财经：获取个股近 N 天行情

```bash
python financial-analysis/scripts/fetch_stock_data.py \
	--stock_code 600519 \
	--days 7 \
	--token "your_tushare_token" \
	--output financial-analysis/output/stock_600519.json
```

（可选）使用 AKShare：

```bash
python financial-analysis/scripts/fetch_stock_data.py \
	--stock_code 600519 \
	--days 7 \
	--use_akshare
```

### GitHub：搜索时间范围内新建的热门仓库并抓取 README

```bash
python github_hot_repo_collect_analysis/github-hot-repos/scripts/search_github_repos.py \
	--start-date "30 days ago" \
	--end-date "1 days ago" \
	--query "llm" \
	--sort stars \
	--limit 20 \
	> github_hot_repo_collect_analysis/output/repos.json
```

### 微信公众号：发布文章

```bash
# 配置环境变量
export WECHAT_APPID="your_appid"
export WECHAT_APPSECRET="your_appsecret"

# 发布文章
python wechat-official-publish/scripts/wechat_publish.py \
	--title "文章标题" \
	--content-file article.md \
	--publish
```

### 飞书归档：将 AI 日报归档到飞书文档

```bash
python feishu-content-archive/scripts/archive_to_feishu.py \
	--date 2026-03-31 \
	--type daily
```

参数说明：
- `--date`: 日期（YYYY-MM-DD 格式）
- `--type`: 文档类型（`daily` 或 `weekly`）

## 产物与参考

- AI 日报输出 JSON/文章/配图：见 [ai-daily-news/](ai-daily-news/)（仓库中也包含 `test_domestic.json`、`test_output.json` 作为示例数据）
- 财经分析参考框架：
	- [financial-analysis/references/news-analysis-guide.md](financial-analysis/references/news-analysis-guide.md)
	- [financial-analysis/references/stock-analysis-guide.md](financial-analysis/references/stock-analysis-guide.md)
- 微信公众号发布流程：[wechat-official-publish/SKILL.md](wechat-official-publish/SKILL.md)
- 飞书归档技能：[feishu-content-archive/SKILL.md](feishu-content-archive/SKILL.md)

## 安全提示

⚠️ **请勿在代码或仓库中存储敏感信息**：

- API Key、Token、Secret 等凭证请通过环境变量传递
- 本仓库已配置 `.gitignore` 排除敏感文件
- 微信、GitHub 等凭证不要提交到版本控制

## 自动化部署（OpenClaw）

本技能集合设计用于 OpenClaw Agent 系统，支持定时任务自动执行：

- **AI 日报**：每天 09:00 自动生成并归档到飞书
- **GitHub 周报**：每周一 10:00 自动生成并归档到飞书

配置示例请参考各技能的 SKILL.md 文档。

---

**维护者**: CherryYin  
**License**: MIT
