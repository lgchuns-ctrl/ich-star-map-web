# -*- coding: utf-8 -*-
"""共享常量、标准化函数与解析工具。"""

from __future__ import annotations

import hashlib
import re
import unicodedata
from datetime import datetime, timezone

from bs4 import BeautifulSoup

# 省级地区：行政区划代码 -> (全称, 地图名称)
REGIONS: dict[str, dict[str, str]] = {
    "110000": {"name": "北京市", "map_name": "北京市"},
    "120000": {"name": "天津市", "map_name": "天津市"},
    "130000": {"name": "河北省", "map_name": "河北省"},
    "140000": {"name": "山西省", "map_name": "山西省"},
    "150000": {"name": "内蒙古自治区", "map_name": "内蒙古自治区"},
    "210000": {"name": "辽宁省", "map_name": "辽宁省"},
    "220000": {"name": "吉林省", "map_name": "吉林省"},
    "230000": {"name": "黑龙江省", "map_name": "黑龙江省"},
    "310000": {"name": "上海市", "map_name": "上海市"},
    "320000": {"name": "江苏省", "map_name": "江苏省"},
    "330000": {"name": "浙江省", "map_name": "浙江省"},
    "340000": {"name": "安徽省", "map_name": "安徽省"},
    "350000": {"name": "福建省", "map_name": "福建省"},
    "360000": {"name": "江西省", "map_name": "江西省"},
    "370000": {"name": "山东省", "map_name": "山东省"},
    "410000": {"name": "河南省", "map_name": "河南省"},
    "420000": {"name": "湖北省", "map_name": "湖北省"},
    "430000": {"name": "湖南省", "map_name": "湖南省"},
    "440000": {"name": "广东省", "map_name": "广东省"},
    "450000": {"name": "广西壮族自治区", "map_name": "广西壮族自治区"},
    "460000": {"name": "海南省", "map_name": "海南省"},
    "500000": {"name": "重庆市", "map_name": "重庆市"},
    "510000": {"name": "四川省", "map_name": "四川省"},
    "520000": {"name": "贵州省", "map_name": "贵州省"},
    "530000": {"name": "云南省", "map_name": "云南省"},
    "540000": {"name": "西藏自治区", "map_name": "西藏自治区"},
    "610000": {"name": "陕西省", "map_name": "陕西省"},
    "620000": {"name": "甘肃省", "map_name": "甘肃省"},
    "630000": {"name": "青海省", "map_name": "青海省"},
    "640000": {"name": "宁夏回族自治区", "map_name": "宁夏回族自治区"},
    "650000": {"name": "新疆维吾尔自治区", "map_name": "新疆维吾尔自治区"},
    "710000": {"name": "台湾省", "map_name": "台湾省"},
    "810000": {"name": "香港特别行政区", "map_name": "香港特别行政区"},
    "820000": {"name": "澳门特别行政区", "map_name": "澳门特别行政区"},
    "990121": {"name": "中直单位", "map_name": ""},
    "990122": {"name": "新疆生产建设兵团", "map_name": ""},
}

# 官方页面 type 下拉：类别 ID -> 类别名
CATEGORIES: dict[str, str] = {
    "1": "民间文学",
    "2": "传统音乐",
    "3": "传统舞蹈",
    "4": "传统戏剧",
    "5": "曲艺",
    "6": "传统体育、游艺与杂技",
    "7": "传统美术",
    "8": "传统技艺",
    "9": "传统医药",
    "10": "民俗",
}

# 官方页面 rx_time 下拉：公布时间 ID -> (批次号, 年份)
BATCH_IDS: dict[str, tuple[int, int]] = {
    "1": (1, 2006),
    "2": (2, 2008),
    "3": (3, 2011),
    "4": (4, 2014),
    "10": (5, 2021),
}

CHINESE_NUM = {"一": 1, "二": 2, "三": 3, "四": 4, "五": 5, "六": 6, "七": 7, "八": 8, "九": 9, "十": 10}

ROMAN_TO_NUM = {"I": 1, "II": 2, "III": 3, "IV": 4, "V": 5, "VI": 6, "VII": 7, "VIII": 8, "IX": 9, "X": 10}


def now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S+00:00")


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def clean_text(text: str | None) -> str:
    """去除空白、HTML 标签与全角空格，压缩连续空白。"""
    if not text:
        return ""
    text = unicodedata.normalize("NFKC", text.replace("\u3000", " "))
    text = BeautifulSoup(text, "lxml").get_text(" ", strip=True)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def normalize_code(code: str | None) -> str:
    """项目编号标准化：全角转半角、统一罗马数字、去空格、补零规则。

    例：'Ⅱ—28' -> 'II-28'；'Ⅹ-1' -> 'X-1'。
    """
    if not code:
        return ""
    code = unicodedata.normalize("NFKC", code.strip())
    # 罗马数字：NFKC 后 Ⅰ 等已转为 I，但再兜底替换
    code = (
        code.replace("Ⅰ", "I")
        .replace("Ⅱ", "II")
        .replace("Ⅲ", "III")
        .replace("Ⅳ", "IV")
        .replace("Ⅴ", "V")
        .replace("Ⅵ", "VI")
        .replace("Ⅶ", "VII")
        .replace("Ⅷ", "VIII")
        .replace("Ⅸ", "IX")
        .replace("Ⅹ", "X")
    )
    code = re.sub(r"[\s\u00a0]+", "", code)
    code = code.replace("—", "-").replace("－", "-").replace("–", "-")
    code = code.replace("：", ":").replace("（", "(").replace("）", ")")
    # 保持罗马数字为大写
    m = re.match(r"^([ivx]+)-(\d+)", code, re.IGNORECASE)
    if m:
        code = f"{m.group(1).upper()}-{m.group(2)}"
    return code


def parse_rx_time(rx_time: str | None) -> dict:
    """解析公布时间字段，如 '2006</br>(第一批)' -> {year:2006, batch_no:1}。"""
    if not rx_time:
        return {"year": None, "batch_no": None}
    text = clean_text(rx_time)
    m_year = re.search(r"(19\d{2}|20\d{2})", text)
    m_batch = re.search(r"第([一二三四五六七八九十]+)批", text)
    batch_no = CHINESE_NUM[m_batch.group(1)] if m_batch else None
    return {"year": int(m_year.group(1)) if m_year else None, "batch_no": batch_no}


def normalize_entry_type(cate: str | None) -> str:
    if not cate:
        return "unknown"
    if "新增" in cate:
        return "new"
    if "扩展" in cate:
        return "extension"
    return "unknown"


def map_province(address: str | None, region_raw: str | None = None) -> tuple[str, str]:
    """按行政区划代码映射省份；失败时从地区原文中匹配。返回 (省份全称, 地图名称)。"""
    code = (address or "").strip()
    if code in REGIONS:
        reg = REGIONS[code]
        return reg["name"], reg["map_name"]
    if region_raw:
        for c, reg in REGIONS.items():
            if reg["map_name"] and reg["name"][:2] in region_raw:
                return reg["name"], reg["map_name"]
    return "未知", ""


def parse_applicant_from_content(content: str | None) -> str:
    """从详情 content 字段提取 '申报地区或单位：...'。"""
    if not content:
        return ""
    text = clean_text(content)
    m = re.search(r"申报地区或单位[：:]\s*([^。\n]*?)(?:\s*$|。)", text)
    if not m:
        m = re.search(r"申报地区或单位[：:]\s*([^\s]+)", text)
    return m.group(1).strip() if m else ""


def build_request_url(base: str, params: dict) -> str:
    """构造带查询参数的规范 URL（用于溯源）。"""
    from urllib.parse import urlencode

    return f"{base}?{urlencode(params)}"


def hash_params(params: dict) -> str:
    return sha256_text(repr(sorted(params.items())))[:16]
