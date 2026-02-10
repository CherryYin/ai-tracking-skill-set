#!/usr/bin/env python3
"""
股票历史数据获取脚本

功能：使用TuShare获取指定股票的历史行情数据
支持：TuShare（需要token，默认）和 AKShare（可选）
输出：JSON格式股票数据
"""

import argparse
import json
import sys
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional


def fetch_with_tushare(stock_code: str, days: int, token: str) -> Dict[str, Any]:
    """
    使用TuShare获取股票历史行情数据

    参数:
        stock_code: 股票代码 (如 000001, 600519)
        days: 获取最近多少天的数据
        token: TuShare API token

    返回:
        股票数据字典
    """
    try:
        import tushare as ts
    except ImportError:
        print("错误: 未安装tushare库", file=sys.stderr)
        print("请执行: pip install tushare", file=sys.stderr)
        sys.exit(1)

    # 初始化TuShare
    ts.set_token(token)
    pro = ts.pro_api()

    # 计算日期范围
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)

    start_date_str = start_date.strftime("%Y%m%d")
    end_date_str = end_date.strftime("%Y%m%d")

    print(f"使用TuShare获取股票 {stock_code} 从 {start_date_str} 到 {end_date_str} 的数据...", file=sys.stderr)

    try:
        # 获取股票基本信息
        stock_info = pro.stock_basic(ts_code=stock_code)
        if len(stock_info) == 0:
            # 尝试其他股票代码格式
            stock_code_formatted = f"{stock_code[:6]}.{('SH' if stock_code.startswith('6') else 'SZ')}"
            stock_info = pro.stock_basic(ts_code=stock_code_formatted)
            if len(stock_info) == 0:
                raise ValueError(f"未找到股票代码 {stock_code} 的信息")

        stock_name = stock_info.iloc[0]["name"]
        ts_code = stock_info.iloc[0]["ts_code"]

        # 获取日线行情
        df = pro.daily(
            ts_code=ts_code,
            start_date=start_date_str,
            end_date=end_date_str
        )

        if len(df) == 0:
            raise ValueError(f"未获取到股票 {stock_code} 的行情数据")

        # 转换数据格式
        data_list = []
        for idx, row in df.iterrows():
            data_item = {
                "date": str(row.get("trade_date", "")),
                "open": float(row.get("open", 0)),
                "close": float(row.get("close", 0)),
                "high": float(row.get("high", 0)),
                "low": float(row.get("low", 0)),
                "volume": float(row.get("vol", 0)),
                "amount": float(row.get("amount", 0)),
                "change_percent": float(row.get("pct_chg", 0)),
                "change_amount": 0,  # TuShare不提供涨跌额
                "turnover": 0  # TuShare日线不直接提供换手率
            }
            data_list.append(data_item)

        result = {
            "stock_code": stock_code,
            "stock_name": stock_name,
            "start_date": start_date_str,
            "end_date": end_date_str,
            "count": len(data_list),
            "data": data_list,
            "source": "TuShare"
        }

        print(f"成功获取 {len(data_list)} 条数据", file=sys.stderr)
        return result

    except Exception as e:
        print(f"TuShare获取数据失败: {str(e)}", file=sys.stderr)
        sys.exit(1)


def fetch_with_akshare(stock_code: str, days: int = 7) -> Dict[str, Any]:
    """
    使用AKShare获取股票历史行情数据（可选，免费，无需token）

    参数:
        stock_code: 股票代码 (如 000001, 600519)
        days: 获取最近多少天的数据 (默认7天)

    返回:
        股票数据字典
    """
    try:
        import akshare as ak
    except ImportError:
        print("错误: 未安装akshare库", file=sys.stderr)
        print("请执行: pip install akshare", file=sys.stderr)
        sys.exit(1)

    # 计算日期范围
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)

    start_date_str = start_date.strftime("%Y%m%d")
    end_date_str = end_date.strftime("%Y%m%d")

    print(f"使用AKShare获取股票 {stock_code} 从 {start_date_str} 到 {end_date_str} 的数据...", file=sys.stderr)

    try:
        # 获取A股历史行情数据
        df = ak.stock_zh_a_hist(
            symbol=stock_code,
            period="daily",
            start_date=start_date_str,
            end_date=end_date_str,
            adjust="qfq"  # 前复权
        )

        # 提取股票名称（从第一条记录中）
        stock_name = df.iloc[0]["股票名称"] if len(df) > 0 else "未知"

        # 转换数据格式
        data_list = []
        for idx, row in df.iterrows():
            data_item = {
                "date": str(row.get("日期", "")),
                "open": float(row.get("开盘", 0)),
                "close": float(row.get("收盘", 0)),
                "high": float(row.get("最高", 0)),
                "low": float(row.get("最低", 0)),
                "volume": float(row.get("成交量", 0)),
                "amount": float(row.get("成交额", 0)),
                "change_percent": float(row.get("涨跌幅", 0)),
                "change_amount": float(row.get("涨跌额", 0)),
                "turnover": float(row.get("换手率", 0))
            }
            data_list.append(data_item)

        result = {
            "stock_code": stock_code,
            "stock_name": stock_name,
            "start_date": start_date_str,
            "end_date": end_date_str,
            "count": len(data_list),
            "data": data_list,
            "source": "AKShare"
        }

        print(f"成功获取 {len(data_list)} 条数据", file=sys.stderr)
        return result

    except Exception as e:
        print(f"AKShare获取数据失败: {str(e)}", file=sys.stderr)
        sys.exit(1)


def fetch_stock_data(stock_code: str, days: int = 7, token: Optional[str] = None, use_akshare: bool = False) -> Dict[str, Any]:
    """
    获取股票历史行情数据（默认使用TuShare）

    参数:
        stock_code: 股票代码 (如 000001, 600519)
        days: 获取最近多少天的数据 (默认7天)
        token: TuShare token（默认使用TuShare时必填）
        use_akshare: 是否强制使用AKShare（默认False）

    返回:
        股票数据字典
    """
    if use_akshare:
        # 使用AKShare
        return fetch_with_akshare(stock_code, days)
    elif token:
        # 使用TuShare
        return fetch_with_tushare(stock_code, days, token)
    else:
        # 未提供token且未指定使用AKShare，报错提示
        print("错误: 需要提供TuShare token或使用 --use_akshare 参数", file=sys.stderr)
        print("\n使用方式1（推荐）：使用TuShare（需要token）", file=sys.stderr)
        print(f"  python3 {sys.argv[0]} --stock_code {stock_code} --days {days} --token \"your_token_here\"", file=sys.stderr)
        print("\n使用方式2：使用AKShare（可选，国内可能无法访问）", file=sys.stderr)
        print(f"  python3 {sys.argv[0]} --stock_code {stock_code} --days {days} --use_akshare", file=sys.stderr)
        print("\n获取TuShare token: https://tushare.pro/", file=sys.stderr)
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description="获取股票历史数据")
    parser.add_argument("--stock_code", type=str, required=True,
                       help="股票代码 (如: 000001, 600519)")
    parser.add_argument("--days", type=int, default=7,
                       help="获取最近多少天的数据 (默认: 7)")
    parser.add_argument("--token", type=str, default=None,
                       help="TuShare token（推荐使用，国内访问稳定）")
    parser.add_argument("--use_akshare", action="store_true",
                       help="强制使用AKShare（国内可能无法访问）")
    parser.add_argument("--output", type=str,
                       help="输出文件路径 (可选，默认输出到stdout)")

    args = parser.parse_args()

    # 获取股票数据
    stock_data = fetch_stock_data(args.stock_code, args.days, args.token, args.use_akshare)

    # 输出结果
    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            json.dump(stock_data, f, ensure_ascii=False, indent=2)
        print(f"结果已保存到: {args.output}", file=sys.stderr)
    else:
        print(json.dumps(stock_data, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
