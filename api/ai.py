"""Vercel serverless：AI 助手（DeepSeek API 代理）。
环境变量：DEEPSEEK_API_KEY。
POST /api/ai  body: {action: plan|quiz|summary|ask, question, topic_name, topic_context}
"""
import json
import os
import urllib.request
from http.server import BaseHTTPRequestHandler


DEEPSEEK_KEY = os.environ.get("DEEPSEEK_API_KEY", "")
MODEL = os.environ.get("DEEPSEEK_MODEL", "deepseek-chat")

BASE_PROMPT = (
    "你是一位资深 AI 产品经理教练。用户背景：有经验的 B 端产品经理，正在向资深 AI 产品经理转型，"
    "正在做主题学习（专题）补短板。回答使用简体中文，结构清晰，给出可执行建议。"
)


def _action_prompt(action: str, payload: dict) -> str:
    name = payload.get("topic_name", "本专题")
    ctx = payload.get("topic_context") or {}
    if action == "plan":
        return (f"请为专题《{name}》生成一份 4 周学习计划：每周主题、每周 3-4 个具体任务"
                "（含学习/练习/输出）、推荐的免费资料检索关键词（便于用户自行检索最新资料）、"
                f"每周末自测建议。基于用户背景：{ctx.get('reason', 'B 端产品经理补短板')}。")
    if action == "quiz":
        modules = "、".join(ctx.get("modules", []) or [])
        return (f"请为专题《{name}》出 5 道高质量自测题，覆盖模块：{modules}。"
                "每题给出选项、答案与解析。格式：\n1. 题目\nA. ...\nB. ...\n答案：X\n解析：...")
    if action == "summary":
        return (f"用户刚完成专题《{name}》的一部分学习，进度：{json.dumps(ctx.get('progress', {}), ensure_ascii=False)}。"
                "请生成本专题阶段性总结与复盘：已掌握要点、薄弱点、下周建议（含资料检索关键词）。")
    if action == "triage_gaps":
        gaps = payload.get("gaps", [])
        topics = payload.get("topics", [])
        return ("以下是我在学习中记录的不足点（JSON 数组，字段 text/source）：\n"
                + json.dumps(gaps, ensure_ascii=False)
                + "\n\n现有学习主题（id/name/modules）：\n"
                + json.dumps(topics, ensure_ascii=False)
                + "\n\n请把每条不足点归入最合适的现有主题；如果都不合适，topic_id 使用 'new:<简短名称>' 表示建议新建专题。"
                  "严格只输出一个 JSON 数组，每项格式：{gap_id, topic_id, title, content}，"
                  "title 是建议新增的学习项标题，content 是 2-4 句可执行学习要点。不要输出其他文字。")
    if action == "daily_content":
        date = payload.get("date", "今天")
        existing = payload.get("existing", {})
        wrong = payload.get("wrong_answers", [])
        topics = payload.get("topics", [])
        return (
            f"请为 AI 产品经理学习系统生成「{date}」的每日学习内容，用于手机碎片化学习。\n"
            "要求：1) 优先围绕错题覆盖的知识点展开；2) 不得与已有内容重复（标题/题目不得与 existing 相同）；"
            "3) 与历史每日内容尽量不重复。\n"
            f"已有内容（避免重复）：{json.dumps(existing, ensure_ascii=False)}\n"
            f"错题记录（优先覆盖）：{json.dumps(wrong, ensure_ascii=False)}\n"
            f"现有专题：{json.dumps(topics, ensure_ascii=False)}\n"
            "严格只输出 JSON（不要其他文字）：\n"
            '{"cards":[{"capability_id":"A1","title":"...","content":"300字以内"}],'
            '"quiz":[{"capability_id":"A1","question":"...","options":["A. ...","B. ...","C. ...","D. ..."],'
            '"answer_index":2,"explanation":"..."}],'
            '"cases":[{"topic_id":"ux","title":"...","summary":"场景/要点/取舍","question":"..."}],'
            '"mocks":[{"section":"behavioral","question":"...","checklist":["..."]}],'
            '"topic_additions":[{"topic_id":"ux","title":"...","content":"..."}]}\n'
            "规模：cards 1-2 张、quiz 3-5 题（每题 4 个选项，answer_index 为 0-3 的随机位置）、"
            "cases 1 个、mocks 2 题、topic_additions 1-2 条。内容控制在手机 5 分钟内读完。")
    question = payload.get("question", "")
    return f"用户提问：{question}\n请结合专题《{name}》与用户背景回答。"


def _chat(user_prompt: str) -> str:
    body = json.dumps({
        "model": MODEL,
        "messages": [
            {"role": "system", "content": BASE_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": 0.7,
    }).encode()
    req = urllib.request.Request(
        "https://api.deepseek.com/chat/completions",
        data=body,
        headers={"Authorization": "Bearer " + DEEPSEEK_KEY,
                 "Content-Type": "application/json"},
        method="POST")
    with urllib.request.urlopen(req, timeout=55) as r:
        data = json.loads(r.read().decode())
    return data["choices"][0]["message"]["content"]


class handler(BaseHTTPRequestHandler):
    def _send(self, code: int, obj) -> None:
        body = json.dumps(obj, ensure_ascii=False).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST,OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self) -> None:
        self._send(200, {})

    def do_POST(self) -> None:
        try:
            n = int(self.headers.get("Content-Length", 0))
            payload = json.loads(self.rfile.read(n).decode() or "{}")
            action = payload.get("action", "ask")
            if action not in ("plan", "quiz", "summary", "ask", "triage_gaps", "daily_content"):
                self._send(400, {"error": "未知 action"})
                return
            if not DEEPSEEK_KEY:
                self._send(500, {"error": "DEEPSEEK_API_KEY 未配置"})
                return
            text = _chat(_action_prompt(action, payload))
            self._send(200, {"text": text})
        except Exception as e:  # noqa: BLE001
            self._send(500, {"error": str(e)})
