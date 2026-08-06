# -*- coding: utf-8 -*-
"""探测中国非物质文化遗产网（ihchina.cn）国家级项目列表接口的参数语义。

仅做少量低频率请求，用于确定试点采集方案。不适用于全量抓取。
"""

from __future__ import annotations

import json
import sys
import time

import requests

BASE_URL = "http://www.ihchina.cn/Article/Index/getProject.html"
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    ),
    "Referer": "http://www.ihchina.cn/project.html",
    "Accept": "application/json, text/plain, */*",
}


def probe(params: dict, label: str) -> None:
    try:
        r = requests.get(BASE_URL, params=params, headers=HEADERS, timeout=30)
        r.raise_for_status()
        data = r.json()
        items = data.get("list", [])
        first = items[0] if items else {}
        print(f"[{label}] total={data.get('total')} pages={data.get('total_pages')} "
              f"list_len={len(items)}")
        if first:
            print(f"    first: num={first.get('num')!r} title={first.get('title')!r} "
                  f"type={first.get('type')!r} cate={first.get('cate')!r} "
                  f"rx_time={first.get('rx_time')!r} province={first.get('province')!r} "
                  f"address={first.get('address')!r} project_num={first.get('project_num')!r}")
    except Exception as exc:  # noqa: BLE001
        print(f"[{label}] ERROR: {exc}")
    time.sleep(1.2)


def main() -> None:
    # 1) category_id 语义
    for cid in [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 16]:
        probe({"category_id": cid, "limit": 2, "p": 1}, f"category_id={cid}")

    # 2) type（疑似门类）
    probe({"type": "民间文学", "limit": 2, "p": 1}, "type=民间文学")
    probe({"type": "传统音乐", "limit": 2, "p": 1}, "type=传统音乐")

    # 3) cate（疑似新增/扩展）
    probe({"cate": "新增项目", "limit": 2, "p": 1}, "cate=新增项目")
    probe({"cate": "扩展项目", "limit": 2, "p": 1}, "cate=扩展项目")

    # 4) rx_time（疑似批次/年份）
    probe({"rx_time": "2006", "limit": 2, "p": 1}, "rx_time=2006")
    probe({"rx_time": "2021", "limit": 2, "p": 1}, "rx_time=2021")

    # 5) province（地区）
    probe({"province": "北京市", "limit": 2, "p": 1}, "province=北京市")
    probe({"province": "北京", "limit": 2, "p": 1}, "province=北京")

    # 6) keywords
    probe({"keywords": "京剧", "limit": 2, "p": 1}, "keywords=京剧")

    # 7) 跨地区子项观察：查看某一项目多条记录的字段差异
    probe({"category_id": 16, "limit": 5, "p": 1}, "page1(默认排序)")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()
