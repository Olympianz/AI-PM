"""8 周学习计划生成：按优先补强清单组装每日任务。"""
from datetime import date as _date, timedelta
from typing import Dict, List


TASK_TYPES = ("input", "practice", "output", "case", "project", "mock", "review")
_THIRD_BY_WEEKDAY = {0: "case", 1: "output", 2: "case", 3: "output",
                     4: "output", 5: "project", 6: None}
_REF_BY_TYPE = {"case": "case_questions", "output": "output_templates/answer_card.md",
                "project": "github_project_template.md", "mock": "mock-interview",
                "review": "weekly-review"}


def _split_duration(total: int, input_pct: float = 0.4, practice_pct: float = 0.4) -> tuple:
    i = int(total * input_pct)
    p = int(total * practice_pct)
    return i, p, total - i - p


def day_tasks(date: str, week: int, weekday: int, focus_ids: List[str],
              daily_minutes: int = 150) -> List[dict]:
    i, p, t = _split_duration(daily_minutes)
    tasks = [
        {"id": f"{date}-input", "date": date, "week": week, "day": weekday,
         "type": "input", "capability_ids": focus_ids[:1],
         "content_ref": f"knowledge_cards/{focus_ids[0]}.md",
         "output_required": False, "duration_min": i},
        {"id": f"{date}-practice", "date": date, "week": week, "day": weekday,
         "type": "practice", "capability_ids": focus_ids[:2],
         "content_ref": "question_bank", "output_required": False,
         "duration_min": p},
    ]
    third = _THIRD_BY_WEEKDAY[weekday]
    if third is None:
        third = "mock" if week % 2 == 1 else "review"
    tasks.append({"id": f"{date}-{third}", "date": date, "week": week,
                  "day": weekday, "type": third,
                  "capability_ids": focus_ids,
                  "content_ref": _REF_BY_TYPE[third],
                  "output_required": third in ("output", "project", "mock"),
                  "duration_min": t})
    return tasks


def _sprint_focus(focus: List[str], week: int) -> List[str]:
    if week <= 2:
        return focus[:2]
    if week <= 4:
        return focus[2:4]
    if week <= 6:
        return focus[4:5]
    return focus[:5]


def generate_plan(model, gaps: List[dict], start_date: str,
                  daily_minutes: int = 150) -> dict:
    focus = [g["item_id"] for g in gaps]
    if len(focus) < 5:
        for it in model.items:
            if it.id not in focus:
                focus.append(it.id)
            if len(focus) >= 5:
                break
    weeks: List[dict] = []
    days: List[dict] = []
    start = _date.fromisoformat(start_date)
    for w in range(1, 9):
        focus_ids = _sprint_focus(focus, w)
        weeks.append({"week": w, "focus_ids": focus_ids})
        for d in range(7):
            date = (start + timedelta(days=(w - 1) * 7 + d)).isoformat()
            days.extend(day_tasks(date, w, d, focus_ids, daily_minutes))
    return {"start_date": start_date, "weeks": weeks, "days": days}
