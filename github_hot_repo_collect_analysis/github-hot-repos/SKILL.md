---
name: github-hot-repos
description: 搜索GitHub热门仓库，获取README内容，并生成分析报告。适用于趋势分析、技术调研、发现优质项目等场景。
dependency:
  python:
    - requests>=2.28.0
---

# GitHub 热门仓库分析

## 任务目标
- 本 Skill 用于：搜索指定时间范围内GitHub热门仓库，分析其功能和特点
- 能力包含：GitHub API搜索、README获取、趋势分析、报告生成
- 触发条件：用户询问"最近热门的GitHub仓库"、"分析GitHub趋势"、"发现优质开源项目"等

## 前置准备
- 依赖说明：脚本需要以下Python包
  ```
  requests>=2.28.0
  ```
- 凭证配置：需配置GitHub Personal Access Token（通过Skill凭证管理）

## 操作步骤

### 1. 参数提取与准备
从用户问题中提取以下参数：
- **时间范围**：分析用户表达中的时间关键词
  - "最近一周" → start_date = 7天前
  - "最近一个月" → start_date = 30天前
  - "最近三个月" → start_date = 90天前
  - "今年" → start_date = 当年1月1日
  - 自定义日期：直接使用用户提供的日期
- **关键词**：可选，用于缩小搜索范围（如"AI"、"machine learning"等）
- **数量限制**：默认返回前20个热门仓库
- **排序方式**：默认按star数量排序

### 2. 调用搜索脚本
执行 `scripts/search_github_repos.py` 获取热门仓库列表和README内容：

```bash
python scripts/search_github_repos.py \
  --start-date 2024-01-01 \
  --end-date 2024-12-31 \
  --query "machine learning" \
  --sort stars \
  --limit 20
```

参数说明：
- `--start-date`: 起始日期（YYYY-MM-DD格式）
- `--end-date`: 结束日期（YYYY-MM-DD格式）
- `--query`: 搜索关键词（可选，默认为空）
- `--sort`: 排序方式（stars/forks）
- `--limit`: 返回结果数量（默认20）

脚本返回JSON格式数据，包含：
```json
{
  "repos": [
    {
      "name": "owner/repo-name",
      "description": "仓库描述",
      "stars": 1000,
      "forks": 200,
      "language": "Python",
      "url": "https://github.com/owner/repo",
      "readme": "README.md内容"
    }
  ]
}
```

### 3. 分析仓库功能
对每个仓库的README内容进行分析，提取：
- **核心功能**：仓库主要解决的问题和提供的功能
- **技术栈**：使用的技术、框架、语言
- **特点亮点**：独特优势、创新点
- **使用场景**：适用场景和目标用户
- **活跃度**：最近更新时间、Issue/PR情况（从README中推断）

### 4. 生成分析报告
基于分析结果，生成结构化报告，包含以下章节：

#### 4.1 概览
- 搜索范围和筛选标准
- 返回仓库总数
- 整体趋势观察

#### 4.2 热门仓库列表
按热门程度排序的仓库列表，每个仓库包含：
- 仓库名称和链接
- Star/Fork数量
- 简要描述
- 编程语言

#### 4.3 详细分析
对每个仓库的详细分析，采用以下标准格式：

```
### [仓库名称]([链接])

**项目简介**
[1-2句话简要描述项目]

**基本功能**
[概括项目的核心功能，列举3-5个主要功能点]

**技术特点**
[概括技术栈、架构设计、性能优化等方面的特点，3-5个要点]

**详细信息**
- 功能描述：[完整的功能说明]
- 技术栈：[使用的技术、框架、语言]
- 特点亮点：[独特优势、创新点]
- 使用场景：[适用场景和目标用户]
- 活跃度评估：[基于更新时间、README信息的分析]
```

注意事项：
- **基本功能**和**技术特点**必须简洁明了，每个要点不超过20字
- **详细信息**部分可以展开详细说明
- 保持格式一致性，便于快速浏览

#### 4.4 趋势总结
- 技术趋势观察（如AI、微服务、云原生等）
- 热门语言分布
- 主题聚类分析
- 推荐关注点

## 资源索引
- 必要脚本：见 [scripts/search_github_repos.py](scripts/search_github_repos.py)（用途：搜索GitHub仓库并获取README内容）
- 参考模板：见 [references/report-template.md](references/report-template.md)（用途：报告格式参考）

## 注意事项
- GitHub API有速率限制（未认证60次/小时，已认证5000次/小时），建议配置Token
- 时间范围过大会导致结果数量多，建议合理设置limit参数
- README内容可能为空或不存在，需要容错处理
- 优先选择有活跃维护的仓库（可根据更新时间过滤）

## 使用示例

### 示例1：搜索最近一个月AI领域的热门仓库
用户请求："分析最近一个月AI领域的热门GitHub项目"

执行步骤：
1. 提取参数：start_date=30天前，query="artificial intelligence OR machine learning"
2. 调用脚本获取仓库列表和README
3. 分析每个仓库的功能和特点
4. 生成报告，包含AI技术趋势分析

### 示例2：搜索今年全栈开发热门项目
用户请求："找一下今年比较火的全栈开发项目"

执行步骤：
1. 提取参数：start_date=2024-01-01，query="fullstack OR full-stack"
2. 调用脚本搜索
3. 重点关注技术栈组合（如Next.js+Prisma、React+Node.js等）
4. 生成报告，对比不同技术栈的特点

### 示例3：搜索最近一周热门开源项目
用户请求："最近一周哪些GitHub项目比较火？"

执行步骤：
1. 提取参数：start_date=7天前，query为空（不限制关键词）
2. 调用脚本搜索
3. 分析热门项目的共同特点
4. 生成趋势报告
