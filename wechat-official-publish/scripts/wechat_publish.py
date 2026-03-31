#!/usr/bin/env python3
"""
微信公众号发布脚本
支持：获取 token、上传图片、创建草稿、正式发布、发送预览
"""

import requests
import json
import sys
import os
import argparse
from datetime import datetime

class WechatPublisher:
    def __init__(self, appid, appsecret):
        self.appid = appid
        self.appsecret = appsecret
        self.token = None
        self.token_cache_file = "/tmp/wechat_access_token.json"
        self.token_url = "https://api.weixin.qq.com/cgi-bin/token"
        
    def get_access_token(self, force_refresh=False):
        """获取 access_token（带缓存）"""
        # 尝试从缓存读取
        if not force_refresh and os.path.exists(self.token_cache_file):
            try:
                with open(self.token_cache_file, 'r') as f:
                    cache = json.load(f)
                    # 检查是否过期（提前 5 分钟刷新）
                    if datetime.now().timestamp() < cache.get('expires_at', 0) - 300:
                        self.token = cache.get('access_token')
                        print(f"✓ 使用缓存的 access_token")
                        return self.token
            except Exception as e:
                print(f"缓存读取失败：{e}")
        
        # 重新获取
        print("正在获取新的 access_token...")
        params = {
            "grant_type": "client_credential",
            "appid": self.appid,
            "secret": self.appsecret
        }
        resp = requests.get(self.token_url, params=params, timeout=10)
        data = resp.json()
        
        if "access_token" in data:
            self.token = data["access_token"]
            expires_in = data.get("expires_in", 7200)
            # 缓存到文件
            cache_data = {
                "access_token": self.token,
                "expires_at": datetime.now().timestamp() + expires_in
            }
            with open(self.token_cache_file, 'w') as f:
                json.dump(cache_data, f)
            print(f"✓ access_token 获取成功，有效期 {expires_in}秒")
            return self.token
        else:
            raise Exception(f"获取 token 失败：{data}")
    
    def upload_image(self, image_path):
        """上传图片到微信素材库"""
        if not os.path.exists(image_path):
            raise Exception(f"图片文件不存在：{image_path}")
            
        url = f"https://api.weixin.qq.com/cgi-bin/media/uploadimg?access_token={self.token}"
        with open(image_path, 'rb') as f:
            files = {'media': f}
            resp = requests.post(url, files=files, timeout=30)
        
        data = resp.json()
        if 'url' in data:
            print(f"✓ 图片上传成功：{image_path} -> {data['url']}")
            return data['url']
        else:
            print(f"⚠ 图片上传失败：{data}")
            return None
    
    def create_draft(self, title, content, author=None, digest=None, thumb_media_id=None):
        """创建草稿"""
        url = f"https://api.weixin.qq.com/cgi-bin/draft/add?access_token={self.token}"
        article = {
            "title": title,
            "content": content,
        }
        if author:
            article["author"] = author
        if digest:
            article["digest"] = digest
        if thumb_media_id:
            article["thumb_media_id"] = thumb_media_id
            
        data = {
            "articles": [article]
        }
        resp = requests.post(url, json=data, timeout=30)
        result = resp.json()
        
        if 'media_id' in result:
            print(f"✓ 草稿创建成功，media_id: {result['media_id']}")
            return result['media_id']
        else:
            print(f"✗ 草稿创建失败：{result}")
            return None
    
    def publish(self, media_id, preview_to_user=None):
        """发布文章或发送预览"""
        if preview_to_user:
            # 发送预览
            url = f"https://api.weixin.qq.com/cgi-bin/draft/preview?access_token={self.token}"
            data = {
                "media_id": media_id,
                "preview_to_user": preview_to_user
            }
            action = "preview"
        else:
            # 正式发布
            url = f"https://api.weixin.qq.com/cgi-bin/freepublish/submit?access_token={self.token}"
            data = {
                "media_id": media_id,
                "preview": False
            }
            action = "publish"
            
        resp = requests.post(url, json=data, timeout=30)
        result = resp.json()
        
        if result.get('errcode', 0) == 0:
            print(f"✓ {action} 成功")
            return {"success": True, "action": action, "result": result}
        else:
            print(f"✗ {action} 失败：{result}")
            return {"success": False, "action": action, "error": result}
    
    def publish_article(self, title, content, author="AI 日报", digest=None, 
                       preview_to_user=None, image_paths=None, force_refresh_token=False):
        """完整发布流程"""
        try:
            # 1. 获取 token
            self.get_access_token(force_refresh=force_refresh_token)
            
            # 2. 上传图片（如果有）
            thumb_media_id = None
            if image_paths:
                for img_path in image_paths:
                    img_url = self.upload_image(img_path)
                    if img_url and not thumb_media_id:
                        # 第一张图作为封面（需要额外上传到素材库获取 media_id）
                        # 这里简化处理，直接用 URL
                        pass
            
            # 3. 创建草稿
            media_id = self.create_draft(title, content, author, digest, thumb_media_id)
            if not media_id:
                return {"success": False, "error": "草稿创建失败"}
            
            # 4. 发布或预览
            result = self.publish(media_id, preview_to_user)
            return result
            
        except Exception as e:
            print(f"✗ 发布失败：{e}")
            return {"success": False, "error": str(e)}


def markdown_to_html(md_content):
    """简单将 Markdown 转换为 HTML（基础版本）"""
    html = md_content
    # 标题
    import re
    html = re.sub(r'^### (.*?)$', r'<h3>\1</h3>', html, flags=re.MULTILINE)
    html = re.sub(r'^## (.*?)$', r'<h2>\1</h2>', html, flags=re.MULTILINE)
    html = re.sub(r'^# (.*?)$', r'<h1>\1</h1>', html, flags=re.MULTILINE)
    # 粗体
    html = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', html)
    # 链接
    html = re.sub(r'\[(.*?)\]\((.*?)\)', r'<a href="\2">\1</a>', html)
    # 图片
    html = re.sub(r'!\[(.*?)\]\((.*?)\)', r'<img src="\2" alt="\1"/>', html)
    # 段落
    html = re.sub(r'\n\n', r'</p><p>', html)
    html = f'<p>{html}</p>'
    return html


def main():
    parser = argparse.ArgumentParser(description='微信公众号发布工具')
    parser.add_argument('--title', required=True, help='文章标题')
    parser.add_argument('--content', help='文章内容（Markdown 格式）')
    parser.add_argument('--content-file', help='文章内容文件路径')
    parser.add_argument('--author', default='AI 日报', help='作者名')
    parser.add_argument('--digest', help='文章摘要')
    parser.add_argument('--preview-to', help='预览发送到的微信号')
    parser.add_argument('--image', action='append', help='图片路径（可多次）')
    parser.add_argument('--publish', action='store_true', help='直接发布（否则仅创建草稿）')
    parser.add_argument('--appid', help='微信公众号 AppID')
    parser.add_argument('--appsecret', help='微信公众号 AppSecret')
    
    args = parser.parse_args()
    
    # 获取凭证（参数或环境变量）
    appid = args.appid or os.getenv('WECHAT_APPID')
    appsecret = args.appsecret or os.getenv('WECHAT_APPSECRET')
    
    if not appid or not appsecret:
        print("错误：请配置 WECHAT_APPID 和 WECHAT_APPSECRET")
        print("用法：")
        print("  1. 通过参数：--appid xxx --appsecret xxx")
        print("  2. 通过环境变量：export WECHAT_APPID=xxx && export WECHAT_APPSECRET=xxx")
        sys.exit(1)
    
    # 获取内容
    content = args.content
    if not content and args.content_file:
        if os.path.exists(args.content_file):
            with open(args.content_file, 'r', encoding='utf-8') as f:
                content = f.read()
        else:
            print(f"错误：文件不存在 {args.content_file}")
            sys.exit(1)
    
    if not content:
        print("错误：请提供文章内容（--content 或 --content-file）")
        sys.exit(1)
    
    # 转换 Markdown 为 HTML
    html_content = markdown_to_html(content)
    
    # 创建发布器
    publisher = WechatPublisher(appid, appsecret)
    
    # 发布
    preview_user = args.preview_to if not args.publish else None
    result = publisher.publish_article(
        title=args.title,
        content=html_content,
        author=args.author,
        digest=args.digest,
        preview_to_user=preview_user,
        image_paths=args.image
    )
    
    # 输出结果
    print("\n=== 发布结果 ===")
    print(json.dumps(result, indent=2, ensure_ascii=False))
    
    if result.get('success'):
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()
