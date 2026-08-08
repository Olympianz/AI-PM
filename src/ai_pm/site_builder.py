"""静态站点生成：从 data/ 生成 site/ 下的移动端 PWA（浅色极简风格）。"""
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
        elif s.startswith("## "):
            out.append(f"<h3>{s[3:]}</h3>")
        elif s.startswith("- "):
            out.append(f"<li>{s[2:]}</li>")
        elif s.startswith("**") and s.endswith("**"):
            out.append(f"<p>{s}</p>")
        else:
            out.append(f"<p>{s}</p>")
    return "\n".join(out)


def _card_title(body: str) -> str:
    for line in body.splitlines():
        s = line.strip()
        if s.startswith("# "):
            return s[2:]
    return ""


_CSS = """\
:root{--bg:#f6f7fb;--card:#fff;--ink:#1a1d29;--muted:#6b7280;--accent:#5b5bd6;--accent-soft:#eef0fd;--line:#e7e9f0;--ok:#16a34a;--warn:#d97706;--radius:14px}
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:system-ui,-apple-system,"PingFang SC","Microsoft YaHei",sans-serif;background:var(--bg);color:var(--ink);padding-bottom:84px;-webkit-font-smoothing:antialiased;font-size:15px;line-height:1.55}
.wrap{max-width:520px;margin:0 auto;padding:18px 16px 8px}
header.top h1{font-size:22px;font-weight:750;letter-spacing:-.2px}
header.top .sub{color:var(--muted);font-size:13px;margin-top:3px}
.card{background:var(--card);border:1px solid var(--line);border-radius:var(--radius);padding:15px;margin-top:14px}
.card h2{font-size:14px;font-weight:650;margin-bottom:4px;color:var(--muted);letter-spacing:.2px}
.chip{display:inline-block;font-size:11px;padding:2px 9px;border-radius:99px;background:var(--accent-soft);color:var(--accent);font-weight:650}
.chip.desk{background:#f0f1f5;color:var(--muted)}
.chip.ok{background:#e8f7ee;color:var(--ok)}
.btn{display:inline-block;border:0;border-radius:99px;padding:11px 20px;font-size:14px;font-weight:650;background:var(--accent);color:#fff;cursor:pointer;text-decoration:none;text-align:center}
.btn.ghost{background:transparent;color:var(--accent);border:1px solid var(--accent)}
.btn[disabled]{opacity:.55;cursor:default}
.task{display:flex;align-items:center;gap:11px;padding:11px 0;border-bottom:1px solid var(--line);text-decoration:none;color:inherit}
.task:last-of-type{border-bottom:0}
.task .t-ico{width:36px;height:36px;border-radius:11px;background:var(--accent-soft);display:flex;align-items:center;justify-content:center;font-size:17px;flex:none}
.task .t-main{flex:1;min-width:0}
.task .t-title{font-size:14px;font-weight:620}
.task .t-meta{font-size:12px;color:var(--muted);margin-top:1px}
.task .t-arrow{color:#c3c8d4;font-size:15px;flex:none}
.check{width:20px;height:20px;border-radius:6px;accent-color:var(--accent);flex:none}
.grid2{display:grid;grid-template-columns:1fr 1fr;gap:11px;margin-top:14px}
.entry{background:var(--card);border:1px solid var(--line);border-radius:var(--radius);padding:14px 13px;text-decoration:none;color:inherit}
.entry .e-ico{font-size:18px}
.entry .e-title{font-size:13.5px;font-weight:650;margin-top:5px}
.entry .e-meta{font-size:11.5px;color:var(--muted);margin-top:2px}
nav.bottom{position:fixed;bottom:0;left:0;right:0;background:rgba(255,255,255,.96);border-top:1px solid var(--line);display:flex;z-index:20;backdrop-filter:blur(6px)}
nav.bottom a{flex:1;text-align:center;padding:8px 0 9px;font-size:10.5px;color:var(--muted);text-decoration:none}
nav.bottom a.active{color:var(--accent);font-weight:680}
nav.bottom .n-ico{display:block;font-size:17px;line-height:1.25}
.stat-row{display:flex;gap:10px;margin-top:14px}
.stat{flex:1;background:var(--card);border:1px solid var(--line);border-radius:var(--radius);padding:13px 10px;text-align:center}
.stat .v{font-size:20px;font-weight:750;color:var(--accent)}
.stat .k{font-size:11.5px;color:var(--muted);margin-top:2px}
.filters{display:flex;gap:8px;overflow-x:auto;padding:4px 0 8px;margin-top:12px}
.filters .chip{cursor:pointer;user-select:none;padding:5px 12px;font-size:12px}
.filters .chip.on{background:var(--accent);color:#fff}
.opt{display:block;margin:8px 0;padding:11px 12px;border:1px solid var(--line);border-radius:11px;background:#fff}
.opt.correct{background:#e8f7ee;border-color:var(--ok);font-weight:650}
.opt.wrong{background:#fdecec;border-color:#dc2626;font-weight:650}
.muted{color:var(--muted)}
.prose h2{font-size:17px;font-weight:720;margin:14px 0 6px}
.prose h3{font-size:14px;font-weight:680;margin:12px 0 4px;color:var(--accent)}
.prose p{margin:7px 0}
.prose li{margin:3px 0 3px 18px}
footer.hint{text-align:center;color:#b7bcc9;font-size:11px;margin-top:22px}
textarea{width:100%;border:1px solid var(--line);border-radius:12px;padding:12px;font-size:14px;line-height:1.6;font-family:inherit;resize:vertical;background:#fff;color:var(--ink)}
pre{white-space:pre-wrap;background:#f8f9fc;border:1px solid var(--line);border-radius:12px;padding:14px;font-size:13px;line-height:1.7;overflow:auto}
.btn-row{display:flex;gap:10px;margin-top:12px;flex-wrap:wrap}
.desk-only{display:none}
@media (min-width:900px){
  body{display:flex;flex-direction:column;padding-bottom:0}
  nav.bottom{order:-1;position:static;border-bottom:1px solid var(--line);justify-content:center;gap:2px;background:#fff}
  nav.bottom a{padding:13px 15px;font-size:12.5px}
  nav.bottom .n-ico{display:none}
  .wrap{max-width:980px}
  .desk-only{display:block}
  .card{max-width:980px}
}
"""


def _nav(active: str) -> str:
    tabs = [("index", "今日", "🏠"), ("learn", "学习", "📚"), ("quiz", "题库", "✏️"),
            ("cases", "案例", "🗂"), ("outputs", "输出", "📝"),
            ("project", "拆解", "🛠"), ("mock", "面试", "🎤"),
            ("review", "复盘", "🔁"), ("progress", "进度", "📈")]
    items = []
    for key, label, ico in tabs:
        cls = "active" if key == active else ""
        cls_attr = f' class="{cls}{" desk-only" if key in ("outputs", "project", "mock", "review") else ""}"'
        items.append(f'<a href="./{key}.html"{cls_attr}><span class="n-ico">{ico}</span>{label}</a>')
    return '<nav class="bottom">' + "".join(items) + "</nav>"


def _page(title: str, active: str, body: str, extra_js: str = "") -> str:
    return (
        '<!doctype html><html lang="zh"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width,initial-scale=1">'
        '<link rel="manifest" href="./manifest.webmanifest">'
        '<link rel="stylesheet" href="./assets/style.css">'
        f"<title>{title}</title></head><body>"
        f'<div class="wrap">{body}</div>'
        f"{_nav(active)}"
        f'<script>window.PAGE="{active}";</script>'
        f"<script>{extra_js}</script>"
        '<script src="./assets/app.js"></script>'
        "</body></html>"
    )


def _cap_names(model: dict) -> str:
    return json.dumps({it["id"]: it["name"] for it in model["items"]}, ensure_ascii=False)


def build_site(data_dir: str, out_dir: str, date: Optional[str] = None) -> List[str]:
    data = Path(data_dir)
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    (out / "assets").mkdir(parents=True, exist_ok=True)
    (out / "cards").mkdir(parents=True, exist_ok=True)
    (out / "cases").mkdir(parents=True, exist_ok=True)
    (out / "assets" / "style.css").write_text(_CSS, encoding="utf-8")

    model = _read_json(data / "capability_model.json")
    cap_names_dict = {it["id"]: it["name"] for it in model["items"]}
    cap_names = _cap_names(model)
    plan = _read_json(data / "learning_plan.json")
    bank = _read_json(data / "content" / "question_bank.json")
    cases = _read_json(data / "content" / "case_questions.json")
    mocks = _read_json(data / "content" / "mock_questions.json")
    baseline = {}
    baseline_path = data / "assessments" / "baseline.json"
    if baseline_path.exists():
        baseline = _read_json(baseline_path)
    baseline_js = ("window.BASELINE = "
                   + json.dumps({"radar": baseline.get("radar", {}),
                                 "gaps": baseline.get("gaps", [])},
                                ensure_ascii=False) + ";")

    # ---- index.html（今日任务由 JS 按日期渲染）----
    plan_tasks = {}
    for t in plan["days"]:
        plan_tasks.setdefault(t["date"], []).append(t)
    index_body = (
        '<header class="top"><h1>AI-PM</h1>'
        '<p class="sub" id="day-sub">加载中…</p></header>'
        '<div class="card"><div class="row" style="display:flex;align-items:center;gap:12px">'
        '<div style="flex:1"><h2>今日打卡</h2>'
        '<p class="muted" style="font-size:12px;margin-top:2px">完成必做任务后点一下</p></div>'
        '<button id="checkin-btn" class="btn">打卡</button></div></div>'
        '<div class="card"><h2 id="task-head">今日任务</h2><div id="task-list"></div></div>'
        '<div class="grid2">'
        '<a class="entry" href="./learn.html"><div class="e-ico">📚</div><div class="e-title">知识卡</div>'
        '<div class="e-meta">12 张 · 每张 ≤5 分钟</div></a>'
        '<a class="entry" href="./quiz.html"><div class="e-ico">✏️</div><div class="e-title">快速自测</div>'
        '<div class="e-meta">21 题 · 即答即反馈</div></a>'
        '<a class="entry" href="./cases.html"><div class="e-ico">🗂</div><div class="e-title">案例拆解</div>'
        '<div class="e-meta">2 个 · 通勤版摘要</div></a>'
        '<a class="entry" href="./progress.html"><div class="e-ico">📈</div><div class="e-title">进度</div>'
        '<div class="e-meta">打卡 · 掌握度</div></a>'
        "</div>"
        '<div class="card"><h2>数据同步</h2>'
        '<p class="muted" style="font-size:12px">答题与打卡保存在本机；导出文件后可合并回本地跟踪。</p>'
        '<p style="margin-top:10px"><button id="export-sync" class="btn ghost">导出同步文件</button></p></div>'
        '<footer class="hint">AI-PM · 通勤学习助手</footer>'
    )
    index_js = f'window.PLAN_TASKS = {json.dumps(plan_tasks, ensure_ascii=False)};'
    (out / "index.html").write_text(_page("AI-PM", "index", index_body, index_js), encoding="utf-8")

    # ---- learn.html（知识卡列表）----
    card_items = []
    for md in sorted((data / "content" / "knowledge_cards").glob("*.md")):
        meta, body = _front_matter(md.read_text(encoding="utf-8"))
        title = _card_title(body) or meta.get("capability_id", md.stem)
        cap = meta.get("capability_id", "")
        cap_label = cap_names_dict.get(cap, "")
        card_items.append(
            f'<a class="task" href="./cards/{meta["id"]}.html">'
            f'<span class="t-ico">📄</span>'
            f'<span class="t-main"><span class="t-title">{title}</span>'
            f'<span class="t-meta">{cap_label} · 约 {meta.get("minutes", 4)} 分钟</span></span>'
            '<span class="t-arrow">›</span></a>')
    learn_body = (
        '<header class="top"><h1>知识卡</h1>'
        '<p class="sub">碎片时间输入 · 每张 ≤5 分钟</p></header>'
        '<div class="card" id="card-list">' + "".join(card_items) + "</div>"
        '<footer class="hint">已读卡片会在进度页统计</footer>'
    )
    learn_js = f'window.CAPABILITY_NAMES = {cap_names};'
    (out / "learn.html").write_text(_page("知识卡", "learn", learn_body, learn_js), encoding="utf-8")

    # ---- cards/<id>.html（知识卡详情）----
    for md in sorted((data / "content" / "knowledge_cards").glob("*.md")):
        meta, body = _front_matter(md.read_text(encoding="utf-8"))
        title = _card_title(body) or meta.get("capability_id", md.stem)
        cap_label = cap_names_dict.get(meta.get("capability_id", ""), "")
        card_html = (
            '<header class="top"><h1>知识卡</h1>'
            f'<p class="sub">{cap_label} · 约 {meta.get("minutes", 4)} 分钟</p></header>'
            f'<div class="card prose">{_md_to_html(body)}</div>'
            '<p style="margin-top:14px;text-align:center"><a class="btn ghost" href="../learn.html">← 返回知识卡</a></p>'
        )
        card_js = f'window.CARD_ID = "{meta["id"]}";'
        (out / "cards" / f'{meta["id"]}.html').write_text(
            _page(title, "learn", card_html, card_js), encoding="utf-8")

    # ---- quiz.html（按能力分组 + 过滤）----
    quiz_body = (
        '<header class="top"><h1>快速自测</h1>'
        '<p class="sub">选择答案后提交，即时查看反馈</p></header>'
        '<div class="filters" id="filters"><span class="chip on" data-cap="">全部</span></div>'
        '<div class="card" id="quiz-root"></div>'
        '<p style="margin-top:14px;text-align:center">'
        '<button id="submit-quiz" class="btn">提交并查看反馈</button></p>'
        '<p style="margin-top:10px;text-align:center"><button id="export-sync" class="btn ghost">导出同步文件</button></p>'
    )
    quiz_js = (f'window.QUIZ_BANK = {json.dumps(bank, ensure_ascii=False)};'
               f'window.CAPABILITY_NAMES = {cap_names};')
    (out / "quiz.html").write_text(_page("快速自测", "quiz", quiz_body, quiz_js), encoding="utf-8")

    # ---- cases.html + cases/<id>.html ----
    case_links = []
    for c in cases:
        caps = " · ".join(cap_names_dict.get(cid, cid) for cid in c.get("capability_ids", []))
        case_links.append(
            f'<a class="task" href="./cases/{c["id"]}.html">'
            '<span class="t-ico">🗂</span>'
            f'<span class="t-main"><span class="t-title">{c.get("title", c["id"])}</span>'
            f'<span class="t-meta">{caps}</span></span>'
            '<span class="t-arrow">›</span></a>')
    cases_body = (
        '<header class="top"><h1>案例拆解</h1>'
        '<p class="sub">通勤版摘要 · 5 分钟读完一个案例</p></header>'
        '<div class="card">' + "".join(case_links) + "</div>"
    )
    cases_js = f'window.CAPABILITY_NAMES = {cap_names};'
    (out / "cases.html").write_text(_page("案例拆解", "cases", cases_body, cases_js), encoding="utf-8")
    for c in cases:
        caps = "".join(f'<span class="chip">{cap_names_dict.get(cid, cid)}</span>' for cid in c.get("capability_ids", []))
        tips = "".join(f"<li>{kw}</li>" for kw in c["rubric"].get("checklist", []))
        body = (
            '<header class="top"><h1>案例拆解</h1>'
            f'<p class="sub">{c.get("title", c["id"])}</p></header>'
            f'<div class="card" style="margin-top:12px">{caps}</div>'
            f'<div class="card prose"><h2>通勤版摘要</h2>{_md_to_html(c.get("summary", ""))}</div>'
            f'<div class="card prose"><h2>面试问题</h2><p>{c["question"]}</p></div>'
            f'<div class="card prose"><h2>答题提示</h2><ul>{tips}</ul></div>'
            '<p style="margin-top:14px;text-align:center"><a class="btn ghost" href="./cases.html">← 返回案例列表</a></p>'
        )
        (out / "cases" / f'{c["id"]}.html').write_text(_page("案例拆解", "cases", body, cases_js), encoding="utf-8")

    # ---- progress.html（客户端从 localStorage 计算）----
    progress_body = (
        '<header class="top"><h1>学习进度</h1>'
        '<p class="sub" id="prog-day"></p></header>'
        '<div class="stat-row">'
        '<div class="stat"><div class="v" id="stat-checkin">-</div><div class="k">今日打卡</div></div>'
        '<div class="stat"><div class="v" id="stat-7d">-</div><div class="k">近 7 天完成率</div></div>'
        '<div class="stat"><div class="v" id="stat-streak">-</div><div class="k">连续打卡</div></div>'
        "</div>"
        '<div class="stat-row">'
        '<div class="stat"><div class="v" id="stat-tasks">-</div><div class="k">今日任务</div></div>'
        '<div class="stat"><div class="v" id="stat-cards">-</div><div class="k">已读卡片</div></div>'
        '<div class="stat"><div class="v" id="stat-quiz">-</div><div class="k">已答题目</div></div>'
        "</div>"
        '<div class="card"><h2>说明</h2>'
        '<p class="muted" style="font-size:12px">数据保存在浏览器 localStorage，'
        '通过「导出同步文件」可合并回本地跟踪（data/tracking/）。</p></div>'
    )
    progress_js = (f'window.PLAN_TASKS = {json.dumps(plan_tasks, ensure_ascii=False)};'
                   f"window.CARD_COUNT = {len(list((data / 'content' / 'knowledge_cards').glob('*.md')))};"
                   f"window.QUIZ_COUNT = {len(bank)};" + baseline_js)
    (out / "progress.html").write_text(_page("学习进度", "progress", progress_body, progress_js), encoding="utf-8")

    # ---- outputs.html（输出物工作台：PRD/案例拆解/答案卡）----
    templates = {}
    for name in ("prd", "case_analysis", "answer_card"):
        tp = data / "content" / "output_templates" / f"{name}.md"
        templates[name] = tp.read_text(encoding="utf-8") if tp.exists() else ""
    outputs_body = (
        '<header class="top"><h1>输出物工作台</h1>'
        '<p class="sub">PRD · 案例拆解 · 答案卡 — 深度任务在桌面完成</p></header>'
        '<div class="card"><h2>选择模板</h2>'
        '<div class="filters" id="tmpl-filters">'
        '<span class="chip on" data-tmpl="prd">PRD</span>'
        '<span class="chip" data-tmpl="case_analysis">案例拆解</span>'
        '<span class="chip" data-tmpl="answer_card">答案卡</span>'
        "</div>"
        '<h2 style="margin-top:12px">编辑</h2>'
        '<textarea id="output-editor" rows="14" placeholder="选择模板后开始写作…"></textarea>'
        '<div class="btn-row">'
        '<button id="save-output" class="btn">保存</button>'
        '<button id="download-output" class="btn ghost">下载 .md</button>'
        '<button id="new-output" class="btn ghost">清空新建</button>'
        "</div></div>"
        '<div class="card"><h2>已保存（<span id="artifact-count">0</span>）</h2>'
        '<div id="artifact-list"></div></div>'
    )
    outputs_js = "window.OUTPUT_TEMPLATES = " + json.dumps(templates, ensure_ascii=False) + ";"
    (out / "outputs.html").write_text(_page("输出物工作台", "outputs", outputs_body, outputs_js), encoding="utf-8")

    # ---- project.html（GitHub 项目拆解工作台）----
    proj_tmpl = (data / "content" / "github_project_template.md").read_text(encoding="utf-8")
    project_body = (
        '<header class="top"><h1>GitHub 项目拆解</h1>'
        '<p class="sub">目标 / 架构 / tradeoff / 产品化启示 / 面试题</p></header>'
        '<div class="card"><h2>编辑</h2>'
        '<textarea id="project-editor" rows="16" placeholder="选择模板开始拆解…"></textarea>'
        '<div class="btn-row">'
        '<button id="save-project" class="btn">保存</button>'
        '<button id="download-project" class="btn ghost">下载 .md</button>'
        "</div></div>"
        '<div class="card"><h2>已保存（<span id="project-count">0</span>）</h2>'
        '<div id="project-list"></div></div>'
    )
    project_js = "window.PROJECT_TEMPLATE = " + json.dumps(proj_tmpl, ensure_ascii=False) + ";"
    (out / "project.html").write_text(_page("项目拆解", "project", project_body, project_js), encoding="utf-8")

    # ---- mock.html（模拟面试）----
    mock_body = (
        '<header class="top"><h1>模拟面试</h1>'
        '<p class="sub">行为面 · 案例面 · 技术面 — 自评打分并沉淀素材</p></header>'
        '<div class="filters" id="mock-filters">'
        '<span class="chip on" data-sec="behavioral">行为面</span>'
        '<span class="chip" data-sec="case">案例面</span>'
        '<span class="chip" data-sec="technical">技术面</span>'
        "</div>"
        '<div id="mock-root"></div>'
        '<p style="margin-top:14px;text-align:center"><button id="mock-score" class="btn">自评并保存</button></p>'
        '<div class="card"><h2>历史成绩（<span id="mock-count">0</span>）</h2>'
        '<div id="mock-history"></div></div>'
    )
    mock_js = "window.MOCK_QUESTIONS = " + json.dumps(mocks, ensure_ascii=False) + ";"
    (out / "mock.html").write_text(_page("模拟面试", "mock", mock_body, mock_js), encoding="utf-8")

    # ---- review.html（周复盘）----
    review_body = (
        '<header class="top"><h1>周复盘</h1><p class="sub" id="rev-day"></p></header>'
        '<div class="stat-row">'
        '<div class="stat"><div class="v" id="rev-rate">-</div><div class="k">本周完成率</div></div>'
        '<div class="stat"><div class="v" id="rev-streak">-</div><div class="k">连续打卡</div></div>'
        '<div class="stat"><div class="v" id="rev-art">-</div><div class="k">输出物</div></div>'
        "</div>"
        '<div class="stat-row">'
        '<div class="stat"><div class="v" id="rev-quiz">-</div><div class="k">已答题目</div></div>'
        '<div class="stat"><div class="v" id="rev-mock">-</div><div class="k">面试均分</div></div>'
        '<div class="stat"><div class="v" id="rev-cards">-</div><div class="k">已读卡片</div></div>'
        "</div>"
        '<div class="card"><h2>能力雷达（基线）</h2>'
        '<div id="radar"></div><div id="radar-gaps"></div>'
        '<p class="muted" style="font-size:12px;margin-top:6px">来自 data/assessments/baseline.json（构建时嵌入）</p></div>'
        '<div class="card"><h2>导入本地跟踪数据（可选）</h2>'
        '<textarea id="tracking-paste" rows="6" placeholder="粘贴 data/tracking/checkins.jsonl 的内容…"></textarea>'
        '<div class="btn-row"><button id="apply-tracking" class="btn ghost">合并计算</button></div></div>'
        '<div class="card"><h2>周报文本</h2><pre id="review-text"></pre>'
        '<div class="btn-row"><button id="copy-review" class="btn">复制周报</button></div></div>'
    )
    review_js = (f'window.PLAN_TASKS = {json.dumps(plan_tasks, ensure_ascii=False)};'
                 f"window.QUIZ_COUNT = {len(bank)};" + baseline_js)
    (out / "review.html").write_text(_page("周复盘", "review", review_body, review_js), encoding="utf-8")

    (out / "manifest.webmanifest").write_text(json.dumps({
        "name": "AI-PM", "short_name": "AI-PM", "start_url": "./index.html",
        "display": "standalone", "background_color": "#f6f7fb",
        "theme_color": "#f6f7fb", "icons": []}, ensure_ascii=False), encoding="utf-8")

    sw_assets = ["./", "./index.html", "./learn.html", "./quiz.html", "./cases.html",
                 "./outputs.html", "./project.html", "./mock.html", "./review.html",
                 "./progress.html", "./manifest.webmanifest", "./assets/app.js", "./assets/style.css"]
    sw = ("const CACHE = \"ai-pm-v2\";\n"
          f"const ASSETS = {json.dumps(sw_assets)};\n"
          'self.addEventListener("install", e => {\n'
          "  e.waitUntil(caches.open(CACHE).then(c => c.addAll(ASSETS)));\n"
          "  self.skipWaiting();\n"
          "});\n"
          'self.addEventListener("activate", e => {\n'
          "  e.waitUntil(caches.keys().then(keys => Promise.all(keys.filter(k => k !== CACHE).map(k => caches.delete(k)))));\n"
          "});\n"
          'self.addEventListener("fetch", e => {\n'
          "  e.respondWith(caches.match(e.request).then(r => r || fetch(e.request)));\n"
          "});\n")
    (out / "sw.js").write_text(sw, encoding="utf-8")
    shutil.copyfile(Path(__file__).parent / "assets" / "app.js", out / "assets" / "app.js")
    return sorted(str(p.relative_to(out)) for p in out.rglob("*") if p.is_file())
