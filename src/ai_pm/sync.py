"""手机端导出文件导入：去重合并到本地跟踪目录。"""
from pathlib import Path
from typing import Dict
import json

from ai_pm.tracking import read_jsonl


def _append(path: Path, record: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")


def import_sync_file(path: str, tracking_dir: str) -> Dict[str, int]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    td = Path(tracking_dir)
    quiz_path = td / "quiz_answers.jsonl"
    checkin_path = td / "checkins.jsonl"
    existing_quiz = {f"{r['date']}|{r['quiz_id']}" for r in read_jsonl(str(quiz_path))}
    existing_checkin = {r["date"] for r in read_jsonl(str(checkin_path))}
    added_quiz = 0
    for a in payload.get("quiz_answers", []):
        key = f"{a['date']}|{a['quiz_id']}"
        if key in existing_quiz:
            continue
        _append(quiz_path, a)
        existing_quiz.add(key)
        added_quiz += 1
    added_checkin = 0
    for c in payload.get("checkins", []):
        if c["date"] in existing_checkin:
            continue
        _append(checkin_path, {"date": c["date"], "task_ids": c.get("task_ids", []),
                               "minutes": c.get("minutes", 0)})
        existing_checkin.add(c["date"])
        added_checkin += 1
    return {"quiz_answers_added": added_quiz, "checkins_added": added_checkin}
