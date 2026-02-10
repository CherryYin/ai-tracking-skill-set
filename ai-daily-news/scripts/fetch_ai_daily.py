#!/usr/bin/env python3
"""
AI热点新闻与论文聚合工具
从多个数据源获取AI相关内容并生成聚合报告
"""

import argparse
import json
import os
import re
import sys
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from urllib.parse import urljoin, urlparse

import feedparser
import requests
from bs4 import BeautifulSoup
from openai import OpenAI

# ====================== 配置 ======================
DEFAULT_MODEL = "doubao-seed-1-8-251228"
DEFAULT_OUTPUT = "ai_daily_news.json"
DEFAULT_HN_LIMIT = 8  # 默认获取8条新闻
DEFAULT_ARXIV_LIMIT = 2  # 默认获取2篇论文
DEFAULT_IMAGE_OUTPUT_DIR = "./images"

# 预设的国内新闻源（RSS feed）
PREDEFINED_SOURCES = {
    "36kr-ai": {
        "name": "36氪AI",
        "url": "https://36kr.com/information/AI/",
        "type": "html"  # 需要解析HTML页面
    },
    "sina-tech": {
        "name": "新浪科技",
        "url": "https://tech.sina.com.cn/",
        "type": "html"
    },
    "zhihu-daily": {
        "name": "知乎日报",
        "url": "https://daily.zhihu.com/",
        "type": "html"
    }
}

# ====================== Hacker News API ======================
def fetch_hacker_news(limit: int = 10, days_back: int = 1) -> List[Dict]:
    """从Hacker News获取AI相关新闻"""
    base_url = "https://hn.algolia.com/api/v1/search"
    
    # 使用简单查询关键词
    query = "AI"
    
    try:
        # 获取数据，按points排序获取热门内容
        response = requests.get(base_url, params={
            "query": query,
            "tags": "story",
            "hitsPerPage": limit * 20  # 获取更多数据以便筛选
        }, timeout=10)
        
        response.raise_for_status()
        data = response.json()
        
        hits = data.get("hits", [])
        
        # 计算时间过滤阈值（最近6个月）
        cutoff_date = datetime.utcnow() - timedelta(days=180)
        
        # 按points排序后过滤
        hits_sorted = sorted(hits, key=lambda x: x.get("points", 0), reverse=True)
        
        # 过滤和转换结果
        entries = []
        seen_urls = set()
        
        for hit in hits_sorted:
            url = hit.get("url", f"https://news.ycombinator.com/item?id={hit.get('objectID')}")
            
            # 去重
            if url in seen_urls:
                continue
            seen_urls.add(url)
            
            # 解析日期并进行时间过滤
            created_timestamp = hit.get("created_at_i", 0)
            if created_timestamp:
                created_at = datetime.fromtimestamp(created_timestamp)
                # 只保留最近6个月内的新闻
                if created_at < cutoff_date:
                    continue
            else:
                created_at = datetime.utcnow()  # fallback
            
            # 提取图片（从OG标签）
            image = None
            try:
                page_resp = requests.get(url, timeout=5, allow_redirects=True)
                if page_resp.status_code == 200:
                    soup = BeautifulSoup(page_resp.text, 'html.parser')
                    og_image = soup.find('meta', property='og:image')
                    if og_image and og_image.get('content'):
                        image = og_image['content']
            except:
                pass
            
            entries.append({
                "title": hit.get("title", "No title"),
                "url": url,
                "summary": hit.get("points", 0),
                "points": hit.get("points", 0),
                "created_at": created_at.strftime("%Y-%m-%d %H:%M:%S"),
                "source": "hacker_news",
                "type": "news",
                "image": image
            })
            
            if len(entries) >= limit:
                break
        
        print(f"✓ 从 Hacker News 获取 {len(entries)} 条新闻")
        return entries
    
    except Exception as e:
        print(f"✗ Hacker News 获取失败: {e}")
        return []


# ====================== ArXiv API ======================
def fetch_arxiv_papers(query: str = "artificial intelligence OR machine learning", 
                       limit: int = 10,
                       max_results: int = 20,
                       target_date: Optional[str] = None) -> List[Dict]:
    """从ArXiv获取最新论文（默认最近一个月）"""
    base_url = "http://export.arxiv.org/api/query"
    
    # ArXiv API参数
    params = {
        "search_query": f"all:{query}",
        "start": 0,
        "max_results": max_results,
        "sortBy": "submittedDate",
        "sortOrder": "descending"
    }
    
    try:
        response = requests.get(base_url, params=params, timeout=15)
        response.raise_for_status()
        
        feed = feedparser.parse(response.content)
        
        entries = []
        seen_ids = set()
        
        # 计算一个月前的日期
        one_month_ago = datetime.utcnow() - timedelta(days=30)
        
        for entry in feed.entries[:max_results]:
            # 提取ArXiv ID
            arxiv_id = entry.get("id", "").split("/abs/")[-1].split("/v")[0]
            if arxiv_id in seen_ids:
                continue
            seen_ids.add(arxiv_id)
            
            # 解析日期
            published = entry.get("published")
            try:
                if published:
                    pub_date = datetime.strptime(published, "%Y-%m-%dT%H:%M:%SZ")
                else:
                    pub_date = datetime.utcnow()
            except:
                pub_date = datetime.utcnow()
            
            # 日期过滤
            if target_date:
                try:
                    target = datetime.strptime(target_date, "%Y-%m-%d")
                    # 只获取当天的论文
                    if pub_date.date() != target.date():
                        continue
                except ValueError:
                    print(f"⚠ 无效的目标日期格式: {target_date}")
                    return []
            else:
                # 默认只获取最近一个月的论文
                if pub_date < one_month_ago:
                    continue
            
            # 提取摘要
            summary = entry.get("summary", "").replace("\n", " ").strip()
            
            # 提取作者
            authors = ", ".join([author.name for author in entry.get("authors", [])])
            
            # 抽取图片（从HTML页面）
            images = extract_arxiv_images(arxiv_id)
            
            entries.append({
                "title": entry.get("title", ""),
                "url": f"https://arxiv.org/abs/{arxiv_id}",
                "arxiv_id": arxiv_id,
                "summary": summary[:300] + "..." if len(summary) > 300 else summary,
                "authors": authors,
                "published": pub_date.strftime("%Y-%m-%d"),
                "source": "arxiv",
                "type": "paper",
                "images": images  # 支持多张图片
            })
            
            if len(entries) >= limit:
                break
        
        print(f"✓ 从 ArXiv 获取 {len(entries)} 篇论文")
        return entries
    
    except Exception as e:
        print(f"✗ ArXiv 获取失败: {e}")
        return []


def extract_arxiv_images(arxiv_id: str) -> List[str]:
    """从ArXiv论文HTML页面提取架构图和流程图"""
    try:
        # 访问ArXiv HTML版本（注意：添加trailing slash以确保urljoin正确工作）
        html_url = f"https://arxiv.org/html/{arxiv_id}/"
        response = requests.get(html_url, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 查找所有图片
        images = []
        for img in soup.find_all('img'):
            src = img.get('src', '')
            
            # 过滤 base64 数据URL
            if src.startswith('data:'):
                continue
            
            # 构建完整URL
            if src.startswith('http'):
                image_url = src
            elif src.startswith('//'):
                image_url = f"https:{src}"
            else:
                # 相对路径，使用urljoin处理
                image_url = urljoin(html_url, src)
            
            # 过滤掉公式图（通常包含 formula、inline 等关键词）
            if any(keyword in src.lower() for keyword in ['formula', 'inline', 'math', 'tex', 'equation']):
                continue
            
            # 过滤掉小图标（通常文件名包含 icon）
            if 'icon' in src.lower():
                continue
            
            # 获取图片尺寸
            width = int(img.get('width', 0)) or int(img.get('data-width', 0)) or 0
            height = int(img.get('height', 0)) or int(img.get('data-height', 0)) or 0
            
            # 只保留较大的图片（可能是架构图或流程图）
            if width > 0 and height > 0:
                if width < 200 or height < 200:
                    continue
            
            images.append(image_url)
        
        # 最多返回5张图片
        return list(set(images))[:5]  # 去重后最多5张
    
    except Exception as e:
        print(f"  ⚠ 无法提取 {arxiv_id} 的图片: {e}")
        return []


# ====================== 自定义新闻源 ======================
def fetch_custom_news_source(custom_url: str, 
                             source_name: str = "custom",
                             limit: int = 10) -> List[Dict]:
    """从自定义URL获取新闻（支持JSON API和RSS/Atom feed）"""
    
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        
        response = requests.get(custom_url, headers=headers, timeout=10)
        response.raise_for_status()
        
        # 尝试解析为RSS/Atom feed
        feed = feedparser.parse(response.content)
        if feed.entries:
            entries = []
            for entry in feed.entries[:limit]:
                url = entry.get('link', '')
                title = entry.get('title', '')
                summary = entry.get('summary', entry.get('description', ''))
                
                # 尝试提取图片
                image = None
                if hasattr(entry, 'enclosures') and entry.enclosures:
                    for enc in entry.enclosures:
                        if enc.get('type', '').startswith('image/'):
                            image = enc.get('href')
                            break
                
                entries.append({
                    "title": title,
                    "url": url,
                    "summary": summary[:500] if summary else '',
                    "source": source_name,
                    "type": "news",
                    "image": image,
                    "created_at": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
                })
            
            print(f"✓ 从自定义源 ({source_name}) 获取 {len(entries)} 条新闻")
            return entries
        
        # 尝试解析为JSON API
        try:
            data = response.json()
            # 尝试不同的数据结构
            items = []
            if isinstance(data, dict):
                for key in ['data', 'items', 'results', 'articles']:
                    if key in data:
                        items = data.get(key, [])
                        if not isinstance(items, list):
                            items = []
                        break
            
            entries = []
            for item in items[:limit]:
                # 提取字段（支持多种格式）
                title_field = item.get('title') or item.get('name') or item.get('headline') or ''
                title = title_field.strip() if title_field else ''
                
                url = item.get('url') or item.get('link') or item.get('href') or item.get('sourceUrl') or ''
                
                summary_field = item.get('summary') or item.get('description') or item.get('content') or item.get('abstract') or ''
                summary = summary_field[:500] if summary_field else ''
                
                # 提取发布时间
                published = item.get('published') or item.get('publish_time') or item.get('created_at') or item.get('pubDate') or item.get('date')
                try:
                    if isinstance(published, str):
                        # 尝试多种时间格式
                        for fmt in ['%Y-%m-%dT%H:%M:%S.%f%z', '%Y-%m-%dT%H:%M:%S%z', '%Y-%m-%d', '%a, %d %b %Y %H:%M:%S %z']:
                            try:
                                pub_time = datetime.strptime(published[:30], fmt)
                                break
                            except:
                                continue
                    else:
                        pub_time = published
                except:
                    pub_time = datetime.utcnow()
                
                # 尝试提取图片
                image = item.get('image') or item.get('imageUrl') or item.get('thumbnail') or item.get('imgUrl') or ''
                
                entries.append({
                    "title": title,
                    "url": url,
                    "summary": summary,
                    "source": source_name,
                    "type": "news",
                    "image": image,
                    "created_at": pub_time.strftime("%Y-%m-%d %H:%M:%S") if pub_time else datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
                })
            
            print(f"✓ 从自定义源 ({source_name}) 获取 {len(entries)} 条新闻")
            return entries
        
        except json.JSONDecodeError:
            print(f"✗ 自定义源 ({source_name}) 无法解析: 既不是有效的RSS/Atom feed也不是JSON API")
            return []
    
    except Exception as e:
        print(f"✗ 自定义源 ({source_name}) 获取失败: {e}")
        return []


# ====================== 国内新闻源解析 ======================
def fetch_domestic_news(source_key: str, limit: int = 10) -> List[Dict]:
    """从预设的国内新闻源获取AI相关新闻"""
    
    if source_key not in PREDEFINED_SOURCES:
        print(f"✗ 未知的国内新闻源: {source_key}")
        return []
    
    source = PREDEFINED_SOURCES[source_key]
    url = source["url"]
    source_name = source["name"]
    
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        entries = []
        
        # AI关键词过滤
        ai_keywords = ['AI', '人工智能', '机器学习', '深度学习', 'LLM', '大模型', '智能', 'ChatGPT', 'GPT']
        
        # 通用解析：查找所有带标题和链接的元素
        seen_urls = set()
        link_count = 0
        
        for link in soup.find_all('a', href=True):
            if link_count >= limit * 3:  # 多获取一些以便筛选
                break
            
            href = link.get('href', '')
            title = link.get_text(strip=True)
            
            # 过滤掉太短的标题和不是新闻的链接
            if len(title) < 10 or len(title) > 100 or not href:
                continue
            
            # 过滤掉导航、页脚等链接
            skip_keywords = ['登录', '注册', '首页', '关于', '联系', '友情链接', '广告', '合作', '招聘']
            if any(keyword in title for keyword in skip_keywords):
                continue
            
            # 只保留包含AI相关关键词的标题
            if not any(keyword in title for keyword in ai_keywords):
                continue
            
            # 去重
            if href in seen_urls:
                continue
            seen_urls.add(href)
            
            if not href.startswith('http'):
                href = urljoin(url, href)
            
            entries.append({
                "title": title,
                "url": href,
                "summary": '',
                "source": source_name,
                "type": "news",
                "image": '',
                "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            })
            
            link_count += 1
            
            if len(entries) >= limit:
                break
        
        print(f"✓ 从国内源 ({source_name}) 获取 {len(entries)} 条新闻")
        return entries
    
    except Exception as e:
        print(f"✗ 国内源 ({source_name}) 获取失败: {e}")
        import traceback
        traceback.print_exc()
        return []


# ====================== 数据整合 ======================
def merge_and_sort_entries(hn_entries: List[Dict], 
                          arxiv_entries: List[Dict],
                          custom_entries: List[Dict] = None,
                          domestic_entries: List[Dict] = None) -> List[Dict]:
    """合并并排序所有条目"""
    
    all_entries = hn_entries + arxiv_entries
    
    # 添加自定义源数据
    if custom_entries:
        all_entries += custom_entries
    
    # 添加国内新闻源数据
    if domestic_entries:
        all_entries += domestic_entries
    
    # 按时间排序
    sorted_entries = sorted(all_entries, key=lambda x: x.get('created_at', ''), reverse=True)
    
    # 去重（基于URL）
    seen = set()
    unique_entries = []
    for entry in sorted_entries:
        url = entry.get('url', '')
        if url not in seen:
            seen.add(url)
            unique_entries.append(entry)
    
    return unique_entries


# ====================== 文章生成 ======================
def generate_article(entries: List[Dict], 
                    model: str = DEFAULT_MODEL,
                    base_url: Optional[str] = None,
                    date: Optional[str] = None) -> str:
    """使用大模型生成深度文章"""
    
    if not entries:
        return "今天没有找到AI相关的热点内容。"
    
    # 按类型分组
    news_items = [e for e in entries if e.get('type') == 'news']
    papers = [e for e in entries if e.get('type') == 'paper']
    
    # 准备提示词
    date_str = date if date else datetime.now().strftime("%Y-%m-%d")
    
    prompt = f"""请基于以下{date_str}的AI热点新闻和最新论文，生成一篇深度文章。

## 新闻热点
{chr(10).join([f"- {n['title']}: {str(n['summary'])[:100]}... (来源: {n['source']})" for n in news_items])}

## 最新论文
{chr(10).join([f"- {p['title']}: {str(p['summary'])[:100]}... (作者: {p['authors']})" for p in papers])}

要求：
1. 以引人入胜的开头引入主题
2. 对新闻热点进行深入分析和评论
3. 选取1-2篇重要论文进行详细介绍
4. 提供对AI行业发展趋势的洞察
5. 使用Markdown格式，适当使用emoji增加可读性
6. 文章长度控制在800-1200字
7. 每段开头标记引用来源（如[Hacker News], [ArXiv]）

生成文章:"""

    try:
        # 初始化客户端
        client_kwargs = {"api_key": "dummy"}
        if base_url:
            client_kwargs["base_url"] = base_url
        
        client = OpenAI(**client_kwargs)
        
        # 调用模型
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "你是一个专业的AI领域评论员，擅长分析技术趋势和撰写深度文章。"},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=2000
        )
        
        article = response.choices[0].message.content
        
        print(f"✓ 文章生成成功 ({len(article)} 字符)")
        return article
    
    except Exception as e:
        print(f"✗ 文章生成失败: {e}")
        return f"文章生成遇到错误，以下是原始数据：\n\n{json.dumps(entries, indent=2, ensure_ascii=False)}"


# ====================== 主程序 ======================
def main():
    parser = argparse.ArgumentParser(description="AI热点新闻与论文聚合工具")
    
    # 数据源选项
    parser.add_argument("--date", type=str, default=None, 
                      help="指定目标日期 (YYYY-MM-DD)，仅用于ArXiv日期过滤")
    parser.add_argument("--custom-url", type=str, default=None,
                      help="自定义新闻源URL (支持JSON API和RSS/Atom feed)")
    parser.add_argument("--custom-source", type=str, default="custom",
                      help="自定义新闻源名称 (默认: custom)")
    parser.add_argument("--domestic-source", type=str, default=None,
                      help=f"使用预设的国内新闻源: {', '.join(PREDEFINED_SOURCES.keys())}")
    parser.add_argument("--domestic-limit", type=int, default=5,
                      help=f"国内新闻源获取数量 (默认: 5)")
    parser.add_argument("--no-hacker-news", action="store_true",
                      help="不获取Hacker News数据")
    parser.add_argument("--no-arxiv", action="store_true",
                      help="不获取ArXiv数据")
    
    # 输出选项
    parser.add_argument("--output", "-o", type=str, default=DEFAULT_OUTPUT,
                       help=f"输出JSON文件路径 (默认: {DEFAULT_OUTPUT})")
    parser.add_argument("--image-output-dir", type=str, default=DEFAULT_IMAGE_OUTPUT_DIR,
                       help=f"图片保存目录 (默认: {DEFAULT_IMAGE_OUTPUT_DIR})")
    
    # 数量选项
    parser.add_argument("--hn-limit", type=int, default=DEFAULT_HN_LIMIT,
                       help=f"Hacker News获取数量 (默认: {DEFAULT_HN_LIMIT})")
    parser.add_argument("--arxiv-limit", type=int, default=DEFAULT_ARXIV_LIMIT,
                       help=f"ArXiv论文获取数量 (默认: {DEFAULT_ARXIV_LIMIT})")
    parser.add_argument("--custom-limit", type=int, default=5,
                       help=f"自定义源获取数量 (默认: 5)")
    
    # 模型选项
    parser.add_argument("--model", type=str, default=DEFAULT_MODEL,
                       help=f"使用的模型 (默认: {DEFAULT_MODEL})")
    parser.add_argument("--base-url", type=str, default=None,
                       help="模型API的base_url")
    parser.add_argument("--no-article", action="store_true",
                       help="不生成文章，仅输出JSON数据")
    
    # 其他选项
    parser.add_argument("--days-back", type=int, default=1,
                       help=f"回溯天数 (默认: 1)")
    parser.add_argument("--download-images", action="store_true",
                       help="下载所有图片到本地目录")
    
    args = parser.parse_args()
    
    # 显示配置信息
    print("=" * 60)
    print("AI热点新闻聚合工具")
    print("=" * 60)
    print(f"📅 目标日期: {args.date or '最新'}")
    print(f"🤖 模型: {args.model}")
    if args.base_url:
        print(f"🌐 Base URL: {args.base_url}")
    if args.custom_url:
        print(f"🔗 自定义新闻源: {args.custom_url} ({args.custom_source})")
    if args.domestic_source:
        print(f"🇨🇳 国内新闻源: {args.domestic_source}")
    print(f"📊 Hacker News: {args.hn_limit if not args.no_hacker_news else 0} 条")
    print(f"📚 ArXiv: {args.arxiv_limit if not args.no_arxiv else 0} 条")
    if args.custom_url:
        print(f"📰 自定义源: {args.custom_limit} 条")
    if args.domestic_source:
        print(f"📰 国内源: {args.domestic_limit} 条")
    print("=" * 60)
    
    # 获取数据
    hn_entries = []
    if not args.no_hacker_news:
        hn_entries = fetch_hacker_news(limit=args.hn_limit, days_back=args.days_back)
    
    arxiv_entries = []
    if not args.no_arxiv:
        arxiv_entries = fetch_arxiv_papers(limit=args.arxiv_limit, max_results=20, target_date=args.date)
    
    # 获取自定义源数据
    custom_entries = []
    if args.custom_url:
        custom_entries = fetch_custom_news_source(
            args.custom_url,
            source_name=args.custom_source,
            limit=args.custom_limit
        )
    
    # 获取国内新闻源数据
    domestic_entries = []
    if args.domestic_source:
        domestic_entries = fetch_domestic_news(
            args.domestic_source,
            limit=args.domestic_limit
        )
    
    # 整合数据
    all_entries = merge_and_sort_entries(hn_entries, arxiv_entries, custom_entries, domestic_entries)
    
    # 下载图片
    if args.download_images:
        os.makedirs(args.image_output_dir, exist_ok=True)
        
        image_count = 0
        for entry in all_entries:
            # 处理单张图片 (Hacker News)
            image_url = entry.get('image')
            if image_url:
                try:
                    img_resp = requests.get(image_url, timeout=5)
                    if img_resp.status_code == 200:
                        # 生成文件名
                        ext = os.path.splitext(urlparse(image_url).path)[1] or '.jpg'
                        filename = f"{entry['source']}_{entry['type']}_0{ext}"
                        filepath = os.path.join(args.image_output_dir, filename)
                        
                        with open(filepath, 'wb') as f:
                            f.write(img_resp.content)
                        
                        print(f"  ✓ 下载图片: {filename}")
                        image_count += 1
                except Exception as e:
                    print(f"  ✗ 下载图片失败 ({image_url}): {e}")
            
            # 处理多张图片 (ArXiv)
            images = entry.get('images', [])
            for i, image_url in enumerate(images):
                try:
                    img_resp = requests.get(image_url, timeout=5)
                    if img_resp.status_code == 200:
                        # 生成文件名
                        ext = os.path.splitext(urlparse(image_url).path)[1] or '.jpg'
                        filename = f"{entry['source']}_{entry['type']}_0{i+1}{ext}"
                        filepath = os.path.join(args.image_output_dir, filename)
                        
                        with open(filepath, 'wb') as f:
                            f.write(img_resp.content)
                        
                        print(f"  ✓ 下载图片: {filename}")
                        image_count += 1
                except Exception as e:
                    print(f"  ✗ 下载图片失败 ({image_url}): {e}")
        
        print(f"✓ 共下载 {image_count} 张图片到 {args.image_output_dir}/")
    
    # 输出JSON
    with open(args.output, 'w', encoding='utf-8') as f:
        json.dump({
            "date": args.date or datetime.now().strftime("%Y-%m-%d"),
            "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "entries": all_entries,
            "stats": {
                "total": len(all_entries),
                "news": len([e for e in all_entries if e.get('type') == 'news']),
                "papers": len([e for e in all_entries if e.get('type') == 'paper'])
            }
        }, f, indent=2, ensure_ascii=False)
    
    print(f"✓ 数据已保存到 {args.output}")
    print("=" * 60)
    
    # 生成文章
    if not args.no_article:
        print("\n🤖 正在生成文章...\n")
        article = generate_article(all_entries, model=args.model, base_url=args.base_url, date=args.date)
        print("\n" + "=" * 60)
        print("生成的文章:")
        print("=" * 60)
        print(article)
        print("=" * 60)
        
        # 保存文章
        article_file = args.output.replace('.json', '_article.md')
        with open(article_file, 'w', encoding='utf-8') as f:
            f.write(article)
        print(f"✓ 文章已保存到 {article_file}")


if __name__ == "__main__":
    main()
