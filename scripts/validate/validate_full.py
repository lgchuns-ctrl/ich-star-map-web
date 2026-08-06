# -*- coding: utf-8 -*-
"""全量数据质量验证：生成全量采集报告、验证报告、差异报告与人工抽样清单。"""

from __future__ import annotations

import csv
import json
import random
import re
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

VALID_YEARS = {2006, 2008, 2011, 2014, 2021}
VALID_BATCHES = {1, 2, 3, 4, 5}
VALID_CATEGORIES = {
    "民间文学", "传统音乐", "传统舞蹈", "传统戏剧", "曲艺",
    "传统体育、游艺与杂技", "传统美术", "传统技艺", "传统医药", "民俗",
}
KNOWN_PROVINCES = {
    "北京市", "天津市", "河北省", "山西省", "内蒙古自治区", "辽宁省", "吉林省",
    "黑龙江省", "上海市", "江苏省", "浙江省", "安徽省", "福建省", "江西省",
    "山东省", "河南省", "湖北省", "湖南省", "广东省", "广西壮族自治区", "海南省",
    "重庆市", "四川省", "贵州省", "云南省", "西藏自治区", "陕西省", "甘肃省",
    "青海省", "宁夏回族自治区", "新疆维吾尔自治区", "台湾省", "香港特别行政区",
    "澳门特别行政区", "新疆生产建设兵团", "中直单位",
}

# 官方公开汇总（仅作校验依据，不硬编码为最终答案）
OFFICIAL = {
    "subitems": 3610,
    "projects": 1557,
    "inheritors_until_2023": 3059,
}


def build_collection_report() -> dict:
    log_csv = ROOT / "data" / "raw" / "request_logs" / "request_log.csv"
    failed = []
    for f in [
        ROOT / "data" / "raw" / "projects" / "failed_records.jsonl",
        ROOT / "data" / "raw" / "inheritors" / "failed_records.jsonl",
    ]:
        if f.exists():
            failed += [
                json.loads(line)
                for line in f.read_text(encoding="utf-8").splitlines()
                if line.strip()
            ]
    rows = []
    if log_csv.exists():
        with log_csv.open(encoding="utf-8", newline="") as f:
            rows = list(csv.DictReader(f))
    return {
        "requests": len(rows),
        "success": sum(1 for r in rows if not r.get("error") and r.get("status") == "200"),
        "failed": len(failed),
        "failed_details": failed,
        "first_request": rows[0]["timestamp"] if rows else None,
        "last_request": rows[-1]["timestamp"] if rows else None,
    }


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    report_dir = ROOT / "data" / "reports"
    report_dir.mkdir(parents=True, exist_ok=True)

    collection = build_collection_report()
    (report_dir / "full_collection_report.json").write_text(
        json.dumps(collection, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    sub = pd.read_csv(ROOT / "data" / "processed" / "subitems_full.csv", dtype=str).fillna("")
    inh = pd.read_csv(ROOT / "data" / "processed" / "inheritors_full.csv", dtype=str).fillna("")
    matches = pd.read_csv(
        ROOT / "data" / "processed" / "inheritor_matches.csv", dtype=str
    ).fillna("")

    checks = {}
    # 编号格式
    bad_codes = [
        c for c in sub["project_code_normalized"]
        if not re.fullmatch(r"[IVX]+-\d+", c)
    ]
    checks["project_code_format"] = {"pass": not bad_codes, "bad": len(bad_codes)}
    # 必填
    required = ["project_code", "project_name", "category", "batch_no", "publish_year",
                "entry_type", "region_raw", "province"]
    missing = {col: int((sub[col].astype(str).str.strip() == "").sum()) for col in required}
    checks["required_fields"] = {"pass": all(v == 0 for v in missing.values()), "missing": missing}
    # 重复（组合键按真实数据调整：加入 project_name，避免把同项目同地区不同子项误判为重复）
    combo = sub[
        ["project_code", "batch_no", "project_name", "region_raw", "protection_unit_raw", "entry_type"]
    ]
    checks["duplicates"] = {
        "pass": bool(combo.duplicated().sum() == 0),
        "count": int(combo.duplicated().sum()),
        "note": "组合键已加入 project_name；试点阶段的口径在多个子项共址时过严，已在全量验证中调整，"
        "实例：津门法鼓(挂甲寺庆音法鼓) 与 (杨家庄永音法鼓)、藏戏多个剧种变体、中医诊疗法多个流派。",
    }
    # 批次/年份
    checks["batch_legal"] = {
        "pass": bool(set(sub["batch_no"].astype(int).unique()) <= VALID_BATCHES),
        "values": sorted(sub["batch_no"].unique().tolist()),
    }
    checks["publish_year"] = {
        "pass": bool(set(sub["publish_year"].astype(int).unique()) <= VALID_YEARS),
        "values": sorted(sub["publish_year"].unique().tolist()),
    }
    # 类别
    checks["category_legal"] = {
        "pass": bool(set(sub["category"].unique()) <= VALID_CATEGORIES),
        "values": sorted(sub["category"].unique().tolist()),
    }
    # 地区映射
    bad_prov = set(sub["province"].unique()) - KNOWN_PROVINCES
    checks["province_mapping"] = {"pass": not bad_prov, "unmapped": sorted(bad_prov)}
    # 传承人批次/年份
    checks["inheritor_batch"] = {
        "pass": bool(
            inh["inheritor_batch_no"].astype(str).str.strip().replace("", "0")
            .astype(int).between(1, 6).all()
        ),
        "values": sorted(inh["inheritor_batch_no"].unique().tolist()),
    }
    # 传承人匹配
    mcount = matches["match_status"].value_counts().to_dict()
    match_rate = round(mcount.get("matched", 0) / len(matches), 4)
    checks["inheritor_match"] = {
        "pass": match_rate >= 0.9,
        "match_rate": match_rate,
        "counts": mcount,
    }

    counts = {
        "subitems": len(sub),
        "distinct_projects": sub["project_code"].nunique(),
        "inheritors": len(inh),
    }
    differences = {
        k: {
            "collected": counts[k],
            "official": v,
            "delta": counts[k] - v,
        }
        for k, v in {
            "subitems": OFFICIAL["subitems"],
            "distinct_projects": OFFICIAL["projects"],
            "inheritors": OFFICIAL["inheritors_until_2023"],
        }.items()
    }
    differences["note"] = (
        "官方总量仅作校验依据；传承人官方口径为截至2023年共3059人，"
        "本站接口返回3995条（含2025年第六批与已故传承人等），差异在质量报告中说明。"
    )

    validation = {
        "dataset": "全量（十大门类）",
        "counts": counts,
        "checks": checks,
        "overall_pass": all(c.get("pass", False) for c in checks.values()),
        "official_comparison": differences,
    }
    (report_dir / "full_validation_report.json").write_text(
        json.dumps(validation, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    # 人工抽样（每批次2条 + 补充至30条）
    rng = random.Random(20260806)
    sample = pd.DataFrame()
    for batch in sorted(sub["batch_no"].astype(int).unique()):
        sub_b = sub[sub["batch_no"] == str(batch)]
        sample = pd.concat([sample, sub_b.sample(min(2, len(sub_b)), random_state=rng.randint(0, 1 << 30))])
    extra = sub[~sub["subitem_id"].isin(sample["subitem_id"])].sample(
        max(0, 30 - len(sample)), random_state=42
    )
    sample = pd.concat([sample, extra]).assign(
        review_result="", review_comment="", reviewed_at="", reviewer=""
    )
    cols = [
        "subitem_id", "project_code", "project_name", "category", "batch_no",
        "publish_year", "entry_type", "region_raw", "province",
        "protection_unit_normalized", "review_result", "review_comment",
        "reviewed_at", "reviewer",
    ]
    sample[cols].to_csv(report_dir / "manual_sample_review_full.csv", index=False, encoding="utf-8-sig")

    print(json.dumps(validation, ensure_ascii=False, indent=2))
    print("抽样清单:", report_dir / "manual_sample_review_full.csv", f"({len(sample)} 条)")


if __name__ == "__main__":
    main()
