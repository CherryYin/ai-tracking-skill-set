#!/usr/bin/env python3
"""
热门财经新闻获取脚本

功能：使用TuShare获取财经新闻
输出：JSON格式新闻列表
"""

import argparse
import json
import sys
from datetime import datetime
from typing import Dict, List, Any, Optional


def fetch_news_tushare(limit: int = 100, token: str = None) -> List[Dict[str, Any]]:
    """
    使用TuShare获取财经新闻

    参数:
        limit: 获取新闻数量，默认100条
        token: TuShare API token

    返回:
        新闻列表，每条新闻包含:
        - title: 新闻标题
        - content: 新闻内容
        - time: 发布时间
        - source: 新闻来源
        - url: 新闻链接（如有）
    """
    if not token:
        print("错误: TuShare token为空", file=sys.stderr)
        print("请使用 --token 参数提供您的TuShare token", file=sys.stderr)
        print("获取token: https://tushare.pro/", file=sys.stderr)
        sys.exit(1)

    try:
        import tushare as ts
    except ImportError:
        print("错误: 未安装tushare库", file=sys.stderr)
        print("请执行: pip install tushare", file=sys.stderr)
        sys.exit(1)

    # 初始化TuShare
    ts.set_token(token)
    pro = ts.pro_api()

    print(f"正在获取最近 {limit} 条财经新闻...", file=sys.stderr)

    try:
        # 获取最新新闻
        df = pro.news_all(src='sina', token=token)

        if df is None or len(df) == 0:
            print("警告: 未获取到新闻数据", file=sys.stderr)
            return []

        # 转换数据格式
        news_list = []
        for idx, row in df.head(limit).iterrows():
            news_item = {
                "title": str(row.get("title", "")),
                "content": str(row.get("content", "")),
                "time": str(row.get("datetime", "")),
                "source": str(row.get("source", "")),
                "url": str(row.get("url", ""))
            }
            news_list.append(news_item)

        print(f"成功获取 {len(news_list)} 条新闻", file=sys.stderr)
        return news_list

    except Exception as e:
        print(f"获取新闻失败: {str(e)}", file=sys.stderr)
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description="获取热门财经新闻")
    parser.add_argument("--limit", type=int, default=100,
                       help="获取新闻数量 (默认: 100)")
    parser.add_argument("--token", type=str, required=True,
                       help="TuShare API token (必填)")
    parser.add_argument("--output", type=str,
                       help="输出文件路径 (可选，默认输出到stdout)")

    args = parser.parse_args()

    # 获取新闻
    news_list = fetch_news_tushare(args.limit, args.token)

    # 输出结果
    result = {
        "fetch_time": datetime.now().isoformat(),
        "count": len(news_list),
        "news": news_list
    }

    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        print(f"结果已保存到: {args.output}", file=sys.stderr)
    else:
        print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
