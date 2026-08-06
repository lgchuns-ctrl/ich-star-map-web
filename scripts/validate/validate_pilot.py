# -*- coding: utf-8 -*-
"""试点数据质量验证：生成采集报告、验证报告与人工抽样清单。"""

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
    "民间文学",
    "传统音乐",
    "传统舞蹈",
    "传统戏剧",
    "曲艺",
    "传统体育、游艺与杂技",
    "传统美术",
    "传统技艺",
    "传统医药",
    "民俗",
}
KNOWN_PROVINCES = {
    "北京市", "天津市", "河北省", "山西省", "内蒙古自治区", "辽宁省", "吉林省",
    "黑龙江省", "上海市", "江苏省", "浙江省", "安徽省", "福建省", "江西省",
    "山东省", "河南省", "湖北省", "湖南省", "广东省", "广西壮族自治区", "海南省",
    "重庆市", "四川省", "贵州省", "云南省", "西藏自治区", "陕西省", "甘肃省",
    "青海省", "宁夏回族自治区", "新疆维吾尔自治区", "台湾省", "香港特别行政区",
    "澳门特别行政区", "新疆生产建设兵团", "中直单位",
}


def check_code_format(code: str) -> tuple[bool, str]:
    m = re.fullmatch(r"([IVX]+)-(\d+)", code)
    if not m:
        return False, f"编号格式异常: {code!r}"
    return True, ""


def build_collection_report() -> dict:
    log_csv = ROOT / "data" / "raw" / "request_logs" / "request_log.csv"
    failed_jsonl = ROOT / "data" / "raw" / "projects" / "failed_records.jsonl"
    raw_jsonl = ROOT / "data" / "raw" / "projects" / "projects_raw.jsonl"
    log_rows = []
    if log_csv.exists():
        with log_csv.open(encoding="utf-8", newline="") as f:
            log_rows = list(csv.DictReader(f))
    failed = []
    if failed_jsonl.exists():
        failed = [
            json.loads(line)
            for line in failed_jsonl.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
    raw_records = []
    if raw_jsonl.exists():
        raw_records = [
            json.loads(line)
            for line in raw_jsonl.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
    ids = [str(r["payload"]["id"]) for r in raw_records]
    return {
        "requests": len(log_rows),
        "success": sum(1 for r in log_rows if not r.get("error") and r.get("status") == "200"),
        "failed": len(failed),
        "raw_records": len(raw_records),
        "unique_records": len(set(ids)),
        "duplicates": len(ids) - len(set(ids)),
        "sources": sorted({r["source_url"].split("?")[0] for r in raw_records}),
        "collection_time_start": log_rows[0]["timestamp"] if log_rows else None,
        "collection_time_end": log_rows[-1]["timestamp"] if log_rows else None,
        "failed_details": failed,
        "known_issues": [
            "试点数据仅覆盖「民间文学」门类（type=1），用于验证采集与清洗结构，不代表全国总量。",
            "接口按「地区子项」口径返回 3610 条记录，试点采集其中民间文学门类 251 条。",
            "keywords 参数在本接口下行为不稳定，试点阶段不依赖服务端关键词检索，搜索在前端本地完成。",
        ],
    }


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    report_dir = ROOT / "data" / "reports"
    report_dir.mkdir(parents=True, exist_ok=True)

    collection = build_collection_report()
    (report_dir / "pilot_collection_report.json").write_text(
        json.dumps(collection, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    csv_path = ROOT / "data" / "processed" / "subitems_pilot.csv"
    if not csv_path.exists():
        print("请先运行 scripts/clean/clean_pilot.py")
        sys.exit(1)
    df = pd.read_csv(csv_path, dtype=str).fillna("")

    checks = {}
    # 1) 项目编号格式
    bad_codes = []
    for code in df["project_code_normalized"]:
        ok, msg = check_code_format(code)
        if not ok:
            bad_codes.append(msg)
    checks["project_code_format"] = {"pass": not bad_codes, "examples": bad_codes[:10]}

    # 2) 必填字段缺失
    required = [
        "project_code", "project_name", "category", "batch_no", "publish_year",
        "entry_type", "region_raw", "province",
    ]
    missing = {col: int((df[col].astype(str).str.strip() == "").sum()) for col in required}
    checks["required_fields"] = {"pass": all(v == 0 for v in missing.values()), "missing": missing}

    # 3) 重复（组合键）
    combo = df[["project_code", "batch_no", "region_raw", "protection_unit_raw", "entry_type"]]
    dup_count = int(combo.duplicated().sum())
    checks["duplicates"] = {"pass": dup_count == 0, "count": dup_count}

    # 4) 批次合法
    bad_batches = df[~df["batch_no"].isin([str(b) for b in VALID_BATCHES])]
    checks["batch_legal"] = {
        "pass": len(bad_batches) == 0,
        "bad": len(bad_batches),
        "values": sorted(df["batch_no"].unique().tolist()),
    }

    # 5) 类别合法
    bad_cats = df[~df["category"].isin(VALID_CATEGORIES)]
    checks["category_legal"] = {
        "pass": len(bad_cats) == 0,
        "bad": len(bad_cats),
        "values": sorted(df["category"].unique().tolist()),
    }

    # 6) 地区映射
    bad_prov = df[~df["province"].isin(KNOWN_PROVINCES)]
    checks["province_mapping"] = {
        "pass": len(bad_prov) == 0,
        "unmapped": len(bad_prov),
        "unknown_values": sorted(bad_prov["province"].unique().tolist()),
    }

    # 7) 新增/扩展类型
    bad_entry = df[~df["entry_type"].isin(["new", "extension", "unknown"])]
    checks["entry_type"] = {
        "pass": len(bad_entry) == 0,
        "values": df["entry_type"].value_counts().to_dict(),
    }

    # 8) 批次-年份一致性
    bad_year = df[
        df["publish_year"].isin([str(y) for y in VALID_YEARS]) == False  # noqa: E712
    ]
    checks["publish_year"] = {
        "pass": len(bad_year) == 0,
        "bad": len(bad_year),
        "values": sorted(df["publish_year"].unique().tolist()),
    }

    validation = {
        "dataset": "pilot（民间文学门类）",
        "rows": len(df),
        "checks": checks,
        "overall_pass": all(c.get("pass", False) for c in checks.values()),
    }
    (report_dir / "validation_report.json").write_text(
        json.dumps(validation, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    # 人工抽样清单：每批次 2 条、每类别（1 类）与不同地区尽量分散
    rng = random.Random(20260806)
    sample = pd.DataFrame()
    for batch in sorted(df["batch_no"].unique()):
        sub = df[df["batch_no"] == batch]
        sample = pd.concat([sample, sub.sample(min(2, len(sub)), random_state=rng.randint(0, 1 << 30))])
    extra = df[~df["subitem_id"].isin(sample["subitem_id"])].sample(
        max(0, 20 - len(sample)), random_state=42
    )
    sample = pd.concat([sample, extra])
    sample = sample.assign(
        review_result="", review_comment="", reviewed_at="", reviewer=""
    )
    sample_cols = [
        "subitem_id", "project_code", "project_name", "category", "batch_no",
        "publish_year", "entry_type", "region_raw", "province",
        "protection_unit_normalized", "review_result", "review_comment",
        "reviewed_at", "reviewer",
    ]
    sample[sample_cols].to_csv(
        report_dir / "manual_sample_review.csv", index=False, encoding="utf-8-sig"
    )

    print("验证结果:", json.dumps(validation, ensure_ascii=False, indent=2))
    print("人工抽样清单:", report_dir / "manual_sample_review.csv", f"({len(sample)} 条)")


if __name__ == "__main__":
    main()
