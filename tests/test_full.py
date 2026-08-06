"""全量数据（阶段C/D）集成测试。"""

import json
from pathlib import Path

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def sub() -> pd.DataFrame:
    p = ROOT / "data" / "processed" / "subitems_full.csv"
    if not p.exists():
        pytest.skip("缺少 subitems_full.csv，请先运行 clean_full.py")
    return pd.read_csv(p, dtype=str).fillna("")


@pytest.fixture(scope="module")
def inh() -> pd.DataFrame:
    p = ROOT / "data" / "processed" / "inheritors_full.csv"
    if not p.exists():
        pytest.skip("缺少 inheritors_full.csv")
    return pd.read_csv(p, dtype=str).fillna("")


def test_official_totals_match(sub, inh):
    assert len(sub) == 3610
    assert sub["project_code"].nunique() == 1557
    assert len(inh) == 3995


def test_no_duplicates_with_adjusted_key(sub):
    key = ["project_code", "batch_no", "project_name", "region_raw", "protection_unit_raw", "entry_type"]
    assert sub[key].duplicated().sum() == 0


def test_all_categories_and_batches(sub):
    assert sub["category"].nunique() == 10
    assert set(sub["batch_no"].astype(int).unique()) == {1, 2, 3, 4, 5}


def test_inheritor_match_rate(inh):
    matches = pd.read_csv(ROOT / "data" / "processed" / "inheritor_matches.csv", dtype=str).fillna("")
    rate = (matches["match_status"] == "matched").mean()
    assert rate >= 0.9
    assert (matches["match_status"] == "unmatched").sum() == 0


def test_analysis_and_exports_consistent():
    reports = ROOT / "data" / "reports"
    region = pd.read_csv(reports / "analysis_region.csv", dtype=str).fillna("")
    assert region["subitem_count"].astype(int).sum() == 3610

    data_dir = ROOT / "web" / "public" / "data"
    meta = json.loads((data_dir / "metadata.json").read_text(encoding="utf-8"))
    assert meta["cleaned_subitem_count"] == 3610
    assert meta["distinct_project_count"] == 1557
    provinces = json.loads((data_dir / "provinces.json").read_text(encoding="utf-8"))
    assert sum(p["subitem_count"] for p in provinces) == 3610
    inheritors = json.loads((data_dir / "inheritors.json").read_text(encoding="utf-8"))
    assert len(inheritors) == 3995
    conclusions = json.loads((data_dir / "conclusions.json").read_text(encoding="utf-8"))
    assert len(conclusions) >= 5
    for c in conclusions:
        assert c["数据版本"] and c["生成日期"] and c["使用字段"]
