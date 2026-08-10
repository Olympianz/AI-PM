"""一次性引导函数：在 Supabase 中创建不足点相关表（幂等）。
用法：部署后 POST /api/db_bootstrap，成功后在本地删除本文件并移除 SUPABASE_DB_PASSWORD 环境变量。
环境变量：SUPABASE_URL、SUPABASE_DB_PASSWORD。
"""
import json
import os
import re
from http.server import BaseHTTPRequestHandler

import psycopg2


DDL = [
    "create table if not exists ai_pm_gaps (id text primary key, text text not null, "
    "source text not null default '', created_at text not null, "
    "status text not null default 'open', topic_id text, suggestion jsonb)",
    "create table if not exists ai_pm_topic_items (id text primary key, topic_id text not null, "
    "title text not null, content text not null, created_at text not null)",
]


class handler(BaseHTTPRequestHandler):
    def _send(self, code: int, obj) -> None:
        body = json.dumps(obj, ensure_ascii=False).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self) -> None:
        try:
            url = os.environ.get("SUPABASE_URL", "")
            pw = os.environ.get("SUPABASE_DB_PASSWORD", "")
            m = re.search(r"https://([^.]+)\.supabase\.co", url)
            if not m or not pw:
                self._send(500, {"error": "SUPABASE_URL 或 SUPABASE_DB_PASSWORD 未配置"})
                return
            ref = m.group(1)
            conn = psycopg2.connect(
                host="aws-0-us-east-1.pooler.supabase.com", port=5432, dbname="postgres",
                user=f"postgres.{ref}", password=pw,
                connect_timeout=15, sslmode="require")
            with conn.cursor() as cur:
                for d in DDL:
                    cur.execute(d)
                conn.commit()
                cur.execute(
                    "select tablename from pg_tables where schemaname='public' "
                    "and tablename like 'ai_pm_%' order by tablename")
                tables = [r[0] for r in cur.fetchall()]
            conn.close()
            self._send(200, {"ok": True, "tables": tables})
        except Exception as e:  # noqa: BLE001
            self._send(500, {"error": str(e)})
