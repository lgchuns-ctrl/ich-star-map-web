"""传承人关联匹配逻辑测试（合成数据）。"""

from scripts.lib.matching import (
    InheritorRecord,
    ProjectCandidate,
    match_inheritor,
)


def test_match_by_code_and_province():
    inh = InheritorRecord("inh-1", "张三", project_code="I-1", project_name="苗族古歌", province="贵州省")
    cands = [
        ProjectCandidate("I-1", "苗族古歌", "贵州省"),
        ProjectCandidate("I-2", "格萨（斯）尔", "四川省"),
    ]
    r = match_inheritor(inh, cands)
    assert r.match_status == "matched"
    assert r.matched_ids == ["I-1"]


def test_multiple_candidates():
    inh = InheritorRecord("inh-2", "李四", project_code="I-1", project_name="苗族古歌")
    cands = [
        ProjectCandidate("I-1", "苗族古歌", "贵州省"),
        ProjectCandidate("I-1", "苗族古歌", "湖南省"),
    ]
    r = match_inheritor(inh, cands)
    assert r.match_status == "multiple_candidates"
    assert r.matched_ids == ["I-1", "I-1"]


def test_unmatched():
    inh = InheritorRecord("inh-3", "王五", project_code="X-99", project_name="不存在项目")
    cands = [ProjectCandidate("I-1", "苗族古歌", "贵州省")]
    r = match_inheritor(inh, cands)
    assert r.match_status == "unmatched"
