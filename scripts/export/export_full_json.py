# -*- coding: utf-8 -*-
"""全量数据导出：将清洗与分析结果导出为前端本地 JSON（web/public/data/）。"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

OUT = ROOT / "web" / "public" / "data"
DATA_VERSION = "v0.2.0-full"
UPDATED_AT = "2026-08-06"


def write_json(fname: str, obj: object) -> None:
    (OUT / fname).write_text(
        json.dumps(obj, ensure_ascii=False, indent=1), encoding="utf-8"
    )
    size = len(json.dumps(obj, ensure_ascii=False))
    print(f"写出 {fname}: {size} bytes")


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    OUT.mkdir(parents=True, exist_ok=True)
    processed = ROOT / "data" / "processed"
    reports = ROOT / "data" / "reports"

    sub = pd.read_csv(processed / "subitems_full.csv", dtype=str).fillna("")
    projects = pd.read_csv(processed / "projects_full.csv", dtype=str).fillna("")
    inh = pd.read_csv(processed / "inheritors_full.csv", dtype=str).fillna("")
    matches = pd.read_csv(processed / "inheritor_matches.csv", dtype=str).fillna("")
    region = pd.read_csv(reports / "analysis_region.csv", dtype=str).fillna("")
    cat = pd.read_csv(reports / "analysis_category.csv", dtype=str).fillna("")
    batch = pd.read_csv(reports / "analysis_batch.csv", dtype=str).fillna("")
    inh_batch = pd.read_csv(reports / "analysis_inheritor_batch.csv", dtype=str).fillna("")
    conclusions = json.loads((reports / "conclusions.json").read_text(encoding="utf-8"))

    sub["batch_no"] = sub["batch_no"].astype(int)
    sub["publish_year"] = sub["publish_year"].astype(int)
    inh["inheritor_batch_no"] = pd.to_numeric(inh["inheritor_batch_no"], errors="coerce").fillna(0).astype(int)
    inh["publish_year"] = pd.to_numeric(inh["publish_year"], errors="coerce").fillna(0).astype(int)

    map_name_by_prov = dict(zip(sub["province"], sub["province_map_name"]))

    # provinces.json（含传承资源指标）
    prov_rows = []
    for _, r in region.iterrows():
        prov_rows.append(
            {
                "province": r["province"],
                "map_name": map_name_by_prov.get(r["province"], ""),
                "subitem_count": int(r["subitem_count"]),
                "project_count": int(r["project_count"]),
                "protection_unit_count": int(r["protection_unit_count"]),
                "categories_covered": int(r["categories_covered"]),
                "inheritor_count": int(r["inheritor_count"]),
                "matched_subitem_count": int(r["matched_subitem_count"]),
                "inheritor_coverage": (
                    float(r["inheritor_coverage"]) if r["inheritor_coverage"] not in ("", "nan") else None
                ),
                "inheritors_per_100_subitems": (
                    float(r["inheritors_per_100_subitems"])
                    if r["inheritors_per_100_subitems"] not in ("", "nan") else None
                ),
            }
        )
    write_json("provinces.json", prov_rows)
    write_json("province_comparison.json", {"version": DATA_VERSION, "provinces": prov_rows})

    # categories.json
    cat_rows = []
    for _, r in cat.iterrows():
        cat_rows.append(
            {
                "category": r["category"],
                "subitem_count": int(r["subitem_count"]),
                "project_count": int(r["project_count"]),
                "province_count": int(r["province_count"]),
                "batch_count": int(r["batch_count"]),
                "new_count": int(r["new_count"]),
                "extension_count": int(r["extension_count"]),
                "inheritor_count": int(r["inheritor_count"]),
                "matched_subitem_count": int(r["matched_subitem_count"]),
                "inheritor_coverage": (
                    float(r["inheritor_coverage"]) if r["inheritor_coverage"] not in ("", "nan") else None
                ),
                "inheritors_per_100_subitems": (
                    float(r["inheritors_per_100_subitems"])
                    if r["inheritors_per_100_subitems"] not in ("", "nan") else None
                ),
            }
        )
    write_json("categories.json", cat_rows)

    # batches.json
    batch_rows = []
    cum = 0
    for _, r in batch.iterrows():
        cum += int(r["subitem_total"])
        batch_rows.append(
            {
                "batch_no": int(r["batch_no"]),
                "publish_year": int(r["publish_year"]),
                "new_count": int(r["new_count"]),
                "extension_count": int(r["extension_count"]),
                "total": int(r["subitem_total"]),
                "project_total": int(r["project_total"]),
                "cumulative": cum,
            }
        )
    write_json("batches.json", batch_rows)

    # inheritor_batches.json
    inh_batch_rows = [
        {
            "batch_no": int(r["inheritor_batch_no"]),
            "publish_year": int(r["publish_year"]),
            "inheritor_count": int(r["inheritor_count"]),
        }
        for _, r in inh_batch.iterrows()
        if str(r["inheritor_batch_no"]) not in ("", "nan")
    ]
    write_json("inheritor_batches.json", inh_batch_rows)

    # projects.json
    project_rows = []
    for _, p in projects.iterrows():
        project_rows.append(
            {
                "project_code": p["project_code"],
                "project_name": p["project_name"],
                "category": p["category"],
                "first_publish_year": int(p["first_publish_year"]),
                "batches": f"{p['min_batch']}-{p['max_batch']}",
                "provinces": p["province_list"],
                "protection_units": int(p["protection_units"]),
                "subitem_count": int(p["subitem_count"]),
            }
        )
    write_json("projects.json", project_rows)

    # subitems.json（精简字段）
    sub_rows = sub[
        ["subitem_id", "project_code", "project_name", "category", "batch_no",
         "publish_year", "entry_type", "region_raw", "province",
         "protection_unit_normalized", "source_url"]
    ].rename(columns={"protection_unit_normalized": "protection_unit"})
    write_json("subitems.json", sub_rows.to_dict(orient="records"))

    # inheritors.json（精简字段）
    match_by_id = dict(zip(matches["inheritor_id"], matches["match_status"]))
    inh_rows = []
    for _, r in inh.iterrows():
        inh_rows.append(
            {
                "inheritor_id": r["inheritor_id"],
                "name": r["name"],
                "gender": r["gender"],
                "ethnicity": r["ethnicity"],
                "project_code": r["project_code"],
                "project_name": r["project_name"],
                "category": r["category"],
                "province": r["province"],
                "batch_no": int(r["inheritor_batch_no"]),
                "publish_year": int(r["publish_year"]),
                "match_status": match_by_id.get(r["inheritor_id"], "unmatched"),
            }
        )
    write_json("inheritors.json", inh_rows)

    # project_search_index.json
    search_rows = [
        {
            "id": r["subitem_id"],
            "name": r["project_name"],
            "code": r["project_code"],
            "category": r["category"],
            "batch_no": int(r["batch_no"]),
            "year": int(r["publish_year"]),
            "entry_type": r["entry_type"],
            "province": r["province"],
            "protection_unit": r["protection_unit"],
        }
        for _, r in sub_rows.iterrows()
    ]
    write_json("project_search_index.json", search_rows)

    # metadata.json
    match_counts = matches["match_status"].value_counts().to_dict()
    metadata = {
        "data_version": DATA_VERSION,
        "updated_at": UPDATED_AT,
        "scope": "全量：国家级非遗代表性项目名录十大门类（含新增与扩展、全部批次）与国家级代表性传承人公开名单",
        "raw_project_record_count": 3610,
        "raw_inheritor_record_count": len(inh),
        "cleaned_subitem_count": len(sub),
        "distinct_project_count": len(projects),
        "inheritor_count": len(inh),
        "inheritor_match_rate": round(match_counts.get("matched", 0) / len(matches), 4),
        "sources": [
            {
                "name": "中国非物质文化遗产网·国家级非物质文化遗产代表性项目名录",
                "url": "http://www.ihchina.cn/Article/Index/getProject.html",
                "accessed_at": UPDATED_AT,
                "type": "api",
                "role": "主要来源",
            },
            {
                "name": "中国非物质文化遗产网·国家级非遗代表性传承人名单",
                "url": "http://www.ihchina.cn/art/representative.html",
                "accessed_at": UPDATED_AT,
                "type": "api",
                "role": "主要来源",
            },
        ],
        "indicators": {
            "project_count": "独立项目数量",
            "subitem_count": "地区子项数量",
            "inheritor_coverage": "已匹配到代表性传承人的子项数 ÷ 子项总数",
            "inheritors_per_100_subitems": "代表性传承人数 ÷ 地区子项数 × 100",
        },
        "disclaimer": "相关指标基于公开国家级名录及国家级代表性传承人数据构建，"
        "仅反映公开数据中的资源配置与覆盖情况，不代表官方濒危等级或保护成效评价。",
        "notes": [
            "传承人接口返回 3995 条记录（含 2025 年第六批 942 条与历史批次），"
            "官方截至 2023 年公开汇总为 3059 人，差异原因见数据质量报告。",
            "统计口径：地区子项按申报地区展开；独立项目按项目编号去重。",
            "传承人-子项匹配优先按 child_num 精确匹配，回退到项目编号+省份；26 条存在多候选，待人工确认。",
        ],
    }
    write_json("metadata.json", metadata)

    write_json("conclusions.json", conclusions)
    write_json(
        "methodology.json",
        {
            "data_sources": metadata["sources"],
            "collection": "官方 JSON 接口低频率采集：项目接口（category_id=16，十大门类共 3610 条）、传承人接口（3995 条）；断点续传、原始响应归档、请求日志",
            "cleaning": "编号/名称/地区/批次/类别标准化；子项组合键按真实数据调整（加入 project_name）；传承人按 child_num 关联",
            "indicators": metadata["indicators"],
            "limitations": metadata["notes"],
            "ethics": "仅使用公开数据，不绕过访问控制，不伪造数据，不将缺失解释为不存在，不把相关描述为因果",
        },
    )
    print("导出完成:", DATA_VERSION)


if __name__ == "__main__":
    main()
