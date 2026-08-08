"""跟踪：打卡记录、完成率、连击、间隔重复与自适应调整。"""
from datetime import date as _date, timedelta
from typing import Dict, List
import json
import pathlib


def read_jsonl(path: str) -> List[dict]:
    p = pathlib.Path(path)
    if not p.exists():
        return []
    return [json.loads(line) for line in p.read_text(encoding="utf-8").splitlines() if line.strip()]


def record_checkin(path: str, date: str, task_ids: List[str], minutes: int) -> None:
    p = pathlib.Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("a", encoding="utf-8") as f:
        f.write(json.dumps({"date": date, "task_ids": task_ids, "minutes": minutes},
                           ensure_ascii=False) + "\n")


def _is_completed(c: dict) -> bool:
    return c.get("minutes", 0) >= 60 and bool(c.get("task_ids"))


def completion_rate(checkins: List[dict], start: str, end: str) -> float:
    days = {c["date"] for c in checkins if _is_completed(c)}
    s = _date.fromisoformat(start)
    e = _date.fromisoformat(end)
    total = (e - s).days + 1
    if total <= 0:
        return 0.0
    ok = sum(1 for i in range(total) if (s + timedelta(days=i)).isoformat() in days)
    return round(ok / total, 2)


def streak(checkins: List[dict]) -> int:
    days = sorted({c["date"] for c in checkins if _is_completed(c)})
    if not days:
        return 0
    count = 1
    cur = _date.fromisoformat(days[-1])
    for d in reversed(days[:-1]):
        if _date.fromisoformat(d) == cur - timedelta(days=1):
            count += 1
            cur -= timedelta(days=1)
        else:
            break
    return count


def next_review(grade: int, interval_days: int, repetitions: int) -> tuple:
    if grade < 3:
        return 1, 0
    if repetitions == 0:
        return 1, 1
    if repetitions == 1:
        return 3, 2
    return interval_days * 2, repetitions + 1


def adapt_plan(plan: dict, checkins: List[dict], quiz_scores: Dict[str, float]) -> List[dict]:
    adjustments: List[dict] = []
    recent = checkins[-3:]
    if recent and sum(1 for c in recent if _is_completed(c)) < 2:
        adjustments.append({"type": "reduce_load", "factor": 0.7,
                            "reason": "近 3 天完成率低，自动减负 30%"})
    for week in plan.get("weeks", []):
        for cid in week["focus_ids"]:
            avg = quiz_scores.get(cid)
            if avg is not None and avg >= 0.8:
                adjustments.append({"type": "mark_focus_done",
                                    "capability_id": cid, "week": week["week"]})
                break
    return adjustments
