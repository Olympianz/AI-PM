import json, pathlib
from ai_pm.tracking import read_jsonl
from ai_pm.sync import import_sync_file


def test_import_deduplicates(tmp_path):
    tracking = pathlib.Path(tmp_path) / "tracking"
    tracking.mkdir()
    export = pathlib.Path(tmp_path) / "ai-pm-sync.json"
    export.write_text(json.dumps({
        "version": 1, "device": "mobile", "exported_at": "2026-08-10T12:00:00",
        "quiz_answers": [
            {"date": "2026-08-10", "quiz_id": "q-001", "choice": "A"},
            {"date": "2026-08-10", "quiz_id": "q-002", "choice": "B"},
        ],
        "checkins": [{"date": "2026-08-10", "task_ids": ["2026-08-10-input"], "minutes": 60}],
    }), encoding="utf-8")
    first = import_sync_file(str(export), str(tracking))
    second = import_sync_file(str(export), str(tracking))
    assert first == {"quiz_answers_added": 2, "checkins_added": 1}
    assert second == {"quiz_answers_added": 0, "checkins_added": 0}
    assert len(read_jsonl(str(tracking / "quiz_answers.jsonl"))) == 2
    assert len(read_jsonl(str(tracking / "checkins.jsonl"))) == 1
