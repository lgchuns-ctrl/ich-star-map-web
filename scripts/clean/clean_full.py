# -*- coding: utf-8 -*-
"""全量数据清洗：项目/子项 + 代表性传承人 + 关联匹配。

输入：
- data/raw/projects/projects_raw.jsonl
- data/raw/inheritors/inheritors_raw.jsonl

输出：
- data/processed/subitems_full.csv
- data/processed/projects_full.csv
- data/processed/inheritors_full.csv
- data/processed/inheritor_matches.csv
"""

from __future__ import annotations

import json
import re
import sys
import unicodedata
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

SUBITEM_FIELDS = [
    "subitem_id",
    "project_code",
    "project_code_raw",
    "project_code_normalized",
    "project_num",
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

INHERITOR_FIELDS = [
    "inheritor_id",
    "name",
    "gender",
    "ethnicity",
    "project_code",
    "project_code_raw",
    "child_num",
    "project_name",
    "category",
    "region_raw",
    "province",
    "inheritor_batch_no",
    "publish_year",
    "source_url",
    "collected_at",
    "raw_record_id",
]

CHINESE_NUM = {"一": 1, "二": 2, "三": 3, "四": 4, "五": 5, "六": 6}


def parse_inheritor_batch(rx_time: str | None) -> tuple[int | None, int | None]:
    text = clean_text(rx_time)
    m_year = re.search(r"(19\d{2}|20\d{2})", text)
    m_batch = re.search(r"第([一二三四五六])批", text)
    year = int(m_year.group(1)) if m_year else None
    batch = CHINESE_NUM[m_batch.group(1)] if m_batch else None
    return batch, year


def normalize_join_key(value: str | None) -> str:
    return unicodedata.normalize("NFKC", (value or "").strip().upper()).replace(" ", "")


def build_subitem(rec: dict) -> dict:
    payload = rec.get("payload", {})
    rx = parse_rx_time(payload.get("rx_time"))
    province, map_name = map_province(
        payload.get("address"), clean_text(payload.get("province"))
    )
    code_raw = clean_text(payload.get("num"))
    code_norm = normalize_code(code_raw)
    applicant = parse_applicant_from_content(payload.get("content"))
    if not applicant:
        applicant = clean_text(payload.get("province"))
    protection = clean_text(payload.get("protect_unit"))
    return {
        "subitem_id": f"subitem_{payload.get('id')}",
        "project_code": code_norm,
        "project_code_raw": code_raw,
        "project_code_normalized": code_norm,
        "project_num": clean_text(payload.get("project_num")),
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


def build_inheritor(rec: dict) -> dict:
    payload = rec.get("payload", {})
    batch, year = parse_inheritor_batch(payload.get("rx_time"))
    region_raw = clean_text(payload.get("province"))
    province, _ = map_province("", region_raw)
    return {
        "inheritor_id": f"inheritor_{payload.get('id')}",
        "name": clean_text(payload.get("title")),
        "gender": clean_text(payload.get("sex")),
        "ethnicity": clean_text(payload.get("nation")),
        "project_code": normalize_code(payload.get("project_num")),
        "project_code_raw": clean_text(payload.get("project_num")),
        "child_num": clean_text(payload.get("child_num")),
        "project_name": clean_text(payload.get("project")),
        "category": clean_text(payload.get("type")),
        "region_raw": region_raw,
        "province": province,
        "inheritor_batch_no": batch,
        "publish_year": year,
        "source_url": rec.get("source_url", ""),
        "collected_at": rec.get("collected_at", ""),
        "raw_record_id": rec.get("raw_record_id", ""),
    }


def match_inheritors(inheritors: pd.DataFrame, subitems: pd.DataFrame) -> pd.DataFrame:
    """按 child_num（子项 project_num）优先匹配，回退到 项目编号+省份。"""
    sub_lookup = {}
    for _, s in subitems.iterrows():
        key = normalize_join_key(s["project_num"])
        sub_lookup.setdefault(key, []).append(s["subitem_id"])

    proj_prov_lookup = {}
    for _, s in subitems.iterrows():
        key = (s["project_code_normalized"], s["province"])
        proj_prov_lookup.setdefault(key, []).append(s["subitem_id"])

    results = []
    for _, inh in inheritors.iterrows():
        candidates = sub_lookup.get(normalize_join_key(inh["child_num"]), [])
        if candidates:
            if len(candidates) == 1:
                status = "matched"
            else:
                status = "multiple_candidates"
            matched_id = candidates[0] if len(candidates) == 1 else ";".join(candidates)
        else:
            key = (inh["project_code"], inh["province"])
            fallback = proj_prov_lookup.get(key, [])
            if len(fallback) == 1:
                status, matched_id = "matched", fallback[0]
            elif len(fallback) > 1:
                status, matched_id = "multiple_candidates", ";".join(fallback)
            else:
                status, matched_id = "unmatched", ""
        results.append(
            {
                "inheritor_id": inh["inheritor_id"],
                "name": inh["name"],
                "project_code": inh["project_code"],
                "child_num": inh["child_num"],
                "province": inh["province"],
                "match_status": status,
                "matched_subitem_id": matched_id,
                "reason": (
                    "child_num 精确匹配" if candidates
                    else ("项目编号+省份回退匹配" if fallback and len(fallback) == 1
                          else ("项目编号+省份存在多个候选" if len(fallback) > 1 else "未匹配"))
                ),
            }
        )
    return pd.DataFrame(results)


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    projects_raw = ROOT / "data" / "raw" / "projects" / "projects_raw.jsonl"
    inheritors_raw = ROOT / "data" / "raw" / "inheritors" / "inheritors_raw.jsonl"
    if not projects_raw.exists():
        print("缺少项目原始数据，请先采集。")
        sys.exit(1)
    if not inheritors_raw.exists():
        print("缺少传承人原始数据，请先采集。")
        sys.exit(1)

    proj_records = [
        json.loads(line)
        for line in projects_raw.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    inh_records = [
        json.loads(line)
        for line in inheritors_raw.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    subitems = pd.DataFrame([build_subitem(r) for r in proj_records], columns=SUBITEM_FIELDS)
    inheritors = pd.DataFrame(
        [build_inheritor(r) for r in inh_records], columns=INHERITOR_FIELDS
    )

    processed = ROOT / "data" / "processed"
    processed.mkdir(parents=True, exist_ok=True)
    subitems.to_csv(processed / "subitems_full.csv", index=False, encoding="utf-8-sig")

    projects = (
        subitems.groupby("project_code_normalized")
        .agg(
            project_name=("project_name", "first"),
            category=("category", "first"),
            min_batch=("batch_no", "min"),
            max_batch=("batch_no", "max"),
            first_publish_year=("publish_year", "min"),
            province_list=("province", lambda s: "、".join(sorted(set(s)))),
            protection_units=("protection_unit_normalized", lambda s: len(set(s))),
            subitem_count=("subitem_id", "nunique"),
        )
        .reset_index()
        .rename(columns={"project_code_normalized": "project_code"})
    )
    projects.to_csv(processed / "projects_full.csv", index=False, encoding="utf-8-sig")

    inheritors.to_csv(processed / "inheritors_full.csv", index=False, encoding="utf-8-sig")
    matches = match_inheritors(inheritors, subitems)
    matches.to_csv(processed / "inheritor_matches.csv", index=False, encoding="utf-8-sig")

    stats = {
        "raw_projects": len(proj_records),
        "cleaned_subitems": len(subitems),
        "distinct_projects": len(projects),
        "raw_inheritors": len(inh_records),
        "cleaned_inheritors": len(inheritors),
        "match_status": matches["match_status"].value_counts().to_dict(),
    }
    print(json.dumps(stats, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
