#!/usr/bin/env python3
"""
Feishu Content Archive Script

读取 content-master output 目录的内容，输出为可被 OpenClaw 处理的格式。
OpenClaw 会读取此脚本的输出并调用 feishu_doc 创建文档。

使用方法:
    python3 archive_to_feishu.py --date 2026-03-31 --type daily
    python3 archive_to_feishu.py --date 2026-03-30 --type weekly
"""

import argparse
import json
import os
import sys
from pathlib import Path
from datetime import datetime

# content-master output 目录
OUTPUT_DIR = Path("/home/ubuntu/.openclaw/workspace-content-master/output")


def read_article_file(date_str: str, doc_type: str) -> tuple[str, str]:
    """读取文章文件，返回标题和内容"""
    if doc_type == "daily":
        filename = f"ai_daily_{date_str}_article.md"
        title_prefix = "AI 日报"
    elif doc_type == "weekly":
        filename = f"github_weekly_{date_str}_status.md"
        # 尝试查找实际的文章文件
        article_file = f"github_weekly_{date_str}_article.md"
        if (OUTPUT_DIR / article_file).exists():
            filename = article_file
        title_prefix = "GitHub 周报"
    else:
        raise ValueError(f"Unknown doc_type: {doc_type}")
    
    filepath = OUTPUT_DIR / filename
    if not filepath.exists():
        raise FileNotFoundError(f"File not found: {filepath}")
    
    content = filepath.read_text(encoding="utf-8")
    
    # 从内容中提取或生成标题
    title = f"{title_prefix}-{date_str}"
    
    return title, content


def generate_feishu_doc_content(title: str, content: str, date_str: str, doc_type: str) -> str:
    """生成飞书文档格式的内容"""
    # 添加文档头部信息
    header = f"""# {title}

> 📌 **说明**: 本文由 content-master 自动生成并归档
> 📁 **来源**: `/home/ubuntu/.openclaw/workspace-content-master/output/`
> 📅 **生成日期**: {date_str}
> 🔄 **归档时间**: {datetime.now().strftime("%Y-%m-%d %H:%M")}

---

"""
    
    return header + content


def main():
    parser = argparse.ArgumentParser(description="Archive content-master output to Feishu")
    parser.add_argument("--date", required=True, help="Date string (YYYY-MM-DD)")
    parser.add_argument("--type", required=True, choices=["daily", "weekly"], help="Document type")
    parser.add_argument("--output", choices=["json", "markdown"], default="json", help="Output format")
    
    args = parser.parse_args()
    
    try:
        title, raw_content = read_article_file(args.date, args.type)
        feishu_content = generate_feishu_doc_content(title, raw_content, args.date, args.type)
        
        if args.output == "json":
            # 输出 JSON 格式，方便 OpenClaw 解析
            result = {
                "title": title,
                "content": feishu_content,
                "date": args.date,
                "type": args.type,
                "source_file": f"/home/ubuntu/.openclaw/workspace-content-master/output/",
            }
            print(json.dumps(result, ensure_ascii=False, indent=2))
        else:
            # 输出 Markdown 格式
            print(feishu_content)
            
    except FileNotFoundError as e:
        print(json.dumps({"error": str(e)}), file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(json.dumps({"error": f"Unexpected error: {str(e)}"}), file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
