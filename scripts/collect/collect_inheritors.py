# -*- coding: utf-8 -*-
"""采集国家级非遗代表性传承人列表（ihchina.cn /art/representative.html）。"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from scripts.lib.collector_base import ApiListCollector  # noqa: E402

BASE_URL = "http://www.ihchina.cn/art/representative.html"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="ihchina 国家级代表性传承人采集")
    parser.add_argument("--limit", type=int, default=100)
    parser.add_argument("--max-records", type=int, default=4200)
    parser.add_argument("--interval", type=float, default=1.2)
    parser.add_argument("--timeout", type=int, default=30)
    parser.add_argument("--retries", type=int, default=3)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--no-resume", action="store_true")
    return parser.parse_args()


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    args = parse_args()
    collector = ApiListCollector(
        outdir=ROOT / "data",
        base_url=BASE_URL,
        referer="http://www.ihchina.cn/representative.html",
        raw_name="inheritors",
        source_title="中国非物质文化遗产网·国家级非遗代表性传承人名单",
        interval=args.interval,
        timeout=args.timeout,
        retries=args.retries,
        max_records=args.max_records,
        limit=args.limit,
        dry_run=args.dry_run,
        resume=not args.no_resume,
    )
    print(f"limit={args.limit}；max_records={args.max_records}；interval={args.interval}s；"
          f"dry_run={args.dry_run}")
    t0 = time.perf_counter()
    stats = collector.collect_pages({})
    elapsed = round(time.perf_counter() - t0, 1)
    print("采集统计:", json.dumps(stats, ensure_ascii=False))
    print(f"耗时 {elapsed}s；原始记录归档：{collector.raw_jsonl}")


if __name__ == "__main__":
    main()
