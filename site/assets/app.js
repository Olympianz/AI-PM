(function () {
  "use strict";
  var KEY = "ai-pm-local";
  function load() {
    try { return JSON.parse(localStorage.getItem(KEY) || "{}"); }
    catch (e) { return {}; }
  }
  function save(state) { localStorage.setItem(KEY, JSON.stringify(state)); }
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
  function renderQuiz() {
    var root = document.getElementById("quiz-root");
    var submit = document.getElementById("submit-quiz");
    if (!root || !submit || !window.QUIZ_BANK) { return; }
    var state = load();
    state.quiz_answers = state.quiz_answers || [];
    var done = {};
    state.quiz_answers.forEach(function (a) { done[a.quiz_id] = true; });
    window.QUIZ_BANK.forEach(function (q, idx) {
      var div = document.createElement("div");
      div.className = "card";
      var html = "<h3>" + (idx + 1) + ". " + q.question + "</h3>";
      q.options.forEach(function (opt) {
        html += '<label><input type="radio" name="q-' + q.id + '" value="' + opt[0] + '"> ' + opt + "</label>";
      });
      div.innerHTML = html;
      root.appendChild(div);
    });
    submit.onclick = function () {
      window.QUIZ_BANK.forEach(function (q) {
        var sel = document.querySelector('input[name="q-' + q.id + '"]:checked');
        if (!sel || done[q.id]) { return; }
        state.quiz_answers.push({ quiz_id: q.id, choice: sel.value, date: new Date().toISOString().slice(0, 10) });
        done[q.id] = true;
        document.querySelectorAll('input[name="q-' + q.id + '"]').forEach(function (inp) {
          if (inp.value === q.answer) { inp.parentElement.classList.add("correct"); }
          else if (inp.checked) { inp.parentElement.classList.add("wrong"); }
          inp.disabled = true;
        });
      });
      save(state);
      alert("已保存本次答题，请记得导出同步文件。");
    };
  }
  function renderCheckin() {
    var btn = document.getElementById("checkin-btn");
    if (!btn) { return; }
    var state = load();
    state.checkins = state.checkins || [];
    var today = new Date().toISOString().slice(0, 10);
    function markDone() {
      btn.textContent = "今日已打卡 ✓";
      btn.disabled = true;
    }
    btn.onclick = function () {
      if (state.checkins.indexOf(today) === -1) { state.checkins.push(today); }
      save(state);
      markDone();
    };
    if (state.checkins.indexOf(today) !== -1) { markDone(); }
  }
  var exp = document.getElementById("export-sync");
  if (exp) { exp.onclick = exportSync; }
  renderQuiz();
  renderCheckin();
})();
