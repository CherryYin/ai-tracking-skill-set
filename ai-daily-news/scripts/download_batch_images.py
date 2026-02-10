#!/usr/bin/env python3
"""
批量下载图片

用法:
    # 从JSON文件中批量下载图片
    python download_batch_images.py --input ./data.json --output ./images
    
    # 指定日期
    python download_batch_images.py --input ./data.json --output ./images --date 2025-02-07
"""

import argparse
import json
import os
import sys
from pathlib import Path

# 添加scripts目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from download_image import download_image


def download_images_from_data(data_file, output_dir, date_str=None):
    """
    从数据文件中批量下载图片
    
    Args:
        data_file: JSON数据文件路径
        output_dir: 输出目录
        date_str: 日期字符串（用于文件命名）
    """
    # 创建输出目录
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    # 读取数据
    with open(data_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # 提取entries列表
    entries = data.get("entries", data) if isinstance(data, dict) else data
    
    print(f"找到 {len(entries)} 条数据", file=sys.stderr)
    
    success_count = 0
    fail_count = 0
    
    # 遍历每个条目
    for idx, entry in enumerate(entries, 1):
        title = entry.get("title", "")[:50]
        source = entry.get("source", "")
        
        print(f"\n[{idx}] {source}: {title}", file=sys.stderr)
        
        # 收集所有图片URL
        image_urls = []
        
        # 单张图片（Hacker News等）
        image = entry.get("image")
        if image:
            image_urls.append(image)
        
        # 多张图片（ArXiv论文）
        images = entry.get("images", [])
        if images:
            image_urls.extend(images)
        
        if not image_urls:
            print(f"  无图片", file=sys.stderr)
            continue
        
        # 下载该条目的所有图片
        for img_idx, img_url in enumerate(image_urls, 1):
            try:
                # 生成文件名
                ext = os.path.splitext(img_url)[1]
                if not ext:
                    ext = ".png"
                
                filename = f"{idx:02d}_{img_idx}{ext}"
                output_path = os.path.join(output_dir, filename)
                
                print(f"  下载图片 {img_idx}: {img_url}", file=sys.stderr)
                download_image(img_url, output_path, timeout=30)
                success_count += 1
                
            except Exception as e:
                print(f"  下载失败 {img_idx}: {e}", file=sys.stderr)
                fail_count += 1
    
    print(f"\n下载完成: 成功 {success_count}, 失败 {fail_count}", file=sys.stderr)
    return success_count, fail_count


def main():
    parser = argparse.ArgumentParser(description="批量下载图片")
    parser.add_argument("--input", required=True, help="输入JSON文件路径")
    parser.add_argument("--output", required=True, help="输出目录")
    parser.add_argument("--date", type=str, help="日期（用于文件命名）")
    
    args = parser.parse_args()
    
    success, fail = download_images_from_data(
        args.input,
        args.output,
        args.date
    )
    
    if fail > 0:
        sys.exit(1)
    
    sys.exit(0)


if __name__ == "__main__":
    main()
