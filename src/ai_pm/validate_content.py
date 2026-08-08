"""内容校验：知识卡、题库、案例题的 schema 与引用完整性。"""
from pathlib import Path
from typing import List
import json


def _front_matter(text: str):
    if not text.startswith("---"):
        return {}, text
    parts = text.split("---", 2)
    meta = {}
    for line in parts[1].strip().splitlines():
        if ":" not in line:
            continue
        k, v = line.split(":", 1)
        v = v.strip()
        if v.startswith("[") and v.endswith("]"):
            v = [x.strip().strip('"\'') for x in v[1:-1].split(",")]
        elif v.isdigit():
            v = int(v)
        else:
            v = v.strip('"\'')
        meta[k] = v
    return meta, parts[2]


def validate_content(data_dir: str) -> List[str]:
    data = Path(data_dir)
    errors: List[str] = []
    model = json.loads((data / "capability_model.json").read_text(encoding="utf-8"))
    item_ids = {it["id"] for it in model["items"]}
    bank = json.loads((data / "content" / "question_bank.json").read_text(encoding="utf-8"))
    quiz_ids = {q["id"] for q in bank}
    for q in bank:
        for field in ("id", "capability_id", "question", "options", "answer"):
            if field not in q:
                errors.append(f"bank:{q.get('id', '?')} 缺少字段 {field}")
        if q.get("capability_id") not in item_ids:
            errors.append(f"bank:{q.get('id')} 引用了不存在的能力项 {q.get('capability_id')}")
    cards = sorted((data / "content" / "knowledge_cards").glob("*.md"))
    for card in cards:
        meta, body = _front_matter(card.read_text(encoding="utf-8"))
        name = card.stem
        for field in ("id", "capability_id", "minutes", "quiz_ids"):
            if field not in meta:
                errors.append(f"card:{name} 缺少 front-matter 字段 {field}")
        if isinstance(meta.get("minutes"), int) and meta["minutes"] > 5:
            errors.append(f"card:{name} minutes={meta['minutes']} 超过 5 分钟限制")
        if meta.get("capability_id") not in item_ids:
            errors.append(f"card:{name} 引用了不存在的能力项 {meta.get('capability_id')}")
        for qid in meta.get("quiz_ids", []):
            if qid not in quiz_ids:
                errors.append(f"card:{name} 引用了不存在的题目 {qid}")
        length = len([c for c in body if not c.isspace()])
        if length < 300 or length > 500:
            errors.append(f"card:{name} 正文字数 {length}，应在 300-500 之间")
    cases = json.loads((data / "content" / "case_questions.json").read_text(encoding="utf-8"))
    for c in cases:
        if not c.get("rubric", {}).get("checklist"):
            errors.append(f"case:{c.get('id')} rubric.checklist 不能为空")
    return errors
