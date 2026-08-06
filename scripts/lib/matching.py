# -*- coding: utf-8 -*-
"""项目-传承人关联匹配（阶段C全量数据启用）。

关联优先级：项目编号 + 项目名称 + 地区；不单独按名称关联。
当前提供可测试的匹配函数与合成数据测试；全量传承人数据采集后接入。
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class InheritorRecord:
    inheritor_id: str
    name: str
    project_code: str = ""
    project_name: str = ""
    region_raw: str = ""
    province: str = ""


@dataclass
class ProjectCandidate:
    project_code: str
    project_name: str
    province: str = ""


@dataclass
class MatchResult:
    match_status: str
    matched_ids: list[str] = field(default_factory=list)
    reason: str = ""


def match_inheritor(
    inheritor: InheritorRecord,
    candidates: list[ProjectCandidate],
) -> MatchResult:
    """返回 matched / multiple_candidates / unmatched / manual_confirmed。"""
    code_cands = [c for c in candidates if c.project_code == inheritor.project_code] if inheritor.project_code else []
    if code_cands:
        narrowed = [
            c
            for c in code_cands
            if not inheritor.province or c.province == inheritor.province
        ]
        pool = narrowed or code_cands
        if len(pool) == 1:
            return MatchResult("matched", [pool[0].project_code], "编号匹配")
        return MatchResult("multiple_candidates", [c.project_code for c in pool], "编号匹配但存在多个候选")

    name_cands = [c for c in candidates if c.project_name == inheritor.project_name]
    if len(name_cands) == 1:
        return MatchResult("matched", [name_cands[0].project_code], "名称匹配")
    if len(name_cands) > 1:
        return MatchResult("multiple_candidates", [c.project_code for c in name_cands], "名称匹配但存在多个候选")
    return MatchResult("unmatched", [], "未找到匹配")
