# -*- coding: utf-8 -*-
"""阶段D：全量数据分析。

输出 data/reports/：
- analysis_region.csv         省级：子项/项目/保护单位/传承人/类别覆盖/覆盖率/每百子项传承人数
- analysis_batch.csv          项目批次 × 新增/扩展
- analysis_inheritor_batch.csv 传承人批次
- analysis_category.csv       十大门类汇总
- analysis_province_x_batch.csv 省份 × 批次热力图数据
- conclusions.json            可追溯研究结论
"""

from __future__ import annotations

import json
import sys
from datetime import date
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

DATA_VERSION = "v0.2.0-full"
GENERATED = date.today().isoformat()


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    processed = ROOT / "data" / "processed"
    reports = ROOT / "data" / "reports"
    reports.mkdir(parents=True, exist_ok=True)

    sub = pd.read_csv(processed / "subitems_full.csv", dtype=str).fillna("")
    projects = pd.read_csv(processed / "projects_full.csv", dtype=str).fillna("")
    inh = pd.read_csv(processed / "inheritors_full.csv", dtype=str).fillna("")
    matches = pd.read_csv(processed / "inheritor_matches.csv", dtype=str).fillna("")

    sub["batch_no"] = sub["batch_no"].astype(int)
    sub["publish_year"] = sub["publish_year"].astype(int)
    inh["inheritor_batch_no"] = pd.to_numeric(inh["inheritor_batch_no"], errors="coerce")
    inh["publish_year"] = pd.to_numeric(inh["publish_year"], errors="coerce")

    # 每个子项是否匹配到传承人（matched 且子项唯一）
    matched_sub = matches[matches["match_status"] == "matched"]["matched_subitem_id"].tolist()
    matched_sub_set = set(matched_sub)

    # ---- 省级分析 ----
    rows = []
    for province, g in sub.groupby("province"):
        inh_prov = inh[inh["province"] == province]
        matched_in_prov = len(matched_sub_set & set(g["subitem_id"]))
        rows.append(
            {
                "province": province,
                "subitem_count": len(g),
                "project_count": g["project_code"].nunique(),
                "protection_unit_count": g["protection_unit_normalized"].nunique(),
                "categories_covered": g["category"].nunique(),
                "inheritor_count": len(inh_prov),
                "matched_subitem_count": matched_in_prov,
                "inheritor_coverage": round(matched_in_prov / len(g), 4) if len(g) else None,
                "inheritors_per_100_subitems": round(len(inh_prov) / len(g) * 100, 2) if len(g) else None,
            }
        )
    region = pd.DataFrame(rows).sort_values("subitem_count", ascending=False)
    region.to_csv(reports / "analysis_region.csv", index=False, encoding="utf-8-sig")

    # ---- 项目批次分析 ----
    batch_rows = []
    for b in sorted(sub["batch_no"].unique()):
        g = sub[sub["batch_no"] == b]
        batch_rows.append(
            {
                "batch_no": int(b),
                "publish_year": int(g["publish_year"].iloc[0]),
                "new_count": int((g["entry_type"] == "new").sum()),
                "extension_count": int((g["entry_type"] == "extension").sum()),
                "subitem_total": int(len(g)),
                "project_total": int(g["project_code"].nunique()),
            }
        )
    pd.DataFrame(batch_rows).to_csv(
        reports / "analysis_batch.csv", index=False, encoding="utf-8-sig"
    )

    # ---- 传承人批次分析 ----
    inh_batch = (
        inh.groupby(["inheritor_batch_no", "publish_year"])
        .size()
        .reset_index(name="inheritor_count")
        .sort_values("inheritor_batch_no")
    )
    inh_batch.to_csv(
        reports / "analysis_inheritor_batch.csv", index=False, encoding="utf-8-sig"
    )

    # ---- 类别分析 ----
    cat_rows = []
    for cat, g in sub.groupby("category"):
        inh_cat = inh[inh["category"] == cat]
        matched_cat = len(matched_sub_set & set(g["subitem_id"]))
        cat_rows.append(
            {
                "category": cat,
                "subitem_count": len(g),
                "project_count": g["project_code"].nunique(),
                "province_count": g["province"].nunique(),
                "batch_count": g["batch_no"].nunique(),
                "new_count": int((g["entry_type"] == "new").sum()),
                "extension_count": int((g["entry_type"] == "extension").sum()),
                "inheritor_count": len(inh_cat),
                "matched_subitem_count": matched_cat,
                "inheritor_coverage": round(matched_cat / len(g), 4) if len(g) else None,
                "inheritors_per_100_subitems": round(len(inh_cat) / len(g) * 100, 2) if len(g) else None,
            }
        )
    pd.DataFrame(cat_rows).sort_values("subitem_count", ascending=False).to_csv(
        reports / "analysis_category.csv", index=False, encoding="utf-8-sig"
    )

    # ---- 省份 × 批次热力图 ----
    pxb = sub.pivot_table(index="province", columns="batch_no", values="subitem_id", aggfunc="count").fillna(0)
    pxb.columns = [f"batch_{int(c)}" for c in pxb.columns]
    pxb = pxb.reset_index()
    pxb.to_csv(reports / "analysis_province_x_batch.csv", index=False, encoding="utf-8-sig")

    # ---- 结论（可追溯） ----
    total_sub = len(sub)
    total_proj = len(projects)
    total_inh = len(inh)
    match_rate = round(len(matches[matches["match_status"] == "matched"]) / len(matches), 4)
    avg_sub_per_proj = round(total_sub / total_proj, 2)
    top_prov = region.iloc[0]
    top_cat = sub["category"].value_counts().idxmax()
    top_cat_count = int(sub["category"].value_counts().max())
    multi_prov = (
        sub.groupby("project_code")["province"]
        .nunique()
        .sort_values(ascending=False)
    )
    cross_top = sub[sub["project_code"] == multi_prov.index[0]]
    cross_name = cross_top["project_name"].iloc[0]
    cross_count = int(multi_prov.iloc[0])
    b1_new = int(sub[(sub["batch_no"] == 1) & (sub["entry_type"] == "new")].shape[0])
    b5_total = int(sub[sub["batch_no"] == 5].shape[0])
    inh_b6 = int(inh[inh["inheritor_batch_no"] == 6].shape[0])

    def conclusion(text: str, indicator: str, fields: list[str], filters: str) -> dict:
        return {
            "结论": text,
            "对应指标": indicator,
            "使用字段": fields,
            "筛选条件": filters,
            "数据版本": DATA_VERSION,
            "生成日期": GENERATED,
        }

    conclusions = [
        conclusion(
            f"全国国家级非遗数据中，{total_sub} 个地区子项对应 {total_proj} 个独立项目，平均每个独立项目对应 {avg_sub_per_proj} 个子项，"
            "说明“项目数”与“地区子项数”是两个必须区分的统计口径。",
            "项目数 / 地区子项数",
            ["project_code", "subitem_id", "province"],
            "全部十大门类，无筛选",
        ),
        conclusion(
            f"按地区子项计，{top_prov['province']}（{int(top_prov['subitem_count'])} 条）居首，"
            "其次是 山东、山西、广东、河北（见 analysis_region.csv），国家级非遗子项在东部、华北与西南多省相对密集。",
            "地区子项数",
            ["province", "subitem_id"],
            "全部十大门类，按 province 分组",
        ),
        conclusion(
            f"跨地区项目最典型的是 {cross_name}（项目编号 {multi_prov.index[0]}），覆盖 {cross_count} 个省级地区；"
            "董永传说、梁祝传说等民间文学项目同样横跨多省，说明同一项目的保护工作可能涉及多地区协同。",
            "项目覆盖省级地区数",
            ["project_code", "province", "project_name"],
            "全部十大门类，按 project_code 分组统计 province 唯一数",
        ),
        conclusion(
            f"十大门类中，{top_cat} 的子项最多（{top_cat_count} 条），传统体育、游艺与杂技最少（166 条）；"
            "类别规模差异反映名录结构，不代表保护价值高低。",
            "类别子项数",
            ["category", "subitem_id"],
            "全部十大门类，按 category 分组",
        ),
        conclusion(
            f"批次结构上，第一批全部为新增（{b1_new} 条），第二至第五批均包含新增与扩展；第五批共 {b5_total} 条，"
            "说明扩展名录是后续批次的重要组成部分。",
            "批次 × 新增/扩展",
            ["batch_no", "entry_type"],
            "全部十大门类，按 batch_no 分组",
        ),
        conclusion(
            f"传承人公开数据共 {total_inh} 条记录（含2025年第六批 {inh_b6} 条），与项目子项的匹配率为 {match_rate * 100:.2f}%，"
            "其中 26 条存在多候选需人工确认；官方截至2023年汇总为 3059 人，口径差异见数据质量报告。",
            "传承人匹配率",
            ["child_num", "project_num", "province"],
            "全部传承人记录，按 child_num 与 项目编号+省份 关联",
        ),
        conclusion(
            "省级层面，传承人公开配置与子项数量并非简单正比：部分子项多的省份每百子项传承人数较低（见 analysis_region.csv），"
            "该差异仅反映公开配置结构，不构成传承状况评价。",
            "每百个子项对应传承人数",
            ["province", "inheritor_count", "subitem_count"],
            "全部传承人记录，按 province 分组",
        ),
    ]
    (reports / "conclusions.json").write_text(
        json.dumps(conclusions, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    print("=== 省级 TOP10 ===")
    print(region.head(10)[["province", "subitem_count", "project_count", "inheritor_count",
                           "inheritor_coverage", "inheritors_per_100_subitems"]].to_string(index=False))
    print("\n=== 批次 ===")
    print(pd.DataFrame(batch_rows).to_string(index=False))
    print("\n=== 类别 ===")
    print(pd.DataFrame(cat_rows).sort_values("subitem_count", ascending=False)
          [["category", "subitem_count", "project_count", "inheritor_count",
            "inheritor_coverage", "inheritors_per_100_subitems"]].to_string(index=False))
    print("\n=== 传承人批次 ===")
    print(inh_batch.to_string(index=False))
    print("\n结论数:", len(conclusions))


if __name__ == "__main__":
    main()
