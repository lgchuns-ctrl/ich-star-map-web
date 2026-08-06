"""试点数据集集成测试：读取清洗后数据与导出 JSON 进行校验。"""

import json
from pathlib import Path

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
VALID_YEARS = {2006, 2008, 2011, 2014, 2021}
KNOWN_PROVINCES = {
    "北京市", "天津市", "河北省", "山西省", "内蒙古自治区", "辽宁省", "吉林省",
    "黑龙江省", "上海市", "江苏省", "浙江省", "安徽省", "福建省", "江西省",
    "山东省", "河南省", "湖北省", "湖南省", "广东省", "广西壮族自治区", "海南省",
    "重庆市", "四川省", "贵州省", "云南省", "西藏自治区", "陕西省", "甘肃省",
    "青海省", "宁夏回族自治区", "新疆维吾尔自治区", "台湾省", "香港特别行政区",
    "澳门特别行政区", "新疆生产建设兵团", "中直单位",
}


@pytest.fixture(scope="module")
def df() -> pd.DataFrame:
    path = ROOT / "data" / "processed" / "subitems_pilot.csv"
    if not path.exists():
        pytest.skip("缺少 subitems_pilot.csv，请先运行采集与清洗")
    return pd.read_csv(path, dtype=str).fillna("")


def test_pilot_has_at_least_100_rows(df):
    assert len(df) >= 100


def test_required_fields_not_empty(df):
    for col in ["project_code", "project_name", "category", "batch_no", "publish_year",
                "entry_type", "region_raw", "province"]:
        assert (df[col].astype(str).str.strip() == "").sum() == 0, f"字段 {col} 存在空值"


def test_no_duplicate_combo(df):
    combo = df[["project_code", "batch_no", "region_raw", "protection_unit_raw", "entry_type"]]
    assert combo.duplicated().sum() == 0


def test_batches_legal(df):
    assert set(df["batch_no"].astype(int).unique()) <= {1, 2, 3, 4, 5}
    assert set(df["publish_year"].astype(int).unique()) <= VALID_YEARS


def test_provinces_mapped(df):
    unknown = set(df["province"].unique()) - KNOWN_PROVINCES
    assert unknown == set()


def test_entry_types_legal(df):
    assert set(df["entry_type"].unique()) <= {"new", "extension", "unknown"}


def test_json_exports_valid_and_consistent():
    data_dir = ROOT / "web" / "public" / "data"
    if not data_dir.exists():
        pytest.skip("缺少前端数据目录")
    meta = json.loads((data_dir / "metadata.json").read_text(encoding="utf-8"))
    assert meta.get("raw_project_record_count", meta.get("raw_record_count", 0)) >= 100
    assert "disclaimer" in meta and "官方濒危等级" in meta["disclaimer"]
    provinces = json.loads((data_dir / "provinces.json").read_text(encoding="utf-8"))
    assert sum(p["subitem_count"] for p in provinces) == meta["cleaned_subitem_count"]
    search = json.loads((data_dir / "project_search_index.json").read_text(encoding="utf-8"))
    assert len(search) == meta["cleaned_subitem_count"]
