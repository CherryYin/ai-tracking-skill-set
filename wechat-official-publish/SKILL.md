---
name: wechat-official-publish
description: 通过微信公众号官方 API 发布文章到公众号，支持草稿创建、预览、正式发布全流程
dependency:
  python:
    - requests>=2.28.0
  system: []
---

# 微信公众号官方发布

## 任务目标
本 Skill 用于：
- 通过微信公众号官方 API 发布文章
- 支持草稿创建、预览、正式发布全流程
- 自动处理图片上传、素材管理

触发条件：
- "发布到公众号"
- "推送文章到微信"
- "公众号发文"

## 前置准备

### 1. 公众号要求
- **必须是服务号**（订阅号无发布 API 权限）
- **已完成微信认证**
- 已开通开发者权限

### 2. 获取 API 凭证
登录 [微信公众平台](https://mp.weixin.qq.com/) → 开发 → 基本配置：

- **AppID** (appid)
- **AppSecret** (appsecret)
- **IP 白名单**：添加服务器 IP

### 3. 配置凭证
将以下信息保存到 TOOLS.md 或环境变量：

```bash
# 微信公众号 API 凭证
export WECHAT_APPID="your_appid"
export WECHAT_APPSECRET="your_appsecret"
export WECHAT_TOKEN_URL="https://api.weixin.qq.com/cgi-bin/token"
```

## 操作步骤

### 步骤 1：获取 Access Token

```bash
curl -G "https://api.weixin.qq.com/cgi-bin/token" \
  -d "grant_type=client_credential" \
  -d "appid=YOUR_APPID" \
  -d "secret=YOUR_APPSECRET"
```

返回：
```json
{
  "access_token": "ACCESS_TOKEN",
  "expires_in": 7200
}
```

**注意**：access_token 有效期 2 小时，需要缓存复用

### 步骤 2：上传图片（可选）

如果文章包含本地图片，需要先上传到微信素材库：

```bash
curl -F "media=@image.jpg" \
  "https://api.weixin.qq.com/cgi-bin/media/uploadimg?access_token=ACCESS_TOKEN"
```

返回图片 URL，用于文章中引用

### 步骤 3：创建草稿

```bash
curl -X POST "https://api.weixin.qq.com/cgi-bin/draft/add?access_token=ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "articles": [
      {
        "title": "文章标题",
        "author": "作者名",
        "digest": "摘要",
        "content": "正文内容（HTML 格式，图片用 URL）",
        "content_source_url": "原文链接",
        "thumb_media_id": "封面图片 ID"
      }
    ]
  }'
```

返回 `media_id` 用于发布

### 步骤 4：正式发布

```bash
curl -X POST "https://api.weixin.qq.com/cgi-bin/freepublish/submit?access_token=ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "media_id": "草稿的 media_id",
    "preview": false
  }'
```

### 步骤 5：发送预览（可选）

发布前可先发送预览到指定微信号：

```bash
curl -X POST "https://api.weixin.qq.com/cgi-bin/draft/preview?access_token=ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "media_id": "草稿的 media_id",
    "preview_to_user": "微信号"
  }'
```

## Python 脚本示例

创建 `scripts/wechat_publish.py`：

```python
#!/usr/bin/env python3
"""微信公众号发布脚本"""

import requests
import json
import sys

class WechatPublisher:
    def __init__(self, appid, appsecret):
        self.appid = appid
        self.appsecret = appsecret
        self.token = None
        self.token_url = "https://api.weixin.qq.com/cgi-bin/token"
        
    def get_access_token(self):
        """获取 access_token"""
        params = {
            "grant_type": "client_credential",
            "appid": self.appid,
            "secret": self.appsecret
        }
        resp = requests.get(self.token_url, params=params)
        data = resp.json()
        if "access_token" in data:
            self.token = data["access_token"]
            return self.token
        else:
            raise Exception(f"获取 token 失败：{data}")
    
    def upload_image(self, image_path):
        """上传图片到微信素材库"""
        url = f"https://api.weixin.qq.com/cgi-bin/media/uploadimg?access_token={self.token}"
        with open(image_path, 'rb') as f:
            files = {'media': f}
            resp = requests.post(url, files=files)
        data = resp.json()
        return data.get('url')
    
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
        resp = requests.post(url, json=data)
        result = resp.json()
        return result.get('media_id')
    
    def publish(self, media_id, preview_to_user=None):
        """发布文章"""
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
            
        resp = requests.post(url, json=data)
        result = resp.json()
        return result
    
    def publish_article(self, title, content, author="AI 日报", digest=None, 
                       preview_to_user=None, image_paths=None):
        """完整发布流程"""
        # 1. 获取 token
        self.get_access_token()
        
        # 2. 上传图片（如果有）
        thumb_media_id = None
        if image_paths:
            for img_path in image_paths:
                img_url = self.upload_image(img_path)
                print(f"上传图片：{img_path} -> {img_url}")
        
        # 3. 创建草稿
        media_id = self.create_draft(title, content, author, digest, thumb_media_id)
        print(f"草稿创建成功，media_id: {media_id}")
        
        # 4. 发布或预览
        if preview_to_user:
            result = self.publish(media_id, preview_to_user)
            print(f"预览已发送到：{preview_to_user}")
        else:
            result = self.publish(media_id)
            print("文章已正式发布")
            
        return result

if __name__ == "__main__":
    import os
    
    appid = os.getenv("WECHAT_APPID")
    appsecret = os.getenv("WECHAT_APPSECRET")
    
    if not appid or not appsecret:
        print("错误：请配置 WECHAT_APPID 和 WECHAT_APPSECRET 环境变量")
        sys.exit(1)
    
    publisher = WechatPublisher(appid, appsecret)
    
    # 示例：发布文章
    title = "AI 日报 - " + sys.argv[1] if len(sys.argv) > 1 else "AI 日报"
    content = "<h1>测试文章</h1><p>这是内容</p>"
    
    result = publisher.publish_article(title, content)
    print(json.dumps(result, indent=2))
```

## 使用示例

### 示例 1：发布 AI 日报到公众号

```bash
# 配置环境变量
export WECHAT_APPID="wx_xxxxxxxxxxxx"
export WECHAT_APPSECRET="xxxxxxxxxxxxxxxxxxxx"

# 发布文章
python scripts/wechat_publish.py "2026-03-30 AI 日报"
```

### 示例 2：先发送预览再发布

```bash
# 在 publish_article 中设置 preview_to_user="your_wechat_id"
# 确认预览无误后，再正式调用发布
```

### 示例 3：在 OpenClaw Agent 中使用

```python
# 在 agent 中调用
exec: python3 /home/ubuntu/.openclaw/workspace-content-master/skills/wechat-official-publish/scripts/wechat_publish.py --title "AI 日报" --content-file /path/to/article.md
```

## API 文档参考

- [access_token 获取](https://developers.weixin.qq.com/doc/offiaccount/Basic_Information/Get_access_token.html)
- [草稿箱 API](https://developers.weixin.qq.com/doc/offiaccount/Draft_Box/Add_draft.html)
- [发布 API](https://developers.weixin.qq.com/doc/offiaccount/Draft_Box/Submit_release.html)
- [预览 API](https://developers.weixin.qq.com/doc/offiaccount/Draft_Box/Preview_draft.html)
- [图片上传](https://developers.weixin.qq.com/doc/offiaccount/Asset_Management/New_temporary_materials.html)

## 注意事项

### 权限限制
- **订阅号没有发布 API 权限**，只能用订阅号助手 APP 手动发
- 服务号必须完成微信认证
- IP 必须在白名单中

### 速率限制
- access_token 调用：2000 次/秒
- 发布接口：有限制，不要频繁调用
- 图片上传：有限制

### 内容规范
- 文章标题：1-64 字
- 摘要：0-120 字
- 内容支持 HTML，但部分标签受限
- 图片建议先上传到素材库

### Token 管理
- access_token 有效期 2 小时
- 建议缓存到文件，避免重复获取
- 失效后自动重新获取

## 错误处理

常见错误码：
- `40001`: appsecret 错误
- `40013`: appid 错误
- `40164`: IP 不在白名单
- `45009`: 调用频率超限
- `40007`: 素材 ID 不存在
