"""周报：完成率、连击、雷达与待补强汇总。"""
from datetime import date as _date, timedelta
from pathlib import Path
import json

from ai_pm.tracking import read_jsonl, streak


def write_weekly_report(plan_path: str, tracking_dir: str, assessments_dir: str,
                        report_path: str, end_date: str) -> str:
    plan = json.loads(Path(plan_path).read_text(encoding="utf-8"))
    checkins = read_jsonl(str(Path(tracking_dir) / "checkins.jsonl"))
    end = _date.fromisoformat(end_date)
    start = end - timedelta(days=6)
    week_dates = {d["date"] for d in plan["days"]
                  if start <= _date.fromisoformat(d["date"]) <= end}
    completed = [c for c in checkins if c["date"] in week_dates
                 and c.get("minutes", 0) >= 60 and c.get("task_ids")]
    rate = round(len(completed) / len(week_dates), 2) if week_dates else 0.0
    baseline_path = Path(assessments_dir) / "baseline.json"
    baseline = json.loads(baseline_path.read_text(encoding="utf-8")) if baseline_path.exists() else {}
    md = (
        f"# 周报 {end_date}\n"
        f"- 完成率：{rate}（{len(completed)}/{len(week_dates)} 天）\n"
        f"- 连击：{streak(checkins)} 天\n"
        f"- 能力雷达：{json.dumps(baseline.get('radar', {}), ensure_ascii=False)}\n"
        f"- 待补强：{json.dumps(baseline.get('gaps', [])[:3], ensure_ascii=False)}\n"
    )
    Path(report_path).parent.mkdir(parents=True, exist_ok=True)
    Path(report_path).write_text(md, encoding="utf-8")
    return md
