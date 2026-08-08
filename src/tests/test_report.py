import json, pathlib
from ai_pm.report import write_weekly_report


def make_fixture(tmp_path):
    root = pathlib.Path(tmp_path)
    plan = {"start_date": "2026-08-10", "weeks": [], "days": [
        {"date": "2026-08-10", "id": "2026-08-10-input", "type": "input"}]}
    (root / "plan.json").write_text(json.dumps(plan, ensure_ascii=False), encoding="utf-8")
    tracking = root / "tracking"
    tracking.mkdir()
    (tracking / "checkins.jsonl").write_text(
        json.dumps({"date": "2026-08-10", "task_ids": ["2026-08-10-input"], "minutes": 150},
                   ensure_ascii=False) + "\n", encoding="utf-8")
    assessments = root / "assessments"
    assessments.mkdir()
    (assessments / "baseline.json").write_text(json.dumps(
        {"radar": {"A": 2.0}, "gaps": [{"name": "Agent 机制"}]}, ensure_ascii=False), encoding="utf-8")
    return root, tracking, assessments


def test_write_weekly_report_sections(tmp_path):
    root, tracking, assessments = make_fixture(tmp_path)
    report = write_weekly_report(str(root / "plan.json"), str(tracking),
                                 str(assessments), str(root / "report.md"), "2026-08-16")
    assert "完成率" in report
    assert "连击" in report
    assert "能力雷达" in report
    assert "待补强" in report
