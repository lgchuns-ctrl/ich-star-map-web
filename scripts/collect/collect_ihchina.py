# -*- coding: utf-8 -*-
"""小规模采集：中国非物质文化遗产网 国家级非遗项目列表（试点）。

默认采集完整「民间文学」门类（type=1，约 251 条），以验证数据结构：
项目编号、类别、批次、新增/扩展、申报地区、保护单位、多地区子项等。

特性：合理 UA、请求间隔、超时、指数退避重试、断点续传（本地缓存）、
失败日志、重复检测、原始响应归档、UTF-8、命令行参数、dry-run。
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import requests
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from scripts.lib.common import (  # noqa: E402
    BATCH_IDS,
    CATEGORIES,
    build_request_url,
    hash_params,
    now_iso,
    sha256_text,
)

BASE_URL = "http://www.ihchina.cn/Article/Index/getProject.html"
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    ),
    "Referer": "http://www.ihchina.cn/project.html",
    "Accept": "application/json, text/plain, */*",
}


class Collector:
    def __init__(
        self,
        outdir: Path,
        interval: float = 1.2,
        timeout: int = 30,
        retries: int = 3,
        max_records: int = 300,
        limit: int = 100,
        dry_run: bool = False,
        resume: bool = True,
    ) -> None:
        self.outdir = outdir
        self.raw_dir = outdir / "raw" / "projects"
        self.page_dir = self.raw_dir / "pages"
        self.log_dir = outdir / "raw" / "request_logs"
        self.page_dir.mkdir(parents=True, exist_ok=True)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.interval = interval
        self.timeout = timeout
        self.retries = retries
        self.max_records = max_records
        self.limit = limit
        self.dry_run = dry_run
        self.resume = resume
        self.session = requests.Session()
        self.session.headers.update(HEADERS)
        self.raw_jsonl = self.raw_dir / "projects_raw.jsonl"
        self.failed_jsonl = self.raw_dir / "failed_records.jsonl"
        self.log_csv = self.log_dir / "request_log.csv"
        self._seen_ids: set[str] = set()
        if self.raw_jsonl.exists():
            for line in self.raw_jsonl.read_text(encoding="utf-8").splitlines():
                if line.strip():
                    rec = json.loads(line)
                    self._seen_ids.add(str(rec["payload"]["id"]))

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, max=30),
        retry=retry_if_exception_type((requests.RequestException,)),
        reraise=True,
    )
    def _get(self, url: str, params: dict) -> requests.Response:
        return self.session.get(url, params=params, timeout=self.timeout)

    def _log_request(
        self,
        url: str,
        params: dict,
        status: int | None,
        size: int,
        elapsed_ms: float,
        error: str = "",
    ) -> None:
        exists = self.log_csv.exists()
        with self.log_csv.open("a", encoding="utf-8", newline="") as f:
            writer = csv.writer(f)
            if not exists:
                writer.writerow(
                    ["timestamp", "url", "params_json", "status", "bytes", "elapsed_ms", "error"]
                )
            writer.writerow(
                [
                    now_iso(),
                    url,
                    json.dumps(params, ensure_ascii=False, sort_keys=True),
                    status,
                    size,
                    round(elapsed_ms, 1),
                    error,
                ]
            )

    def _log_failed(self, url: str, params: dict, error: str) -> None:
        with self.failed_jsonl.open("a", encoding="utf-8") as f:
            f.write(
                json.dumps(
                    {"timestamp": now_iso(), "url": url, "params": params, "error": error},
                    ensure_ascii=False,
                )
                + "\n"
            )

    def _archive_page(self, params: dict, data: dict) -> Path:
        fname = f"{hash_params(params)}.json"
        path = self.page_dir / fname
        path.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
        return path

    def _append_records(self, params: dict, page: int, items: list[dict]) -> tuple[int, int]:
        """追加原始记录，返回 (新增条数, 跳过重复条数)。"""
        added = skipped = 0
        with self.raw_jsonl.open("a", encoding="utf-8") as f:
            for item in items:
                rid = str(item.get("id", ""))
                if rid in self._seen_ids:
                    skipped += 1
                    continue
                self._seen_ids.add(rid)
                payload_str = json.dumps(item, ensure_ascii=False, sort_keys=True)
                rec = {
                    "raw_record_id": rid,
                    "source_url": build_request_url(BASE_URL, params),
                    "source_title": "中国非物质文化遗产网·国家级非物质文化遗产代表性项目名录",
                    "source_type": "api",
                    "request_params": params,
                    "page": page,
                    "collected_at": now_iso(),
                    "content_hash": sha256_text(payload_str),
                    "payload": item,
                }
                f.write(json.dumps(rec, ensure_ascii=False) + "\n")
                added += 1
        return added, skipped

    def _fetch_page(self, params: dict, page: int) -> tuple[int, int, int]:
        url = build_request_url(BASE_URL, params)
        archive = self.page_dir / f"{hash_params(params)}.json"
        if self.resume and archive.exists():
            data = json.loads(archive.read_text(encoding="utf-8"))
            total = int(data.get("total") or 0)
            items = data.get("list") or []
            added, skipped = self._append_records(params, page, items)
            return total, added, skipped

        if self.dry_run:
            print(f"[dry-run] GET {url}")
            return 0, 0, 0

        t0 = time.perf_counter()
        try:
            resp = self._get(url, params)
            resp.raise_for_status()
            data = resp.json()
        except Exception as exc:  # noqa: BLE001
            elapsed = (time.perf_counter() - t0) * 1000
            self._log_request(url, params, None, 0, elapsed, repr(exc))
            self._log_failed(url, params, repr(exc))
            raise
        elapsed = (time.perf_counter() - t0) * 1000
        self._log_request(url, params, resp.status_code, len(resp.content), elapsed)
        self._archive_page(params, data)
        total = int(data.get("total") or 0)
        items = data.get("list") or []
        added, skipped = self._append_records(params, page, items)
        return total, added, skipped

    def collect_pages(self, params: dict, start_page: int, end_page: int | None) -> dict:
        stats = {"requests": 0, "success": 0, "failed": 0, "added": 0, "skipped_duplicates": 0}
        total = 0
        page = start_page
        while True:
            if end_page is not None and page > end_page:
                break
            if self.max_records and stats["added"] >= self.max_records:
                break
            p = dict(params, limit=self.limit, p=page)
            stats["requests"] += 1
            try:
                total, added, skipped = self._fetch_page(p, page)
                stats["success"] += 1
                stats["added"] += added
                stats["skipped_duplicates"] += skipped
                print(
                    f"[page {page}] total={total} added={added} skipped={skipped} "
                    f"cumulative_added={stats['added']}"
                )
            except Exception as exc:  # noqa: BLE001
                stats["failed"] += 1
                print(f"[page {page}] FAILED: {exc}")
                if not self.resume:
                    break
            if total == 0 or len(self._seen_ids) >= total:
                break
            page += 1
            time.sleep(self.interval)
        return stats

    def run(self, scope: str, value: str | None) -> dict:
        base: dict = {"category_id": "16"}
        label = ""
        if scope == "category":
            base["type"] = value
            label = f"门类={CATEGORIES.get(value or '', value or '')}"
        elif scope == "batch":
            base["rx_time"] = value
            label = f"批次ID={value}"
        elif scope == "pages":
            label = "默认顺序分页"
        print(f"采集范围：{label}；limit={self.limit}；max_records={self.max_records}；"
              f"interval={self.interval}s；dry_run={self.dry_run}")
        return self.collect_pages(base, start_page=1, end_page=None)


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
    collector = Collector(
        outdir=ROOT / "data",
        interval=args.interval,
        timeout=args.timeout,
        retries=args.retries,
        max_records=args.max_records,
        limit=args.limit,
        dry_run=args.dry_run,
        resume=not args.no_resume,
    )
    t0 = time.perf_counter()
    stats = collector.run(args.scope, args.value)
    elapsed = round(time.perf_counter() - t0, 1)
    print("采集统计:", json.dumps(stats, ensure_ascii=False))
    print(f"耗时 {elapsed}s；原始记录归档：{collector.raw_jsonl}")


if __name__ == "__main__":
    main()
