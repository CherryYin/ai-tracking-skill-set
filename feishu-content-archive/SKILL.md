# Feishu Content Archive Skill

将 content-master 生成的内容自动归档到飞书文档。

## 功能

- 每日 AI 日报 → 创建独立飞书文档
- 每周 GitHub 周报 → 创建独立飞书文档
- 自动按日期命名和归档

## 配置

### 飞书文档配置

在 `TOOLS.md` 中配置：

```markdown
### AI 内容聚合文档（content-master）
- **文件夹名称**: AI 内容聚合 - 日报周报
- **父文档 Token**: （可选，留空则创建到根目录）
```

### 环境变量（可选）

```bash
# 飞书文档父文件夹 Token（用于归档到指定文件夹）
export FEISHU_CONTENT_PARENT_TOKEN=""
```

## 使用方法

### 手动调用

```bash
cd /home/ubuntu/.openclaw/workspace-content-master/skills/feishu-content-archive
python3 scripts/archive_to_feishu.py --date 2026-03-31 --type daily
```

### 通过 OpenClaw 对话

```
把今天的 AI 日报归档到飞书
把上周的 GitHub 周报归档到飞书
```

## 文档命名规范

- AI 日报：`AI 日报-YYYY-MM-DD`
- GitHub 周报：`GitHub 周报-YYYY-MM-DD`

## 输出位置

飞书文档根目录或指定的父文档下。

## 依赖

- `feishu_doc` tool (OpenClaw 内置)
- Python 3.12+

## 文件结构

```
feishu-content-archive/
├── SKILL.md
├── scripts/
│   └── archive_to_feishu.py
└── README.md
```
