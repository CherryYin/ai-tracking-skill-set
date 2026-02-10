#!/usr/bin/env python3
"""
调用兼容OpenAI API格式的LLM服务

支持通过base_url配置任意兼容OpenAI格式的LLM服务，如：
- Ark DeepSeek
- 自部署的vLLM
- 其他兼容OpenAI API的服务

用法:
    # 智能筛选内容
    python call_llm.py \
        --base_url "https://ark.cn-beijing.volces.com/api/v3" \
        --model "deepseek-chat" \
        --prompt "$(cat prompt.txt)" \
        --output result.json

    # 生成文章
    python call_llm.py \
        --base_url "https://ark.cn-beijing.volces.com/api/v3" \
        --model "deepseek-chat" \
        --prompt "$(cat article_prompt.txt)" \
        --output article.md \
        --format markdown

参数:
    --base_url: LLM服务的基础URL（必需）
    --model: 模型名称（必需）
    --prompt: 输入提示文本（必需）
    --output: 输出文件路径（必需）
    --format: 输出格式，json或markdown（默认json）
    --temperature: 温度参数（默认0.7）
    --max_tokens: 最大生成token数（默认2000）
"""

import argparse
import json
import os
import sys

# 检查是否安装了依赖
try:
    from openai import OpenAI
except ImportError:
    print("错误: 需要安装openai包", file=sys.stderr)
    print("请运行: pip install openai", file=sys.stderr)
    sys.exit(1)


def call_llm(base_url, model, prompt, output_path, 
             output_format="json", temperature=0.7, max_tokens=2000,
             api_key=None):
    """
    调用LLM服务
    
    Args:
        base_url: LLM服务的基础URL
        model: 模型名称
        prompt: 输入提示
        output_path: 输出文件路径
        output_format: 输出格式（json/markdown）
        temperature: 温度参数
        max_tokens: 最大token数
        api_key: API密钥（如果为None，从环境变量读取）
    
    Returns:
        str: LLM的响应
    """
    # 获取API密钥
    if api_key is None:
        api_key = os.getenv("ARK_API_KEY") or os.getenv("OPENAI_API_KEY")
    
    if not api_key:
        raise ValueError("未找到API密钥，请设置环境变量 ARK_API_KEY 或 OPENAI_API_KEY")
    
    # 创建客户端
    client = OpenAI(
        api_key=api_key,
        base_url=base_url
    )
    
    # 调用API
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "你是一个有帮助的AI助手。"},
                {"role": "user", "content": prompt}
            ],
            temperature=temperature,
            max_tokens=max_tokens
        )
        
        result = response.choices[0].message.content
        
        # 根据格式保存结果
        if output_format == "json":
            # 尝试解析为JSON
            try:
                # 如果结果是markdown代码块中的JSON，提取出来
                if "```json" in result:
                    result = result.split("```json")[1].split("```")[0].strip()
                elif "```" in result:
                    result = result.split("```")[1].split("```")[0].strip()
                
                json_result = json.loads(result)
                with open(output_path, 'w', encoding='utf-8') as f:
                    json.dump(json_result, f, ensure_ascii=False, indent=2)
            except json.JSONDecodeError:
                # 如果不是JSON，作为普通文本保存
                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write(result)
        else:
            # markdown格式，直接保存
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(result)
        
        print(f"成功: 已保存到 {output_path}", file=sys.stderr)
        return result
        
    except Exception as e:
        raise Exception(f"调用LLM失败: {str(e)}")


def main():
    parser = argparse.ArgumentParser(description="调用兼容OpenAI API格式的LLM服务")
    parser.add_argument("--base_url", required=True, help="LLM服务的基础URL")
    parser.add_argument("--model", required=True, help="模型名称")
    parser.add_argument("--prompt", required=True, help="输入提示文本")
    parser.add_argument("--output", required=True, help="输出文件路径")
    parser.add_argument("--format", choices=["json", "markdown"], default="json",
                       help="输出格式（默认json）")
    parser.add_argument("--temperature", type=float, default=0.7,
                       help="温度参数（默认0.7）")
    parser.add_argument("--max_tokens", type=int, default=2000,
                       help="最大生成token数（默认2000）")
    parser.add_argument("--api_key", help="API密钥（可选，默认从环境变量读取）")
    
    args = parser.parse_args()
    
    try:
        call_llm(
            base_url=args.base_url,
            model=args.model,
            prompt=args.prompt,
            output_path=args.output,
            output_format=args.format,
            temperature=args.temperature,
            max_tokens=args.max_tokens,
            api_key=args.api_key
        )
        sys.exit(0)
    except Exception as e:
        print(f"错误: {str(e)}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
