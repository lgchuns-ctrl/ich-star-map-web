# -*- coding: utf-8 -*-
"""下载中国省级 GeoJSON 底图（DataV.GeoAtlas），归档到 web/public/data/geojson/。"""

from __future__ import annotations

import sys
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[2]
URL = "https://geo.datav.aliyun.com/areas_v3/bound/100000_full.json"


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/124.0"}
    r = requests.get(URL, headers=headers, timeout=60)
    r.raise_for_status()
    out_dir = ROOT / "web" / "public" / "data" / "geojson"
    out_dir.mkdir(parents=True, exist_ok=True)
    out = out_dir / "china.json"
    out.write_bytes(r.content)
    import json

    data = json.loads(r.content)
    names = [f.get("properties", {}).get("name", "") for f in data.get("features", [])]
    print(f"保存: {out} ({len(r.content)} bytes, {len(names)} features)")
    print("名称:", names)


if __name__ == "__main__":
    main()
