#!/usr/bin/env python3
"""
搜索GitHub热门仓库并获取README内容

授权方式: ApiKey
凭证Key: COZE_GITHUB_PAT_7606697694219796480
"""

import os
import sys
import argparse
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from coze_workload_identity import requests


def get_github_token():
    """获取GitHub Personal Access Token"""
    skill_id = "7606697694219796480"
    token = os.getenv("COZE_GITHUB_PAT_" + skill_id)
    if not token:
        raise ValueError(
            "缺少GitHub凭证配置。请通过Skill凭证管理配置GitHub Personal Access Token。\n"
            "访问 https://github.com/settings/tokens 创建Token，选择public_repo权限。"
        )
    return token


def search_repos(
    token: str,
    query: str,
    start_date: str,
    end_date: str,
    sort: str = "stars",
    limit: int = 20
) -> List[Dict]:
    """
    搜索GitHub仓库
    
    Args:
        token: GitHub Personal Access Token
        query: 搜索关键词
        start_date: 起始日期 (YYYY-MM-DD)
        end_date: 结束日期 (YYYY-MM-DD)
        sort: 排序方式 (stars/forks)
        limit: 返回结果数量
    
    Returns:
        仓库列表
    """
    # 构建搜索查询
    date_query = f"created:{start_date}..{end_date}"
    if query:
        full_query = f"{date_query} {query}"
    else:
        full_query = date_query
    
    url = "https://api.github.com/search/repositories"
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github.v3+json"
    }
    params = {
        "q": full_query,
        "sort": sort,
        "order": "desc",
        "per_page": min(limit, 100)  # GitHub API最大100条每页
    }
    
    try:
        response = requests.get(url, headers=headers, params=params, timeout=30)
        
        if response.status_code >= 400:
            error_msg = f"GitHub API请求失败: 状态码 {response.status_code}"
            if response.status_code == 403:
                error_msg += " (可能是API速率限制，请检查Token配置)"
            error_msg += f", 响应: {response.text}"
            raise Exception(error_msg)
        
        data = response.json()
        
        # 检查GitHub API错误
        if "message" in data and "documentation_url" in data:
            raise Exception(f"GitHub API错误: {data['message']}")
        
        return data.get("items", [])
        
    except requests.exceptions.RequestException as e:
        raise Exception(f"网络请求失败: {str(e)}")


def get_readme(token: str, owner: str, repo: str) -> Optional[str]:
    """
    获取仓库的README内容
    
    Args:
        token: GitHub Personal Access Token
        owner: 仓库所有者
        repo: 仓库名称
    
    Returns:
        README内容（base64解码后的文本），如果不存在则返回None
    """
    url = f"https://api.github.com/repos/{owner}/{repo}/readme"
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github.v3+json"
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=30)
        
        if response.status_code == 404:
            return None  # README不存在
        
        if response.status_code >= 400:
            print(f"警告: 获取 {owner}/{repo} README失败: {response.status_code}", file=sys.stderr)
            return None
        
        data = response.json()
        
        # 解码base64内容
        import base64
        content = data.get("content", "")
        if content:
            try:
                decoded = base64.b64decode(content)
                return decoded.decode("utf-8", errors="ignore")
            except Exception as e:
                print(f"警告: 解码 {owner}/{repo} README失败: {str(e)}", file=sys.stderr)
                return None
        
        return None
        
    except requests.exceptions.RequestException as e:
        print(f"警告: 获取 {owner}/{repo} README失败: {str(e)}", file=sys.stderr)
        return None


def format_repo_info(repo: Dict, readme: Optional[str]) -> Dict:
    """
    格式化仓库信息
    
    Args:
        repo: 原始仓库数据
        readme: README内容
    
    Returns:
        格式化后的仓库信息
    """
    return {
        "name": repo.get("full_name"),
        "description": repo.get("description") or "",
        "stars": repo.get("stargazers_count", 0),
        "forks": repo.get("forks_count", 0),
        "language": repo.get("language") or "Unknown",
        "url": repo.get("html_url"),
        "created_at": repo.get("created_at"),
        "updated_at": repo.get("updated_at"),
        "readme": readme or ""
    }


def parse_date(date_str: str) -> str:
    """
    解析日期字符串为YYYY-MM-DD格式
    
    支持格式：
    - YYYY-MM-DD
    - N days ago (如 "7 days ago")
    - N weeks ago
    - N months ago
    """
    # 尝试解析相对日期
    date_str = date_str.lower().strip()
    
    if "days ago" in date_str or "day ago" in date_str:
        days = int(date_str.split()[0])
        date = datetime.now() - timedelta(days=days)
        return date.strftime("%Y-%m-%d")
    elif "weeks ago" in date_str or "week ago" in date_str:
        weeks = int(date_str.split()[0])
        date = datetime.now() - timedelta(weeks=weeks)
        return date.strftime("%Y-%m-%d")
    elif "months ago" in date_str or "month ago" in date_str:
        months = int(date_str.split()[0])
        date = datetime.now() - timedelta(days=months * 30)
        return date.strftime("%Y-%m-%d")
    else:
        # 尝试解析为YYYY-MM-DD格式
        try:
            datetime.strptime(date_str, "%Y-%m-%d")
            return date_str
        except ValueError:
            raise ValueError(f"不支持的日期格式: {date_str}")


def main():
    parser = argparse.ArgumentParser(
        description="搜索GitHub热门仓库并获取README内容"
    )
    parser.add_argument(
        "--start-date",
        required=True,
        help="起始日期 (YYYY-MM-DD格式，或如'30 days ago'的相对日期)"
    )
    parser.add_argument(
        "--end-date",
        required=True,
        help="结束日期 (YYYY-MM-DD格式，或如'1 days ago'的相对日期)"
    )
    parser.add_argument(
        "--query",
        default="",
        help="搜索关键词（可选）"
    )
    parser.add_argument(
        "--sort",
        choices=["stars", "forks"],
        default="stars",
        help="排序方式（默认：stars）"
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=20,
        help="返回结果数量（默认：20，最大100）"
    )
    
    args = parser.parse_args()
    
    # 解析日期
    try:
        start_date = parse_date(args.start_date)
        end_date = parse_date(args.end_date)
    except ValueError as e:
        print(f"错误: {str(e)}", file=sys.stderr)
        sys.exit(1)
    
    # 获取GitHub Token
    try:
        token = get_github_token()
    except ValueError as e:
        print(f"错误: {str(e)}", file=sys.stderr)
        sys.exit(1)
    
    # 搜索仓库
    print(f"正在搜索GitHub仓库...", file=sys.stderr)
    print(f"  时间范围: {start_date} 至 {end_date}", file=sys.stderr)
    print(f"  搜索关键词: {args.query or '(无)'}", file=sys.stderr)
    print(f"  排序方式: {args.sort}", file=sys.stderr)
    print(f"  结果数量: {args.limit}", file=sys.stderr)
    
    try:
        repos = search_repos(
            token=token,
            query=args.query,
            start_date=start_date,
            end_date=end_date,
            sort=args.sort,
            limit=args.limit
        )
    except Exception as e:
        print(f"错误: {str(e)}", file=sys.stderr)
        sys.exit(1)
    
    if not repos:
        print("未找到匹配的仓库", file=sys.stderr)
        print(json.dumps({"repos": []}, ensure_ascii=False, indent=2))
        sys.exit(0)
    
    print(f"找到 {len(repos)} 个仓库，正在获取README内容...", file=sys.stderr)
    
    # 获取每个仓库的README
    results = []
    for i, repo in enumerate(repos):
        owner, repo_name = repo["full_name"].split("/")
        print(f"  [{i+1}/{len(repos)}] 获取 {owner}/{repo_name} README...", file=sys.stderr)
        
        readme = get_readme(token, owner, repo_name)
        
        # 格式化仓库信息
        repo_info = format_repo_info(repo, readme)
        results.append(repo_info)
    
    # 输出JSON结果
    output = {
        "repos": results,
        "search_params": {
            "start_date": start_date,
            "end_date": end_date,
            "query": args.query,
            "sort": args.sort,
            "limit": args.limit
        }
    }
    
    print(json.dumps(output, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
