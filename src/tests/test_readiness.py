from ai_pm.capability_model import CapabilityModel, CapabilityItem
from ai_pm.readiness import score_interview, verdict, portfolio_checklist


RUBRICS = {
    "behavioral": {"checklist": ["STAR", "结果", "反思"]},
    "case": {"checklist": ["指标", "权衡"]},
    "technical": {"checklist": ["RAG", "评估"]},
}


def make_model():
    model = CapabilityModel(domains={"A": "AI 技术理解"})
    model.add_item(CapabilityItem(id="A1", domain="A", name="LLM 边界",
                                  target_level=4, weight=1.0))
    return model


def test_score_interview_hits_and_misses():
    session = {"behavioral": [{"answer_text": "用 STAR 讲项目，结果提升了 30%，反思了不足"}],
               "case": [{"answer_text": "看指标并做权衡"}],
               "technical": [{"answer_text": "完全没提关键词"}]}
    scores = score_interview(session, RUBRICS)
    assert scores["behavioral"] == 5.0
    assert scores["technical"] == 1.0


def test_verdict_three_states():
    model = make_model()
    levels_ok = {"A1": 4}
    levels_bad = {"A1": 2}
    assert verdict(model, levels_ok, {"behavioral": 4.2, "case": 4.0, "technical": 4.5})["verdict"] == "达到"
    assert verdict(model, levels_bad, {"behavioral": 3.6, "case": 3.7, "technical": 3.6})["verdict"] == "接近"
    assert verdict(model, levels_bad, {"behavioral": 2.8, "case": 3.0, "technical": 2.5})["verdict"] == "未达到"
    assert verdict(model, levels_ok, {"behavioral": 3.0, "case": 3.0, "technical": 3.0})["verdict"] == "接近"


def test_portfolio_checklist_status():
    model = make_model()
    item = model.find("A1")
    item.evidence_requirements = ["有 STAR 案例", "有方案输出物"]
    artifacts = [{"id": "a1", "item_id": "A1", "type": "answer_card", "title": "RAG 案例"}]
    checklist = portfolio_checklist(model, artifacts)
    statuses = [c["status"] for c in checklist]
    assert statuses == ["已具备", "待补"]
