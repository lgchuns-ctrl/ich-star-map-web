# -*- coding: utf-8 -*-
"""试点数据清洗与标准化。

读取 data/raw/projects/projects_raw.jsonl，产出：
- data/interim/pilot_projects.csv        （子项口径，按官方行记录展开）
- data/processed/subitems_pilot.csv      （同上，完整字段）
- data/processed/projects_pilot.csv      （独立项目口径，去重后）
"""

from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from scripts.lib.common import (  # noqa: E402
    clean_text,
    map_province,
    normalize_code,
    normalize_entry_type,
    parse_applicant_from_content,
    parse_rx_time,
)

RAW_JSONL = ROOT / "data" / "raw" / "projects" / "projects_raw.jsonl"
INTERIM_CSV = ROOT / "data" / "interim" / "pilot_projects.csv"
SUBITEMS_CSV = ROOT / "data" / "processed" / "subitems_pilot.csv"
PROJECTS_CSV = ROOT / "data" / "processed" / "projects_pilot.csv"

SUBITEM_FIELDS = [
    "subitem_id",
    "project_code",
    "project_code_raw",
    "project_code_normalized",
    "project_name",
    "category",
    "batch_no",
    "publish_year",
    "entry_type",
    "region_raw",
    "province",
    "province_map_name",
    "city_code",
    "county_code",
    "applicant_region_or_unit",
    "protection_unit_raw",
    "protection_unit_normalized",
    "source_url",
    "collected_at",
    "raw_record_id",
    "manual_review_status",
]


def clean_protection_unit(value: str | None) -> str:
    return clean_text(value).replace("  ", " ")


def build_subitem(rec: dict) -> dict:
    payload = rec.get("payload", {})
    rx = parse_rx_time(payload.get("rx_time"))
    province, map_name = map_province(
        payload.get("address"), clean_text(payload.get("province"))
    )
    code_raw = clean_text(payload.get("num"))
    applicant = parse_applicant_from_content(payload.get("content"))
    if not applicant:
        applicant = clean_text(payload.get("province"))
    protection = clean_protection_unit(payload.get("protect_unit"))
    project_code_normalized = normalize_code(code_raw)
    return {
        "subitem_id": f"subitem_{payload.get('id')}",
        "project_code": project_code_normalized,
        "project_code_raw": code_raw,
        "project_code_normalized": project_code_normalized,
        "project_name": clean_text(payload.get("title")),
        "category": clean_text(payload.get("type")),
        "batch_no": rx["batch_no"],
        "publish_year": rx["year"],
        "entry_type": normalize_entry_type(payload.get("cate")),
        "region_raw": clean_text(payload.get("province")),
        "province": province,
        "province_map_name": map_name,
        "city_code": str(payload.get("city") or ""),
        "county_code": str(payload.get("area") or ""),
        "applicant_region_or_unit": applicant,
        "protection_unit_raw": str(payload.get("protect_unit") or "").strip(),
        "protection_unit_normalized": protection,
        "source_url": rec.get("source_url", ""),
        "collected_at": rec.get("collected_at", ""),
        "raw_record_id": rec.get("raw_record_id", ""),
        "manual_review_status": "",
    }


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    if not RAW_JSONL.exists():
        print(f"未找到原始数据：{RAW_JSONL}，请先运行采集脚本。")
        sys.exit(1)

    records = [
        json.loads(line)
        for line in RAW_JSONL.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    subitems = [build_subitem(r) for r in records]

    df = pd.DataFrame(subitems, columns=SUBITEM_FIELDS)
    df = df.sort_values(["project_code_normalized", "batch_no", "subitem_id"]).reset_index(
        drop=True
    )
    INTERIM_CSV.parent.mkdir(parents=True, exist_ok=True)
    SUBITEMS_CSV.parent.mkdir(parents=True, exist_ok=True)

    # 1) 子项口径 CSV（interim 与 processed 均输出）
    interim_cols = [
        "project_code",
        "project_name",
        "category",
        "batch_no",
        "publish_year",
        "entry_type",
        "region_raw",
        "province",
        "protection_unit_normalized",
        "source_url",
        "collected_at",
    ]
    df[interim_cols].to_csv(INTERIM_CSV, index=False, encoding="utf-8-sig")
    df.to_csv(SUBITEMS_CSV, index=False, encoding="utf-8-sig")

    # 2) 独立项目口径：按标准化编号去重，聚合申报省份与批次
    projects = (
        df.groupby("project_code_normalized")
        .agg(
            project_name=("project_name", "first"),
            category=("category", "first"),
            min_batch=("batch_no", "min"),
            max_batch=("batch_no", "max"),
            first_publish_year=("publish_year", "min"),
            province_list=("province", lambda s: "、".join(sorted(set(s)))),
            subitem_count=("subitem_id", "nunique"),
        )
        .reset_index()
        .rename(columns={"project_code_normalized": "project_code"})
    )
    projects.to_csv(PROJECTS_CSV, index=False, encoding="utf-8-sig")

    stats = {
        "raw_records": len(records),
        "cleaned_subitems": len(df),
        "distinct_projects": len(projects),
        "distinct_province_level": df["province"].nunique(),
        "missing": {
            col: int(df[col].isna().sum() + (df[col].astype(str) == "").sum())
            for col in [
                "project_code",
                "project_name",
                "category",
                "batch_no",
                "publish_year",
                "entry_type",
                "region_raw",
                "province",
            ]
        },
        "outputs": {
            "interim": str(INTERIM_CSV),
            "subitems": str(SUBITEMS_CSV),
            "projects": str(PROJECTS_CSV),
        },
    }
    print(json.dumps(stats, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
