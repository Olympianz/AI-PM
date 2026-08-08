import json
from ai_pm.tracking import (record_checkin, read_jsonl, completion_rate, streak,
                            next_review, adapt_plan)


def test_completion_rate(tmp_path):
    path = str(tmp_path / "checkins.jsonl")
    record_checkin(path, "2026-08-10", ["2026-08-10-input"], 150)
    record_checkin(path, "2026-08-11", ["2026-08-11-input"], 30)
    record_checkin(path, "2026-08-12", [], 120)
    rate = completion_rate(read_jsonl(path), "2026-08-10", "2026-08-12")
    assert rate == round(1 / 3, 2)


def test_streak_consecutive_days():
    checkins = [
        {"date": "2026-08-08", "task_ids": ["x"], "minutes": 60},
        {"date": "2026-08-09", "task_ids": ["x"], "minutes": 60},
        {"date": "2026-08-10", "task_ids": ["x"], "minutes": 60},
    ]
    assert streak(checkins) == 3


def test_next_review_sm2():
    assert next_review(2, 7, 3) == (1, 0)
    assert next_review(5, 1, 0) == (1, 1)
    assert next_review(5, 1, 1) == (3, 2)
    assert next_review(5, 6, 3) == (12, 4)


def test_adapt_plan_reduce_load_and_mark_done():
    plan = {"weeks": [{"week": 1, "focus_ids": ["A2", "C3"]}]}
    low = [{"date": "2026-08-10", "task_ids": ["a"], "minutes": 30},
           {"date": "2026-08-11", "task_ids": ["a"], "minutes": 30},
           {"date": "2026-08-12", "task_ids": ["a"], "minutes": 30}]
    adj = adapt_plan(plan, low, {"A2": 0.9})
    types = [a["type"] for a in adj]
    assert "reduce_load" in types
    assert "mark_focus_done" in types
