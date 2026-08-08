import json, pathlib
from ai_pm.validate_content import validate_content


def make_fixture(tmp_path):
    data = pathlib.Path(tmp_path) / "data"
    (data / "content" / "knowledge_cards").mkdir(parents=True)
    model = {"version": 1, "domains": {"A": "AI 技术理解"},
             "items": [{"id": "A2", "domain": "A", "name": "Agent 机制", "weight": 1.0,
                        "target_level": 4, "sources": []}]}
    (data / "capability_model.json").write_text(json.dumps(model, ensure_ascii=False), encoding="utf-8")
    bank = [{"id": "q-001", "capability_id": "A2", "question": "Q", "options": ["A", "B"],
             "answer": "A", "difficulty": 1}]
    (data / "content" / "question_bank.json").write_text(json.dumps(bank, ensure_ascii=False), encoding="utf-8")
    (data / "content" / "case_questions.json").write_text("[]", encoding="utf-8")
    (data / "content" / "mock_questions.json").write_text(json.dumps([
        {"id": "m-01", "section": "technical", "question": "Q", "checklist": ["A"]}
    ], ensure_ascii=False), encoding="utf-8")
    (data / "content" / "topics.json").write_text(json.dumps([
        {"id": "ux", "name": "UX", "reason": "r", "goals": ["g"],
         "modules": [{"title": "m", "points": ["p"]}], "resources": [{"title": "t"}],
         "quiz": [{"question": "q", "options": ["A"], "answer": "A", "explanation": "e"}],
         "outputs": ["o"]}
    ], ensure_ascii=False), encoding="utf-8")
    card = ("---\nid: A2-agent-loop\ncapability_id: A2\nminutes: 4\nquiz_ids: [q-001]\n"
            "---\n# Agent Loop\n" + "这是正文。" * 80)
    (data / "content" / "knowledge_cards" / "A2-agent-loop.md").write_text(card, encoding="utf-8")
    return data


def test_validate_passes_on_valid_fixture(tmp_path):
    errors = validate_content(str(make_fixture(tmp_path)))
    assert errors == []


def test_validate_reports_broken_card(tmp_path):
    data = make_fixture(tmp_path)
    (data / "content" / "knowledge_cards" / "A2-agent-loop.md").write_text(
        "---\nid: A2-agent-loop\ncapability_id: A2\nminutes: 10\nquiz_ids: [q-999]\n---\n太短",
        encoding="utf-8")
    errors = validate_content(str(data))
    joined = "\n".join(errors)
    assert "minutes" in joined
    assert "q-999" in joined


def test_validate_reports_case_without_summary(tmp_path):
    data = make_fixture(tmp_path)
    (data / "content" / "case_questions.json").write_text(json.dumps([
        {"id": "c-001", "capability_ids": ["A2"], "question": "Q",
         "rubric": {"checklist": ["A"]}}], ensure_ascii=False), encoding="utf-8")
    errors = validate_content(str(data))
    assert any("summary" in e for e in errors)


def test_validate_reports_mock_missing_question(tmp_path):
    data = make_fixture(tmp_path)
    (data / "content" / "mock_questions.json").write_text(json.dumps([
        {"id": "m-01", "section": "behavioral", "checklist": ["A"]}], ensure_ascii=False),
        encoding="utf-8")
    errors = validate_content(str(data))
    assert any("mock" in e and "question" in e for e in errors)


def test_validate_reports_topic_missing_goals(tmp_path):
    data = make_fixture(tmp_path)
    (data / "content" / "topics.json").write_text(json.dumps([
        {"id": "ux", "name": "UX", "reason": "r", "modules": [],
         "resources": [], "quiz": [], "outputs": []}], ensure_ascii=False),
        encoding="utf-8")
    errors = validate_content(str(data))
    assert any("topic" in e and "goals" in e for e in errors)
