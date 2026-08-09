(function () {
  "use strict";
  var KEY = "ai-pm-local";

  function load() {
    try { return JSON.parse(localStorage.getItem(KEY) || "{}"); }
    catch (e) { return {}; }
  }
  function save(state) { localStorage.setItem(KEY, JSON.stringify(state)); }
  function todayISO() { return new Date().toISOString().slice(0, 10); }
  function capName(id) {
    return (window.CAPABILITY_NAMES && window.CAPABILITY_NAMES[id]) || id || "";
  }

  function exportSync() {
    var state = load();
    var payload = {
      version: 1,
      device: "mobile",
      exported_at: new Date().toISOString(),
      quiz_answers: state.quiz_answers || [],
      checkins: state.checkins || []
    };
    var blob = new Blob([JSON.stringify(payload, null, 2)], { type: "application/json" });
    var a = document.createElement("a");
    a.href = URL.createObjectURL(blob);
    a.download = "ai-pm-sync.json";
    a.click();
    URL.revokeObjectURL(a.href);
  }

  function tasksPayload(state) {
    var out = [];
    var tasks = state.tasks || {};
    Object.keys(tasks).forEach(function (date) {
      Object.keys(tasks[date]).forEach(function (taskId) {
        out.push({ date: date, task_id: taskId, done: !!tasks[date][taskId] });
      });
    });
    return out;
  }

  function readCardsPayload(state) {
    return Object.keys(state.read_cards || {}).map(function (cid) {
      return { card_id: cid, read_at: todayISO() };
    });
  }

  function cloudPush() {
    var state = load();
    var payload = {
      checkins: (state.checkins || []).map(function (d) {
        return { date: d, task_ids: [], minutes: 60 };
      }),
      quiz_answers: state.quiz_answers || [],
      artifacts: (state.artifacts || []).map(function (a) {
        return { id: String(a.id), type: a.type, title: a.title,
                 content: a.content, updated_at: a.updated_at };
      }),
      mocks: (state.mocks || []).map(function (m) {
        return { id: m.question_id + "-" + m.date, date: m.date, section: m.section,
                 question_id: m.question_id, score: m.score, covered: m.covered,
                 total: m.total };
      }),
      topic_progress: Object.keys(state.topic_progress || {}).map(function (tid) {
        return { topic_id: tid, data: state.topic_progress[tid] };
      }),
      tasks: tasksPayload(state),
      read_cards: readCardsPayload(state),
      _delete: state._deleted || {}
    };
    return fetch("/api/sync", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    }).then(function (r) { return r.json(); });
  }

  function cloudPull() {
    return fetch("/api/sync")
      .then(function (r) { return r.json(); })
      .then(function (data) {
        var state = load();
        state.checkins = state.checkins || [];
        state.quiz_answers = state.quiz_answers || [];
        state.artifacts = state.artifacts || [];
        state.mocks = state.mocks || [];
        state.topic_progress = state.topic_progress || {};
        state.tasks = state.tasks || {};
        state.read_cards = state.read_cards || {};
        state._deleted = { artifacts: [], mocks: [] };
        (data.checkins || []).forEach(function (c) {
          if (state.checkins.indexOf(c.date) === -1) { state.checkins.push(c.date); }
        });
        var quizKeys = {};
        state.quiz_answers.forEach(function (a) { quizKeys[a.date + "|" + a.quiz_id] = 1; });
        (data.quiz_answers || []).forEach(function (a) {
          var k = a.date + "|" + a.quiz_id;
          if (!quizKeys[k]) { state.quiz_answers.push(a); quizKeys[k] = 1; }
        });
        state.artifacts = (data.artifacts || []).map(function (a) {
          return { id: a.id, type: a.type, title: a.title,
                   content: a.content, updated_at: a.updated_at };
        });
        state.mocks = (data.mocks || []).map(function (m) {
          return { date: m.date, section: m.section, question_id: m.question_id,
                   score: Number(m.score), covered: m.covered, total: m.total };
        });
        (data.topic_progress || []).forEach(function (tp) {
          if (tp && tp.topic_id) { state.topic_progress[tp.topic_id] = tp.data || {}; }
        });
        state.tasks = {};
        (data.tasks || []).forEach(function (t) {
          state.tasks[t.date] = state.tasks[t.date] || {};
          state.tasks[t.date][t.task_id] = !!t.done;
        });
        state.read_cards = {};
        (data.read_cards || []).forEach(function (r) {
          state.read_cards[r.card_id] = true;
        });
        save(state);
        return state;
      });
  }

  var _syncTimer = null;
  function queueSync() {
    if (_syncTimer) { clearTimeout(_syncTimer); }
    _syncTimer = setTimeout(function () {
      _syncTimer = null;
      cloudPush().then(function (r) {
        if (r && r.deleted) {
          var state = load();
          state._deleted = { artifacts: [], mocks: [] };
          save(state);
        }
      }).catch(function () { /* 离线时静默，下次再同步 */ });
    }, 500);
  }

  function renderCloudSync() {
    var btn = document.getElementById("cloud-sync");
    if (!btn) { return; }
    btn.onclick = function () {
      btn.disabled = true;
      btn.textContent = "同步中…";
      cloudPush().then(function (r) {
        var saved = (r && r.saved) || {};
        if (r && r.deleted) {
          var st = load();
          st._deleted = { artifacts: [], mocks: [] };
          save(st);
        }
        btn.textContent = "已同步 ✓";
        setTimeout(function () {
          btn.textContent = "☁ 云端同步";
          btn.disabled = false;
        }, 2000);
        alert("已保存到云端：" +
          "打卡 " + (saved.checkins || 0) + "、答题 " + (saved.quiz_answers || 0) +
          "、输出物 " + (saved.artifacts || 0) + "、面试 " + (saved.mocks || 0));
      }).catch(function () {
        btn.textContent = "同步失败";
        btn.disabled = false;
        setTimeout(function () { btn.textContent = "☁ 云端同步"; }, 2000);
      });
    };
  }

  function renderCheckin() {
    var btn = document.getElementById("checkin-btn");
    if (!btn) { return; }
    var state = load();
    state.checkins = state.checkins || [];
    var today = todayISO();
    function markDone() {
      btn.textContent = "已打卡 ✓";
      btn.disabled = true;
    }
    btn.onclick = function () {
      if (state.checkins.indexOf(today) === -1) { state.checkins.push(today); }
      save(state);
      queueSync();
      markDone();
    };
    if (state.checkins.indexOf(today) !== -1) { markDone(); }
  }

  var TASK_ICON = { input: "📖", practice: "✏️", case: "🗂", output: "📝",
                    project: "🛠", mock: "🎤", review: "🔁" };
  var DESKTOP_TYPES = { output: 1, project: 1, mock: 1, review: 1 };

  function taskLink(t) {
    var cap0 = (t.capability_ids || [])[0] || "";
    var desktop = window.innerWidth >= 900;
    if (t.type === "input") { return "/cards/" + cap0 + ".html"; }
    if (t.type === "practice") { return "/quiz.html#cap-" + cap0; }
    if (t.type === "case") { return "/cases.html"; }
    if (desktop && t.type === "output") { return "/outputs.html"; }
    if (desktop && t.type === "project") { return "/project.html"; }
    if (desktop && t.type === "mock") { return "/mock.html"; }
    if (desktop && t.type === "review") { return "/review.html"; }
    return null;
  }
  function taskTitle(t) {
    if (t.type === "input") { return "阅读：" + capName((t.capability_ids || [])[0]); }
    if (t.type === "practice") { return "练习：" + (t.capability_ids || []).map(capName).join(" / "); }
    if (t.type === "case") { return "案例拆解"; }
    if (t.type === "output") { return "输出：答案卡"; }
    if (t.type === "project") { return "GitHub 项目拆解"; }
    if (t.type === "mock") { return "模拟面试"; }
    if (t.type === "review") { return "周复盘"; }
    return t.type;
  }

  function renderIndex() {
    var root = document.getElementById("task-list");
    if (!root || !window.PLAN_TASKS) { return; }
    root.innerHTML = "";
    var today = todayISO();
    var keys = Object.keys(window.PLAN_TASKS).sort();
    var pick = window.PLAN_TASKS[today] ? today : null;
    var label = "今日任务";
    var subText = today;
    if (!pick) {
      var next = keys.filter(function (k) { return k > today; })[0];
      pick = next || keys[0];
      label = next ? "开营预览（明日任务）" : "学习任务";
      subText = "今天是 " + today + " · " + pick + " 开营";
    } else {
      subText = today + " · Day " + (keys.indexOf(today) + 1);
    }
    var sub = document.getElementById("day-sub");
    if (sub) { sub.textContent = subText; }
    var head = document.getElementById("task-head");
    if (head) { head.textContent = label; }

    var state = load();
    state.tasks = state.tasks || {};
    var done = state.tasks[pick] || {};
    (window.PLAN_TASKS[pick] || []).forEach(function (t) {
      var link = taskLink(t);
      var li = document.createElement("div");
      li.className = "task";
      li.innerHTML =
        '<input type="checkbox" class="check" data-task="' + t.id + '"' + (done[t.id] ? " checked" : "") + ">" +
        '<span class="t-ico">' + (TASK_ICON[t.type] || "•") + "</span>" +
        '<span class="t-main"><span class="t-title">' + taskTitle(t) + "</span>" +
        '<span class="t-meta">' + t.type + " · " + t.duration_min + " 分钟</span></span>" +
        (link ? '<a class="t-arrow" href="' + link + '">›</a>' : '<span class="chip desk">桌面端</span>');
      var cb = li.querySelector("input");
      cb.addEventListener("change", function () {
        state.tasks = state.tasks || {};
        state.tasks[pick] = state.tasks[pick] || {};
        state.tasks[pick][t.id] = cb.checked;
        save(state);
        queueSync();
      });
      root.appendChild(li);
    });
    if (!(window.PLAN_TASKS[pick] || []).length) {
      root.innerHTML = '<p class="muted" style="padding:8px 0">今天没有计划任务，休息一下。</p>';
    }
  }

  function renderQuiz() {
    var root = document.getElementById("quiz-root");
    var submit = document.getElementById("submit-quiz");
    var filters = document.getElementById("filters");
    if (!root || !submit || !window.QUIZ_BANK) { return; }
    root.innerHTML = "";
    var state = load();
    state.quiz_answers = state.quiz_answers || [];
    var done = {};
    state.quiz_answers.forEach(function (a) { done[a.quiz_id] = true; });

    var chips = {};
    filters.querySelectorAll(".chip[data-cap]").forEach(function (chip) {
      chips[chip.dataset.cap] = chip;
      if (!window.__quizChipsBound) {
        chip.addEventListener("click", function () {
          setFilter(chip.dataset.cap || "", chip);
        });
      }
    });
    window.__quizChipsBound = true;
    function setFilter(c, chip) {
      var allChips = filters.querySelectorAll(".chip");
      allChips.forEach(function (x) { x.classList.remove("on"); });
      chip.classList.add("on");
      root.querySelectorAll(".quiz-group").forEach(function (sec) {
        sec.style.display = (!c || sec.dataset.cap === c) ? "" : "none";
      });
    }

    var groups = {};
    window.QUIZ_BANK.forEach(function (q) {
      (groups[q.capability_id] = groups[q.capability_id] || []).push(q);
    });
    Object.keys(groups).forEach(function (c) {
      var sec = document.createElement("section");
      sec.className = "quiz-group";
      sec.dataset.cap = c;
      var h = document.createElement("h2");
      h.textContent = capName(c);
      sec.appendChild(h);
      groups[c].forEach(function (q, idx) {
        var div = document.createElement("div");
        div.className = "card";
        div.style.marginTop = "10px";
        div.dataset.qid = q.id;
        var html = "<p style=\"font-weight:620\">" + (idx + 1) + ". " + q.question + "</p>";
        q.options.forEach(function (opt) {
          html += '<label class="opt"><input type="radio" name="q-' + q.id + '" value="' + opt[0] + '"> ' + opt + "</label>";
        });
        div.innerHTML = html;
        sec.appendChild(div);
      });
      root.appendChild(sec);
    });

    submit.onclick = function () {
      window.QUIZ_BANK.forEach(function (q) {
        var card = root.querySelector('.card[data-qid="' + q.id + '"]');
        if (!card || done[q.id]) { return; }
        var sel = card.querySelector('input[name="q-' + q.id + '"]:checked');
        if (!sel) { return; }
        state.quiz_answers.push({ quiz_id: q.id, choice: sel.value, date: todayISO() });
        done[q.id] = true;
        card.querySelectorAll(".opt").forEach(function (label) {
          var inp = label.querySelector("input");
          if (inp.value === q.answer) { label.classList.add("correct"); }
          else if (inp.checked) { label.classList.add("wrong"); }
          inp.disabled = true;
        });
      });
      save(state);
      queueSync();
      alert("已保存本次答题，请记得导出同步文件。");
    };

    var hashCap = (location.hash || "").replace("#cap-", "");
    if (hashCap && chips[hashCap]) { setFilter(hashCap, chips[hashCap]); }
  }

  function markCardRead() {
    if (!window.CARD_ID) { return; }
    var state = load();
    state.read_cards = state.read_cards || {};
    state.read_cards[window.CARD_ID] = true;
    save(state);
    queueSync();
  }

  function renderProgress() {
    var ids = ["prog-day", "stat-checkin", "stat-7d", "stat-streak",
               "stat-tasks", "stat-cards", "stat-quiz"];
    var any = ids.some(function (id) { return document.getElementById(id); });
    if (!any) { return; }
    var state = load();
    state.checkins = state.checkins || [];
    state.tasks = state.tasks || {};
    state.quiz_answers = state.quiz_answers || [];
    state.read_cards = state.read_cards || {};
    var today = todayISO();
    var el = function (id) { return document.getElementById(id); };
    if (el("prog-day")) { el("prog-day").textContent = "数据截止 " + today; }
    if (el("stat-checkin")) {
      el("stat-checkin").textContent = state.checkins.indexOf(today) !== -1 ? "✓" : "—";
    }
    var days = [];
    for (var i = 0; i < 7; i++) {
      var d = new Date();
      d.setDate(d.getDate() - i);
      days.push(d.toISOString().slice(0, 10));
    }
    var hit7 = days.filter(function (d) { return state.checkins.indexOf(d) !== -1; }).length;
    if (el("stat-7d")) { el("stat-7d").textContent = hit7 + "/7"; }
    var sorted = state.checkins.slice().sort();
    var streak = 0;
    if (sorted.length) {
      var cur = new Date(sorted[sorted.length - 1] + "T00:00:00");
      while (state.checkins.indexOf(cur.toISOString().slice(0, 10)) !== -1) {
        streak += 1;
        cur.setDate(cur.getDate() - 1);
      }
    }
    if (el("stat-streak")) { el("stat-streak").textContent = streak + " 天"; }
    var tasks = (window.PLAN_TASKS && window.PLAN_TASKS[today]) || [];
    var doneTasks = tasks.filter(function (t) {
      return state.tasks[today] && state.tasks[today][t.id];
    }).length;
    if (el("stat-tasks")) {
      el("stat-tasks").textContent = tasks.length ? doneTasks + "/" + tasks.length : "—";
    }
    if (el("stat-cards")) {
      var cardTotal = window.CARD_COUNT || 0;
      el("stat-cards").textContent = Object.keys(state.read_cards).length + "/" + cardTotal;
    }
    if (el("stat-quiz")) {
      el("stat-quiz").textContent = state.quiz_answers.length + "/" + (window.QUIZ_COUNT || 0);
    }
  }

  function escapeHtml(s) {
    return String(s).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
  }
  function mdToHtml(md) {
    var out = [];
    (md || "").split("\n").forEach(function (line) {
      var s = line.trim();
      if (!s) { return; }
      var m = s.match(/^(#{1,4})\s+(.*)$/);
      if (m) {
        var lv = m[1].length;
        out.push("<h" + lv + ">" + escapeHtml(m[2]) + "</h" + lv + ">");
      } else if (s.indexOf("- ") === 0) {
        out.push("<li>" + escapeHtml(s.slice(2)) + "</li>");
      } else if (s.indexOf("**") === 0 && s.lastIndexOf("**") === s.length - 2) {
        out.push("<p><strong>" + escapeHtml(s.slice(2, -2)) + "</strong></p>");
      } else {
        out.push("<p>" + escapeHtml(s) + "</p>");
      }
    });
    return out.join("");
  }

  function renderOutputs() {
    var editor = document.getElementById("output-editor");
    if (!editor) { return; }
    var state = load();
    state.artifacts = state.artifacts || [];
    var currentType = "prd";
    var filters = document.getElementById("tmpl-filters");
    if (filters) {
      filters.querySelectorAll(".chip").forEach(function (chip) {
        chip.addEventListener("click", function () {
          filters.querySelectorAll(".chip").forEach(function (x) { x.classList.remove("on"); });
          chip.classList.add("on");
          currentType = chip.dataset.tmpl;
          if (window.OUTPUT_TEMPLATES) { editor.value = window.OUTPUT_TEMPLATES[currentType] || ""; }
        });
      });
    }
    function titleOf(content) {
      var m = (content || "").match(/^#\s+(.+)$/m);
      return m ? m[1].trim() : currentType;
    }
    function renderList() {
      var list = document.getElementById("artifact-list");
      var count = document.getElementById("artifact-count");
      if (!list) { return; }
      var items = state.artifacts.filter(function (a) {
        return a.type !== "project";
      });
      if (count) { count.textContent = items.length; }
      list.innerHTML = items.map(function (a) {
        return '<div class="task">' +
          '<span class="t-ico">📝</span>' +
          '<span class="t-main"><span class="t-title">' + escapeHtml(a.title) + "</span>" +
          '<span class="t-meta">' + a.type + " · " + a.updated_at + "</span></span>" +
          '<button class="btn ghost" data-load="' + a.id + '" style="padding:6px 12px;font-size:12px">打开</button>' +
          '<button class="btn ghost" data-del="' + a.id + '" style="padding:6px 12px;font-size:12px">删除</button>' +
          "</div>";
      }).join("") || '<p class="muted" style="padding:8px 0">还没有输出物，写一份 PRD 开始吧。</p>';
      list.querySelectorAll("[data-load]").forEach(function (btn) {
        btn.addEventListener("click", function () {
          var a = state.artifacts.find(function (x) { return String(x.id) === btn.dataset.load; });
          if (a) { editor.value = a.content; }
        });
      });
      list.querySelectorAll("[data-del]").forEach(function (btn) {
        btn.addEventListener("click", function () {
          state.artifacts = state.artifacts.filter(function (x) { return String(x.id) !== btn.dataset.del; });
          state._deleted = state._deleted || { artifacts: [], mocks: [] };
          state._deleted.artifacts.push(String(btn.dataset.del));
          save(state);
          queueSync();
          renderList();
        });
      });
    }
    document.getElementById("save-output").onclick = function () {
      if (!editor.value.trim()) { alert("内容为空"); return; }
      state.artifacts.push({ id: Date.now(), type: currentType,
                             title: titleOf(editor.value), content: editor.value,
                             updated_at: todayISO() });
      save(state);
      queueSync();
      renderList();
      alert("已保存");
    };
    var dl = document.getElementById("download-output");
    if (dl) {
      dl.onclick = function () {
        if (!editor.value.trim()) { alert("内容为空"); return; }
        var blob = new Blob([editor.value], { type: "text/markdown" });
        var a = document.createElement("a");
        a.href = URL.createObjectURL(blob);
        a.download = titleOf(editor.value) + ".md";
        a.click();
        URL.revokeObjectURL(a.href);
      };
    }
    var neu = document.getElementById("new-output");
    if (neu) { neu.onclick = function () { editor.value = ""; }; }
    if (window.OUTPUT_TEMPLATES) { editor.value = window.OUTPUT_TEMPLATES.prd || ""; }
    renderList();
  }

  function renderProject() {
    var editor = document.getElementById("project-editor");
    if (!editor) { return; }
    var state = load();
    state.artifacts = state.artifacts || [];
    if (window.PROJECT_TEMPLATE) { editor.value = window.PROJECT_TEMPLATE; }
    function renderList() {
      var list = document.getElementById("project-list");
      var count = document.getElementById("project-count");
      var items = state.artifacts.filter(function (a) { return a.type === "project"; });
      if (count) { count.textContent = items.length; }
      list.innerHTML = items.map(function (a) {
        return '<div class="task"><span class="t-ico">🛠</span>' +
          '<span class="t-main"><span class="t-title">' + escapeHtml(a.title) + "</span>" +
          '<span class="t-meta">' + a.updated_at + "</span></span>" +
          '<button class="btn ghost" data-load="' + a.id + '" style="padding:6px 12px;font-size:12px">打开</button>' +
          '<button class="btn ghost" data-del="' + a.id + '" style="padding:6px 12px;font-size:12px">删除</button>' +
          "</div>";
      }).join("") || '<p class="muted" style="padding:8px 0">还没有拆解记录。</p>';
      list.querySelectorAll("[data-load]").forEach(function (btn) {
        btn.addEventListener("click", function () {
          var a = state.artifacts.find(function (x) { return String(x.id) === btn.dataset.load; });
          if (a) { editor.value = a.content; }
        });
      });
      list.querySelectorAll("[data-del]").forEach(function (btn) {
        btn.addEventListener("click", function () {
          state.artifacts = state.artifacts.filter(function (x) { return String(x.id) !== btn.dataset.del; });
          state._deleted = state._deleted || { artifacts: [], mocks: [] };
          state._deleted.artifacts.push(String(btn.dataset.del));
          save(state);
          queueSync();
          renderList();
        });
      });
    }
    document.getElementById("save-project").onclick = function () {
      if (!editor.value.trim()) { alert("内容为空"); return; }
      var m = editor.value.match(/^#\s+(.+)$/m);
      state.artifacts.push({ id: Date.now(), type: "project",
                             title: m ? m[1].trim() : "项目拆解", content: editor.value,
                             updated_at: todayISO() });
      save(state);
      queueSync();
      renderList();
      alert("已保存");
    };
    var dl = document.getElementById("download-project");
    if (dl) {
      dl.onclick = function () {
        var blob = new Blob([editor.value], { type: "text/markdown" });
        var a = document.createElement("a");
        a.href = URL.createObjectURL(blob);
        a.download = "项目拆解.md";
        a.click();
        URL.revokeObjectURL(a.href);
      };
    }
    renderList();
  }

  function renderMock() {
    var root = document.getElementById("mock-root");
    if (!root || !window.MOCK_QUESTIONS) { return; }
    var state = load();
    state.mocks = state.mocks || [];
    var section = "behavioral";
    var filters = document.getElementById("mock-filters");
    function render() {
      var qs = window.MOCK_QUESTIONS.filter(function (q) { return q.section === section; });
      root.innerHTML = qs.map(function (q, idx) {
        return '<div class="card" data-qid="' + q.id + '" style="margin-top:12px">' +
          "<h2>Q" + (idx + 1) + "</h2>" +
          '<p style="font-weight:620">' + escapeHtml(q.question) + "</p>" +
          '<textarea data-answer rows="5" placeholder="写下你的回答…" style="margin-top:8px"></textarea>' +
          '<p class="muted" style="font-size:12px;margin-top:6px">自评：回答覆盖了哪些要点？</p>' +
          q.checklist.map(function (kw) {
            return '<label style="display:block;margin:4px 0;font-size:13px">' +
              '<input type="checkbox" data-kw value="' + escapeHtml(kw) + '"> ' + escapeHtml(kw) + "</label>";
          }).join("") +
          '<p class="muted" data-score style="font-size:12px;margin-top:6px"></p></div>';
      }).join("") || '<p class="muted">该场次暂无题目。</p>';
    }
    filters.querySelectorAll(".chip").forEach(function (chip) {
      chip.addEventListener("click", function () {
        filters.querySelectorAll(".chip").forEach(function (x) { x.classList.remove("on"); });
        chip.classList.add("on");
        section = chip.dataset.sec;
        render();
      });
    });
    document.getElementById("mock-score").onclick = function () {
      var saved = 0;
      root.querySelectorAll(".card[data-qid]").forEach(function (card) {
        var qid = card.dataset.qid;
        var answer = card.querySelector("[data-answer]").value.trim();
        if (!answer) { return; }
        var kws = card.querySelectorAll("[data-kw]");
        var checked = 0;
        kws.forEach(function (k) { if (k.checked) { checked += 1; } });
        var total = kws.length || 1;
        var score = Math.round((1 + 4 * checked / total) * 100) / 100;
        state.mocks = state.mocks.filter(function (m) {
          return !(m.section === section && m.question_id === qid && m.date === todayISO());
        });
        state.mocks.push({ date: todayISO(), section: section, question_id: qid,
                           score: score, covered: checked, total: total });
        saved += 1;
        card.querySelector("[data-score]").textContent = "得分 " + score.toFixed(2) + "（覆盖 " + checked + "/" + total + "）";
      });
      save(state);
      queueSync();
      renderHistory();
      alert(saved ? "已保存 " + saved + " 道题的自评" : "请先填写回答");
    };
    function renderHistory() {
      var list = document.getElementById("mock-history");
      var count = document.getElementById("mock-count");
      if (!list) { return; }
      if (count) { count.textContent = state.mocks.length; }
      var names = { behavioral: "行为面", case: "案例面", technical: "技术面" };
      var html = "";
      ["behavioral", "case", "technical"].forEach(function (sec) {
        var rows = state.mocks.filter(function (m) { return m.section === sec; });
        if (!rows.length) { return; }
        var avg = rows.reduce(function (s, m) { return s + m.score; }, 0) / rows.length;
        html += '<p style="font-size:13px;margin:6px 0"><strong>' + names[sec] + "</strong> · " +
          rows.length + " 次 · 均分 " + avg.toFixed(2) + "</p>";
      });
      list.innerHTML = html || '<p class="muted">还没有模拟面试记录。</p>';
    }
    render();
    renderHistory();
  }

  function renderReview() {
    if (!document.getElementById("review-text")) { return; }
    var state = load();
    state.checkins = state.checkins || [];
    state.tasks = state.tasks || {};
    state.quiz_answers = state.quiz_answers || [];
    state.read_cards = state.read_cards || {};
    state.artifacts = state.artifacts || [];
    state.mocks = state.mocks || [];
    var today = todayISO();
    if (document.getElementById("rev-day")) {
      document.getElementById("rev-day").textContent = "数据截止 " + today;
    }
    var checkins = state.checkins.slice();
    var paste = document.getElementById("tracking-paste");
    if (paste && paste.value.trim()) {
      paste.value.trim().split("\n").forEach(function (line) {
        try {
          var rec = JSON.parse(line);
          if (rec && rec.date && checkins.indexOf(rec.date) === -1) { checkins.push(rec.date); }
        } catch (e) { /* 忽略坏行 */ }
      });
    }
    var days = [];
    for (var i = 0; i < 7; i++) {
      var d = new Date();
      d.setDate(d.getDate() - i);
      days.push(d.toISOString().slice(0, 10));
    }
    var hit = days.filter(function (d) { return checkins.indexOf(d) !== -1; }).length;
    var sorted = checkins.slice().sort();
    var streak = 0;
    if (sorted.length) {
      var cur = new Date(sorted[sorted.length - 1] + "T00:00:00");
      while (checkins.indexOf(cur.toISOString().slice(0, 10)) !== -1) {
        streak += 1;
        cur.setDate(cur.getDate() - 1);
      }
    }
    var artifacts = state.artifacts.length;
    var quiz = state.quiz_answers.length;
    var cards = Object.keys(state.read_cards).length;
    var mocks = state.mocks;
    var mockAvg = mocks.length
      ? (mocks.reduce(function (s, m) { return s + m.score; }, 0) / mocks.length).toFixed(2)
      : "—";
    document.getElementById("rev-rate").textContent = hit + "/7";
    document.getElementById("rev-streak").textContent = streak + " 天";
    document.getElementById("rev-art").textContent = artifacts;
    document.getElementById("rev-quiz").textContent = quiz + "/" + (window.QUIZ_COUNT || 0);
    document.getElementById("rev-mock").textContent = mockAvg;
    document.getElementById("rev-cards").textContent = cards + "/" + (window.CARD_COUNT || 0);

    var radar = (window.BASELINE && window.BASELINE.radar) || {};
    var names = { A: "AI 技术理解", B: "产品设计与体验", C: "数据与科学方法",
                  D: "战略与规划", E: "工程协作与工具", F: "软技能" };
    var radarHtml = Object.keys(names).map(function (k) {
      var v = radar[k] || 0;
      return '<p style="font-size:13px;margin:5px 0">' + names[k] +
        '<span style="float:right">L' + v + "</span></p>" +
        '<div style="background:var(--line);border-radius:6px;height:8px;overflow:hidden">' +
        '<div style="width:' + Math.min(v / 5 * 100, 100) + '%;height:100%;background:var(--accent)"></div></div>';
    }).join("");
    var radarEl = document.getElementById("radar");
    if (radarEl) { radarEl.innerHTML = radarHtml; }
    var gaps = (window.BASELINE && window.BASELINE.gaps) || [];
    var gapsEl = document.getElementById("radar-gaps");
    if (gapsEl) {
      gapsEl.innerHTML = '<h2 style="margin-top:12px">待补强</h2>' + gaps.slice(0, 5).map(function (g) {
        return '<p style="font-size:13px;margin:4px 0">· ' + escapeHtml(g.name) +
          "（L" + g.current_level + " → L" + g.target_level + "）</p>";
      }).join("") || '<p class="muted">暂无数据</p>';
    }
    function buildText() {
      return "# 周复盘 " + today + "\n" +
        "- 完成率：" + hit + "/7\n" +
        "- 连击：" + streak + " 天\n" +
        "- 输出物：" + artifacts + " 份\n" +
        "- 已答题目：" + quiz + "/" + (window.QUIZ_COUNT || 0) + "\n" +
        "- 已读卡片：" + cards + "/" + (window.CARD_COUNT || 0) + "\n" +
        "- 模拟面试均分：" + mockAvg + "\n" +
        "- 能力雷达：" + JSON.stringify(radar) + "\n" +
        "- 待补强：" + JSON.stringify(gaps.slice(0, 5)) + "\n";
    }
    var pre = document.getElementById("review-text");
    pre.textContent = buildText();
    var applyBtn = document.getElementById("apply-tracking");
    if (applyBtn) { applyBtn.onclick = function () { renderReview(); }; }
    var copyBtn = document.getElementById("copy-review");
    if (copyBtn) {
      copyBtn.onclick = function () {
        navigator.clipboard.writeText(pre.textContent).then(function () { alert("已复制周报"); });
      };
    }
  }

  function getTopicProgress() {
    var topic = window.TOPIC;
    if (!topic) { return {}; }
    var state = load();
    state.topic_progress = state.topic_progress || {};
    return state.topic_progress[topic.id] || { modules: {}, quiz_correct: 0, quiz_total: 0 };
  }

  function aiCall(action, question) {
    var topic = window.TOPIC || {};
    return fetch("/api/ai", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        action: action,
        question: question || "",
        topic_name: topic.name || "",
        topic_context: {
          reason: topic.reason || "",
          goals: topic.goals || [],
          modules: (topic.modules || []).map(function (m) { return m.title; }),
          progress: getTopicProgress()
        }
      })
    }).then(function (r) { return r.json(); }).then(function (d) {
      if (d.error) { throw new Error(d.error); }
      return d.text;
    });
  }

  function renderTopic() {
    var topic = window.TOPIC;
    if (!topic) { return; }
    var state = load();
    state.topic_progress = state.topic_progress || {};
    var prog = state.topic_progress[topic.id] ||
      { modules: {}, quiz_correct: 0, quiz_total: 0, summary: "" };
    var moduleTitles = (topic.modules || []).map(function (m) { return m.title; });
    function updateProgress() {
      var doneCount = moduleTitles.filter(function (t) { return prog.modules[t]; }).length;
      var el = document.getElementById("topic-progress");
      if (el) {
        el.textContent = "模块完成 " + doneCount + "/" + moduleTitles.length +
          " · 自测 " + prog.quiz_correct + "/" + prog.quiz_total;
      }
    }
    if (!window.__topicBound) {
      document.querySelectorAll("#topic-modules input[data-module]").forEach(function (box) {
        if (prog.modules[box.dataset.module]) { box.checked = true; }
        box.addEventListener("change", function () {
          prog.modules[box.dataset.module] = box.checked;
          state.topic_progress[topic.id] = prog;
          save(state);
          queueSync();
          updateProgress();
        });
      });
      window.__topicBound = true;
    }
    var submit = document.getElementById("topic-quiz-submit");
    if (submit) {
      submit.onclick = function () {
        var correct = 0, total = (topic.quiz || []).length, answered = 0;
        (topic.quiz || []).forEach(function (q, i) {
          var card = document.querySelectorAll("#topic-quiz .card")[i];
          if (!card) { return; }
          var sel = card.querySelector('input[name="tq-' + i + '"]:checked');
          var explain = card.querySelector("[data-explain]");
          if (!sel) { return; }
          answered += 1;
          card.querySelectorAll(".opt").forEach(function (label) {
            var inp = label.querySelector("input");
            if (inp.value === q.answer) { label.classList.add("correct"); }
            else if (inp.checked) { label.classList.add("wrong"); }
            inp.disabled = true;
          });
          if (sel.value === q.answer) { correct += 1; }
          if (explain) { explain.style.display = "block"; }
        });
        if (!answered) { alert("请先作答再提交"); return; }
        prog.quiz_correct = correct;
        prog.quiz_total = total;
        state.topic_progress[topic.id] = prog;
        save(state);
        queueSync();
        updateProgress();
        alert("答对 " + correct + "/" + total);
      };
    }
    var resultEl = document.getElementById("ai-result");
    function runAi(action, label, question) {
      if (resultEl) {
        resultEl.classList.add("show");
        resultEl.textContent = label + "…";
      }
      aiCall(action, question).then(function (text) {
        if (resultEl) { resultEl.textContent = text; }
        if (action === "summary") {
          prog.summary = text;
          state.topic_progress[topic.id] = prog;
          save(state);
          queueSync();
        }
      }).catch(function (e) {
        if (resultEl) { resultEl.textContent = "AI 请求失败：" + e.message; }
      });
    }
    var planBtn = document.getElementById("ai-plan");
    if (planBtn) { planBtn.onclick = function () { runAi("plan", "正在生成学习计划"); }; }
    var quizBtn = document.getElementById("ai-quiz");
    if (quizBtn) { quizBtn.onclick = function () { runAi("quiz", "正在出题"); }; }
    var sumBtn = document.getElementById("ai-summary");
    if (sumBtn) { sumBtn.onclick = function () { runAi("summary", "正在总结进度"); }; }
    var askBtn = document.getElementById("ai-ask");
    if (askBtn) {
      askBtn.onclick = function () {
        var q = document.getElementById("ai-question").value.trim();
        if (!q) { alert("请输入问题"); return; }
        runAi("ask", "正在回答", q);
      };
    }
    updateProgress();
  }

  var exp = document.getElementById("export-sync");
  if (exp) { exp.onclick = exportSync; }
  function renderAll() {
    renderCheckin();
    renderIndex();
    renderQuiz();
    renderProgress();
    renderOutputs();
    renderProject();
    renderMock();
    renderReview();
    renderTopic();
  }
  renderAll();
  markCardRead();
  renderCloudSync();
  cloudPull().then(function () {
    renderAll();
    return cloudPush();
  })
    .catch(function () { /* 本地环境无 API，静默 */ });
  if ("serviceWorker" in navigator) {
    navigator.serviceWorker.register("/sw.js").catch(function () { /* 静默 */ });
  }
})();
