# -*- coding: utf-8 -*-
"""通用低频率 API 列表采集器。

特性：合理 UA、请求间隔、超时、指数退避重试、断点续传（本地缓存）、
失败日志、重复检测、原始响应归档、UTF-8、dry-run。
"""

from __future__ import annotations

import csv
import json
import math
import time
from pathlib import Path

import requests
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from scripts.lib.common import build_request_url, hash_params, now_iso, sha256_text


class ApiListCollector:
    def __init__(
        self,
        *,
        outdir: Path,
        base_url: str,
        referer: str,
        raw_name: str,
        source_title: str,
        interval: float = 1.2,
        timeout: int = 30,
        retries: int = 3,
        max_records: int = 300,
        limit: int = 100,
        dry_run: bool = False,
        resume: bool = True,
    ) -> None:
        self.outdir = outdir
        self.base_url = base_url
        self.referer = referer
        self.raw_name = raw_name
        self.source_title = source_title
        self.interval = interval
        self.timeout = timeout
        self.retries = retries
        self.max_records = max_records
        self.limit = limit
        self.dry_run = dry_run
        self.resume = resume
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
                ),
                "Referer": referer,
                "Accept": "application/json, text/plain, */*",
            }
        )
        self.raw_dir = outdir / "raw" / raw_name
        self.page_dir = self.raw_dir / "pages"
        self.log_dir = outdir / "raw" / "request_logs"
        self.page_dir.mkdir(parents=True, exist_ok=True)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.raw_jsonl = self.raw_dir / f"{raw_name}_raw.jsonl"
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
        path = self.page_dir / f"{hash_params(params)}.json"
        path.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
        return path

    def _append_records(self, params: dict, page: int, items: list[dict]) -> tuple[int, int]:
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
                    "source_url": build_request_url(self.base_url, params),
                    "source_title": self.source_title,
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
        url = build_request_url(self.base_url, params)
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

    def collect_pages(self, params: dict, start_page: int = 1, end_page: int | None = None) -> dict:
        stats = {"requests": 0, "success": 0, "failed": 0, "added": 0, "skipped_duplicates": 0}
        total = 0
        total_pages: int | None = None
        page = start_page
        while True:
            if end_page is not None and page > end_page:
                break
            if self.max_records and stats["added"] >= self.max_records:
                break
            if total_pages is not None and page > total_pages:
                break
            p = dict(params, limit=self.limit, p=page)
            stats["requests"] += 1
            try:
                total, added, skipped = self._fetch_page(p, page)
                if total > 0:
                    total_pages = max(total_pages or 0, math.ceil(total / self.limit))
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
            # 终止条件：总数/页数达到、空页、或一页无任何新记录且无待续页
            if total == 0:
                break
            if total_pages is not None and page >= total_pages:
                break
            if end_page is not None and page >= end_page:
                break
            page += 1
            time.sleep(self.interval)
        return stats
