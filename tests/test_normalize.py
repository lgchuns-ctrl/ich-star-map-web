"""编号、地区、批次、类型标准化测试。"""

from scripts.lib.common import (
    map_province,
    normalize_code,
    normalize_entry_type,
    parse_rx_time,
)


def test_normalize_code_roman_variants():
    assert normalize_code("Ⅱ—28") == "II-28"
    assert normalize_code("Ⅱ-28") == "II-28"
    assert normalize_code("II-28") == "II-28"
    assert normalize_code("Ⅹ-1") == "X-1"
    assert normalize_code("Ⅰ-001") == "I-001"
    assert normalize_code(" Ⅰ-1 ") == "I-1"


def test_normalize_code_empty():
    assert normalize_code(None) == ""
    assert normalize_code("") == ""


def test_parse_rx_time():
    assert parse_rx_time("2006</br>(第一批)") == {"year": 2006, "batch_no": 1}
    assert parse_rx_time("2021</br>(第五批)") == {"year": 2021, "batch_no": 5}
    assert parse_rx_time(None) == {"year": None, "batch_no": None}


def test_map_province():
    assert map_province("520000")[0] == "贵州省"
    assert map_province("990121")[0] == "中直单位"
    assert map_province("", "浙江省杭州市")[0] == "浙江省"
    assert map_province("999999")[0] == "未知"


def test_entry_type():
    assert normalize_entry_type("新增项目") == "new"
    assert normalize_entry_type("扩展项目") == "extension"
    assert normalize_entry_type(None) == "unknown"
    assert normalize_entry_type("其他") == "unknown"
