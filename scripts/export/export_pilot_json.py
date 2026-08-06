# -*- coding: utf-8 -*-
"""试点数据导出：将清洗后的数据聚合为前端 JSON（web/public/data/）。"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

OUT = ROOT / "web" / "public" / "data"
DATA_VERSION = "v0.1.0-pilot"
UPDATED_AT = "2026-08-06"


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    OUT.mkdir(parents=True, exist_ok=True)
    subitems = pd.read_csv(ROOT / "data" / "processed" / "subitems_pilot.csv", dtype=str).fillna("")
    projects = pd.read_csv(ROOT / "data" / "processed" / "projects_pilot.csv", dtype=str).fillna("")

    # provinces.json：省级聚合（当前试点数据口径）
    prov_rows = []
    for province, g in subitems.groupby("province"):
        prov_rows.append(
            {
                "province": province,
                "map_name": g["province_map_name"].iloc[0],
                "subitem_count": int(len(g)),
                "project_count": int(g["project_code"].nunique()),
                "categories_covered": int(g["category"].nunique()),
                "new_count": int((g["entry_type"] == "new").sum()),
                "extension_count": int((g["entry_type"] == "extension").sum()),
            }
        )
    prov_rows.sort(key=lambda r: r["subitem_count"], reverse=True)

    # categories.json
    cat_rows = []
    for cat, g in subitems.groupby("category"):
        cat_rows.append(
            {
                "category": cat,
                "subitem_count": int(len(g)),
                "project_count": int(g["project_code"].nunique()),
                "batch_count": int(g["batch_no"].nunique()),
                "province_count": int(g["province"].nunique()),
                "new_count": int((g["entry_type"] == "new").sum()),
                "extension_count": int((g["entry_type"] == "extension").sum()),
            }
        )
    cat_rows.sort(key=lambda r: r["subitem_count"], reverse=True)

    # batches.json（含累计）
    batch_rows = []
    cum = 0
    for batch in sorted(subitems["batch_no"].unique(), key=int):
        g = subitems[subitems["batch_no"] == batch]
        n_new = int((g["entry_type"] == "new").sum())
        n_ext = int((g["entry_type"] == "extension").sum())
        cum += len(g)
        batch_rows.append(
            {
                "batch_no": int(batch),
                "publish_year": int(g["publish_year"].iloc[0]),
                "new_count": n_new,
                "extension_count": n_ext,
                "total": int(len(g)),
                "cumulative": cum,
            }
        )

    # projects.json：独立项目
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
                "subitem_count": int(p["subitem_count"]),
            }
        )

    # subitems.json（精简字段）
    subitem_rows = subitems[
        [
            "subitem_id", "project_code", "project_name", "category", "batch_no",
            "publish_year", "entry_type", "region_raw", "province",
            "protection_unit_normalized", "source_url",
        ]
    ].rename(columns={"protection_unit_normalized": "protection_unit"})
    subitem_rows["batch_no"] = subitem_rows["batch_no"].astype(int)
    subitem_rows["publish_year"] = subitem_rows["publish_year"].astype(int)

    # project_search_index.json：轻量搜索索引
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
        for _, r in subitem_rows.iterrows()
    ]

    raw_count = sum(
        1
        for line in (ROOT / "data" / "raw" / "projects" / "projects_raw.jsonl")
        .read_text(encoding="utf-8")
        .splitlines()
        if line.strip()
    )

    metadata = {
        "data_version": DATA_VERSION,
        "updated_at": UPDATED_AT,
        "scope": "试点：国家级非物质文化遗产代表性项目名录「民间文学」门类（含新增与扩展、全部批次）",
        "raw_record_count": raw_count,
        "cleaned_subitem_count": len(subitems),
        "distinct_project_count": len(projects),
        "sources": [
            {
                "name": "中国非物质文化遗产网·国家级非物质文化遗产代表性项目名录",
                "url": "http://www.ihchina.cn/Article/Index/getProject.html",
                "accessed_at": UPDATED_AT,
                "type": "api",
                "role": "主要来源",
            }
        ],
        "indicators": {
            "project_count": "独立项目数量",
            "subitem_count": "地区子项数量",
            "inheritor_coverage": "代表性传承人覆盖率（全量阶段实现）",
        },
        "disclaimer": "相关指标基于公开国家级名录及国家级代表性传承人数据构建，"
        "仅反映公开数据中的资源配置与覆盖情况，不代表官方濒危等级或保护成效评价。",
        "notes": [
            "试点数据仅覆盖「民间文学」门类，用于 MVP 验收；全量阶段将覆盖全部十大门类。",
            "统计口径：地区子项（项目在各省申报形成的记录）；独立项目按项目编号去重。",
        ],
    }

    files = {
        "metadata.json": metadata,
        "provinces.json": prov_rows,
        "categories.json": cat_rows,
        "batches.json": batch_rows,
        "projects.json": project_rows,
        "subitems.json": subitem_rows.to_dict(orient="records"),
        "project_search_index.json": search_rows,
        "methodology.json": {
            "data_sources": metadata["sources"],
            "collection": "官方 JSON 接口，低频率、断点续传、原始响应归档",
            "cleaning": "编号/名称/地区/批次/类别标准化；保留原始字段；人工修正留痕",
            "indicators": metadata["indicators"],
            "limitations": metadata["notes"],
            "ethics": "仅使用公开数据，不绕过访问控制，不伪造数据，不将缺失解释为不存在",
        },
    }
    for fname, obj in files.items():
        (OUT / fname).write_text(
            json.dumps(obj, ensure_ascii=False, indent=1), encoding="utf-8"
        )
        print(f"写出 {fname}: {len(json.dumps(obj, ensure_ascii=False))} bytes")


if __name__ == "__main__":
    main()
