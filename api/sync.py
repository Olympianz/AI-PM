"""Vercel serverless：AI-PM 云端同步（Supabase 后端）。
环境变量：SUPABASE_URL、SUPABASE_SERVICE_ROLE_KEY。
GET  /api/sync              -> 拉取全部本地数据
POST /api/sync              -> 合并写入（按主键 upsert）
"""
import json
import os
import urllib.request
from http.server import BaseHTTPRequestHandler


SUPABASE_URL = os.environ.get("SUPABASE_URL", "").rstrip("/")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY", "")

TABLES = {
    "checkins": ("ai_pm_checkins", "date"),
    "quiz_answers": ("ai_pm_quiz_answers", "date,quiz_id"),
    "artifacts": ("ai_pm_artifacts", "id"),
    "mocks": ("ai_pm_mocks", "id"),
    "topic_progress": ("ai_pm_topic_progress", "topic_id"),
    "tasks": ("ai_pm_tasks", "date,task_id"),
    "read_cards": ("ai_pm_read_cards", "card_id"),
    "bookmarks": ("ai_pm_bookmarks", "card_id"),
    "gaps": ("ai_pm_gaps", "id"),
    "topic_items": ("ai_pm_topic_items", "id"),
}
DELETE_TABLES = ("artifacts", "mocks", "gaps")


def _rest(key, method="GET", payload=None):
    table, conflict = TABLES[key]
    path = f"/rest/v1/{table}"
    if method == "POST":
        path += f"?on_conflict={conflict}"
    req = urllib.request.Request(
        SUPABASE_URL + path,
        data=json.dumps(payload).encode() if payload is not None else None,
        headers={
            "apikey": SUPABASE_KEY,
            "Authorization": "Bearer " + SUPABASE_KEY,
            "Content-Type": "application/json",
            "Prefer": "resolution=merge-duplicates,return=minimal",
        },
        method=method)
    with urllib.request.urlopen(req, timeout=20) as r:
        body = r.read().decode()
        return json.loads(body) if body else None


def _rest_delete(key: str, ids: list) -> int:
    table, _ = TABLES[key]
    quoted = ",".join(ids)
    req = urllib.request.Request(
        SUPABASE_URL + f"/rest/v1/{table}?id=in.({quoted})",
        headers={
            "apikey": SUPABASE_KEY,
            "Authorization": "Bearer " + SUPABASE_KEY,
            "Prefer": "return=minimal",
        },
        method="DELETE")
    with urllib.request.urlopen(req, timeout=20) as r:
        return len(ids)


class handler(BaseHTTPRequestHandler):
    def _send(self, code: int, obj) -> None:
        body = json.dumps(obj, ensure_ascii=False).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET,POST,OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self) -> None:
        self._send(200, {})

    def do_GET(self) -> None:
        try:
            out = {}
            missing = []
            for key in TABLES:
                try:
                    out[key] = _rest(key) or []
                except Exception:  # noqa: BLE001 表未建时容错，返回空
                    out[key] = []
                    missing.append(key)
            self._send(200, out)
        except Exception as e:  # noqa: BLE001
            self._send(500, {"error": str(e)})

    def do_POST(self) -> None:
        try:
            n = int(self.headers.get("Content-Length", 0))
            payload = json.loads(self.rfile.read(n).decode() or "{}")
            saved = {key: 0 for key in TABLES}
            errors = {}
            for key in TABLES:
                for rec in payload.get(key, []):
                    try:
                        _rest(key, "POST", rec)
                        saved[key] += 1
                    except Exception as e:  # noqa: BLE001
                        errors[key] = errors.get(key, 0) + 1
            deleted = {key: 0 for key in DELETE_TABLES}
            for key in DELETE_TABLES:
                ids = payload.get("_delete", {}).get(key, [])
                if ids:
                    try:
                        deleted[key] = _rest_delete(key, ids)
                    except Exception:  # noqa: BLE001
                        errors["_delete_" + key] = errors.get("_delete_" + key, 0) + 1
            self._send(200, {"saved": saved, "deleted": deleted, "errors": errors})
        except Exception as e:  # noqa: BLE001
            self._send(500, {"error": str(e)})
