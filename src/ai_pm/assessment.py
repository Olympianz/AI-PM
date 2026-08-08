"""测评：客观题评分、案例题评分、能力等级与优先补强清单。"""
from typing import Dict, List, Optional
import json

from ai_pm.capability_model import CapabilityModel


def load_bank(path: str) -> List[dict]:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def score_objective(answers: Dict[str, str], bank: List[dict]) -> Dict[str, float]:
    by_cap: Dict[str, List[int]] = {}
    for q in bank:
        by_cap.setdefault(q["capability_id"], []).append(
            1 if answers.get(q["id"]) == q["answer"] else 0)
    return {cap: round(sum(vals) / len(vals), 3) for cap, vals in by_cap.items()}


def score_case(answer_text: str, rubric: dict) -> float:
    checklist = rubric.get("checklist", [])
    if not checklist:
        return float(rubric.get("default_score", 3.0))
    hit = sum(1 for kw in checklist if kw in answer_text)
    return round(1 + 4 * min(hit / len(checklist), 1.0), 2)


def current_levels(model: CapabilityModel,
                   objective_scores: Optional[Dict[str, float]] = None,
                   case_scores: Optional[Dict[str, float]] = None) -> Dict[str, int]:
    obj = objective_scores or {}
    case = case_scores or {}
    out: Dict[str, int] = {}
    for it in model.items:
        o, c = obj.get(it.id), case.get(it.id)
        if o is not None and c is not None:
            composite = 0.6 * o + 0.4 * c
        else:
            composite = o if o is not None else c
        out[it.id] = 1 if composite is None else max(1, min(5, round(1 + 4 * composite)))
    return out


def build_radar(model: CapabilityModel, levels: Dict[str, int]) -> Dict[str, float]:
    by_domain: Dict[str, List[int]] = {}
    for it in model.items:
        by_domain.setdefault(it.domain, []).append(levels.get(it.id, 1))
    return {d: round(sum(v) / len(v), 2) for d, v in by_domain.items()}


def priority_gaps(model: CapabilityModel, levels: Dict[str, int], top_n: int = 5) -> List[dict]:
    scored = []
    for it in model.items:
        gap = (it.target_level - levels.get(it.id, 1)) * it.weight
        if gap > 0:
            scored.append({"item_id": it.id, "name": it.name,
                           "current_level": levels.get(it.id, 1),
                           "target_level": it.target_level,
                           "gap": round(gap, 3)})
    scored.sort(key=lambda x: x["gap"], reverse=True)
    return scored[:top_n]
