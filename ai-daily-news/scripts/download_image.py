#!/usr/bin/env python3
"""
下载单个图片到本地

用法:
    python download_image.py --url <IMAGE_URL> --output <OUTPUT_PATH>

参数:
    --url: 图片的完整URL（必需）
    --output: 本地保存路径（必需）
    --timeout: 请求超时时间（秒，默认30）
"""

import argparse
import os
import sys
from pathlib import Path

import requests


def download_image(url, output_path, timeout=30):
    """
    下载图片到本地
    
    Args:
        url: 图片URL
        output_path: 输出路径
        timeout: 请求超时时间（秒）
    
    Returns:
        str: 保存的文件路径
    
    Raises:
        Exception: 下载失败时抛出异常
    """
    # 创建输出目录
    output_dir = os.path.dirname(output_path)
    if output_dir:
        Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    # 发送请求
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=timeout, stream=True)
        response.raise_for_status()
        
        # 检查内容类型
        content_type = response.headers.get('content-type', '')
        if not content_type.startswith('image/'):
            raise Exception(f"URL不是图片: {content_type}")
        
        # 获取文件大小
        content_length = int(response.headers.get('content-length', 0))
        if content_length > 10 * 1024 * 1024:  # 限制10MB
            raise Exception(f"图片过大: {content_length / 1024 / 1024:.2f}MB")
        
        # 保存文件
        with open(output_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
        
        # 验证文件大小
        file_size = os.path.getsize(output_path)
        if file_size == 0:
            raise Exception("下载的文件为空")
        
        print(f"成功下载: {output_path} ({file_size / 1024:.1f}KB)", file=sys.stderr)
        return output_path
        
    except requests.exceptions.Timeout:
        raise Exception(f"下载超时: {url}")
    except requests.exceptions.RequestException as e:
        raise Exception(f"下载失败: {str(e)}")
    except Exception as e:
        raise Exception(f"保存失败: {str(e)}")


def main():
    parser = argparse.ArgumentParser(description="下载单个图片到本地")
    parser.add_argument("--url", required=True, help="图片的完整URL")
    parser.add_argument("--output", required=True, help="本地保存路径")
    parser.add_argument("--timeout", type=int, default=30, help="请求超时时间（秒）")
    
    args = parser.parse_args()
    
    try:
        download_image(args.url, args.output, args.timeout)
        sys.exit(0)
    except Exception as e:
        print(f"错误: {str(e)}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
