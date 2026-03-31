# Feishu Content Archive

将 content-master 生成的 AI 日报和 GitHub 周报自动归档到飞书文档。

## 为什么需要这个技能？

微信公众号订阅号**没有发布 API 权限**，无法自动发布内容。此技能将生成的内容转存到飞书文档，实现：

- ✅ 每日自动归档
- ✅ 独立文档，便于查找
- ✅ 支持历史追溯
- ✅ 可分享、可协作

## 快速开始

### 1. 手动归档单篇文档

```bash
# 归档 AI 日报
python3 scripts/archive_to_feishu.py --date 2026-03-31 --type daily

# 归档 GitHub 周报
python3 scripts/archive_to_feishu.py --date 2026-03-30 --type weekly
```

### 2. 通过 OpenClaw 对话

```
把今天的 AI 日报归档到飞书
```

### 3. 自动归档（推荐）

配置 cron 任务，在内容生成后自动归档：

```json
{
  "name": "AI 日报 - 飞书归档",
  "schedule": { "kind": "cron", "expr": "0 9 * * *", "tz": "Asia/Shanghai" },
  "payload": {
    "kind": "systemEvent",
    "text": "读取 /home/ubuntu/.openclaw/workspace-content-master/output/ai_daily_$(date +%Y-%m-%d)_article.md 并创建飞书文档"
  }
}
```

## 文档命名规范

| 类型 | 命名格式 | 示例 |
|------|----------|------|
| AI 日报 | `AI 日报-YYYY-MM-DD` | `AI 日报-2026-03-31` |
| GitHub 周报 | `GitHub 周报-YYYY-MM-DD` | `GitHub 周报-2026-03-30` |

## 输出位置

飞书文档根目录。如需归档到指定文件夹，需要：

1. 在飞书中创建文件夹
2. 获取文件夹 Token
3. 在调用 feishu_doc 时指定 parent_block_id

## 文件结构

```
feishu-content-archive/
├── SKILL.md              # 技能定义
├── README.md             # 本文档
└── scripts/
    └── archive_to_feishu.py  # 归档脚本
```

## 依赖

- Python 3.12+
- OpenClaw feishu_doc tool

## 注意事项

1. **飞书权限**: 确保飞书机器人有创建文档的权限
2. **内容生成时序**: 归档任务应在内容生成任务之后执行
3. **错误处理**: 如果源文件不存在，脚本会返回错误

## 未来改进

- [ ] 支持归档到指定飞书文件夹
- [ ] 支持批量归档历史文档
- [ ] 添加飞书通知（归档完成后发送消息）
- [ ] 支持自定义文档模板
