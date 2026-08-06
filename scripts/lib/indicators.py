# -*- coding: utf-8 -*-
"""透明、可解释的传承资源观察指标。"""

from __future__ import annotations


def inheritor_coverage(matched_subitems: int, total_subitems: int) -> float | None:
    """代表性传承人覆盖率 = 已匹配传承人的子项数 / 子项总量。

    返回 0-1 浮点数；分母为 0 时返回 None（表示无法计算）。
    """
    if total_subitems <= 0:
        return None
    return matched_subitems / total_subitems


def inheritors_per_100_subitems(inheritor_count: int, total_subitems: int) -> float | None:
    """每百个子项对应传承人数 = 传承人数 / 子项数 * 100。"""
    if total_subitems <= 0:
        return None
    return inheritor_count / total_subitems * 100


def category_diversity(covered_categories: int, total_categories: int) -> float | None:
    """类别覆盖度 = 已覆盖类别数 / 十大门类总数。"""
    if total_categories <= 0:
        return None
    return covered_categories / total_categories
