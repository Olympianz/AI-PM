"""面试就绪度：模拟面试评分、达标判定与作品集清单。"""
from typing import Dict, List
import json

from ai_pm.capability_model import CapabilityModel


def load_rubrics(path: str) -> dict:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def score_interview(session: Dict[str, List[dict]], rubrics: dict) -> Dict[str, float]:
    out: Dict[str, float] = {}
    for section, answers in session.items():
        checklist = rubrics.get(section, {}).get("checklist", [])
        if not checklist:
            out[section] = 3.0
            continue
        ratios = []
        for a in answers:
            hit = sum(1 for kw in checklist if kw in a.get("answer_text", ""))
            ratios.append(hit / len(checklist))
        avg = sum(ratios) / len(ratios) if ratios else 0.0
        out[section] = round(1 + 4 * avg, 2)
    return out


def verdict(model: CapabilityModel, levels: Dict[str, int],
            interview_scores: Dict[str, float],
            thresholds: tuple = (4.0, 3.5)) -> dict:
    core = [it for it in model.items if it.target_level >= 4]
    missing = [it.id for it in core if levels.get(it.id, 1) < it.target_level]
    avg = sum(interview_scores.values()) / len(interview_scores) if interview_scores else 0.0
    if not missing:
        if avg >= thresholds[0]:
            return {"verdict": "达到", "avg_score": round(avg, 2), "missing": []}
        return {"verdict": "接近", "avg_score": round(avg, 2), "missing": [],
                "reason": "能力达标，面试表达待提升"}
    if len(missing) <= 2 and avg >= thresholds[1]:
        return {"verdict": "接近", "avg_score": round(avg, 2), "missing": missing}
    return {"verdict": "未达到", "avg_score": round(avg, 2), "missing": missing}


def portfolio_checklist(model: CapabilityModel, artifacts: List[dict]) -> List[dict]:
    owned: Dict[str, set] = {}
    for a in artifacts:
        owned.setdefault(a["item_id"], set()).add(a.get("type", ""))
    out = []
    for it in model.items:
        if it.target_level < 4:
            continue
        for req in it.evidence_requirements:
            req_types = _required_types(req)
            has = it.id in owned
            if has and req_types is not None:
                has = bool(owned[it.id] & req_types)
            out.append({"item_id": it.id, "evidence": req,
                        "status": "已具备" if has else "待补"})
    return out


def _required_types(req: str):
    types = set()
    if ("STAR" in req) or ("案例" in req):
        types |= {"star_case", "answer_card"}
    if ("方案" in req) or ("PRD" in req) or ("输出物" in req) or ("原型" in req):
        types |= {"prd", "case_analysis", "prototype"}
    return types or None
