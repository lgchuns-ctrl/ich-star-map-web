"""传承资源观察指标计算测试。"""

from scripts.lib.indicators import (
    category_diversity,
    inheritor_coverage,
    inheritors_per_100_subitems,
)


def test_inheritor_coverage():
    assert inheritor_coverage(50, 100) == 0.5
    assert inheritor_coverage(0, 100) == 0.0
    assert inheritor_coverage(0, 0) is None


def test_inheritors_per_100_subitems():
    assert inheritors_per_100_subitems(25, 100) == 25.0
    assert inheritors_per_100_subitems(0, 0) is None


def test_category_diversity():
    assert category_diversity(7, 10) == 0.7
    assert category_diversity(0, 10) == 0.0
    assert category_diversity(1, 0) is None
