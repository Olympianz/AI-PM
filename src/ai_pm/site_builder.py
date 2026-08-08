"""静态站点生成：从 data/ 生成 site/ 下的 PWA 页面。"""
from datetime import date as _date
from pathlib import Path
from typing import List, Optional
import json, shutil


def _read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


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


def _md_to_html(body: str) -> str:
    out = []
    for line in body.splitlines():
        s = line.strip()
        if not s:
            continue
        if s.startswith("# "):
            out.append(f"<h2>{s[2:]}</h2>")
        elif s.startswith("- "):
            out.append(f"<li>{s[2:]}</li>")
        else:
            out.append(f"<p>{s}</p>")
    return "\n".join(out)


_PAGE_HEAD = ('<!doctype html><html lang="zh"><head><meta charset="utf-8">'
              '<meta name="viewport" content="width=device-width,initial-scale=1">'
              '<link rel="manifest" href="./manifest.webmanifest">'
              '<title>{title}</title></head><body>')
_PAGE_TAIL = ('<script src="./assets/app.js"></script></body></html>')

_INDEX_TEMPLATE = _PAGE_HEAD + """
<h1>AI-PM · {date}</h1>
<p><button id="checkin-btn">今日打卡</button> <button id="export-sync">导出同步文件</button></p>
<p><a href="./quiz.html">今日快速自测 →</a></p>
<h2>今日任务</h2><ul>{tasks}</ul>
""" + _PAGE_TAIL

_QUIZ_TEMPLATE = _PAGE_HEAD + """
<h1>快速自测</h1>
<div id="quiz-root"></div>
<p><button id="submit-quiz">提交并查看反馈</button> <button id="export-sync">导出同步文件</button></p>
<script>window.QUIZ_BANK = {bank_json};</script>
""" + _PAGE_TAIL

_CARD_TEMPLATE = _PAGE_HEAD + """
<h1>{title}</h1>
<p>预计 {minutes} 分钟</p>
{body}
<p><a href="../index.html">← 返回今日任务</a></p>
""" + _PAGE_TAIL

_SW_TEMPLATE = """const CACHE = "ai-pm-v1";
const ASSETS = ["./", "./index.html", "./quiz.html", "./manifest.webmanifest", "./assets/app.js"];
self.addEventListener("install", e => {
  e.waitUntil(caches.open(CACHE).then(c => c.addAll(ASSETS)));
  self.skipWaiting();
});
self.addEventListener("activate", e => {
  e.waitUntil(caches.keys().then(keys => Promise.all(keys.filter(k => k !== CACHE).map(k => caches.delete(k)))));
});
self.addEventListener("fetch", e => {
  e.respondWith(caches.match(e.request).then(r => r || fetch(e.request)));
});
"""


def build_site(data_dir: str, out_dir: str, date: Optional[str] = None) -> List[str]:
    data = Path(data_dir)
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    (out / "assets").mkdir(parents=True, exist_ok=True)
    target = date or _date.today().isoformat()
    plan = _read_json(data / "learning_plan.json")
    tasks = [d for d in plan["days"] if d["date"] == target]
    task_html = "".join(
        f'<li class="task"><input type="checkbox" data-task="{t["id"]}"> '
        f'{t["type"]} · {t["duration_min"]} 分钟 · {t["content_ref"]}</li>'
        for t in tasks)
    (out / "index.html").write_text(
        _INDEX_TEMPLATE.format(title="AI-PM", date=target, tasks=task_html), encoding="utf-8")
    bank = _read_json(data / "content" / "question_bank.json")
    (out / "quiz.html").write_text(
        _QUIZ_TEMPLATE.format(title="快速自测",
                              bank_json=json.dumps(bank, ensure_ascii=False)),
        encoding="utf-8")
    cards_dir = out / "cards"
    cards_dir.mkdir(exist_ok=True)
    for md in sorted((data / "content" / "knowledge_cards").glob("*.md")):
        meta, body = _front_matter(md.read_text(encoding="utf-8"))
        (cards_dir / f"{meta['id']}.html").write_text(
            _CARD_TEMPLATE.format(title=meta.get("capability_id", md.stem),
                                  minutes=meta.get("minutes", ""),
                                  body=_md_to_html(body)),
            encoding="utf-8")
    (out / "manifest.webmanifest").write_text(json.dumps({
        "name": "AI-PM", "short_name": "AI-PM", "start_url": "./index.html",
        "display": "standalone", "background_color": "#0f172a",
        "theme_color": "#0f172a", "icons": []}, ensure_ascii=False), encoding="utf-8")
    (out / "sw.js").write_text(_SW_TEMPLATE, encoding="utf-8")
    shutil.copyfile(Path(__file__).parent / "assets" / "app.js", out / "assets" / "app.js")
    return sorted(str(p.relative_to(out)) for p in out.rglob("*") if p.is_file())
