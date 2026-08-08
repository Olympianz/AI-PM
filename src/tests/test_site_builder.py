import json, pathlib
from ai_pm.site_builder import build_site


def make_fixture(tmp_path):
    data = pathlib.Path(tmp_path) / "data"
    (data / "content" / "knowledge_cards").mkdir(parents=True)
    plan = {"start_date": "2026-08-10", "weeks": [{"week": 1, "focus_ids": ["A2"]}],
            "days": [{"id": "2026-08-10-input", "date": "2026-08-10", "week": 1, "day": 0,
                      "type": "input", "capability_ids": ["A2"],
                      "content_ref": "knowledge_cards/A2.md",
                      "output_required": False, "duration_min": 60}]}
    (data / "learning_plan.json").write_text(json.dumps(plan, ensure_ascii=False), encoding="utf-8")
    bank = [{"id": "q-001", "capability_id": "A2", "question": "Q", "options": ["A", "B"],
             "answer": "A", "difficulty": 1}]
    (data / "content" / "question_bank.json").write_text(json.dumps(bank, ensure_ascii=False), encoding="utf-8")
    (data / "content" / "case_questions.json").write_text("[]", encoding="utf-8")
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
    assert "cards/A2.html" in written
    index = (out / "index.html").read_text(encoding="utf-8")
    assert "2026-08-10" in index
    assert "2026-08-10-input" in index
    quiz = (out / "quiz.html").read_text(encoding="utf-8")
    assert "q-001" in quiz
    manifest = json.loads((out / "manifest.webmanifest").read_text(encoding="utf-8"))
    assert manifest["name"] == "AI-PM"
    sw = (out / "sw.js").read_text(encoding="utf-8")
    assert "ai-pm-v1" in sw
