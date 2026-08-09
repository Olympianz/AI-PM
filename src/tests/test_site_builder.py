import json, pathlib
from ai_pm.site_builder import build_site


def make_fixture(tmp_path):
    data = pathlib.Path(tmp_path) / "data"
    (data / "content" / "knowledge_cards").mkdir(parents=True)
    (data / "content" / "output_templates").mkdir(parents=True, exist_ok=True)
    model = {"version": 1, "domains": {"A": "AI 技术理解", "C": "数据与科学方法"},
             "items": [{"id": "A2", "domain": "A", "name": "Agent 机制", "weight": 1.0,
                        "target_level": 4, "sources": []}]}
    (data / "capability_model.json").write_text(json.dumps(model, ensure_ascii=False), encoding="utf-8")
    plan = {"start_date": "2026-08-10", "weeks": [{"week": 1, "focus_ids": ["A2"]}],
            "days": [{"id": "2026-08-10-input", "date": "2026-08-10", "week": 1, "day": 0,
                      "type": "input", "capability_ids": ["A2"],
                      "content_ref": "knowledge_cards/A2.md",
                      "output_required": False, "duration_min": 60}]}
    (data / "learning_plan.json").write_text(json.dumps(plan, ensure_ascii=False), encoding="utf-8")
    bank = [{"id": "q-001", "capability_id": "A2", "question": "Q", "options": ["A", "B"],
             "answer": "A", "difficulty": 1}]
    (data / "content" / "question_bank.json").write_text(json.dumps(bank, ensure_ascii=False), encoding="utf-8")
    cases = [{"id": "c-001", "capability_ids": ["A2"], "question": "Q",
              "summary": "**场景**：客服。**要点**：RAG。",
              "rubric": {"checklist": ["RAG"], "default_score": 3.0}}]
    (data / "content" / "case_questions.json").write_text(json.dumps(cases, ensure_ascii=False), encoding="utf-8")
    mocks = [{"id": "m-01", "section": "technical", "question": "解释 Agent Loop",
              "checklist": ["Agent Loop"]}]
    (data / "content" / "mock_questions.json").write_text(json.dumps(mocks, ensure_ascii=False), encoding="utf-8")
    (data / "content" / "github_project_template.md").write_text("# 项目拆解模板", encoding="utf-8")
    for name in ("prd", "case_analysis", "answer_card"):
        (data / "content" / "output_templates" / f"{name}.md").write_text(
            f"# {name} 模板", encoding="utf-8")
    (data / "content" / "topics.json").write_text(json.dumps([
        {"id": "ux", "name": "用户体验设计", "reason": "r", "goals": ["g"],
         "modules": [{"title": "m", "points": ["p"]}], "resources": [{"title": "t"}],
         "quiz": [{"question": "q", "options": ["A"], "answer": "A", "explanation": "e"}],
         "outputs": ["o"]}
    ], ensure_ascii=False), encoding="utf-8")
    card = "---\nid: A2\ncapability_id: A2\nminutes: 4\nquiz_ids: [q-001]\n---\n# Agent Loop\n正文内容"
    (data / "content" / "knowledge_cards" / "A2.md").write_text(card, encoding="utf-8")
    return data


def test_build_site_writes_all_pwa_files(tmp_path):
    data = make_fixture(tmp_path)
    out = pathlib.Path(tmp_path) / "site"
    written = build_site(str(data), str(out), date="2026-08-10")
    assert "index.html" in written
    assert "quiz.html" in written
    assert "manifest.webmanifest" in written
    assert "sw.js" in written
    assert "assets/app.js" in written
    assert "assets/style.css" in written
    assert "cards/A2.html" in written
    assert "learn.html" in written
    assert "cases.html" in written
    assert "cases/c-001.html" in written
    assert "progress.html" in written
    assert "outputs.html" in written
    assert "project.html" in written
    assert "mock.html" in written
    assert "review.html" in written
    assert "topics.html" in written
    assert "topics/ux.html" in written
    index = (out / "index.html").read_text(encoding="utf-8")
    assert "2026-08-10" in index
    assert "2026-08-10-input" in index
    assert "/learn.html" in index
    quiz = (out / "quiz.html").read_text(encoding="utf-8")
    assert "q-001" in quiz
    assert 'data-cap="A2"' in quiz
    assert 'id="tag-modal"' in quiz
    assert 'id="tag-grid"' in quiz
    assert 'class="chip ghost-btn" id="open-tags"' in quiz
    learn = (out / "learn.html").read_text(encoding="utf-8")
    assert "cards/A2.html" in learn
    case_page = (out / "cases" / "c-001.html").read_text(encoding="utf-8")
    assert "客服" in case_page
    mock_page = (out / "mock.html").read_text(encoding="utf-8")
    assert "Agent Loop" in mock_page
    review_page = (out / "review.html").read_text(encoding="utf-8")
    assert "BASELINE" in review_page
    topics_page = (out / "topics" / "ux.html").read_text(encoding="utf-8")
    assert "用户体验设计" in topics_page
    assert "window.TOPIC" in topics_page
    manifest = json.loads((out / "manifest.webmanifest").read_text(encoding="utf-8"))
    assert manifest["name"] == "AI-PM"
    sw = (out / "sw.js").read_text(encoding="utf-8")
    assert "ai-pm-v4" in sw
    assert "learn.html" in sw
