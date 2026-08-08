from ai_pm.capability_model import CapabilityModel, CapabilityItem
from ai_pm.assessment import (score_objective, score_case, current_levels,
                              build_radar, priority_gaps)


BANK = [
    {"id": "q-001", "capability_id": "A2", "question": "Q1", "options": ["A", "B"], "answer": "A", "difficulty": 1},
    {"id": "q-002", "capability_id": "A2", "question": "Q2", "options": ["A", "B"], "answer": "B", "difficulty": 1},
    {"id": "q-003", "capability_id": "C3", "question": "Q3", "options": ["A", "B"], "answer": "A", "difficulty": 2},
]


def make_model():
    model = CapabilityModel(domains={"A": "AI 技术理解", "C": "数据与科学方法"})
    model.add_item(CapabilityItem(id="A2", domain="A", name="Agent 机制", target_level=4, weight=0.6))
    model.add_item(CapabilityItem(id="C3", domain="C", name="A/B 测试", target_level=3, weight=0.4))
    return model


def test_score_objective_per_capability():
    scores = score_objective({"q-001": "A", "q-002": "A", "q-003": "B"}, BANK)
    assert scores["A2"] == 0.5
    assert scores["C3"] == 0.0


def test_score_case_checklist_hits():
    rubric = {"checklist": ["RAG", "召回", "评估"], "default_score": 3.0}
    assert score_case("方案用 RAG 提升召回率，并做离线抽检", rubric) == round(1 + 4 * 2 / 3, 2)
    assert score_case("没提关键词", rubric) == 1.0


def test_current_levels_and_radar():
    model = make_model()
    levels = current_levels(model, {"A2": 1.0, "C3": 0.5})
    assert levels["A2"] == 5
    assert levels["C3"] == 3
    radar = build_radar(model, levels)
    assert radar["A"] == 5.0
    assert radar["C"] == 3.0


def test_priority_gaps_weighted():
    model = make_model()
    levels = {"A2": 2, "C3": 3}
    gaps = priority_gaps(model, levels)
    assert gaps[0]["item_id"] == "A2"
    assert gaps[0]["gap"] == round((4 - 2) * 0.6, 3)
