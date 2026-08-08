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
      markDone();
    };
    if (state.checkins.indexOf(today) !== -1) { markDone(); }
  }

  var TASK_ICON = { input: "📖", practice: "✏️", case: "🗂", output: "📝",
                    project: "🛠", mock: "🎤", review: "🔁" };
  var DESKTOP_TYPES = { output: 1, project: 1, mock: 1, review: 1 };

  function taskLink(t) {
    var cap0 = (t.capability_ids || [])[0] || "";
    if (t.type === "input") { return "./cards/" + cap0 + ".html"; }
    if (t.type === "practice") { return "./quiz.html#cap-" + cap0; }
    if (t.type === "case") { return "./cases.html"; }
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
    var state = load();
    state.quiz_answers = state.quiz_answers || [];
    var done = {};
    state.quiz_answers.forEach(function (a) { done[a.quiz_id] = true; });

    var caps = [];
    window.QUIZ_BANK.forEach(function (q) {
      if (caps.indexOf(q.capability_id) === -1) { caps.push(q.capability_id); }
    });
    var chips = {};
    caps.forEach(function (c) {
      var chip = document.createElement("span");
      chip.className = "chip";
      chip.textContent = capName(c);
      chip.dataset.cap = c;
      chip.addEventListener("click", function () { setFilter(c, chip); });
      filters.appendChild(chip);
      chips[c] = chip;
    });
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

  var exp = document.getElementById("export-sync");
  if (exp) { exp.onclick = exportSync; }
  renderCheckin();
  renderIndex();
  renderQuiz();
  markCardRead();
  renderProgress();
})();
