# -*- coding: utf-8 -*-
"""小规模采集：中国非物质文化遗产网 国家级非遗项目列表（试点）。

默认采集完整「民间文学」门类（type=1，约 251 条），以验证数据结构：
项目编号、类别、批次、新增/扩展、申报地区、保护单位、多地区子项等。

特性：合理 UA、请求间隔、超时、指数退避重试、断点续传（本地缓存）、
失败日志、重复检测、原始响应归档、UTF-8、命令行参数、dry-run。
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from scripts.lib.collector_base import ApiListCollector  # noqa: E402
from scripts.lib.common import CATEGORIES  # noqa: E402

BASE_URL = "http://www.ihchina.cn/Article/Index/getProject.html"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="ihchina 国家级非遗项目列表采集（试点）")
    parser.add_argument("--scope", choices=["category", "batch", "pages"], default="category")
    parser.add_argument("--value", help="type 或 rx_time 的数字 ID")
    parser.add_argument("--limit", type=int, default=100)
    parser.add_argument("--max-records", type=int, default=300)
    parser.add_argument("--interval", type=float, default=1.2)
    parser.add_argument("--timeout", type=int, default=30)
    parser.add_argument("--retries", type=int, default=3)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--no-resume", action="store_true", help="忽略本地缓存重新请求")
    return parser.parse_args()


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    args = parse_args()
    collector = ApiListCollector(
        outdir=ROOT / "data",
        base_url=BASE_URL,
        referer="http://www.ihchina.cn/project.html",
        raw_name="projects",
        source_title="中国非物质文化遗产网·国家级非物质文化遗产代表性项目名录",
        interval=args.interval,
        timeout=args.timeout,
        retries=args.retries,
        max_records=args.max_records,
        limit=args.limit,
        dry_run=args.dry_run,
        resume=not args.no_resume,
    )
    t0 = time.perf_counter()
    base: dict = {"category_id": "16"}
    label = ""
    if args.scope == "category":
        base["type"] = args.value
        label = f"门类={CATEGORIES.get(args.value or '', args.value or '')}"
    elif args.scope == "batch":
        base["rx_time"] = args.value
        label = f"批次ID={args.value}"
    else:
        label = "默认顺序分页"
    print(f"采集范围：{label}；limit={args.limit}；max_records={args.max_records}；"
          f"interval={args.interval}s；dry_run={args.dry_run}")
    stats = collector.collect_pages(base)
    elapsed = round(time.perf_counter() - t0, 1)
    print("采集统计:", json.dumps(stats, ensure_ascii=False))
    print(f"耗时 {elapsed}s；原始记录归档：{collector.raw_jsonl}")


if __name__ == "__main__":
    main()
